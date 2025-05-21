import json
import logging
import time
import signal
import sys
from rabbitmq_utils import conectar_a_rabbitmq, configurar_consumidor, enviar_a_rabbitmq, enviar_a_peticiones_ia
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
    try:
        data = json.loads(body)
        logger.info(f"Datos recibidos del formulario: {data}")
        
        conn = get_db_connection()
        if not conn:
            logger.error("No se pudo conectar a la base de datos")
            return
            
        cursor = conn.cursor()
        
        try:
            # Insertar usuario y obtener su ID
            cursor.execute(
                "INSERT INTO usuarios (nombreUsuario, edad) VALUES (%s, %s) RETURNING id",
                (data['nombreUsuario'], data['edad'])
            )
            user_id = cursor.fetchone()[0]
            logger.info(f"Usuario insertado con ID: {user_id}")
            
            # Insertar test y obtener su ID
            cursor.execute(
                """INSERT INTO tests (motivoCompra, fuenteInformacion, temasDeInteres, comprasNoNecesarias, 
                importanciaMarca, probarNuevosProductos, aspiraciones, nivelSocial, tiempoLibre, 
                identidad, tendencias) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                (data['motivoCompra'], data['fuenteInformacion'], data['temasDeInteres'], data['comprasNoNecesarias'],
                data['importanciaMarca'], data['probarNuevosProductos'], data['aspiraciones'], data['nivelSocial'],
                data['tiempoLibre'], data['identidad'], data['tendencias'])
            )
            test_id = cursor.fetchone()[0]
            logger.info(f"Test insertado con ID: {test_id}")
            
            # Insertar solicitud
            cursor.execute(
                "INSERT INTO solicitudes (userId, testsId, comentarioSolicitud) VALUES (%s, %s, %s)",
                (user_id, test_id, data['comentarioSolicitud'])
            )
            
            # Al enviar el perfil al servicio de IA, incluir el ID de usuario
            perfil_usuario_ia = {
                'id_usuario': user_id,  # Agregar el ID de usuario aquí
                'usuario': {
                    'id': user_id,
                    'nombreUsuario': data['nombreUsuario'],
                    'edad': data['edad']
                },
                'formulario': {
                    'motivoCompra': data['motivoCompra'],
                    'fuenteInformacion': data['fuenteInformacion'],
                    'temasDeInteres': data['temasDeInteres'],
                    'comprasNoNecesarias': data['comprasNoNecesarias'],
                    'importanciaMarca': data['importanciaMarca'],
                    'probarNuevosProductos': data['probarNuevosProductos'],
                    'aspiraciones': data['aspiraciones'],
                    'nivelSocial': data['nivelSocial'],
                    'tiempoLibre': data['tiempoLibre'],
                    'identidad': data['identidad'],
                    'tendencias': data['tendencias']
                }
            }

            logger.info(f"Enviando perfil de usuario {user_id} al servicio de IA")
            if not enviar_a_peticiones_ia(perfil_usuario_ia):
                logger.error(f"No se pudo enviar el perfil del usuario {user_id} al servicio de IA")

            conn.commit()
            
            # Enviar mensaje de respuesta a la cola de respuestas
            respuesta = {
                'id_usuario': user_id,
                'nombre': data['nombreUsuario'],
                'mensaje': f"Hola {data['nombreUsuario']}, tu información ha sido registrada correctamente."
            }
            enviar_a_rabbitmq(json.dumps(respuesta), queue=QUEUE_RESPUESTAS)
            
        except Exception as e:
            logger.error(f"Error procesando solicitud: {e}")
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        logger.error(f"Error en procesar_solicitud: {e}")
        # Asegurarse de que el mensaje sea procesado
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
