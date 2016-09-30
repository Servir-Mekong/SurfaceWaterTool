(task-options!
 pom  {:project     'Servir-Mekong/SurfaceWaterTool
       :version     "1.0.0"
       :description "Surface water web explorer for Southeast Asia"
       :url         "http://surface-water-beta.appspot.com"}
 repl {:eval        '(set! *warn-on-reflection* true)})

(set-env!
 :source-paths   #{"src"}
 :resource-paths #{"../static"}
 :dependencies   '[[org.clojure/clojure         "1.8.0"]
                   [org.clojure/clojurescript   "1.8.51"]
                   [com.cognitect/transit-cljs  "0.8.239"]
                   [org.clojure/core.async      "0.2.391"]
                   [cljs-http                   "0.1.41"]
                   [reagent                     "0.6.0"]
                   [cljsjs/google-maps          "3.18-1"]
                   [adzerk/boot-cljs            "1.7.228-1" :scope "test"]
                   [adzerk/boot-cljs-repl       "0.3.0"     :scope "test"]
                   [com.cemerick/piggieback     "0.2.1"     :scope "test"]
                   [weasel                      "0.7.0"     :scope "test"]
                   [org.clojure/tools.nrepl     "0.2.12"    :scope "test"]])

(require
  '[adzerk.boot-cljs      :refer [cljs]]
  '[adzerk.boot-cljs-repl :refer [cljs-repl start-repl]])

(deftask dev []
  (comp (watch)
        (cljs-repl)
        (cljs :optimizations    :none
              :source-map       true
              :compiler-options {:asset-path "static/surface_water.out"})
        (target :dir #{"target"})))

(deftask prod []
  (comp (cljs :optimizations    :advanced
              :source-map       true
              :compiler-options {:externs ["google_charts_externs.js"]})
        (target :dir #{"target"})))
