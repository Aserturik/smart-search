# Usa la imagen oficial de PostgreSQL
FROM postgres:15

# Establece las variables de entorno para el usuario, contraseña y base de datos
ENV POSTGRES_USER=admin
ENV POSTGRES_PASSWORD=admin123
ENV POSTGRES_DB=smart_search_db

# Copia un archivo SQL de inicialización
COPY init.sql /docker-entrypoint-initdb.d/

# Exponer el puerto predeterminado de PostgreSQL
EXPOSE 5432