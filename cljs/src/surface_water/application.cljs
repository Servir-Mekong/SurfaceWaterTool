(ns surface-water.application
  (:require [goog.dom :as dom]
            [goog.string :as str]
            [reagent.core :as r]
            [cognitect.transit :as transit]
            [cljs-http.client :as http]
            [cljs.core.async :refer [<!]])
  (:require-macros [cljs.core.async.macros :refer [go]]))

;;===========================
;; Show/Hide Page Components
;;===========================

(defonce visible-controls (r/atom #{:info :settings-button}))

(defn visible-control? [control]
  (contains? @visible-controls control))

(defn get-display-style [control]
  (if (visible-control? control)
    {:display "block"}
    {:display "none"}))

(defn show-control! [control]
  (swap! visible-controls conj control))

(defn hide-control! [control]
  (swap! visible-controls disj control))

;;===========================
;; Multi-Range Slider Widget
;;===========================

(defonce slider-vals (r/atom {}))

(defn get-slider-vals [slider-id]
  (into [] (sort (vals (@slider-vals slider-id)))))

(defn get-formatted-slider-vals [slider-id]
  (let [[min max] (get-slider-vals slider-id)]
    (str min " - " max)))

(defn update-slider-vals! [slider-id idx slider-val]
  (swap! slider-vals assoc-in [slider-id idx] (str slider-val)))

(defn multi-range [slider-id min max step low high]
  (update-slider-vals! slider-id 0 low)
  (update-slider-vals! slider-id 1 high)
  (fn []
    [:div.range-slider
     [:p (get-formatted-slider-vals slider-id)]
     [:input {:type "range" :min (str min) :max (str max)
              :step (str step) :default-value (str low)
              :on-change #(let [val (.-value (.-currentTarget %))]
                            (update-slider-vals! slider-id 0 val))}]
     [:input {:type "range" :min (str min) :max (str max)
              :step (str step) :default-value (str high)
              :on-change #(let [val (.-value (.-currentTarget %))]
                            (update-slider-vals! slider-id 1 val))}]]))

;;==============
;; Map Controls
;;==============

(defonce multi-range1 (multi-range :baseline 2000 2017 1 2006 2008))
(defonce multi-range2 (multi-range :study 2000 2017 1 2009 2011))

(defonce polygon-selection-method (r/atom ""))

(defonce polygon-selection (r/atom []))

(defonce spinner-visible? (r/atom false))

(defn show-progress! []
  (reset! spinner-visible? true))

(defn hide-progress! []
  (reset! spinner-visible? false))

(defn get-spinner-visibility []
  (if @spinner-visible?
    {:visibility "visible"}
    {:visibility "hidden"}))

(declare show-map! remove-map-features! enable-province-selection!
         enable-country-selection! enable-custom-polygon-selection!)

