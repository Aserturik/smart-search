import psycopg2
from psycopg2 import pool
import time
import logging

# Crear un pool de conexiones para PostgreSQL
connection_pool = None

def init_db_connection_pool(max_attempts=5):
    global connection_pool
    attempt = 0
    while attempt < max_attempts:
        try:
            logging.info(f"Intento {attempt + 1} de conectar a la base de datos...")
            connection_pool = psycopg2.pool.SimpleConnectionPool(
                1,  # min_connections
                10,  # max_connections
                host="postgres",  # nombre del servicio en docker-compose
                database="postgres",
                user="postgres",
                password="postgres",
                connect_timeout=10
            )
            logging.info("Conexión exitosa a la base de datos")
            return True
        except Exception as e:
            logging.error(f"Intento {attempt + 1} fallido: {e}")
            attempt += 1
            if attempt < max_attempts:
                logging.info(f"Intentando de nuevo en 5 segundos...")
                time.sleep(5)
    
    logging.error("No se pudo establecer conexión a la base de datos después de varios intentos")
    return False

def get_db_connection():
    global connection_pool
    if connection_pool is None:
        # Intentar inicializar nuevamente el pool si no existe
        init_db_connection_pool()
    
    if connection_pool:
        try:
            return connection_pool.getconn()
        except Exception as e:
            logging.error(f"Error al obtener conexión del pool: {e}")
    return None

def release_db_connection(conn):
    if connection_pool and conn:
        try:
            connection_pool.putconn(conn)
        except Exception as e:
            logging.error(f"Error al devolver conexión al pool: {e}") 