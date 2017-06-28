# SurfaceWaterTool
A web application for the water detection algorithm of SERVIR-Mekong using Google Earth Engine and App Engine. The application itself can be found at <a href="http://surface-water-servir.adpc.net/">http://surface-water-servir.adpc.net/</a>.

![Screenshot](static/images/screenshot.png)

This tool is still in development. The two most important additions will be:
- Export data within drawn region to Google Drive
- Demo to help users understand the application

Dependencies are:
- ee
- httplib2
- oauth2client 

The Python and JavaScript client libraries for calling the Earth Engine API can be found here: <a  href="https://github.com/google/earthengine-api/">https://github.com/google/earthengine-api</a>. More information about Google Earth Engine is listed here: <a href="https://developers.google.com/earth-engine/">https://developers.google.com/earth-engine</a>.

The SurfaceWaterTool was developed, in part, by checking out the code of one of the Earth Engine application demos at <a href="https://github.com/google/earthengine-api/tree/master/demos/export-to-drive">https://github.com/google/earthengine-api/tree/master/demos/export-to-drive</a>.
