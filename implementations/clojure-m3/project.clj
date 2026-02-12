(defproject bowtie-m3 "0.1.0"
  :description "Bowtie harness for M3 JSON Schema validator"
  :dependencies [[org.clojure/clojure "1.12.4"]
                 [org.clojure/data.json "2.5.2"]
                 [org.clojars.jules_gosnell/m3 "1.0.0-beta3"]]
  :main bowtie.harness
  :aot [bowtie.harness]
  :uberjar-name "bowtie-m3-standalone.jar"
  :profiles {:uberjar {:aot :all}})
