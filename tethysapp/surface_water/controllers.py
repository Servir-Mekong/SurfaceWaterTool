from django.shortcuts import render, reverse
from django.contrib.auth.decorators import login_required
from tethys_sdk.gizmos import Button, DatePicker, MVView, MapView, MVLayer, TextInput

from .surface_water import SurfaceWater

@login_required()
def home(request):
    """
    Controller for the app home page.
    """

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

    start_date_gizmo = DatePicker(
        name = 'start-date',
        display_text = 'Start Date',
        autoclose = True,
        format = 'yyyy-mm-dd',
        start_view = 'decade',
        initial = '2000-01-01'
    )

    end_date_gizmo = DatePicker(
        name = 'date-built',
        display_text = 'End Date',
        autoclose = True,
        format = 'yyyy-mm-dd',
        start_view = 'decade',
        initial = '2010-12-31'
    )

    update_map = Button(
        display_text = 'Update map',
        name = 'update-button',
        icon = 'glyphicon glyphicon-refresh',
        style = 'success'
    )

    view_options = MVView(
        projection='EPSG:4326',
        center=[98.218, 18.041],
        zoom=5,
        maxZoom=18,
        minZoom=2
    )

    tile_url_template = 'https://earthengine.googleapis.com/map/{mapid}/{{z}}/{{x}}/{{y}}?token={token}'

    surface_water = SurfaceWater(time_start, time_end, climatology, month_index, defringe, pcnt_perm, pcnt_temp, water_thresh, ndvi_thresh, hand_thresh, cloud_thresh)
    water_map_id = surface_water.get_water_map_id()
    water_map_url = tile_url_template.format(**water_map_id)

    hand_map_id = SurfaceWater.get_hand_map_id()
    hand_map_url = tile_url_template.format(**hand_map_id)

    map_view = MapView(
        height='100%',
        width='100%',
        basemap='OpenStreetMap',
        #layers=[gee_layer],
        view=view_options
    )

    context = {
        'start_date_gizmo' : start_date_gizmo,
        'end_date_gizmo'   : end_date_gizmo,
        'map_view'         : map_view,
        'update_map'       : update_map,
        'water_map_url'    : water_map_url,
        'hand_map_url'     : hand_map_url
    }

    return render(request, 'surface_water/home.html', context)
