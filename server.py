#!/usr/bin/env python
"""Google Earth Engine python code for the SERVIR-Mekong Surface Water Tool"""

# This script handles the loading of the web application and its timeout settings,
# as well as the complete Earth Engine code for all the calculations.

import json
import os

import config
import ee
import jinja2
import webapp2

import socket

from google.appengine.api import urlfetch

# ------------------------------------------------------------------------------------ #
# Initialization
# ------------------------------------------------------------------------------------ #

# The URL fetch timeout time (seconds).
URL_FETCH_TIMEOUT = 60

# Create the Jinja templating system we use to dynamically generate HTML. See:
# http://jinja.pocoo.org/docs/dev/
JINJA2_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    autoescape=True,
    extensions=['jinja2.ext.autoescape'])

ee.Initialize(config.EE_CREDENTIALS)

ee.data.setDeadline(URL_FETCH_TIMEOUT)
socket.setdefaulttimeout(URL_FETCH_TIMEOUT)
urlfetch.set_default_fetch_deadline(URL_FETCH_TIMEOUT)

# ------------------------------------------------------------------------------------ #
# Web request handlers
# ------------------------------------------------------------------------------------ #

class MainHandler(webapp2.RequestHandler):
    """A servlet to handle requests to load the main web page."""

    def get(self):
        template = JINJA2_ENVIRONMENT.get_template('index.html')
        self.response.out.write(template.render())


class GetBasicMapsHandler(webapp2.RequestHandler):
    """A servlet to handle requests to load background maps upon loading the main web page."""
    
    def get(self):
        
        basic_maps = basicMaps()
        
        AoI_border        = basic_maps['aoi_border']
        AoI_fill          = basic_maps['aoi_fill']
        
        AoI_border_mapid  = AoI_border.getMapId()
        AoI_fill_mapid    = AoI_fill.getMapId()
        
        content = {
            'eeMapId_border': AoI_border_mapid['mapid'],
            'eeToken_border': AoI_border_mapid['token'],
            'eeMapId_fill': AoI_fill_mapid['mapid'],
            'eeToken_fill': AoI_fill_mapid['token']
        }
        
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(content))


class GetWaterMapHandler(webapp2.RequestHandler):
    """A servlet to handle requests to load the water map."""

    def get(self):
    
        # get time period values
        time_start   = self.request.params.get('time_start')
        time_end     = self.request.params.get('time_end')
        
        # get expert input values
        climatology  = self.request.params.get('climatology')
        month_index  = self.request.params.get('month_index')
        defringe     = self.request.params.get('defringe')
        pcnt_perm    = self.request.params.get('pcnt_perm')
        pcnt_temp    = self.request.params.get('pcnt_temp')
        water_thresh = self.request.params.get('water_thresh')
        ndvi_thresh  = self.request.params.get('veg_thresh')
        hand_thresh  = self.request.params.get('hand_thresh')
        cloud_thresh = self.request.params.get('cloud_thresh')
        
        # calculate new map and obtain mapId/token
        water        = SurfaceWaterToolAlgorithm(time_start, time_end, climatology, month_index, defringe, pcnt_perm, pcnt_temp, water_thresh, ndvi_thresh, hand_thresh, cloud_thresh)
        water_styled = SurfaceWaterToolStyle(water)
        
        mapid   = water_styled.getMapId()
        content = {
            'eeMapId': mapid['mapid'],
            'eeToken': mapid['token']
        }
        #mapid_permanent_water = water['permanent'].getMapId()
        #mapid_temporary_water   = water['temporary'].getMapId()
        #content = {
        #    'eeMapId_permanent': mapid_permanent_water['mapid'],
        #    'eeToken_permanent': mapid_permanent_water['token'],
        #    'eeMapId_temporary': mapid_temporary_water['mapid'],
        #    'eeToken_temporary': mapid_temporary_water['token']
        #}
        
        # send content using json
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(content))


class GetAdmBoundsMapHandler(webapp2.RequestHandler):
    """A servlet to handle requests to load the administrative boundaries fusion table."""

    def get(self):
        #mapid = Adm_bounds.getMapId({'color':'lightgrey'})
        mapid = ee.Image().byte().paint(Adm_bounds, 0, 2).getMapId()
        content = {
            'eeMapId': mapid['mapid'],
            'eeToken': mapid['token']
        }
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(content))


