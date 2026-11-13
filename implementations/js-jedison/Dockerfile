FROM node:26-alpine
COPY . /usr/app
WORKDIR /usr/app
ENV NODE_ENV=production
ARG IMPLEMENTATION_VERSION=latest
RUN npm install --omit=dev jedison@${IMPLEMENTATION_VERSION}
CMD ["node", "bowtie_jedison.js"]
