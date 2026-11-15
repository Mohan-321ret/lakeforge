# Stage 1: Build Vite React SPA
FROM node:20-alpine AS build

WORKDIR /app

# Copy dependency definitions
COPY package*.json ./
RUN npm ci

# Copy frontend source and build static artifacts
COPY . .
RUN npm run build

# Stage 2: Serve with lightweight NGINX
FROM nginx:alpine

# Copy built static assets from Stage 1
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom NGINX configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
