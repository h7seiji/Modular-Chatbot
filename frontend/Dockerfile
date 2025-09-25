# Multi-stage build for React frontend
FROM node:18-alpine AS development

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies
RUN npm install --legacy-peer-deps

# Copy source code
COPY . .

# Expose port for development server
EXPOSE 3000

# Start development server
CMD ["npm", "start"]

# Builder stage for production
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including dev dependencies for building)
RUN npm install --legacy-peer-deps

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage with nginx
FROM nginx:alpine AS production

# Install curl for health checks
RUN apk add --no-cache curl

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built application from builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# # Create nginx user and set permissions
# RUN chown -R nginx:nginx /usr/share/nginx/html && \
#     chown -R nginx:nginx /var/cache/nginx && \
#     chown -R nginx:nginx /var/log/nginx && \
#     chown -R nginx:nginx /etc/nginx/conf.d

# # Switch to nginx user
# USER nginx

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/ || exit 1

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]