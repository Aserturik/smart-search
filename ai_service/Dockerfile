# Usar una imagen oficial de Python
FROM python:3.9-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar el archivo .env y los archivos de la aplicación al contenedor
# El archivo .env debe estar presente en el contexto de construcción (directorio ai_service)
COPY .env .env
COPY requirements.txt requirements.txt
COPY app.py app.py

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto en el que la aplicación Flask se ejecutará (definido en app.py)
EXPOSE 5001

# Comando para ejecutar la aplicación
# Usamos gunicorn para un entorno más robusto que el servidor de desarrollo de Flask
# CMD ["flask", "run", "--host=0.0.0.0", "--port=5001"]
# Si gunicorn no está en requirements.txt, añadirlo o usar el servidor de desarrollo de Flask:
CMD ["python", "app.py"] 