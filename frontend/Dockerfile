# Etapa 1: Compilação do código
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# No Docker a API vive atras do proxy /api/ do nginx (sem sniffing de Accept).
ENV VITE_API_URL=/api
RUN npm run build

# Etapa 2: Servidor de produção
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
