FROM node:18-alpine
COPY . /usr/app
WORKDIR /usr/app
ENV NODE_ENV=production
RUN npm install --omit=dev
CMD ["node", "bowtie_hyperjump.js"]
