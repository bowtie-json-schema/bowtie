FROM node:22-alpine AS builder
RUN apk add --no-cache openjdk21-jre git

WORKDIR /usr/src
RUN git clone https://github.com/JulesGosnell/m3.git

WORKDIR /usr/src/m3
RUN npm install

# Copy harness source
COPY src/bowtie /usr/src/m3/src/cljs/bowtie

# Write a standalone shadow-cljs config that includes harness
RUN echo '{:source-paths ["src/cljc" "src/cljs"] \
           :dependencies [[com.widdindustries/cljc.java-time "0.1.21"]] \
           :builds {:harness {:target :node-script \
                              :output-dir "target/bowtie" \
                              :output-to "target/bowtie/bowtie-m3.js" \
                              :main bowtie.harness/-main}}}' > shadow-cljs.edn

RUN npx shadow-cljs release harness

FROM node:22-alpine
WORKDIR /usr/src/app
COPY --from=builder /usr/src/m3/target/bowtie/bowtie-m3.js .
COPY --from=builder /usr/src/m3/node_modules ./node_modules
COPY --from=builder /usr/src/m3/resources/schemas ./resources/schemas
CMD ["node", "bowtie-m3.js"]
