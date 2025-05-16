# Stage 1: Build the frontend
FROM node:24-alpine
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
RUN npm install amqplib
COPY . .

# Exponer puerto y configurar para acceso desde exterior
EXPOSE 5173
ENV HOST=0.0.0.0

# Usar vite directamente para desarrollo
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]