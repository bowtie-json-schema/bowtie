FROM node:24-alpine
COPY . /usr/app
WORKDIR /usr/app
ENV NODE_ENV=production
ARG IMPLEMENTATION_VERSION=latest
RUN npm install --omit=dev @hyperjump/json-schema@${IMPLEMENTATION_VERSION}
CMD ["node", "bowtie_hyperjump.js"]
