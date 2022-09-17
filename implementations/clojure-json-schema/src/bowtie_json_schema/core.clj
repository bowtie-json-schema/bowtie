(ns bowtie-json-schema.core
  (:require [clojure.data.json :as json]
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
                        {:ready true
                         :version 1
                         :implementation
                         {:language :clojure
                          :name :json-schema
                          :homepage "https://github.com/luposlip/json-schema"
                          :issues "https://github.com/luposlip/json-schema/issues"

                          :dialects ["http://json-schema.org/draft-07/schema#",
                                     "http://json-schema.org/draft-06/schema#",
                                     "http://json-schema.org/draft-04/schema#"]}})
            "dialect" (do (assert @started "Not started!")
                          {:ok false})
            "run" (do (assert @started "Not started!")
                      {:seq (request "seq")
                       :results (let [test-case (request "case")]
                                  (mapv #(try
                                           (json-schema/validate (test-case "schema") %)
                                           {:valid true}
                                           (catch clojure.lang.ExceptionInfo _ {:valid false}))
                                        (test-case "tests")))})
            "stop" (do (assert @started "Not started!")
                       (System/exit 0))))))))
