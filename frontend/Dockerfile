FROM node:22-alpine

WORKDIR /app

# Copy package descriptors
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy application files
COPY . .

# Expose Vite preview/dev port
EXPOSE 5173

# Run vite dev server, exposing to all network interfaces
CMD ["npm", "run", "dev", "--", "--host"]