class GetTilesMapHandler(webapp2.RequestHandler):
    """A servlet to handle requests to load the tiles fusion table."""

    def get(self):
        #mapid = Tiles.getMapId({'color':'lightgrey'})
        mapid = ee.Image().byte().paint(Tiles, 0, 2).getMapId()
        content = {
            'eeMapId': mapid['mapid'],
            'eeToken': mapid['token']
        }
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(content))


class GetSelectedAdmBoundsHandler(webapp2.RequestHandler):
    """A servlet to handle requests to select an administrative boundary from the fusion table."""

    def get(self):
        lat   = ee.Number(float(self.request.params.get('lat')))
        lng   = ee.Number(float(self.request.params.get('lng')))
        point = ee.Geometry.Point([lng, lat])
        area  = ee.Feature(Adm_bounds.filterBounds(point).first())
        size  = area.geometry().area().divide(1e6).getInfo()
        mapid = area.getMapId({'color':'grey'})
        content = {
            'eeMapId': mapid['mapid'],
            'eeToken': mapid['token'],
            'size': size
        }
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(content))


class GetSelectedTileHandler(webapp2.RequestHandler):
    """A servlet to handle requests to select a tile from the fusion table."""

    def get(self):
        lat   = ee.Number(float(self.request.params.get('lat')))
        lng   = ee.Number(float(self.request.params.get('lng')))
        point = ee.Geometry.Point([lng, lat])
        area  = ee.Feature(Tiles.filterBounds(point).first())
        mapid = area.getMapId({'color':'grey'})
        content = {
            'eeMapId': mapid['mapid'],
            'eeToken': mapid['token']
        }
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(content))


class ExportDrawnHandler(webapp2.RequestHandler):
    """A servlet to handle requests to download data using a drawn polygon."""

    def get(self):
        
        # get time period values
        time_start   = self.request.params.get('time_start')
        time_end     = self.request.params.get('time_end')
        
        # get expert input values
        climatology  = self.request.params.get('climatology')
        month_index  = self.request.params.get('month_index')
        defringe     = self.request.params.get('defringe')
        pcnt_perm    = self.request.params.get('pcnt_perm')
        pcnt_temp    = self.request.params.get('pcnt_temp')
        water_thresh = self.request.params.get('water_thresh')
        ndvi_thresh  = self.request.params.get('veg_thresh')
        hand_thresh  = self.request.params.get('hand_thresh')
        cloud_thresh = self.request.params.get('cloud_thresh')
        
        # obtain water map
        water = SurfaceWaterToolAlgorithm(time_start, time_end, climatology, month_index, defringe, pcnt_perm, pcnt_temp, water_thresh, ndvi_thresh, hand_thresh, cloud_thresh)
        
        # get drawn polygon and convert to list of coords
        coords_json = json.loads(self.request.params.get('coords'))
        coords_list  = []
        for items in coords_json:
			coords_list.append([items[0],items[1]])
        #content = coords_list
        
        polygon = ee.Geometry.Polygon(coords_list)
        coords  = polygon.coordinates().getInfo()
        #content = coords
        
        #test = ee.Feature(polygon).getMapId()
        #content = {
        #    'eeMapId': test['mapid'],
        #    'eeToken': test['token']
        #}
        
        # get filename
        export_name = self.request.params.get('export_name')
        
        # get to-be-downloaded image
        export_image = water
        #export_image = water.clip(polygon).updateMask(water.clip(polygon))
        
        # get download URL
        content = export_image.rename(['water']).getDownloadURL({
            'name': export_name,
            'scale': 30,
            'crs': 'EPSG:4326',
            'region': coords
		});
        
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(content))