(defn map-controls []
  [:div#controls
   [:h3 "Step 1: Select a time period to use as the baseline EVI"]
   [multi-range1]
   [:h3 "Step 2: Select a time period to measure ∆EVI"]
   [multi-range2]
   [:h3 "Step 3: Update the map with the cumulative ∆EVI"]
   [:input {:type "button" :name "update-map" :value "Update Map"
            :on-click #(do (remove-map-features!)
                           (reset! polygon-selection-method "")
                           (show-map!))}]
   [:h3 "Step 4: Choose a polygon selection method"]
   [:ul
    [:li
     [:input {:type "radio" :name "polygon-selection-method" :value "Province"
              :checked (if (= @polygon-selection-method "Province")
                         "checked"
                         "")
              :on-click #(do (reset! polygon-selection-method
                                     (.-value (.-currentTarget %)))
                             (remove-map-features!)
                             (enable-province-selection!))}]
     [:label "Province"]]
    [:li
     [:input {:type "radio" :name "polygon-selection-method" :value "Country"
              :checked (if (= @polygon-selection-method "Country")
                         "checked"
                         "")
              :on-click #(do (reset! polygon-selection-method
                                     (.-value (.-currentTarget %)))
                             (remove-map-features!)
                             (enable-country-selection!))}]
     [:label "Country"]]
    [:li
     [:input {:type "radio" :name "polygon-selection-method" :value "Draw Polygon"
              :checked (if (= @polygon-selection-method "Draw Polygon")
                         "checked"
                         "")
              :on-click #(do (reset! polygon-selection-method
                                     (.-value (.-currentTarget %)))
                             (remove-map-features!)
                             (enable-custom-polygon-selection!))}]
     [:label "Draw Polygon"]]]
   [:h3 "Step 5: Click a polygon on the map or draw your own"]
   [:p#polygon
    (str @polygon-selection-method " Selection: ")
    [:em (clojure.string/join ", " @polygon-selection)]]
   [:h3 "Step 6: Review the historical ∆EVI in the selection"]
   [:div#chart {:style (get-display-style :chart)}]])

;;=========================
;; Application Page Layout
;;=========================

(defonce opacity (r/atom 1.0))

(declare update-opacity!)

(defn content [page-visibility]
  [:div#ecodash page-visibility
   [:div#map]
   [:div#ui {:style (get-display-style :ui)}
    [:header
     [:h1 "SurfaceWaterTool Controls"]
     [:div#collapse-button {:on-click (fn []
                                        (hide-control! :ui)
                                        (show-control! :settings-button))}
      (str/unescapeEntities "&#171;")]
     [:input#info-button {:type "button" :name "info-button" :value "i"
                          :on-click (fn []
                                      (if (visible-control? :info)
                                        (hide-control! :info)
                                        (show-control! :info)))}]]
    [map-controls]]
   [:div#settings-button {:style (get-display-style :settings-button)
                          :on-click (fn []
                                      (hide-control! :settings-button)
                                      (show-control! :ui))}
    (str/unescapeEntities "&#9776;")]
   [:div#general-info {:style (get-display-style :info)}
    [:h1 "Surface Water Tool"]
    [:h2 "Surface Water Detection and Mapping"]
    [:h3 "Explore regional droughts, floods, and baseline conditions."]
    [:hr]
    [:p
     "The Surface Water Tool is a collaborative effort between its developers and "
     "its community of users. We welcome suggestions for improvements on our "
     [:a {:href "https://github.com/Servir-Mekong/SurfaceWaterTool/issues"
          :target "_blank"}
      "Github"]
     " issues page."]
    [:input {:type "button" :name "get-started-button" :value "Get Started!"
             :on-click (fn []
                         (hide-control! :info)
                         (hide-control! :settings-button)
                         (show-control! :ui))}]]
   [:div#legend
    [:h2 "∆EVI"]
    [:table
     [:tbody
      [:tr
       [:td {:row-span "3"} [:img {:src "/static/images/mylegend.png"}]]
       [:td "Increase"]]
      [:tr
       [:td "Stable"]]
      [:tr
       [:td "Decrease"]]]]]
   [:div#opacity
    [:p (str "Opacity: " @opacity)]
    [:input {:type "range" :min "0" :max "1" :step "0.1" :default-value "1"
             :on-change #(update-opacity!
                          (js/parseFloat (.-value (.-currentTarget %))))}]]
   [:p#feedback [:a {:href "https://docs.google.com/a/sig-gis.com/forms/d/1pOgXeWJaDWg8NlC-ZalZJTzUdv9sVjNdXibZVPo4l4I/edit?ts=57ec6a52"
                     :target "_blank"}
                 "Give us Feedback!"]]
   [:div.spinner {:style (get-spinner-visibility)}]])

;;===================
;; Application Logic
;;===================

(defonce google-map (atom nil))

(defonce province-names (atom []))

(defonce country-names (atom []))

(defonce country-or-province (atom nil))

(defonce polygon-counter (atom 0))

(defonce active-drawing-manager (atom nil))

(defonce all-overlays (atom []))

