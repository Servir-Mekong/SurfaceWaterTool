#!/usr/bin/env python
"""Google Earth Engine python code for the SERVIR-Mekong Surface Water Mapping Tool"""

# This script handles the loading of the web application and its time out settings,
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

# Memcache is used to avoid exceeding our EE quota. Entries in the cache expire
# 24 hours after they are added. See:
# https://cloud.google.com/appengine/docs/python/memcache/
MEMCACHE_EXPIRATION = 60 * 60 * 24


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
    """Handles requests to load the main web page."""
    def get(self):
        template = JINJA2_ENVIRONMENT.get_template('index.html')
        self.response.out.write(template.render())


class GetBackgroundHandler(webapp2.RequestHandler):
    """Handles requests to load the background map upon loading the main web page."""
    def get(self):
        AoI_mapid    = ee.Image().byte().paint(AoI, 1000).getMapId()
        HAND_style = '\
        <RasterSymbolizer>\
          <ColorMap extended="true" >\
            <ColorMapEntry color="#3288bd" quantity="0.0" label="-1"/>\
            <ColorMapEntry color="#99d594" quantity="20.0" label="-1"/>\
            <ColorMapEntry color="#e6f598" quantity="40.0" label="-1"/>\
            <ColorMapEntry color="#fc8d59" quantity="60.0" label="-1"/>\
            <ColorMapEntry color="#d53e4f" quantity="80.0" label="-1"/>\
            <ColorMapEntry color="#ffffff" quantity="100.0" label="-1"/>\
          </ColorMap>\
        </RasterSymbolizer>'
        HAND_mapid = ee.Image('users/arjenhaag/SERVIR-Mekong/HAND_MERIT').clip(AoI).sldStyle(HAND_style).getMapId()
        content = {
            'AoImapId': AoI_mapid['mapid'],
            'AoItoken': AoI_mapid['token'],
            'HANDmapId': HAND_mapid['mapid'],
            'HANDtoken': HAND_mapid['token']
        }
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(content))


class GetDefaultHandler(webapp2.RequestHandler):
    """Handles requests to load the default map upon loading the main web page."""
    def get(self):
        default = SurfaceWaterToolStyle(ee.Image('users/arjenhaag/SERVIR-Mekong/SWMT_default_2017_2')).getMapId()
        content = {
            'eeMapId': default['mapid'],
            'eeToken': default['token']
        }
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(content))


class GetWaterMapHandler(webapp2.RequestHandler):
    """Handles requests to load the water map."""
    def get(self):
        # get input parameters
        time_start   = self.request.params.get('time_start')
        time_end     = self.request.params.get('time_end')
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
        water        = SurfaceWaterToolUpdate(time_start, time_end, climatology, month_index, defringe, pcnt_perm, pcnt_temp, water_thresh, ndvi_thresh, hand_thresh, cloud_thresh)
        mapid        = SurfaceWaterToolStyle(water).getMapId()
        content      = {
            'eeMapId': mapid['mapid'],
            'eeToken': mapid['token']
        }
        # send content using json
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(content))


class GetExampleMapHandler(webapp2.RequestHandler):
    """Handles requests to load an example map."""
    def get(self):
        # get clicked example id
        example_id  = self.request.params.get('example_id')
        # pre-calculated example maps
        EXAMPLES = {
            'example_1': ee.Image('users/arjenhaag/SERVIR-Mekong/SWMT_example_delta_2'),
            'example_2': ee.Image('users/arjenhaag/SERVIR-Mekong/SWMT_example_reservoir_2'),
            'example_3': ee.Image('users/arjenhaag/SERVIR-Mekong/SWMT_example_floods_2'),
            'example_4': ee.Image('users/arjenhaag/SERVIR-Mekong/SWMT_example_river_2')
        }
        # get example map with matching id
        example_map = ee.Image(EXAMPLES[example_id])
        mapid       = SurfaceWaterToolStyle(example_map).getMapId()
        content     = {
            'eeMapId': mapid['mapid'],
            'eeToken': mapid['token']
        }
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(content))


