from tethys_sdk.base import TethysAppBase, url_map_maker


class SurfaceWater(TethysAppBase):
    """
    Tethys app class for Surface Water Mapping Tool.
    """

    name = 'Surface Water Mapping Tool'
    index = 'surface_water:home'
    icon = 'surface_water/images/icon.gif'
    package = 'surface_water'
    root_url = 'surface-water'
    color = '#8e44ad'
    description = 'Place a brief description of your app here.'
    tags = ''
    enable_feedback = False
    feedback_emails = []

    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        url_maps = (
            UrlMap(
                name='home',
                url='surface-water',
                controller='surface_water.controllers.home'
            ),
            UrlMap(
                name='update_map',
                url='surface-water/update-map',
                controller='surface_water.api.update_map'
            ),
        )

        return url_maps
