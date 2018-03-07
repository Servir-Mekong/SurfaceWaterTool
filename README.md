# Surface Water Mapping Tool
A web application for the water detection algorithm of <a href="https://servir.adpc.net/">SERVIR-Mekong</a> using Google Earth Engine and App Engine. The tool is part of the  <a href="https://servir.adpc.net/tools">SERVIR-Mekong Decision Support Tools</a> and has a dedicated page there as well: <a href="https://servir.adpc.net/tools/surface-water-mapping-tool">https://servir.adpc.net/tools/surface-water-mapping-tool</a>. The application itself can be found at <a href="http://surface-water-servir.adpc.net/">http://surface-water-servir.adpc.net/</a>.

A User Guide and Background Documentation are included in the About page of the tool.

![Screenshot](static/images/screenshot.png)

The export functionality of this tool is still under development. Users are able to download data directly from a browser, but the area for which data can be downloaded is limited. Efforts are underway to allow an export to Google Drive, which would not have this limitation.

Dependencies are:
- ee
- httplib2
- oauth2client 

The Python and JavaScript client libraries for calling the Earth Engine API can be found here: <a  href="https://github.com/google/earthengine-api/">https://github.com/google/earthengine-api</a>. More information about Google Earth Engine is listed here: <a href="https://developers.google.com/earth-engine/">https://developers.google.com/earth-engine</a>.


# Development and Acknowledgement
The development of the algorithm using Landsat 8 data was initiated in the PhD research of Gennadii Donchyts (co-funded by Deltares and the Technical University of Delft). Testing and further development of the algorithm using the Murray-Darling basin in Australia was funded by the EC FP7 project eartH2Observe (under grant agreement No 603608), which led to the publication of Donchyts et al. (2016), see below.

Application to the Mekong basin, which included testing, applying and adjusting thresholds, as well as further optimisation of the scripts to fully take advantage of Google Earth Engine capabilities, was supported by the SERVIR-Mekong project. This also included the addition of data from Landsat 4, 5 and 7. The development of the method to calculate the main supporting dataset (HAND) was fully supported by the eartH2Observe project, but the application for the Mekong, as well as refinement for this area, was supported by the SERVIR-Mekong project.

The creation of the Google Appspot based online application was fully supported by the SERVIR-Mekong project. Processing support and Google cloud storage needed to calculate the HAND product were supported by a grant from Google.

Landsat and SRTM data are made freely available by the U.S. Geological Survey (USGS) / National Aeronautics and Space Administration (NASA). Both are accessed and processed in Google Earth Engine.

The Surface Water Mapping Tool was developed, in part, by checking out the code of one of the Earth Engine application demos at <a href="https://github.com/google/earthengine-api/tree/master/demos/export-to-drive">https://github.com/google/earthengine-api/tree/master/demos/export-to-drive</a>.


<a href="http://www.mdpi.com/2072-4292/8/5/386">Gennadii, D., Schellekens, J., Winsemius, H., Eisemann, E. & van de Giesen, N. (2016). A 30 m Resolution Surface Water Mask Including Estimation of Positional and Thematic Differences Using Landsat 8, SRTM and OpenStreetMap: A Case Study in the Murray-Darling Basin, Australia. Remote Sensing, 8(5), 386.</a>
