FROM node:20-alpine

WORKDIR /app/apps/admin-web

COPY apps/admin-web/package.json apps/admin-web/package-lock.json* ./
RUN npm install

COPY apps/admin-web/ ./

EXPOSE 5173

# Plain `vite dev`, not a production build: this is a TCC dev/demo
# compose setup (see README2 section 16), not a deployment artifact —
# no nginx/static-serving stage needed for the MVP.
CMD ["npm", "run", "dev"]
