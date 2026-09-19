FROM node:22-alpine
WORKDIR /usr/src/myapp
COPY package.json ./
RUN npm install --omit=dev
COPY meta-schemas/ ./meta-schemas/
COPY bowtie_jetio.mjs ./
CMD ["node", "bowtie_jetio.mjs"]
