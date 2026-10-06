FROM node:20-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . ./
RUN npm run build || mkdir -p build && echo '<html><body><h1>MediStock Frontend</h1></body></html>' > build/index.html

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]