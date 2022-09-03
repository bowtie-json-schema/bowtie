FROM node:18
COPY . /usr/app
WORKDIR /usr/app
ENV NODE_ENV=production
RUN npm install --production
CMD ["node", "bowtie_hyperjump.js"]
