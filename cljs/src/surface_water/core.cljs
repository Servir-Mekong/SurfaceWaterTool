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
   [:div.logos
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
    "In simple terms, the tool works by first merging data from different"
    " landsat satellite missions to one big stack of images for the selected"
    " period. From this stack of images two percentiles are calculated for"
    " each pixel, one rather low percentile (default 8%) and one higher"
    " percentile (40%). Here, a percentile is a measure indicating the value"
    " below which a given percentage of pixels in a group of pixels falls. For"
    " these two percentile maps the Normalized Difference Water Index (NDWI)"
    " is calculated. This index combines several spectral bands that are"
    " sensitive the the occurrence of water. For each percentile map a threshold"
    " value is applied classifying pixels as water or non-water. The resulting"
    " maps give an indication of the number of times a given pixel was classified"
    " as water vs. non water over the selected period (but not an exact value)."
    " So for the 8% map the pixels are covered with water much less than the 40%"
    " maps and these are indicated as temporary and permanent water respectively."
    " Due to the statistical nature of this method the maps are asynchronous in"
    " time, i.e. not each pixel is covered with water at the same time but these"
    " maps are an integration over the selected period. In further steps, the"
    " water detection is refined by checking for areas that are unlikely to have"
    " surface water and filter out dark vegetation wrongly detected as water."]
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
    " supported by the SERVIR Mekong project. Processing support and Google"
    " cloud storage needed to calculate the HAND product were supported by"
    " a grant from Google."]
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
    " Remote Sensing of Environment, 112(9), 3469-3481."]])

(defn page-content []
  [:div#all-pages
   [app/content (make-page-visibility-style 0)]
   [about-page  (make-page-visibility-style 1)]])

;;=============
;; Page Footer
;;=============

(defn page-footer []
  [:footer
   [:div.logos
    [:img#sig      {:src "/static/images/logosig.png"}]
    [:img#sei      {:src "/static/images/sei_tr.png"}]
    [:img#deltares {:src "/static/images/deltares_tr.png"}]]])

;;==================
;; CLJS Entry Point
;;==================

(defn ^:export main [country-polygons province-polygons]
  (r/render [page-header] (dom/getElement "pageheader"))
  (r/render [page-content] (dom/getElement "pagecontent"))
  (r/render [page-footer] (dom/getElement "pagefooter"))
  (app/init country-polygons province-polygons))