(defonce chart-data (atom nil))

(defonce css-colors
  ["Aqua" "Black" "Blue" "BlueViolet" "Brown" "Aquamarine" "BurlyWood" "CadetBlue"
   "Chartreuse" "Chocolate" "Coral" "CornflowerBlue" "Cornsilk" "Crimson" "Cyan"
   "DarkBlue" "DarkCyan" "DarkGoldenRod" "DarkGray" "DarkGrey" "DarkGreen"
   "DarkKhaki" "DarkMagenta" "DarkOliveGreen" "Darkorange" "DarkOrchid" "DarkRed"
   "DarkSalmon" "DarkSeaGreen" "DarkSlateBlue" "DarkSlateGray" "DarkSlateGrey"
   "DarkTurquoise" "DarkViolet" "DeepPink" "DeepSkyBlue" "DimGray" "DimGrey"
   "DodgerBlue" "FireBrick" "FloralWhite" "ForestGreen" "Fuchsia" "Gainsboro"
   "GhostWhite" "Gold" "GoldenRod" "Gray" "Grey" "Green" "GreenYellow" "HoneyDew"
   "HotPink" "IndianRed" "Indigo" "Ivory" "Khaki" "Lavender" "LavenderBlush"
   "LawnGreen" "LemonChiffon" "LightBlue" "LightCoral" "LightCyan"
   "LightGoldenRodYellow" "LightGray" "LightGrey" "LightGreen" "LightPink"
   "LightSalmon" "LightSeaGreen" "LightSkyBlue" "LightSlateGray" "LightSlateGrey"
   "LightSteelBlue" "LightYellow" "Lime" "LimeGreen" "Linen" "Magenta" "Maroon"
   "MediumAquaMarine" "MediumBlue" "MediumOrchid" "MediumPurple" "MediumSeaGreen"
   "MediumSlateBlue" "MediumSpringGreen" "MediumTurquoise" "MediumVioletRed"
   "MidnightBlue" "MintCream" "MistyRose" "Moccasin" "NavajoWhite" "Navy" "OldLace"
   "Olive" "OliveDrab" "Orange" "OrangeRed" "Orchid" "PaleGoldenRod" "PaleGreen"
   "PaleTurquoise" "PaleVioletRed" "PapayaWhip" "PeachPuff" "Peru" "Pink" "Plum"
   "PowderBlue" "Purple" "Red" "RosyBrown" "RoyalBlue" "SaddleBrown" "Salmon"
   "SandyBrown" "SeaGreen" "SeaShell" "Sienna" "Silver" "SkyBlue" "SlateBlue"
   "SlateGray" "SlateGrey" "Snow" "SpringGreen" "SteelBlue" "Tan" "Teal" "Thistle"
   "Tomato" "Turquoise" "Violet" "Wheat" "White" "WhiteSmoke" "Yellow"
   "YellowGreen"])

(defn log [& vals]
  (.log js/console (apply str vals)))

(defn create-map []
  (google.maps.Map.
   (dom/getElement "map")
   #js {:center #js {:lng 107.5 :lat 17.0}
        :zoom 5
        :maxZoom 12
        :streetViewControl false}))

(defn clear-chart! []
  (reset! chart-data nil)
  (hide-control! :chart)
  (set! (.-innerHTML (dom/getElement "chart")) nil))

