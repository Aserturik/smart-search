# Utiliza una imagen oficial de Python
FROM python:3.11-slim

# Establece el directorio de trabajo
WORKDIR /app

# Instala supervisor y otras dependencias del sistema si son necesarias
RUN apt-get update && apt-get install -y supervisor && rm -rf /var/lib/apt/lists/*

# Crea los directorios de log para supervisor
RUN mkdir -p /var/log/supervisor

# Copia el archivo de requisitos primero para aprovechar la caché de capas de Docker
COPY requirements.txt .

# Instala las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia todos los archivos del backend
COPY . .

# Copia la configuración de supervisor
COPY supervisor.conf /etc/supervisor/conf.d/supervisor.conf

# Comando para ejecutar supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisor.conf"]