class GetExampleMonthsHandler(webapp2.RequestHandler):
    """Handles requests to obtain mapId and token for each monthly map."""
    def get(self):
        # get example map
        example_map = ee.Image('users/arjenhaag/SERVIR-Mekong/SWMT_example_months_2')
        # get content for each monthly image
        mapid_1  = SurfaceWaterToolStyle(example_map.select(ee.String('water_').cat(ee.String('1')))).getMapId()
        mapid_2  = SurfaceWaterToolStyle(example_map.select(ee.String('water_').cat(ee.String('2')))).getMapId()
        mapid_3  = SurfaceWaterToolStyle(example_map.select(ee.String('water_').cat(ee.String('3')))).getMapId()
        mapid_4  = SurfaceWaterToolStyle(example_map.select(ee.String('water_').cat(ee.String('4')))).getMapId()
        mapid_5  = SurfaceWaterToolStyle(example_map.select(ee.String('water_').cat(ee.String('5')))).getMapId()
        mapid_6  = SurfaceWaterToolStyle(example_map.select(ee.String('water_').cat(ee.String('6')))).getMapId()
        mapid_7  = SurfaceWaterToolStyle(example_map.select(ee.String('water_').cat(ee.String('7')))).getMapId()
        mapid_8  = SurfaceWaterToolStyle(example_map.select(ee.String('water_').cat(ee.String('8')))).getMapId()
        mapid_9  = SurfaceWaterToolStyle(example_map.select(ee.String('water_').cat(ee.String('9')))).getMapId()
        mapid_10 = SurfaceWaterToolStyle(example_map.select(ee.String('water_').cat(ee.String('10')))).getMapId()
        mapid_11 = SurfaceWaterToolStyle(example_map.select(ee.String('water_').cat(ee.String('11')))).getMapId()
        mapid_12 = SurfaceWaterToolStyle(example_map.select(ee.String('water_').cat(ee.String('12')))).getMapId()
        content_1 = {
            'eeMapId': mapid_1['mapid'],
            'eeToken': mapid_1['token']
        }
        content_2 = {
            'eeMapId': mapid_2['mapid'],
            'eeToken': mapid_2['token']
        }
        content_3 = {
            'eeMapId': mapid_3['mapid'],
            'eeToken': mapid_3['token']
        }
        content_4 = {
            'eeMapId': mapid_4['mapid'],
            'eeToken': mapid_4['token']
        }
        content_5 = {
            'eeMapId': mapid_5['mapid'],
            'eeToken': mapid_5['token']
        }
        content_6 = {
            'eeMapId': mapid_6['mapid'],
            'eeToken': mapid_6['token']
        }
        content_7 = {
            'eeMapId': mapid_7['mapid'],
            'eeToken': mapid_7['token']
        }
        content_8 = {
            'eeMapId': mapid_8['mapid'],
            'eeToken': mapid_8['token']
        }
        content_9 = {
            'eeMapId': mapid_9['mapid'],
            'eeToken': mapid_9['token']
        }
        content_10 = {
            'eeMapId': mapid_10['mapid'],
            'eeToken': mapid_10['token']
        }
        content_11 = {
            'eeMapId': mapid_11['mapid'],
            'eeToken': mapid_11['token']
        }
        content_12 = {
            'eeMapId': mapid_12['mapid'],
            'eeToken': mapid_12['token']
        }
        content = {
            '1': content_1,
            '2': content_2,
            '3': content_3,
            '4': content_4,
            '5': content_5,
            '6': content_6,
            '7': content_7,
            '8': content_8,
            '9': content_9,
            '10': content_10,
            '11': content_11,
            '12': content_12,
        }
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(content))


class GetAdmBoundsMapHandler(webapp2.RequestHandler):
    """Handles requests to load the administrative boundaries fusion table."""
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
    """Handles requests to load the tiles fusion table."""
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
    """Handles requests to select an administrative boundary from the fusion table."""
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
    """Handles requests to select a tile from the fusion table."""
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
    """Handles requests to download data using a drawn polygon."""
    def get(self):
        # get input parameters
        time_start   = self.request.params.get('time_start')
        time_end     = self.request.params.get('time_end')
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
        water = SurfaceWaterToolUpdate(time_start, time_end, climatology, month_index, defringe, pcnt_perm, pcnt_temp, water_thresh, ndvi_thresh, hand_thresh, cloud_thresh)
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
		})
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(content))


