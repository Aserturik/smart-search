# Usar una imagen oficial de Python
FROM python:3.11-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar primero el archivo de requerimientos e instalar dependencias
# Esto aprovecha el cache de Docker si solo cambian los fuentes y no las dependencias
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el archivo .env (si existe y es necesario en el build o runtime)
# Si solo es para runtime y se monta con docker-compose, esta línea puede no ser necesaria aquí.
# Si es necesario durante el build de la app (poco común para .env), entonces sí.
# Por seguridad, .env usualmente no se copia a la imagen; se provee en runtime.
# Considera si realmente necesitas copiarlo a la imagen.
COPY .env /app/.env

# Copiar todo el contenido del directorio de construcción (ai_service/) a /app/
# Esto incluirá app.py, rabbitmq_client.py, openrouter_client.py, etc.
COPY . /app/

# Exponer el puerto en el que la aplicación Flask se ejecutará
EXPOSE 5001

# Variables de entorno
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Comando para ejecutar la aplicación
CMD ["python", "app.py"] 