class ExportSelectedHandler(webapp2.RequestHandler):
    """A servlet to handle requests to download data using a selected polygon."""

    def get(self):
        
        # get time period values
        time_start   = self.request.params.get('time_start')
        time_end     = self.request.params.get('time_end')
        
        # get expert input values
        climatology  = self.request.params.get('climatology')
        month_index  = self.request.params.get('month_index')
        defringe     = self.request.params.get('defringe')
        pcnt_perm    = self.request.params.get('pcnt_perm')
        pcnt_temp    = self.request.params.get('pcnt_temp')
        water_thresh = self.request.params.get('water_thresh')
        ndvi_thresh  = self.request.params.get('veg_thresh')
        hand_thresh  = self.request.params.get('hand_thresh')
        cloud_thresh = self.request.params.get('cloud_thresh')
        
        # obtain water map
        water = SurfaceWaterToolAlgorithm(time_start, time_end, climatology, month_index, defringe, pcnt_perm, pcnt_temp, water_thresh, ndvi_thresh, hand_thresh, cloud_thresh)
        
        # get selected polygon and convert to list of coords
        lat     = ee.Number(float(self.request.params.get('lat')))
        lng     = ee.Number(float(self.request.params.get('lng')))
        point   = ee.Geometry.Point([lng, lat])
        
        region_selection = self.request.params.get('region_selection')
        
        if region_selection == 'Tiles':
            polygon = ee.Feature(Tiles.filterBounds(point).first()).geometry()
        else:
            polygon = ee.Feature(Adm_bounds.filterBounds(point).first()).geometry()
        
        coords  = polygon.coordinates().getInfo()
        
        #content = coords
        
        #test = ee.Feature(polygon).getMapId()
        #content = {
        #    'eeMapId': test['mapid'],
        #    'eeToken': test['token']
        #}
        
        # get filename
        export_name = self.request.params.get('export_name')
        
        # get to-be-downloaded image
        export_image = water
        #export_image = water.clip(polygon).updateMask(water.clip(polygon))
        
        # get download URL
        content = export_image.rename(['water']).getDownloadURL({
            'name': export_name,
            'scale': 30,
            'crs': 'EPSG:4326',
            'region': coords
		});
        
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(content))


# Define webapp2 routing from URL paths to web request handlers. See:
# http://webapp-improved.appspot.com/tutorials/quickstart.html
app = webapp2.WSGIApplication([
    ('/export_selected', ExportSelectedHandler),
    ('/export_drawn', ExportDrawnHandler),
    ('/select_adm_bounds', GetSelectedAdmBoundsHandler),
    ('/select_tile', GetSelectedTileHandler),
    ('/get_adm_bounds_map', GetAdmBoundsMapHandler),
    ('/get_tiles_map', GetTilesMapHandler),
    ('/get_water_map', GetWaterMapHandler),
    ('/get_basic_maps', GetBasicMapsHandler),
    ('/', MainHandler)
    ], debug=True)

# ------------------------------------------------------------------------------------ #
# Surface Water Tool algorithm
# ------------------------------------------------------------------------------------ #

# Area of Interest
AoI = ee.FeatureCollection("ft:1nrjAesEg6hU_R7bt76AlNDN2hZl6o5-Ljw_Dglc4")

# Region selection / download layers
#Adm_bounds = ee.FeatureCollection("ft:1v8sEZW2eXQvpddyZshITeC9uPaAuvwFl5OQ8PLdX")  # created from raw data, merge of lvl 2 (Myanmar) with lvl 1 (others)
Adm_bounds = ee.FeatureCollection("ft:1EoP3xf8FAI3ctTLSD7mqSmVR-ghuotnRR3eqtSKE")  # copy (june 2017) of polygons used in (javascript branch of) EcoDash tool
#Adm_bounds = ee.FeatureCollection("ft:1y94brggqzFF7XTKphcV94TwP_zwc8cRcAD8WSJHb")   # copy (june 2017) of polygons used in (master branch of) EcoDash tool
Tiles      = ee.FeatureCollection("ft:1MsfMsevkTAyPJswCXy-PFdmqBIE39Th8sn2yk1zu")

# Height Above Nearest Drainage (HAND) map for Mekong region
#HAND = ee.Image('users/gena/ServirMekong/SRTM_30_Asia_Mekong_hand')  # old/obsolete version, Mekong basin only (not complete countries)
HAND = ee.Image('users/gena/GlobalHAND/30m/hand-5000').clip(AoI)  # global version, clipped to AoI

# assign large (positive!) HAND value to value found in strange horizontal lines (-99999), so it is masked unless user specifies a very large threshold
HAND = HAND.where(HAND.lt(0), 1000)

# helper function: filter images
def filterImages (image_collection, bands, bounds, dates):
    return image_collection.select(bands[0], bands[1]).filterBounds(bounds).filterDate(dates[0], ee.Date(dates[1]).advance(1, 'day'))
    
