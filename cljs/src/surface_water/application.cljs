(ns surface-water.application
  (:require [goog.dom :as dom]
            [goog.string :as str]
            [reagent.core :as r]
            [cognitect.transit :as transit]
            [cljs-http.client :as http]
            [cljs.core.async :refer [<!]])
  (:require-macros [cljs.core.async.macros :refer [go]])
  (:import (goog.i18n DateTimeFormat)
           (goog.i18n DateTimeParse)
           (goog.ui InputDatePicker)))

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

;;==============
;; Map Controls
;;==============

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

(declare remove-map-features! enable-province-selection!
         enable-country-selection! enable-custom-polygon-selection! get-slider-vals
         refresh-image)

(defn set-val! [id val]
  (set! (.-value (dom/getElement id)) val))

(defn check! [id]
  (set! (.-checked (dom/getElement id)) true))

(defn uncheck! [id]
  (set! (.-checked (dom/getElement id)) false))

(defonce month (r/atom 1))

(def month-id-to-name
  {"1" "January"
   "2" "February"
   "3" "March"
   "4" "April"
   "5" "May"
   "6" "June"
   "7" "July"
   "8" "August"
   "9" "September"
   "10" "October"
   "11" "November"
   "12" "December"})

(defn expert-controls []
  [:div#expert-controls
   [:ul
    [:li
     [:label "Show months:"]
     [:input#climatology-input {:type "checkbox" :value "None"
                                :on-click #(if (visible-control? :month-control)
                                             (hide-control! :month-control)
                                             (show-control! :month-control))}]
     [:div#month-control (get-display-style :month-control)
      [:p (str "Month: " (month-id-to-name @month))]
      [:input#month-slider {:type "range" :min "1" :max "12" :step "1"
                            :default-value "1"
                            :on-change #(reset! month
                                                (.-value (.-currentTarget %)))}]]]
    [:li
     [:label "Defringe images:"]
     [:input#defringe-input {:type "checkbox" :value "None"}]]
    [:li
     [:label "Permanent water percentile:"]
     [:input#percentile-input-perm {:type "number" :min "0" :max "100" :default-value "40"}]]
    [:li
     [:label "Temporary water percentile:"]
     [:input#percentile-input-temp {:type "number" :min "0" :max "100" :default-value "8"}]]
    [:li
     [:label "Water threshold:"]
     [:input#water-threshold-input
      {:type "number" :min "-1" :max "1" :step "0.05" :default-value "0.3"}]]
    [:li
     [:label "Vegetation threshold:"]
     [:input#veg-threshold-input
      {:type "number" :min "-1" :max "1" :step "0.05" :default-value "0.35"}]]
    [:li
     [:label "HAND threshold:"]
     [:input#hand-threshold-input
      {:type "number" :min "0" :max "9999" :step "1" :default-value "25"}]]
    [:li
     [:label "Cloud threshold:"]
     [:input#cloud-threshold-input
      {:type "number" :min "0" :max "1" :step "0.05" :default-value "0"}]]]
   [:input#expert-reset {:type "button" :value "Reset"
                         :on-click (fn [_]
                                     (uncheck! "climatology-input")
                                     (uncheck! "defringe-input")
                                     (set-val! "percentile-input-perm" "40")
                                     (set-val! "percentile-input-temp" "8")
                                     (set-val! "water-threshold-input" "0.3")
                                     (set-val! "veg-threshold-input" "0.35")
                                     (set-val! "hand-threshold-input" "25")
                                     (set-val! "cloud-threshold-input" "0"))}]
   [:input#expert-submit {:type "button" :value "Submit"}]])

(defn map-controls []
  [:div#controls
   [:h3 "Step 1: Select a time period for the calculation"]
   [:ul
    [:li [:input#start-date {:type "text"}]]
    [:li "-"]
    [:li [:input#end-date {:type "text"}]]]
   [:h3 "Step 2: Update the map with the new water layer"]
   [:input {:type "button" :name "update-map" :value "Update Map"
            :on-click #(do (remove-map-features!)
                           (reset! polygon-selection-method "")
                           (refresh-image))}]
   [:h3 "Step 3: Choose a polygon selection method"]
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
   [:h3 "Step 4: Click a polygon on the map or draw your own"]
   [:p#polygon
    (str @polygon-selection-method " Selection: ")
    [:em (clojure.string/join ", " @polygon-selection)]]
   [:h3 "Step 5: Export the selected region's water data"]
   [:input.filename.form-control
    {:type "text" :name "filename"
     :placeholder "default: SurfaceWater_Export_<year>"}]
   [expert-controls]])

;;=========================
;; Application Page Layout
;;=========================

(defonce opacity (r/atom 1.0))

(declare update-opacity!)

(defn content [page-visibility]
  [:div#water page-visibility
   [:div#map]
   [:div#ui {:style (get-display-style :ui)}
    [:header
     [:h1 "Surface Water Tool Controls"]
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
    [:h2 "Legend"]
    [:table
     [:tbody
      [:tr
       [:td [:div#legend-study-area]]
       [:td "Study area"]]
      [:tr
       [:td [:div#legend-permanent-water]]
       [:td "Permanent water"]]
      [:tr
       [:td [:div#legend-temporary-water]]
       [:td "Temporary water"]]]]]
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

(def *minimum-time-period-regular* 90) ;; days

(def *minimum-time-period-climatology* 1095) ;; days

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

(declare get-ee-map-type show-basic-map)

(defn log [& vals]
  (.log js/console (apply str vals)))

(defn create-map []
  (google.maps.Map.
   (dom/getElement "map")
   ;; #js {:center #js {:lng 107.5 :lat 17.0}
   ;;      :zoom 5
   ;;      :maxZoom 12
   ;;      :streetViewControl false}
   #js {:center #js {:lng 104.0 :lat 12.5}
        :zoom 7
        :maxZoom 14
        :streetViewControl false}))

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
    (reset! polygon-selection [])))

(defn update-opacity! [val]
  (reset! opacity val)
  (let [overlay-map-types (.-overlayMapTypes @google-map)]
    (.forEach overlay-map-types
              (fn [map-type index]
                (if map-type
                  (.setOpacity (.getAt overlay-map-types index) val))))))

;; 1. load the JSON file from disk for each province and display them on the map
;; 2. set the stroke and fill colors to SandyBrown and the stroke weight to 2
(defn enable-province-selection! []
  (let [map-features (.-data @google-map)]
    (doseq [province @province-names]
      (.loadGeoJson map-features (str "/static/province/" province ".json")))
    (.setStyle map-features
               (fn [feature] #js {:fillColor "SandyBrown"
                                  :strokeColor "SandyBrown"
                                  :strokeWeight 2}))
    (reset! country-or-province 0)))

;; 1. load the JSON file from disk for each country and display them on the map
;; 2. set the stroke and fill colors to SandyBrown and the stroke weight to 2
(defn enable-country-selection! []
  (let [map-features (.-data @google-map)]
    (doseq [country @country-names]
      (.loadGeoJson map-features (str "/static/country/" country ".json")))
    (.setStyle map-features
               (fn [feature] #js {:fillColor "SandyBrown"
                                  :strokeColor "SandyBrown"
                                  :strokeWeight 2}))
    (reset! country-or-province 1)))

;; 1. add event to all-overlays
;; 2. increment polygon-counter
;; 3. update the drawing-manager to use the next polygon color
;; 4. collect the polygon coords and reads the baseline and study slider vals
;; 5. send an AJAX request for that polygon over the specified time ranges
;; 6. log the AJAX request url and response maps to the console
;; 7. add (str "my area " @polygon-counter) to my-name
;; 8. show a new chart
;;
;; NOTE: geom is (-> event .-overlay .getPath .getArray)
(defn custom-overlay-handler [drawing-manager event]
  (swap! all-overlays conj event)
  (swap! polygon-counter inc)
  (swap! polygon-selection conj (str "Shape " @polygon-counter)))

;; 1. create drawing-manager
;; 2. attach it to the map
;; 3. add event listener to the map to call custom-overlay-handler when done drawing
(defn enable-custom-polygon-selection! []
  (let [counter         @polygon-counter
        drawing-manager (google.maps.drawing.DrawingManager.
                         #js {:drawingMode google.maps.drawing.OverlayType.POLYGON
                              :drawingControl false
                              :polygonOptions
                              #js {:fillColor "SandyBrown"
                                   :strokeColor "SandyBrown"
                                   :strokeWeight 2}})]
    (google.maps.event.addListener drawing-manager
                                   "overlaycomplete"
                                   #(custom-overlay-handler drawing-manager %))
    (.setMap drawing-manager @google-map)
    (reset! active-drawing-manager drawing-manager)))

(defn handle-polygon-click [event]
  (let [feature (.-feature event)
        title   (.getProperty feature "title")]
    (swap! polygon-selection conj title)
    (swap! polygon-counter inc)))

(defn get-ee-map-type [ee-map-id ee-token layer-name]
  (google.maps.ImageMapType.
   #js {:name layer-name
        :opacity 1.0
        :tileSize (google.maps.Size. 256 256)
        :getTileUrl (fn [tile zoom]
                      (str "https://earthengine.googleapis.com/map/"
                           ee-map-id "/" zoom "/" (.-x tile) "/" (.-y tile)
                           "?token=" ee-token))}))

(defn show-basic-map [ee-map-id ee-token layer-name]
  (.push (.-overlayMapTypes @google-map)
         (get-ee-map-type ee-map-id ee-token layer-name)))

(defn checked? [id]
  (.-checked (dom/getElement id)))

(defn val-as-float [id]
  (js/parseFloat (.-value (dom/getElement id))))

(defn ms-to-days [milliseconds]
  (-> milliseconds
      (/ 1000)
      (/ 60)
      (/ 60)
      (/ 24)))

(defn number-of-days [start-date end-date]
  (ms-to-days (- (.getTime (js/Date. end-date))
                 (.getTime (js/Date. start-date)))))

(defn remove-layer [layer-name]
  (let [map-types (.-overlayMapTypes @google-map)]
    (.forEach map-types (fn [map-type index]
                          (if (and map-type (= (.-name map-type) layer-name))
                            (.removeAt map-types index))))))

;; FIXME: Store params in an atom and skip the AJAX query if no parameters
;;        have changed since last time.
(defn refresh-image []
  (let [time-start   (.-value (dom/getElement "start-date"))
        time-end     (.-value (dom/getElement "end-date"))
        climatology  (checked? "climatology-input")
        month-index  @month
        defringe     (checked? "defringe-input")
        pcnt-perm    (val-as-float "percentile-input-perm")
        pcnt-temp    (val-as-float "percentile-input-temp")
        water-thresh (val-as-float "water-threshold-input")
        veg-thresh   (val-as-float "veg-threshold-input")
        hand-thresh  (val-as-float "hand-threshold-input")
        cloud-thresh (val-as-float "cloud-threshold-input")]
    (cond (and (true? climatology)
               (< (number-of-days time-start time-end)
                  *minimum-time-period-climatology*))
          (js/alert (str "Warning! Time period for climatology is too short! "
                         "Make sure it is at least 3 years (1095 days)!"))

          (< (number-of-days time-start time-end) *minimum-time-period-regular*)
          (js/alert (str "Warning! Time period is too short! "
                         "Make sure it is at least 3 months (90 days)!"))

          :otherwise
          (do (if (true? climatology)
                (show-control! :month-control)
                (hide-control! :month-control))
              (let [map-url (str "/get_water_map?"
                                 "time_start=" time-start "&"
                                 "time_end=" time-end "&"
                                 "climatology=" climatology "&"
                                 "month_index=" month-index "&"
                                 "defringe=" defringe "&"
                                 "pcnt_perm=" pcnt-perm "&"
                                 "pcnt_temp=" pcnt-temp "&"
                                 "water_thresh=" water-thresh "&"
                                 "veg_thresh=" veg-thresh "&"
                                 "hand_thresh=" hand-thresh "&"
                                 "cloud_thresh=" cloud-thresh)]
                (show-progress!)
                (log "AJAX Request: " map-url)
                (go (let [response (<! (http/get map-url))]
                      (log "AJAX Response: " response)
                      (if (:success response)
                        (let [ee-map-id (-> response :body :eeMapId)
                              ee-token  (-> response :body :eeToken)]
                          (remove-layer "water")
                          (show-basic-map ee-map-id ee-token "water"))
                        (js/alert "An error occurred! Please refresh the page."))
                      (hide-progress!))))))))

;; FIXME: Should we reduce these layers' opacity or simply not show them at all?
(defn load-basic-maps []
  (let [map-url "/get_basic_maps"]
    (show-progress!)
    (log "AJAX Request: " map-url)
    (go (let [response (<! (http/get map-url))]
          (log "AJAX Response: " response)
          (if (:success response)
            (let [ee-map-id-border (-> response :body :eeMapId_border)
                  ee-token-border  (-> response :body :eeToken_border)
                  ee-map-id-fill   (-> response :body :eeMapId_fill)
                  ee-token-fill    (-> response :body :eeToken_fill)]
              ;; (show-basic-map ee-map-id-fill ee-token-fill "AoI_fill")
              (show-basic-map ee-map-id-border ee-token-border "AoI_border"))
            (js/alert "An error occurred! Please refresh the page."))
          (hide-progress!)))))

(defn parse-date [js-date]
  {:year  (.getFullYear js-date)
   :month (inc (.getMonth js-date))
   :date  (.getDate js-date)})

;; FIXME: Set the min date to 1988-01-01 and the max date to today (js/Date.)
(defn attach-datepicker! [element]
  (let [pattern   "yyyy'-'MM'-'dd"
        formatter (DateTimeFormat. pattern)
        parser    (DateTimeParse. pattern)]
    (doto (InputDatePicker. formatter parser)
      ;; (.addEventListener
      ;;  goog.ui.DatePicker.Events.CHANGE
      ;;  (fn [evt] (reset! atom (.-date evt))))
      (.decorate element))))

(defn init-date-pickers []
  (let [start-date-picker (dom/getElement "start-date")
        end-date-picker   (dom/getElement "end-date")]
    (attach-datepicker! start-date-picker)
    (attach-datepicker! end-date-picker)
    (set! (.-value start-date-picker) "2014-01-01")
    (set! (.-value end-date-picker) "2014-12-31")))

;; FIXME: Finish implementing the commented out functions
(defn init [country-polygons province-polygons]
  (let [json-reader       (transit/reader :json)
        country-polygons  (transit/read json-reader country-polygons)
        province-polygons (transit/read json-reader province-polygons)]
    (log "Countries: " (count country-polygons))
    (log "Provinces: " (count province-polygons))
    (reset! google-map (create-map))
    (reset! country-names country-polygons)
    (reset! province-names province-polygons)
    ;; (create-drawing-manager)
    (init-date-pickers)
    ;; (init-region-picker)
    ;; (opacity-sliders)
    ;; (expert-submit)
    ;; (climatology-slider)
    ;; (init-export)
    (.addListener (.-data @google-map) "click" handle-polygon-click)
    (load-basic-maps)
    (refresh-image)))
