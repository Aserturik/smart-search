# Utiliza una imagen oficial de Python
FROM python:3.11-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia el archivo de requisitos primero para aprovechar la caché de capas de Docker
COPY requirements.txt .

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia los archivos del backend
COPY index.py ./

# Expone el puerto 5000
EXPOSE 5000

# Comando para ejecutar la app
CMD ["python", "index.py"]
