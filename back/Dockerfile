# Utiliza una imagen oficial de Python
FROM python:3.11-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos del backend
COPY index.py ./

# Instala Flask
RUN pip install flask


RUN pip install requests


RUN pip install flask-cors

# Expone el puerto 5000
EXPOSE 5000

# Comando para ejecutar la app
CMD ["python", "index.py"]
