from flask import request, jsonify, Response
import uuid
import requests
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
            print(f"Intento {attempt + 1} de conectar a la base de datos...", flush=True)
            connection_pool = psycopg2.pool.SimpleConnectionPool(
                1,  # min_connections
                10,  # max_connections
                host="postgres",  # nombre del servicio en docker-compose
                database="postgres",
                user="postgres",
                password="postgres",
                connect_timeout=10
            )
            print("Conexión exitosa a la base de datos", flush=True)
            return True
        except Exception as e:
            print(f"Intento {attempt + 1} fallido: {e}", flush=True)
            attempt += 1
            if attempt < max_attempts:
                print(f"Intentando de nuevo en 5 segundos...", flush=True)
                time.sleep(5)
    
    print("No se pudo establecer conexión a la base de datos después de varios intentos", flush=True)
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
            print(f"Error al obtener conexión del pool: {e}", flush=True)
    return None

def release_db_connection(conn):
    if connection_pool and conn:
        try:
            connection_pool.putconn(conn)
        except Exception as e:
            print(f"Error al devolver conexión al pool: {e}", flush=True)

def register_routes(app):
    # Iniciar el pool de conexiones
    init_db_connection_pool()
    
    @app.route('/recomendar-productos', methods=['POST'])
    def recomendar_productos():
        data = request.json
        app.logger.info(f"Datos recibidos del formulario: {data}")
        
        nombre = data.get('nombreUsuario', 'Usuario Anónimo')
        
        # Intentar convertir la edad a entero
        try:
            edad = int(data.get('edad', 0))
        except (TypeError, ValueError):
            app.logger.error("Error al convertir edad a entero")
            edad = 0
            
        correo = data.get('correo', 'correo@ejemplo.com')
        
        # Datos del test
        motivo_compra = data.get('motivoCompra', '')
        fuente_informacion = data.get('fuenteInformacion', '')
        temas_interes = data.get('temasDeInteres', '')
        compras_no_necesarias = data.get('comprasNoNecesarias', '')
        importancia_marca = data.get('importanciaMarca', '')
        probar_nuevos_productos = data.get('probarNuevosProductos', '')
        aspiraciones = data.get('aspiraciones', '')
        nivel_social = data.get('nivelSocial', '')
        tiempo_libre = data.get('tiempoLibre', '')
        identidad = data.get('identidad', '')
        tendencias = data.get('tendencias', '')
        
        # Comentario de la solicitud
        comentario_solicitud = data.get('comentarioSolicitud', '')
        
        # Usar logger en lugar de print
        app.logger.info(f"Formulario recibido - Nombre: {nombre}, Edad: {edad}, Correo: {correo}")
        
        conn = None
        # Guardar en la base de datos
        try:
            conn = get_db_connection()
            if conn is None:
                app.logger.error("No se pudo conectar a la base de datos")
                return jsonify({
                    'error': 'No se pudo conectar a la base de datos'
                }), 500
                
            cursor = conn.cursor()
            
            # Insertar usuario
            cursor.execute(
                "INSERT INTO usuarios (nombreUsuario, edad, correo) VALUES (%s, %s, %s) RETURNING id",
                (nombre, edad, correo)
            )
            user_id = cursor.fetchone()[0]
            app.logger.info(f"Usuario insertado con ID: {user_id}")
            
            # Insertar test
            cursor.execute(
                """INSERT INTO tests (motivoCompra, fuenteInformacion, temasDeInteres, comprasNoNecesarias, 
                importanciaMarca, probarNuevosProductos, aspiraciones, nivelSocial, tiempoLibre, 
                identidad, tendencias) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                (motivo_compra, fuente_informacion, temas_interes, compras_no_necesarias,
                importancia_marca, probar_nuevos_productos, aspiraciones, nivel_social,
                tiempo_libre, identidad, tendencias)
            )
            test_id = cursor.fetchone()[0]
            app.logger.info(f"Test insertado con ID: {test_id}")
            
            # Insertar solicitud
            cursor.execute(
                "INSERT INTO solicitudes (userId, testsId, comentarioSolicitud) VALUES (%s, %s, %s)",
                (user_id, test_id, comentario_solicitud)
            )
            
            conn.commit()
            app.logger.info("Transacción completada correctamente")
            
            return jsonify({
                'id_usuario': user_id,
                'nombre': nombre,
                'mensaje': f"Hola {nombre}, tu información ha sido registrada correctamente."
            })
            
        except Exception as e:
            app.logger.error(f"Error al guardar en la base de datos: {e}")
            if conn:
                try:
                    conn.rollback()
                    app.logger.info("Transacción revertida")
                except Exception as rollback_error:
                    app.logger.error(f"Error al revertir transacción: {rollback_error}")
            return jsonify({
                'error': f"Error al guardar en la base de datos: {str(e)}"
            }), 500
        finally:
            if conn:
                release_db_connection(conn)
                app.logger.info("Conexión devuelta al pool")

    @app.route('/recomendar-productos', defaults={'path': ''}, methods=['GET'])
    @app.route('/recomendar-productos/<path:path>', methods=['GET'])
    def recomendar_productos_front(path):
        # Proxy cualquier ruta al frontend
        try:
            url = f'http://front:5173/{path}'
            resp = requests.get(url)
            return Response(resp.content, status=resp.status_code, content_type=resp.headers.get('Content-Type'))
        except Exception as e:
            app.logger.error(f"Error al conectar con el frontend: {e}")
            return f"Error al conectar con el frontend: {e}", 502