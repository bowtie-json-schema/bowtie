(ns bowtie.harness
  "Bowtie IHOP protocol harness for M3 JSON Schema validator (ClojureScript/Node.js)."
  (:require
   [m3.json-schema :as m3]))

(def dialect->draft
  {"https://json-schema.org/draft/2020-12/schema" :draft2020-12
   "https://json-schema.org/draft/2019-09/schema" :draft2019-09
   "http://json-schema.org/draft-07/schema#"       :draft7
   "http://json-schema.org/draft-06/schema#"       :draft6
   "http://json-schema.org/draft-04/schema#"       :draft4
   "http://json-schema.org/draft-03/schema#"       :draft3})

(def supported-dialects (clj->js (keys dialect->draft)))

(def current-draft (atom :draft2020-12))

(defn cmd-start [_request]
  #js {"version" 1
       "implementation"
       #js {"language"         "clojurescript"
            "name"             "m3"
            "version"          "1.0.0-beta3"
            "homepage"         "https://github.com/JulesGosnell/m3"
            "issues"           "https://github.com/JulesGosnell/m3/issues"
            "source"           "https://github.com/JulesGosnell/m3"
            "dialects"         supported-dialects
            "language_version" (str "Node.js " js/process.version)}})

(defn cmd-dialect [request]
  (let [dialect (aget request "dialect")]
    (if-let [draft (dialect->draft dialect)]
      (do (reset! current-draft draft)
          #js {"ok" true})
      #js {"ok" false})))

(defn run-test [validator instance]
  (try
    (let [result (validator instance)]
      #js {"valid" (:valid? result)})
    (catch :default t
      #js {"errored" true
           "context" #js {"message" (ex-message t)}})))

(defn cmd-run [request]
  (try
    (let [seq-val  (aget request "seq")
          test-case (aget request "case")
          schema   (js->clj (aget test-case "schema"))
          registry-js (aget test-case "registry")
          registry (when registry-js (js->clj registry-js))
          tests    (array-seq (aget test-case "tests"))
          opts     (cond-> {:draft @current-draft :quiet? true}
                     registry (assoc :registry registry))
          validator (m3/validator schema opts)
          results   (into-array (map #(run-test validator (js->clj (aget % "instance"))) tests))]
      #js {"seq" seq-val "results" results})
    (catch :default t
      #js {"seq"     (aget request "seq")
           "errored" true
           "context" #js {"message" (ex-message t)}})))

(defn process-line [line]
  (let [request (js/JSON.parse line)
        cmd     (aget request "cmd")]
    (case cmd
      "start"   (cmd-start request)
      "dialect" (cmd-dialect request)
      "run"     (cmd-run request)
      "stop"    nil)))

(defn -main []
  (let [readline (js/require "readline")
        rl (.createInterface readline
             #js {:input  js/process.stdin
                  :output js/process.stdout
                  :terminal false})]
    (.on rl "line"
      (fn [line]
        (when-not (empty? line)
          (if-let [response (process-line line)]
            (.write js/process.stdout
              (str (js/JSON.stringify response) "\n"))
            ;; stop command
            (js/process.exit 0)))))))

(-main)
