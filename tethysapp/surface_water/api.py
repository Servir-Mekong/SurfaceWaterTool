import json
from .surface_water import SurfaceWater 

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authentication import TokenAuthentication
from django.views.decorators.http import require_GET

@csrf_exempt
def update_map(request):
    '''
    API Controller for getting data
    '''

    request_get  = request.GET.get
    time_start   = request_get('start_date', '2000-01-01')
    time_end     = request_get('end_date', '2010-12-31')
    climatology  = request_get('climatology', False)
    month_index  = request_get('month_index')
    defringe     = request_get('defringe', False)
    pcnt_perm    = request_get('pcnt_perm', 40)
    pcnt_temp    = request_get('pcnt_temp', 8)
    water_thresh = request_get('water_thresh', 0.3)
    ndvi_thresh  = request_get('veg_thresh', 0.5)
    hand_thresh  = request_get('hand_thresh', 50)
    cloud_thresh = request_get('cloud_thresh', -1)

    tile_url_template = 'https://earthengine.googleapis.com/map/{mapid}/{{z}}/{{x}}/{{y}}?token={token}'

    surface_water = SurfaceWater(time_start, time_end, climatology, month_index, defringe, pcnt_perm, pcnt_temp, water_thresh, ndvi_thresh, hand_thresh, cloud_thresh)
    water_map_id = surface_water.get_water_map_id()
    water_map_url = tile_url_template.format(**water_map_id)

    hand_map_id = SurfaceWater.get_hand_map_id()
    hand_map_url = tile_url_template.format(**hand_map_id)

    data = {
        'waterMapUrl': water_map_url,
        'handMapUrl' : hand_map_url
    }

    return JsonResponse(data)
