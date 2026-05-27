FROM node:26-bookworm AS builder
RUN apt-get update && \
    apt-get install -y --no-install-recommends libre2-dev libabsl-dev libmimalloc-dev && \
    rm -rf /var/lib/apt/lists/*
COPY . /usr/app
WORKDIR /usr/app
ENV NODE_ENV=production
RUN npm install --omit=dev

FROM node:26-bookworm-slim
RUN apt-get update && \
    apt-get install -y --no-install-recommends libre2-9 libabsl20220623 libmimalloc2.0 && \
    rm -rf /var/lib/apt/lists/*
COPY --from=builder /usr/app /usr/app
WORKDIR /usr/app
ENV NODE_ENV=production
CMD ["node", "bowtie_ata.js"]
