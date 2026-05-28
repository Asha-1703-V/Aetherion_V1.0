FROM node:18-alpine

WORKDIR /app

# Копируем package.json
COPY package*.json ./

# Устанавливаем зависимости
RUN npm install

# Копируем весь код
COPY . .

# Отключаем телеметрию
ENV NEXT_TELEMETRY_DISABLED=1

EXPOSE 3000

# Запускаем в режиме разработки
CMD ["npm", "run", "dev"]