import json
import logging
import time
import signal
import sys
from rabbitmq_utils import conectar_a_rabbitmq, configurar_consumidor, enviar_a_rabbitmq
from rabbitmq_utils import QUEUE_SOLICITUDES, QUEUE_RESPUESTAS, setup_rabbitmq
from database_utils import init_db_connection_pool, get_db_connection, release_db_connection

# Configurar el logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

# Bandera para controlar si el servicio sigue en ejecución
running = True

def signal_handler(sig, frame):
    """Manejador de señales para terminar el servicio correctamente"""
    global running
    logger.info("Recibida señal de terminación. Deteniendo servicio...")
    running = False

# Registrar manejadores de señales
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def procesar_solicitud(ch, method, properties, body):
    """Procesa los mensajes de solicitud recibidos de RabbitMQ"""
    try:
        # Decodificar el mensaje JSON
        data = json.loads(body)
        logger.info(f"Datos recibidos del formulario via RabbitMQ: {data}")
        
        nombre = data.get('nombreUsuario', 'Usuario Anónimo')
        
        # Intentar convertir la edad a entero
        try:
            edad = int(data.get('edad', 0))
        except (TypeError, ValueError):
            logger.error("Error al convertir edad a entero")
            edad = 0
            
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
        
        logger.info(f"Formulario recibido - Nombre: {nombre}, Edad: {edad}")
        
        conn = None
        # Guardar en la base de datos
        try:
            conn = get_db_connection()
            if conn is None:
                logger.error("No se pudo conectar a la base de datos")
                # Enviar respuesta de error
                enviar_a_rabbitmq(
                    json.dumps({'error': 'No se pudo conectar a la base de datos'}),
                    queue=QUEUE_RESPUESTAS
                )
                return
                
            cursor = conn.cursor()
            
            # Insertar usuario
            cursor.execute(
                "INSERT INTO usuarios (nombreUsuario, edad) VALUES (%s, %s) RETURNING id",
                (nombre, edad)
            )
            user_id = cursor.fetchone()[0]
            logger.info(f"Usuario insertado con ID: {user_id}")
            
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
            logger.info(f"Test insertado con ID: {test_id}")
            
            # Insertar solicitud
            cursor.execute(
                "INSERT INTO solicitudes (userId, testsId, comentarioSolicitud) VALUES (%s, %s, %s)",
                (user_id, test_id, comentario_solicitud)
            )
            
            conn.commit()
            logger.info("Transacción completada correctamente")
            
            # Enviar mensaje de respuesta a la cola de respuestas
            respuesta = {
                'id_usuario': user_id,
                'nombre': nombre,
                'mensaje': f"Hola {nombre}, tu información ha sido registrada correctamente."
            }
            enviar_a_rabbitmq(json.dumps(respuesta), queue=QUEUE_RESPUESTAS)
            
        except Exception as e:
            logger.error(f"Error al guardar en la base de datos: {e}")
            if conn:
                try:
                    conn.rollback()
                    logger.info("Transacción revertida")
                except Exception as rollback_error:
                    logger.error(f"Error al revertir transacción: {rollback_error}")
            
            # Enviar mensaje de error a la cola de respuestas
            respuesta_error = {
                'error': f"Error al guardar en la base de datos: {str(e)}"
            }
            enviar_a_rabbitmq(json.dumps(respuesta_error), queue=QUEUE_RESPUESTAS)
        finally:
            if conn:
                release_db_connection(conn)
                logger.info("Conexión devuelta al pool")
            
            # Confirmar el procesamiento del mensaje
            ch.basic_ack(delivery_tag=method.delivery_tag)
    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar JSON: {e}")
        # Confirmar el mensaje para que no se reintente indefinidamente
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error(f"Error inesperado procesando el mensaje: {e}")
        # Confirmar el mensaje para que no se reintente indefinidamente
        ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    """Función principal"""
    logger.info("Iniciando servicio de backend con RabbitMQ...")
    
    # Configurar RabbitMQ
    if not setup_rabbitmq():
        logger.error("No se pudo configurar RabbitMQ. Saliendo...")
        sys.exit(1)
    
    # Inicializar la conexión a la base de datos
    if not init_db_connection_pool():
        logger.error("No se pudo inicializar la conexión a la base de datos. Saliendo...")
        sys.exit(1)
    
    # Establecer conexión con RabbitMQ
    conexion = conectar_a_rabbitmq()
    if not conexion:
        logger.error("No se pudo establecer conexión con RabbitMQ. Saliendo...")
        sys.exit(1)
    
    canal = conexion.channel()
    
    # Configurar el consumidor para la cola de solicitudes
    configurar_consumidor(canal, QUEUE_SOLICITUDES, procesar_solicitud)
    
    logger.info(f"Esperando mensajes en la cola '{QUEUE_SOLICITUDES}'. Para salir presiona CTRL+C")
    
    # Iniciar el bucle de consumo de RabbitMQ
    try:
        while running:
            conexion.process_data_events(time_limit=1)  # Procesar eventos con timeout para poder comprobar 'running'
    except KeyboardInterrupt:
        logger.info("Interrumpido por el usuario")
    except Exception as e:
        logger.error(f"Error en el bucle principal: {e}")
    finally:
        if conexion and conexion.is_open:
            conexion.close()
        logger.info("Servicio de backend finalizado")

if __name__ == '__main__':
    main()