class ExportSelectedHandler(webapp2.RequestHandler):
    """Handles requests to download data using a selected polygon."""
    def get(self):
        # get input parameters
        time_start   = self.request.params.get('time_start')
        time_end     = self.request.params.get('time_end')
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
        water = SurfaceWaterToolUpdate(time_start, time_end, climatology, month_index, defringe, pcnt_perm, pcnt_temp, water_thresh, ndvi_thresh, hand_thresh, cloud_thresh)
        # get selected polygon and convert to list of coords
        lat     = ee.Number(float(self.request.params.get('lat')))
        lng     = ee.Number(float(self.request.params.get('lng')))
        point   = ee.Geometry.Point([lng, lat])
        # get region
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
		})
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
    ('/get_background', GetBackgroundHandler),
    ('/get_default', GetDefaultHandler),
    ('/get_example_map', GetExampleMapHandler),
    ('/get_example_months', GetExampleMonthsHandler),
    ('/', MainHandler)
    ], debug=True)

# ------------------------------------------------------------------------------------ #
# Surface Water Mapping Tool algorithm
# ------------------------------------------------------------------------------------ #

# Geometries
AoI        = ee.FeatureCollection("projects/servir-mekong/SWMT/AoI")
#AoI        = ee.FeatureCollection("ft:1RUtGuo9OZU2IdLTICNc7iif4dxgOMIsvWoyPvPJa")
Adm_bounds = ee.FeatureCollection("projects/servir-mekong/SWMT/Adm_bounds")
Tiles      = ee.FeatureCollection("projects/servir-mekong/SWMT/Tiles")

# Landsat band names
LC457_BANDS = ['B1',    'B1',   'B2',    'B3',  'B4',  'B5',    'B7']
LC8_BANDS   = ['B1',    'B2',   'B3',    'B4',  'B5',  'B6',    'B7']
STD_NAMES   = ['blue2', 'blue', 'green', 'red', 'nir', 'swir1', 'swir2']

def SurfaceWaterToolAlgorithm(images, pcnt_perm, pcnt_temp, water_thresh, ndvi_thresh, hand_mask):

    # calculate percentile images
    prcnt_img_perm = images.reduce(ee.Reducer.percentile([float(pcnt_perm)])).rename(STD_NAMES)
    prcnt_img_temp = images.reduce(ee.Reducer.percentile([float(pcnt_temp)])).rename(STD_NAMES)

    # MNDWI
    MNDWI_perm = prcnt_img_perm.normalizedDifference(['green', 'swir1'])
    MNDWI_temp = prcnt_img_temp.normalizedDifference(['green', 'swir1'])

    # water
    water_perm = MNDWI_perm.gt(float(water_thresh))
    water_temp = MNDWI_temp.gt(float(water_thresh))

    # get NDVI masks
    NDVI_perm_pcnt = prcnt_img_perm.normalizedDifference(['nir', 'red'])
    NDVI_temp_pcnt = prcnt_img_temp.normalizedDifference(['nir', 'red'])
    NDVI_mask_perm = NDVI_perm_pcnt.gt(float(ndvi_thresh))
    NDVI_mask_temp = NDVI_temp_pcnt.gt(float(ndvi_thresh))

    # combined NDVI and HAND masks
    full_mask_perm = NDVI_mask_perm.add(hand_mask)
    full_mask_temp = NDVI_mask_temp.add(hand_mask)

    # apply NDVI and HAND masks
    water_perm_masked = water_perm.updateMask(full_mask_perm.Not())
    water_temp_masked = water_temp.updateMask(full_mask_perm.Not())

    # single image with permanent and temporary water
    water_complete = water_perm_masked.add(water_temp_masked).clip(AoI)

    #return water_complete.updateMask(water_complete)
    return water_complete

