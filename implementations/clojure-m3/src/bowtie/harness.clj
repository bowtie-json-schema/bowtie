(ns bowtie.harness
  "Bowtie IHOP protocol harness for M3 JSON Schema validator (JVM)."
  (:require
   [clojure.data.json :as json]
   [m3.json-schema :as m3])
  (:gen-class))

(def dialect->draft
  {"https://json-schema.org/draft/2020-12/schema" :draft2020-12
   "https://json-schema.org/draft/2019-09/schema" :draft2019-09
   "http://json-schema.org/draft-07/schema#"       :draft7
   "http://json-schema.org/draft-06/schema#"       :draft6
   "http://json-schema.org/draft-04/schema#"       :draft4
   "http://json-schema.org/draft-03/schema#"       :draft3})

(def supported-dialects (keys dialect->draft))

(def ^:dynamic *current-draft* :draft2020-12)

(defn cmd-start [_request]
  {"version" 1
   "implementation"
   {"language"         "clojure"
    "name"             "m3"
    "version"          (or (System/getProperty "m3.version") "1.0.0-beta3")
    "homepage"         "https://github.com/JulesGosnell/m3"
    "issues"           "https://github.com/JulesGosnell/m3/issues"
    "source"           "https://github.com/JulesGosnell/m3"
    "dialects"         supported-dialects
    "os"               (System/getProperty "os.name")
    "os_version"       (System/getProperty "os.version")
    "language_version" (clojure-version)}})

(defn cmd-dialect [{dialect "dialect"}]
  (if-let [draft (dialect->draft dialect)]
    (do (alter-var-root #'*current-draft* (constantly draft))
        {"ok" true})
    {"ok" false}))

(defn run-test [validator instance]
  (try
    (let [result (validator instance)]
      {"valid" (:valid? result)})
    (catch Throwable t
      {"errored" true
       "context" {"message"   (ex-message t)
                  "traceback" (with-out-str (.printStackTrace t))}})))

(defn cmd-run [{seq-val "seq" test-case "case"}]
  (try
    (let [schema   (get test-case "schema")
          registry (get test-case "registry")
          tests    (get test-case "tests")
          opts     (cond-> {:draft *current-draft* :quiet? true}
                     registry (assoc :registry registry))
          validator (m3/validator schema opts)
          results   (mapv #(run-test validator (get % "instance")) tests)]
      {"seq" seq-val "results" results})
    (catch Throwable t
      {"seq"     seq-val
       "errored" true
       "context" {"message"   (ex-message t)
                  "traceback" (with-out-str (.printStackTrace t))}})))

(defn process-line [line]
  (let [request (json/read-str line)
        cmd     (get request "cmd")]
    (case cmd
      "start"   (cmd-start request)
      "dialect" (cmd-dialect request)
      "run"     (cmd-run request)
      "stop"    nil)))

(defn -main [& _args]
  (let [reader (java.io.BufferedReader. (java.io.InputStreamReader. System/in))]
    (loop []
      (when-let [line (.readLine reader)]
        (when-not (clojure.string/blank? line)
          (if-let [response (process-line line)]
            (do (println (json/write-str response))
                (.flush System/out)
                (recur))
            ;; stop command — exit
            (System/exit 0)))))))
