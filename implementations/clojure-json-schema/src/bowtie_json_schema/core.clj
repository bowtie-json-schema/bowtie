(ns bowtie-json-schema.core
  (:require [clojure.stacktrace]
            [clojure.data.json :as json]
            [json-schema.core :as json-schema])
  (:gen-class))

(defn -main []
  (let [started (atom false)]
    (doseq [request (map json/read-str (line-seq (java.io.BufferedReader. *in*)))]
      (println
        (json/write-str
          (case (request "cmd")
            "start" (do (assert (= (request "version") 1) "Not version 1!")
                        (reset! started true)
                        {:version 1
                         :implementation
                         {:language :clojure
                          :name :json-schema
                          :homepage "https://github.com/luposlip/json-schema"
                          :issues "https://github.com/luposlip/json-schema/issues"
                          :source "https://github.com/luposlip/json-schema"

                          :dialects ["http://json-schema.org/draft-07/schema#",
                                     "http://json-schema.org/draft-06/schema#",
                                     "http://json-schema.org/draft-04/schema#"]
                          :os (System/getProperty "os.name")
                          :os_version (System/getProperty "os.version")
                          :language_version (clojure-version)}})
            "dialect" (do (assert @started "Not started!")
                          {:ok false})
            "run" (do (assert @started "Not started!")
                      (let [test-case (request "case")]
                        (try
                          {:seq (request "seq")
                           :results (mapv #(try
                                             (json-schema/validate (test-case "schema") %)
                                             {:valid true}
                                             (catch clojure.lang.ExceptionInfo _ {:valid false}))
                                          (test-case "tests"))}
                          (catch Throwable e
                            {:seq (request "seq")
                             :errored true
                             :context {:traceback (with-out-str (clojure.stacktrace/print-cause-trace e 4))}}))))
            "stop" (do (assert @started "Not started!")
                       (System/exit 0))))))))
