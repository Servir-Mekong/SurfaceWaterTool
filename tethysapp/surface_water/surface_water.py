# -*- coding: utf-8 -*-

import ee

# ----------------------------------------------------------------------
class SurfaceWater():
    '''
        Google Earth Engine API
    '''

    ee.Initialize()

    # geometries
    MEKONG_FEATURE_COLLECTION = ee.FeatureCollection('ft:1tdSwUL7MVpOauSgRzqVTOwdfy17KDbw-1d9omPw')
    COUNTRIES_NAME = ['Myanmar (Burma)', 'Thailand', 'Laos', 'Vietnam', 'Cambodia']
    COUNTRIES_GEOM = MEKONG_FEATURE_COLLECTION.filter(ee.Filter.inList('Country',
                                                      COUNTRIES_NAME)).geometry()
    LC457_BANDS = ['B1', 'B1', 'B2', 'B3', 'B4', 'B5', 'B7']
    LC8_BANDS   = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7']
    BAND_NAMES  = ['blue2', 'blue', 'green', 'red', 'nir', 'swir1', 'swir2']

    # ------------------------------------------------------------------
    def __init__(self, time_start, time_end, climatology, month_index, defringe, pcnt_perm, pcnt_temp, water_thresh, ndvi_thresh, hand_thresh, cloud_thresh):

        self.time_start   = time_start
        self.time_end     = time_end
        self.climatology  = climatology
        self.month_index  = month_index
        self.defringe     = defringe
        self.pcnt_perm    = pcnt_perm
        self.pcnt_temp    = pcnt_temp
        self.water_thresh = water_thresh
        self.ndvi_thresh  = ndvi_thresh
        self.hand_thresh  = hand_thresh
        self.cloud_thresh = cloud_thresh

        L4 = ee.ImageCollection('LANDSAT/LT04/C01/T1_TOA')\
                .filterBounds(SurfaceWater.COUNTRIES_GEOM)\
                .filterDate(time_start, ee.Date(time_end).advance(1, 'day'))
        L5 = ee.ImageCollection('LANDSAT/LT05/C01/T1_TOA')\
                .filterBounds(SurfaceWater.COUNTRIES_GEOM)\
                .filterDate(time_start, ee.Date(time_end).advance(1, 'day'))
        L7 = ee.ImageCollection('LANDSAT/LE07/C01/T1_TOA')\
                .filterBounds(SurfaceWater.COUNTRIES_GEOM)\
                .filterDate(time_start, ee.Date(time_end).advance(1, 'day'))
        L8 = ee.ImageCollection('LANDSAT/LC08/C01/T1_TOA')\
                .filterBounds(SurfaceWater.COUNTRIES_GEOM)\
                .filterDate(time_start, ee.Date(time_end).advance(1, 'day'))

        # apply cloud masking
        if cloud_thresh > 0:
            L4, L5, L7, L8 = self._cloud_busting(L4, L5, L7, L8)

        # select bands and rename
        L4 = L4.select(SurfaceWater.LC457_BANDS, SurfaceWater.BAND_NAMES)
        L5 = L5.select(SurfaceWater.LC457_BANDS, SurfaceWater.BAND_NAMES)
        L7 = L7.select(SurfaceWater.LC457_BANDS, SurfaceWater.BAND_NAMES)
        L8 = L8.select(SurfaceWater.LC8_BANDS, SurfaceWater.BAND_NAMES)

        # apply defringing
        if defringe:
            L5, L7 = self._apply_defringe(L5, L7)

        # merge collections
        images = ee.ImageCollection(L4.merge(L5).merge(L7).merge(L8))

        # filter on selected month
        if climatology:
            images = images.filter(ee.Filter.calendarRange(month_index, month_index, 'month'))

        self.images = images

    # ------------------------------------------------------------------
    def _cloud_busting(self, L4, L5, L7, L8):

        # helper function: cloud busting
        # (https://code.earthengine.google.com/63f075a9e212f6ed4770af44be18a4fe, Ian Housman and Carson Stam)
        def bust_clouds(img):
            cloud_score = ee.Algorithms.Landsat.simpleCloudScore(img).select('cloud')
            image = img.mask(img.mask().And(cloud_score.lt(ee.Number(cloud_thresh))))
            return image.copyProperties(img)

        # apply cloud busting function
        L4 = L4.map(bustClouds)
        L5 = L5.map(bustClouds)
        L7 = L7.map(bustClouds)
        L8 = L8.map(bustClouds)

        return L4, L5, L7, L8

    # ------------------------------------------------------------------
    def _apply_defringe(self, L5, L7):

        # helper function: defringe Landsat 5 and/or 7
        # (https://code.earthengine.google.com/63f075a9e212f6ed4770af44be18a4fe, Bonnie Ruefenacht)
        kernel = ee.Kernel.fixed(41, 41, \
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

        def defringe_landsat(img):
            _min   = img.mask().reduce(ee.Reducer.min())
            _sum = _min.reduceNeighborhood(ee.Reducer.sum(), kernel, 'kernel')
            _sum = _sum.gte(fringeCountThreshold)
            img = img.mask(img.mask().And(_sum))
            return img

        L5 = L5.map(defringe_landsat)
        L7 = L7.map(defringe_landsat)

        return L5, L7

    # ------------------------------------------------------------------
    def get_water_map_id(self):
        image = self.get_water_map()
        image = self.style_water_map(image)
        map_id = image.getMapId()
        return map_id

    # ------------------------------------------------------------------
    @staticmethod
    def get_hand_map_id():
        hand_style = '\
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
        hand_map_id = ee.Image('users/arjenhaag/SERVIR-Mekong/HAND_MERIT')\
                        .clip(SurfaceWater.COUNTRIES_GEOM)\
                        .sldStyle(hand_style).getMapId()
        return hand_map_id

    # ------------------------------------------------------------------
    def get_water_map(self):
        
        # Height Above Nearest Drainage (HAND)
        hand = ee.Image('users/arjenhaag/SERVIR-Mekong/HAND_MERIT')\
                .clip(SurfaceWater.COUNTRIES_GEOM)

        # get HAND mask
        hand_mask = hand.gt(self.hand_thresh)
        
        water = self.apply_algorithm(hand_mask)
        
        return water.updateMask(water)

    # ------------------------------------------------------------------
    def style_water_map(self, image):
        water_style = '\
        <RasterSymbolizer>\
          <ColorMap extended="true" >\
            <ColorMapEntry color="#ffffff" quantity="0.0" label="-1"/>\
            <ColorMapEntry color="#9999ff" quantity="1.0" label="-1"/>\
            <ColorMapEntry color="#00008b" quantity="2.0" label="-1"/>\
          </ColorMap>\
        </RasterSymbolizer>'
        return image.sldStyle(water_style)

    # ------------------------------------------------------------------
    def apply_algorithm(self, hand_mask):

        # calculate percentile images
        prcnt_img_perm = self.images.reduce(ee.Reducer.percentile([self.pcnt_perm]))\
                            .rename(SurfaceWater.BAND_NAMES)
        prcnt_img_temp = self.images.reduce(ee.Reducer.percentile([self.pcnt_temp]))\
                            .rename(SurfaceWater.BAND_NAMES)

        # MNDWI
        MNDWI_perm = prcnt_img_perm.normalizedDifference(['green', 'swir1'])
        MNDWI_temp = prcnt_img_temp.normalizedDifference(['green', 'swir1'])

        # water
        water_perm = MNDWI_perm.gt(self.water_thresh)
        water_temp = MNDWI_temp.gt(self.water_thresh)

        # get NDVI masks
        NDVI_perm_pcnt = prcnt_img_perm.normalizedDifference(['nir', 'red'])
        NDVI_temp_pcnt = prcnt_img_temp.normalizedDifference(['nir', 'red'])
        NDVI_mask_perm = NDVI_perm_pcnt.gt(self.ndvi_thresh)
        NDVI_mask_temp = NDVI_temp_pcnt.gt(self.ndvi_thresh)

        # combined NDVI and HAND masks
        full_mask_perm = NDVI_mask_perm.add(hand_mask)
        full_mask_temp = NDVI_mask_temp.add(hand_mask)
        
        # apply NDVI and HAND masks
        water_perm_masked = water_perm.updateMask(full_mask_perm.Not())
        water_temp_masked = water_temp.updateMask(full_mask_perm.Not())
        
        # single image with permanent and temporary water
        water_complete = water_perm_masked.add(water_temp_masked)\
                            .clip(SurfaceWater.COUNTRIES_GEOM)
        
        #return water_complete.updateMask(water_complete)
        return water_complete