(defn remove-map-features! []
  (let [map-features (.-data @google-map)]
    (.forEach map-features #(.remove map-features %))
    (.revertStyle map-features)
    (doseq [event @all-overlays]
      (.setMap (.-overlay event) nil))
    (when @active-drawing-manager
      (.setMap @active-drawing-manager nil)
      (reset! active-drawing-manager nil))
    (reset! all-overlays [])
    (reset! polygon-counter 0)
    (reset! polygon-selection [])
    (clear-chart!)))

(defn update-opacity! [val]
  (reset! opacity val)
  (let [overlay-map-types (.-overlayMapTypes @google-map)]
    (.forEach overlay-map-types
              (fn [map-type index]
                (if map-type
                  (.setOpacity (.getAt overlay-map-types index) val))))))

;; 1. load the JSON file from disk for each province and display them on the map
;; 2. set the stroke and fill colors to white and the stroke weight to 2
(defn enable-province-selection! []
  (let [map-features (.-data @google-map)]
    (doseq [province @province-names]
      (.loadGeoJson map-features (str "/static/province/" province ".json")))
    (.setStyle map-features
               (fn [feature] #js {:fillColor "white"
                                  :strokeColor "white"
                                  :strokeWeight 2}))
    (reset! country-or-province 0)))

;; 1. load the JSON file from disk for each country and display them on the map
;; 2. set the stroke and fill colors to white and the stroke weight to 2
(defn enable-country-selection! []
  (let [map-features (.-data @google-map)]
    (doseq [country @country-names]
      (.loadGeoJson map-features (str "/static/country/" country ".json")))
    (.setStyle map-features
               (fn [feature] #js {:fillColor "white"
                                  :strokeColor "white"
                                  :strokeWeight 2}))
    (reset! country-or-province 1)))

(defn show-chart! [time-series]
  (if @chart-data
    (swap! chart-data
           #(mapv (fn [val-stack [time val]] (conj val-stack val))
                  %
                  time-series))
    (reset! chart-data
            (mapv (fn [[time val]] [(js/Date. (js/parseInt time 10)) val])
                  time-series)))
  (let [table (google.visualization.DataTable.)]
    (.addColumn table "date")
    (doseq [polygon-name @polygon-selection]
      (.addColumn table "number" polygon-name))
    (.addRows table (clj->js @chart-data))
    (doto (google.visualization.ChartWrapper.
           #js {:chartType "LineChart"
                :dataTable table
                :options #js {:height 200
                              :width 385
                              :title "Biophysical Health"
                              :titleTextStyle #js {:fontName "Open Sans"}
                              :legend #js {:position "right"}
                              :curveType "function"
                              :chartArea #js {:left 50
                                              :top 50
                                              :height 100
                                              :width 200}
                              :colors (clj->js css-colors)}})
      (.setContainerId (dom/getElement "chart"))
      (.draw))
    (show-control! :chart)))

;; 1. add event to all-overlays
;; 2. increment polygon-counter
;; 3. update the drawing-manager to use the next polygon color
;; 4. collect the polygon coords and reads the baseline and study slider vals
;; 5. send an AJAX request for that polygon over the specified time ranges
;; 6. log the AJAX request url and response maps to the console
;; 7. add (str "my area " @polygon-counter) to my-name
;; 8. show a new chart
(defn custom-overlay-handler [drawing-manager event]
  (show-progress!)
  (swap! all-overlays conj event)
  (swap! polygon-counter inc)
  (let [color (css-colors @polygon-counter)]
    (.setOptions drawing-manager
                 #js {:polygonOptions
                      #js {:fillColor color
                           :strokeColor color}}))
  (let [geom           (-> event .-overlay .getPath .getArray)
        baseline       (get-slider-vals :baseline)
        study          (get-slider-vals :study)
        polygon-url    (str "/polygon?"
                            "polygon=" geom "&"
                            "refLow=" (baseline 0) "&"
                            "refHigh=" (baseline 1) "&"
                            "studyLow=" (study 0) "&"
                            "studyHigh=" (study 1))
        counter         @polygon-counter]
    (swap! polygon-selection conj (str "Shape " counter))
    (log "AJAX Request: " polygon-url)
    (go (let [response (<! (http/get polygon-url))]
          (log "AJAX Response: " response)
          (if (:success response)
            (show-chart! (-> response :body))
            (js/alert "An error occurred! Please refresh the page."))
          (hide-progress!)))))

