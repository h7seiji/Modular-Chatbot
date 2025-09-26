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

# Set build-time environment variables for React
ARG REACT_APP_API_URL=/api
ARG REACT_APP_ENVIRONMENT=production

# Build the application with error handling
ENV REACT_APP_API_URL=$REACT_APP_API_URL
ENV REACT_APP_ENVIRONMENT=$REACT_APP_ENVIRONMENT
RUN npm run build || (echo "Build failed!" && exit 1)

# Verify build was successful
RUN ls -la /app/build/ || (echo "Build directory not found!" && exit 1)
RUN test -f /app/build/index.html || (echo "index.html not found!" && exit 1)

# Production stage with nginx
FROM nginx:alpine AS production

# Install curl for health checks
RUN apk add --no-cache curl

# Copy custom nginx configuration template
COPY nginx.conf.template /etc/nginx/conf.d/default.conf.template

# Copy built application from builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Verify files were copied successfully
RUN ls -la /usr/share/nginx/html/ || (echo "HTML directory not found!" && exit 1)
RUN test -f /usr/share/nginx/html/index.html || (echo "index.html not found in nginx directory!" && exit 1)

# Create nginx user and set permissions
RUN touch /var/run/nginx.pid && \
    chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d && \
    chown -R nginx:nginx /var/run/nginx.pid

# Set environment variables for backend configuration
ENV BACKEND_HOST=localhost
ENV BACKEND_PORT=8000

# Switch to nginx user
USER nginx

# Health check with more robust endpoint
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# Expose port
EXPOSE 80

# Start nginx with environment variable substitution
CMD ["sh", "-c", "envsubst '$$BACKEND_HOST $$BACKEND_PORT' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]