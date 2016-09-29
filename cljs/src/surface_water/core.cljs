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
    [:img#google {:src "/static/images/googlelogo_color_272x92dp.png"}]
    [:img#adpc   {:src "/static/images/adpclogo.jpg"}]
    [:img#servir {:src "/static/images/servir.png"}]]
   [:nav
    [:ul
     [:li (make-nav-link-style 0) "Home"]
     [:li (make-nav-link-style 1) "About"]
     [:li (make-nav-link-style 2) "Application"]]]])

;;===========
;; Page Body
;;===========

(defn make-page-visibility-style [link-num]
  (if (= @active-link link-num)
    {:style {:visibility "visible"}}
    {:style {:visibility "hidden"}}))

(defn home-page [page-visibility]
  [:div#home page-visibility
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
    " issues page."]])

(defn about-page [page-visibility]
  [:div#about page-visibility
   [:h1 "About the Surface Water Tool"]
   [:p (str "The Surface Water Tool is an open-source, web GIS tool created by"
            " SERVIR-Mekong for exploring the historic change in surface water"
            " levels throughout the Mekong River region of southeast Asia.")]
   [:hr]
   [:img {:src "/static/images/servir.png"}]
   [:img {:src "/static/images/usaid.png"}]
   [:img {:src "/static/images/nasa.png"}]
   [:img {:src "/static/images/googlelogo_color_272x92dp.png"}]
   [:img {:src "/static/images/adpclogo.jpg"}]
   [:img {:src "/static/images/logosig.png"}]
   [:img {:src "/static/images/winrocklogo.jpg"}]
   [:img {:src "/static/images/mardlogo.jpg"}]
   [:img {:src "/static/images/sei_tr.png"}]
   [:img {:src "/static/images/deltares_tr.png"}]
   [:p#copyright
    "Copyright "
    (str/unescapeEntities "&copy;")
    " "
    [:a {:href "http://www.sig-gis.com" :target "_blank"} "SIG-GIS"]
    " 2016"]])

(defn page-content []
  [:div#all-pages
   [home-page   (make-page-visibility-style 0)]
   [about-page  (make-page-visibility-style 1)]
   [app/content (make-page-visibility-style 2)]])

;;==================
;; CLJS Entry Point
;;==================

(defn ^:export main []
  (r/render [page-header] (dom/getElement "pageheader"))
  (r/render [page-content] (dom/getElement "pagecontent")))