def SurfaceWaterToolImages(time_start, time_end, climatology, month_index, defringe, cloud_thresh):

    # filter Landsat collections on bounds and dates
    L4 = ee.ImageCollection('LANDSAT/LT04/C01/T1_TOA').filterBounds(AoI).filterDate(time_start, ee.Date(time_end).advance(1, 'day'))
    L5 = ee.ImageCollection('LANDSAT/LT05/C01/T1_TOA').filterBounds(AoI).filterDate(time_start, ee.Date(time_end).advance(1, 'day'))
    L7 = ee.ImageCollection('LANDSAT/LE07/C01/T1_TOA').filterBounds(AoI).filterDate(time_start, ee.Date(time_end).advance(1, 'day'))
    L8 = ee.ImageCollection('LANDSAT/LC08/C01/T1_TOA').filterBounds(AoI).filterDate(time_start, ee.Date(time_end).advance(1, 'day'))

    # apply cloud masking
    if int(cloud_thresh) >= 0:
        # helper function: cloud busting
        # (https://code.earthengine.google.com/63f075a9e212f6ed4770af44be18a4fe, Ian Housman and Carson Stam)
        def bustClouds(img):
            t = img
            cs = ee.Algorithms.Landsat.simpleCloudScore(img).select('cloud')
            out = img.mask(img.mask().And(cs.lt(ee.Number(int(cloud_thresh)))))
            return out.copyProperties(t)
        # apply cloud busting function
        L4 = L4.map(bustClouds)
        L5 = L5.map(bustClouds)
        L7 = L7.map(bustClouds)
        L8 = L8.map(bustClouds)

    # select bands and rename
    L4 = L4.select(LC457_BANDS, STD_NAMES)
    L5 = L5.select(LC457_BANDS, STD_NAMES)
    L7 = L7.select(LC457_BANDS, STD_NAMES)
    L8 = L8.select(LC8_BANDS, STD_NAMES)

    # apply defringing
    if defringe == 'true':
        # helper function: defringe Landsat 5 and/or 7
        # (https://code.earthengine.google.com/63f075a9e212f6ed4770af44be18a4fe, Bonnie Ruefenacht)
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
        fringeCountThreshold = 279  # define number of non null observations for pixel to not be classified as a fringe
        def defringeLandsat(img):
            m   = img.mask().reduce(ee.Reducer.min())
            sum = m.reduceNeighborhood(ee.Reducer.sum(), k, 'kernel')
            sum = sum.gte(fringeCountThreshold)
            img = img.mask(img.mask().And(sum))
            return img
        L5 = L5.map(defringeLandsat)
        L7 = L7.map(defringeLandsat)

    # merge collections
    images = ee.ImageCollection(L4.merge(L5).merge(L7).merge(L8))

    # filter on selected month
    if climatology == 'true':
        images = images.filter(ee.Filter.calendarRange(int(month_index), int(month_index), 'month'))

    return images

def SurfaceWaterToolUpdate(time_start, time_end, climatology, month_index, defringe, pcnt_perm, pcnt_temp, water_thresh, ndvi_thresh, hand_thresh, cloud_thresh):

    # get images
    images = SurfaceWaterToolImages(time_start, time_end, climatology, month_index, defringe, cloud_thresh)

    # Height Above Nearest Drainage (HAND)
    HAND = ee.Image('users/arjenhaag/SERVIR-Mekong/HAND_MERIT').clip(AoI)

    # get HAND mask
    HAND_mask = HAND.gt(float(hand_thresh))

    water = SurfaceWaterToolAlgorithm(images, pcnt_perm, pcnt_temp, water_thresh, ndvi_thresh, HAND_mask)

    return water.updateMask(water)

def SurfaceWaterToolStyle(map):
    water_style = '\
    <RasterSymbolizer>\
      <ColorMap extended="true" >\
        <ColorMapEntry color="#ffffff" quantity="0.0" label="-1"/>\
        <ColorMapEntry color="#9999ff" quantity="1.0" label="-1"/>\
        <ColorMapEntry color="#00008b" quantity="2.0" label="-1"/>\
      </ColorMap>\
    </RasterSymbolizer>'
    return map.sldStyle(water_style)
