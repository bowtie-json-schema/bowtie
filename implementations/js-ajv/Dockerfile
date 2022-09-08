FROM node:18
COPY . /usr/app
WORKDIR /usr/app
ENV NODE_ENV=production
RUN npm install --omit=dev
CMD ["node", "bowtie_ajv.js"]
