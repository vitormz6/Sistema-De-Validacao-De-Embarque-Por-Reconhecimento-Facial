FROM node:20-alpine

WORKDIR /app/apps/operator-web

COPY apps/operator-web/package.json apps/operator-web/package-lock.json* ./
RUN npm install

COPY apps/operator-web/ ./

EXPOSE 5174

# Plain `vite dev`, not a production build: same reasoning as admin-web —
# this is a TCC dev/demo compose setup (see README2 section 16), no nginx
# stage needed for the MVP.
CMD ["npm", "run", "dev"]
