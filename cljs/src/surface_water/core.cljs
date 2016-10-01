(ns surface-water.core
  (:require [goog.dom :as dom]
            [goog.string :as str]
            [reagent.core :as r]
            [surface-water.application :as app]))

;;=============
;; Page Header
;;=============

(defonce active-link (r/atom 0))

(defonce hover-link (r/atom nil))

(defn make-nav-link-style [link-num]
  {:class (if (or (= @active-link link-num)
                  (= @hover-link link-num))
            "highlight" "")
   :on-mouse-over #(reset! hover-link link-num)
   :on-mouse-out #(reset! hover-link nil)
   :on-click #(reset! active-link link-num)})

(defn page-header []
  [:header
   [:div#logos
    [:img#usaid  {:src "/static/images/usaid.png"}]
    [:img#nasa   {:src "/static/images/nasa.png"}]
    [:img#adpc   {:src "/static/images/adpclogo.jpg"}]
    [:img#servir {:src "/static/images/servir.png"}]]
   [:nav
    [:ul
     [:li (make-nav-link-style 0) "Home"]
     [:li (make-nav-link-style 1) "About"]]]])

;;===========
;; Page Body
;;===========

(defn make-page-visibility-style [link-num]
  (if (= @active-link link-num)
    {:style {:visibility "visible"}}
    {:style {:visibility "hidden"}}))

(defn about-page [page-visibility]
  [:div#about page-visibility
   [:h1 "About the Surface Water Mapping Tool"]
   [:p
    "Surface water distribution changes over space and time and these patterns"
    " can provide insight into ecological structure and function, patterns of"
    " flooding and flood risk, and the impacts of infrastructure and climate"
    " change on landscapes and hydrological systems. However, such patterns have"
    " been difficult to track and measure over large areas and longer time spans."
    " With increased access to large volumes of remotely sensed data and"
    " innovative techniques for optimizing the processing and interpretation of"
    " those data, these measurements are now more accessible than ever before. This"
    " tool leverages the extensive archive of Landsat data in the Google Earth"
    " Engine archive and Google’s cloud processing power to quickly perform"
    " calculations that reveal these patterns and dynamics."]
   [:p
    "The tool was initially developed to document the historical dynamics of"
    " seasonal flooding cycles on the Mekong River in order to better understand"
    " some of the likely impacts of completed and proposed dams. Other uses"
    " include identifying areas of permanent water (valuable in the context of"
    " severe drought response) and assessing flood risk for planning and disaster"
    " preparedness. Specific applications include detecting permanent water,"
    " identifying flood seasonality and likelihood, and documenting water dynamics."]
   [:p
    "In simple terms, the tool works by first individually processing Landsat"
    " images and classifying each pixel as water, non-water, or covered by cloud."
    " A secondary calculation is applied to stacks of such classified images"
    " -- essentially calculating the number of times a given pixel was classified"
    " as water vs. non water. Based on careful calibration work, this frequency"
    " information can be used to estimate which areas are covered by water during"
    " the entire period of analysis and which areas are covered only part of the"
    " year. These thresholds can then be used to construct maps of the"
    " distribution of permanent water, and the likelihood that other areas will"
    " be inundated at a given time of year."]
   [:hr]
   [:h1 "Technical Description of the Procedures Used to Identify Surface Water"]
   [:p
    "The most used methods to detect water based on multispectral (satellite)"
    " imagery are based on the fact that water absorbs radiation at near-infrared"
    " wavelengths and beyond.  This allows the detection of clear water by"
    " introducing a spectral index (Normalized Difference Water Index, NDWI)"
    " representing slope of water spectral curve. Later, [Xu, 2006] introduced"
    " another spectral index, called Modified Normalized Difference Water Index"
    " (MNDWI), which appears to be more sensitive for water feature detection."
    " While detection of clear water features appears to be trivial, a number of"
    " factors make it more difficult, these are mainly caused by the presence of"
    " clouds, snow and ice. Additionally, false positives can be observed in the"
    " areas with shadows due to topographic conditions or presence of clouds."
    " Furthermore,  water is almost never clear in a real world, resulting in"
    " changes of its spectral curve and as a result uniform threshold values that"
    " should be used to separate water pixels may no longer work. One of the"
    " approaches to overcome this problem was to use methods which allow"
    " detection of threshold values based on a histogram of all NDWI values in"
    " a given area."]
   [:p
    "Figure 1 demonstrates several situations, where water can be easily false"
    " detected using spectral indices. As can be seen from the NDWI and MNDWI"
    " figures, it is difficult to exclude mountain shadows and snow pixels using"
    " only a single threshold. Additionally, using MNDWI it is almost impossible"
    " to distinguish between snow and water."]
   [:figure
    [:img {:src "static/images/about_page_figure1.png"}]
    [:figcaption
     "Figure 1: Cloud-free Landsat 8 image showing why it is difficult to"
     " separate water using a single zero threshold value approach, Switzerland,"
     " 46.87⁰N, 8.63⁰E. Left - false-color composite (swir, nir, green) image,"
     " middle - NDWI (nir, green), right - MNDWI (swir1, green). Red color shows"
     " where threshold value is equal to zero."]]
   [:p
    "A significant improvement in water detection can be achieved when optical"
    " satellite imagery is combined with the elevation data, assuming that"
    " usually water does not flow on steep hilly areas and that most of the"
    " permanent water is concentrated in local valleys. The use of elevation"
    " data to extract drainage network is also a common practice in hydrological"
    " applications. Some of more recent developments include derived products"
    " such as height above nearest drainage (HAND), (Rennó, 2008)."]
   [:figure
    [:img {:src "static/images/about_page_figure2.png"}]
    [:figcaption
     "Figure 2: Example of rasters used for hydrological modeling, DEM (left),"
     " Flow Accumulation shaded using raster (center) and HAND (right). DEM is"
     " based on 30m SRTM, slightly smoothed using anisotropic diffusion filter"
     " to remove high frequency noise."]]
   [:p
    "To extract water mask from Landsat imagery we have developed a new"
    " non-parametric method based on MNDWI and dynamic threshold detected using"
    " Canny edge filter and Otsu thresholding. Additional steps include the use"
    " of NDVI index with a very high threshold (0.4) to exclude very dark"
    " vegetated areas, correction on hill shadows and snow/ice. For both water"
    " and hill shadow detection we’ve trained Cart classifier using features"
    " digitized manually, only for those areas, where the first step did not"
    " produce acceptable results."]
   [:p
    "For permanent water detection is performed on temporally averaged TOA"
    " reflectance images. By selection of specific percentiles we were able to"
    " exclude most of the cloud, cloud shadow and snow pixels. For the detection"
    " of water dynamics different percentiles, or specific temporal averaging"
    " periods  may be chosen in combination with different MNDWI thresholds."]
   [:figure
    [:img {:src "static/images/about_page_figure4.png"}]
    [:figcaption
     "Figure 4: False-color composite image (swir1, nir and green) (left),"
     " MNDWI index values (middle) and its histogram (right)."]]
   [:figure
    [:img {:src "static/images/about_page_figure5.png"}]
    [:figcaption
     "Figure 5: Method of water detection, consisting of the following steps:"
     " 1) compute water index,  2) compute edges using Canny edge detector"
     " 3) create buffer around the edges using dilation 4) compute threshold"
     " value using Otsu method 5) threshold index values."]]
   [:hr]
   [:h1 "Development and Acknowledgment"]
   [:p
    "The development of the algorithm that transforms Landsat7/8 was initiated"
    " in the PhD research of Gennadii Donchyts (co-funded by Deltares and"
    " Technical University Delft). Testing and further development of the"
    " algorithm using the Murray-Darling basin in Australia was funded by the"
    " EC FP7 project eartH2Observe (under grant agreement No 603608 which led"
    " to the publication of Donchyts et.al. 2016 (see below))."]
   [:p
    "Application to the Mekong-Basin, which includes testing, applying and"
    " adjusting dynamic thresholds and further optimisation of the scripts to"
    " fully take advantage of GEE capabilities was supported by the"
    " SERVIR-Mekong project. The development of the method to calculate the"
    " main supporting dataset (Height Above Nearest Drain, HAND) was fully"
    " supported by the eartH2Observe project, but the application for the"
    " MEKONG was supported by the SERVIR Mekong project."]
   [:p
    "The Google Appspot based user interface for the Mekong was fully"
    " supported by the SERVIR Mekong project."]
   [:p
    "Processing support and Google cloud storage needed to calculate the"
    " HAND product were supported by a grant from Google."]
   [:div#about-logos
    [:img {:src "/static/images/servir.png"}]
    [:img {:src "/static/images/usaid.png"}]
    [:img {:src "/static/images/nasa.png"}]
    [:img {:src "/static/images/adpclogo.jpg"}]
    [:img {:src "/static/images/googlelogo_color_272x92dp.png"}]
    [:img {:src "/static/images/logosig.png"}]
    [:img {:src "/static/images/winrocklogo.jpg"}]
    [:img {:src "/static/images/mardlogo.jpg"}]
    [:img {:src "/static/images/sei_tr.png"}]
    [:img {:src "/static/images/deltares_tr.png"}]]
   [:p#copyright
    "Copyright "
    (str/unescapeEntities "&copy;")
    " Deltares and "
    [:a {:href "http://www.sig-gis.com" :target "_blank"} "SIG-GIS"]
    " 2016"]
   [:hr]
   [:h1 "References"]
   [:p
    "Gennadii Donchyts, Jaap Schellekens, Hessel Winsemius, Elmar Eisemann and"
    " Nick van de Giesen (2016) 30 m Resolution Surface Water Mask Including"
    " Estimation of Positional and Thematic Differences Using Landsat 8, SRTM"
    " and OpenStreetMap: A Case Study in the Murray-Darling Basin, Australia."
    " Remote Sensing, 8(5), 386."]
   [:p
    "Rennó, C. D., Nobre, A. D., Cuartas, L. A., Soares, J. V., Hodnett, M. G.,"
    " Tomasella, J., & Waterloo, M. J. (2008). HAND, a new terrain descriptor"
    " using SRTM-DEM: Mapping terra-firme rainforest environments in Amazonia."
    " Remote Sensing of Environment, 112(9), 3469-3481."]
   [:div#bottom-spacer]])

(defn page-content []
  [:div#all-pages
   [app/content (make-page-visibility-style 0)]
   [about-page  (make-page-visibility-style 1)]])

;;==================
;; CLJS Entry Point
;;==================

(defn ^:export main [country-polygons province-polygons]
  (r/render [page-header] (dom/getElement "pageheader"))
  (r/render [page-content] (dom/getElement "pagecontent"))
  (app/init country-polygons province-polygons))