# helper function: merge image collections
def mergeImages (image_collections):
    image_collections_merged = ee.ImageCollection(image_collections[0])
    for i in range(1, len(image_collections)):
        image_collections_merged = ee.ImageCollection(image_collections_merged.merge(image_collections[i]))
    return image_collections_merged

# helper function: defringe Landsat 5 and/or 7
# Defringe algorithm credits:
# Author:
#
# Bonnie Ruefenacht, PhD
# Senior Specialist
# RedCastle Resources, Inc.
# Working onsite at: 
# USDA Forest Service 
# Remote Sensing Applications Center (RSAC) 
# 2222 West 2300 South
# Salt Lake City, UT 84119
# Office: (801) 975-3828 
# Mobile: (801) 694-9215
# Email: bruefenacht@fs.fed.us
# RSAC FS Intranet website: http://fsweb.rsac.fs.fed.us/
# RSAC FS Internet website: http://www.fs.fed.us/eng/rsac/
#
# Purpose: Remove the fringes of landsat 5 and 7 scenes.
#
# Kernel for masking fringes found and L5 and L7 imagery
k = ee.Kernel.fixed(41, 41, \
[[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], \
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]])
fringeCountThreshold = 279;  #Define number of non null observations for pixel to not be classified as a fringe
def defringeLandsat(img):
    m   = img.mask().reduce(ee.Reducer.min())
    sum = m.reduceNeighborhood(ee.Reducer.sum(), k, 'kernel')
    sum = sum.gte(fringeCountThreshold)
    img = img.mask(img.mask().And(sum))
    return img

