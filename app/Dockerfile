# Stage 1: Build the React app
FROM node:18-alpine AS build
WORKDIR /app

# Copy package.json and package-lock.json (if available)
COPY package*.json ./
RUN npm install

# Copy the source files
COPY src/ ./src
COPY public/ ./public

# Build the React app
RUN npm run build

# Stage 2: Serve the app with Nginx
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