;; 1. create drawing-manager
;; 2. attach it to the map
;; 3. add event listener to the map to call custom-overlay-handler when done drawing
(defn enable-custom-polygon-selection! []
  (let [counter         @polygon-counter
        drawing-manager (google.maps.drawing.DrawingManager.
                         #js {:drawingMode google.maps.drawing.OverlayType.POLYGON
                              :drawingControl false
                              :polygonOptions
                              #js {:fillColor (css-colors counter)
                                   :strokeColor (css-colors counter)}})]
    (google.maps.event.addListener drawing-manager
                                   "overlaycomplete"
                                   #(custom-overlay-handler drawing-manager %))
    (.setMap drawing-manager @google-map)
    (reset! active-drawing-manager drawing-manager)))

(defn get-ee-map-type [ee-map-id ee-token]
  (google.maps.ImageMapType.
   #js {:name "ecomap"
        :opacity 1.0
        :tileSize (google.maps.Size. 256 256)
        :getTileUrl (fn [tile zoom]
                      (str "https://earthengine.googleapis.com/map/"
                           ee-map-id "/" zoom "/" (.-x tile) "/" (.-y tile)
                           "?token=" ee-token))}))

(defn show-map! []
  (let [overlay-map-types (.-overlayMapTypes @google-map)
        baseline          (get-slider-vals :baseline)
        study             (get-slider-vals :study)
        map-url           (str "/getmap?"
                               "refLow=" (baseline 0) "&"
                               "refHigh=" (baseline 1) "&"
                               "studyLow=" (study 0) "&"
                               "studyHigh=" (study 1))]
    (show-progress!)
    (.clear overlay-map-types)
    (log "AJAX Request: " map-url)
    (go (let [response (<! (http/get map-url))]
          (log "AJAX Response: " response)
          (if (:success response)
            (let [ee-map-id (-> response :body :eeMapId)
                  ee-token  (-> response :body :eeToken)]
              (.push overlay-map-types (get-ee-map-type ee-map-id ee-token)))
            (js/alert "An error occurred! Please refresh the page."))
          (hide-progress!)))))

(defn handle-polygon-click [event]
  (show-progress!)
  (let [feature (.-feature event)
        color   (css-colors @polygon-counter)]
    (.overrideStyle (.-data @google-map)
                    feature
                    #js {:fillColor color
                         :strokeColor color
                         :strokeWeight 6})
    (swap! polygon-counter inc)
    (let [title       (.getProperty feature "title")
          id          (.getProperty feature "id")
          baseline    (get-slider-vals :baseline)
          study       (get-slider-vals :study)
          details-url (str "/details?"
                           "polygon_id=" id "&"
                           "refLow=" (baseline 0) "&"
                           "refHigh=" (baseline 1) "&"
                           "studyLow=" (study 0) "&"
                           "studyHigh=" (study 1) "&"
                           "folder=" @country-or-province)]
      (swap! polygon-selection conj title)
      (log "AJAX Request: " details-url)
      (go (let [response (<! (http/get details-url))]
            (log "AJAX Response: " response)
            (if (:success response)
              (show-chart! (-> response :body :timeSeries))
              (js/alert "An error occurred! Please refresh the page."))
            (hide-progress!))))))

(defn refresh-image [ee-map-id ee-token]
  (.push (.-overlayMapTypes @google-map)
         (get-ee-map-type ee-map-id ee-token)))

(defn init [ee-map-id ee-token country-polygons province-polygons]
  (let [json-reader       (transit/reader :json)
        country-polygons  (transit/read json-reader country-polygons)
        province-polygons (transit/read json-reader province-polygons)]
    (log "EE Map ID: " ee-map-id)
    (log "EE Token: " ee-token)
    (log "Countries: " (count country-polygons))
    (log "Provinces: " (count province-polygons))
    (.load js/google "visualization" "1.0")
    (reset! google-map (create-map))
    (reset! country-names country-polygons)
    (reset! province-names province-polygons)
    (.addListener (.-data @google-map) "click" handle-polygon-click)
    (refresh-image ee-map-id ee-token)))
