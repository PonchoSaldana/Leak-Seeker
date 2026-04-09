# Usar la imagen oficial de Node.js (versión LTS)
FROM node:20-slim

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY package*.json ./

# Instalar dependencias
# Usar 'npm ci' es mejor para producción si existe package-lock.json
RUN npm install --production

# Copiar el resto de los archivos del proyecto
COPY . .

# Exponer el puerto que usará la app (Render lo detectará automáticamente)
EXPOSE 3000

# Comando para iniciar la aplicación
CMD ["npm", "start"]
