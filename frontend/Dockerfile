FROM node:18-alpine
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install --legacy-peer-deps
COPY frontend/app.js ./
COPY frontend/public ./public
EXPOSE 3000
CMD ["node", "app.js"]