# water detection algorithm
def SurfaceWaterToolAlgorithm(time_start, time_end, climatology, month_index, defringe, pcnt_perm, pcnt_temp, water_thresh, ndvi_thresh, hand_thresh, cloud_thresh):
    
    # create date range for image filtering
    date_range = [time_start, time_end]
    
    # percentiles
    percentile_permanent   = float(pcnt_perm)
    percentile_temporary   = float(pcnt_temp)
    
    # MNDWI threshold (water detection)
    water_index_threshold  = float(water_thresh)
    
    # NDVI threshold (vegetation masking)
    NDVI_threshold         = float(ndvi_thresh)
    
    # HAND threshold (e.g. hill shade masking)
    HAND_threshold         = float(hand_thresh)
    
    # Landsat band names
    LC457_BANDS = ['B1',    'B1',   'B2',    'B3',  'B4',  'B5',    'B7']
    LC8_BANDS   = ['B1',    'B2',   'B3',    'B4',  'B5',  'B6',    'B7']
    STD_NAMES   = ['blue2', 'blue', 'green', 'red', 'nir', 'swir1', 'swir2']
    
    # Get Landsat image collection
    if int(cloud_thresh) < 0:
        images_l4 = filterImages(ee.ImageCollection('LANDSAT/LT4_L1T_TOA'), [LC457_BANDS, STD_NAMES], AoI, [date_range[0], date_range[1]])
        images_l5 = filterImages(ee.ImageCollection('LANDSAT/LT5_L1T_TOA'), [LC457_BANDS, STD_NAMES], AoI, [date_range[0], date_range[1]])
        images_l7 = filterImages(ee.ImageCollection('LANDSAT/LE7_L1T_TOA'), [LC457_BANDS, STD_NAMES], AoI, [date_range[0], date_range[1]])
        images_l8 = filterImages(ee.ImageCollection('LANDSAT/LC8_L1T_TOA'), [LC8_BANDS, STD_NAMES], AoI, [date_range[0], date_range[1]])
    else:
        # helper function: cloud busting
        # (https://code.earthengine.google.com/63f075a9e212f6ed4770af44be18a4fe, Ian Housman and Carson Stam)
        def bustClouds(img):
            t = img
            cs = ee.Algorithms.Landsat.simpleCloudScore(img).select('cloud')
            out = img.mask(img.mask().And(cs.lt(ee.Number(int(cloud_thresh)))))
            return out.copyProperties(t)
        images_l4 = filterImages(ee.ImageCollection('LANDSAT/LT4_L1T_TOA').map(bustClouds), [LC457_BANDS, STD_NAMES], AoI, [date_range[0], date_range[1]])
        images_l5 = filterImages(ee.ImageCollection('LANDSAT/LT5_L1T_TOA').map(bustClouds), [LC457_BANDS, STD_NAMES], AoI, [date_range[0], date_range[1]])
        images_l7 = filterImages(ee.ImageCollection('LANDSAT/LE7_L1T_TOA').map(bustClouds), [LC457_BANDS, STD_NAMES], AoI, [date_range[0], date_range[1]])
        images_l8 = filterImages(ee.ImageCollection('LANDSAT/LC8_L1T_TOA').map(bustClouds), [LC8_BANDS, STD_NAMES], AoI, [date_range[0], date_range[1]])
    
    if defringe == 'true':
        images_l5 = images_l5.map(defringeLandsat)
        images_l7 = images_l7.map(defringeLandsat)
    
    images = mergeImages([images_l4, images_l5, images_l7, images_l8]);
    
    if climatology == 'true':
        images = images.filter(ee.Filter.calendarRange(int(month_index), int(month_index), 'month'))
        
    # calculate percentile images
    prcnt_img_permanent = images.reduce(ee.Reducer.percentile([percentile_permanent])).rename(STD_NAMES)
    prcnt_img_temporary = images.reduce(ee.Reducer.percentile([percentile_temporary])).rename(STD_NAMES)

    # MNDWI
    MNDWI_permanent = prcnt_img_permanent.normalizedDifference(['green', 'swir1'])
    MNDWI_temporary = prcnt_img_temporary.normalizedDifference(['green', 'swir1'])

    # water
    water_permanent = MNDWI_permanent.gt(water_index_threshold)
    water_temporary = MNDWI_temporary.gt(water_index_threshold)
    
    # get NDVI masks
    NDVI_permanent_pcnt = prcnt_img_permanent.normalizedDifference(['nir', 'red'])
    NDVI_temporary_pcnt = prcnt_img_temporary.normalizedDifference(['nir', 'red'])
    NDVI_mask_permanent = NDVI_permanent_pcnt.gt(NDVI_threshold)
    NDVI_mask_temporary = NDVI_temporary_pcnt.gt(NDVI_threshold)
    
    # get HAND mask
    HAND_mask           = HAND.gt(HAND_threshold)
    
    # combined NDVI and HAND masks
    NDVI_and_HAND_mask_permanent = NDVI_mask_permanent.add(HAND_mask)
    NDVI_and_HAND_mask_temporary = NDVI_mask_temporary.add(HAND_mask)
    
    # apply NDVI and HAND masks
    water_permanent_NDVImasked = water_permanent.eq(1).And(NDVI_mask_permanent.eq(0))
    water_permanent_HANDmasked = water_permanent.eq(1).And(HAND_mask.eq(0))
    water_permanent_masked     = water_permanent.eq(1).And(NDVI_and_HAND_mask_permanent.eq(0))
    
    water_temporary_NDVImasked     = water_temporary.eq(1).And(NDVI_mask_temporary.eq(0))
    water_temporary_HANDmasked     = water_temporary.eq(1).And(HAND_mask.eq(0))
    water_temporary_masked         = water_temporary.eq(1).And(NDVI_and_HAND_mask_temporary.eq(0))
    #water_temporary_masked = water_temporary_masked.subtract(water_permanent_masked)    # for separate layers

    # single image with permanent and temporary water
    #water_complete = water_permanent.add(water_temporary).clip(AoI)
    water_complete = water_permanent_masked.add(water_temporary_masked).clip(AoI)
    
    return water_complete.updateMask(water_complete)

def SurfaceWaterToolStyle(map):

    water_style = '\
    <RasterSymbolizer>\
      <ColorMap extended="true" >\
        <ColorMapEntry color="#ffffff" quantity="0.0" label="-1"/>\
        <ColorMapEntry color="#9999ff" quantity="1.0" label="-1"/>\
        <ColorMapEntry color="#00008b" quantity="2.0" label="-1"/>\
      </ColorMap>\
    </RasterSymbolizer>';
    
    return map.sldStyle(water_style)

# ------------------------------------------------------------------------------------ #
# Additional functions
# ------------------------------------------------------------------------------------ #

def basicMaps():
    AoI_border = ee.Image().byte().paint(AoI, 0, 3)
    AoI_fill   = ee.Image().byte().paint(AoI, 1000)
    return {'aoi_border': AoI_border, 'aoi_fill': AoI_fill}
