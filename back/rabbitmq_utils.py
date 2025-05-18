import pika
import logging
import time
import os
import json

# Obtener configuración de variables de entorno o usar valores predeterminados
RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_PORT = int(os.environ.get('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.environ.get('RABBITMQ_USER', 'guest')
RABBITMQ_PASS = os.environ.get('RABBITMQ_PASS', 'guest')

# Nombre de las colas
QUEUE_SOLICITUDES = 'solicitudes'
QUEUE_RESPUESTAS = 'respuestas'
QUEUE_PETICIONES_IA = 'peticiones_ia'
QUEUE_SCRAPED_URLS = 'scraped_urls_queue'

# Configuración de intercambio de mensajes
EXCHANGE_NAME = 'formularios'

def get_connection_params():
    """Obtiene los parámetros de conexión a RabbitMQ"""
    return pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS),
        heartbeat=600,
        blocked_connection_timeout=300
    )

# Función para enviar mensajes a RabbitMQ
def enviar_a_rabbitmq(mensaje, queue=QUEUE_SOLICITUDES, exchange=None, routing_key=''):
    try:
        # Conexión a RabbitMQ
        conexion = pika.BlockingConnection(get_connection_params())
        canal = conexion.channel()
        
        # Si se especifica un exchange, declararlo
        if exchange:
            canal.exchange_declare(exchange=exchange, exchange_type='direct', durable=True)
            
            # Declarar la cola (asegura que exista)
            canal.queue_declare(queue=queue, durable=True)
            
            # Vincular cola al exchange
            canal.queue_bind(exchange=exchange, queue=queue, routing_key=routing_key)
            
            # Publicar el mensaje al exchange
            canal.basic_publish(
                exchange=exchange,
                routing_key=routing_key or queue,
                body=mensaje if isinstance(mensaje, str) else json.dumps(mensaje),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Hacer que el mensaje sea persistente
                    content_type='application/json'
                )
            )
        else:
            # Declarar la cola (asegura que exista)
            canal.queue_declare(queue=queue, durable=True)

            # Publicar el mensaje directamente a la cola
            canal.basic_publish(
                exchange='',
                routing_key=queue,
                body=mensaje if isinstance(mensaje, str) else json.dumps(mensaje),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Hacer que el mensaje sea persistente
                    content_type='application/json'
                )
            )
        
        logging.info(f"Mensaje enviado a RabbitMQ ({queue}): {mensaje}")
        conexion.close()
    except Exception as e:
        logging.error(f"Error al enviar mensaje a RabbitMQ: {e}")

# Función para establecer conexión con RabbitMQ con reintentos
def conectar_a_rabbitmq(max_intentos=5, tiempo_espera=5):
    intentos = 0
    while intentos < max_intentos:
        try:
            conexion = pika.BlockingConnection(get_connection_params())
            logging.info("Conexión establecida con RabbitMQ")
            return conexion
        except Exception as e:
            intentos += 1
            logging.error(f"Intento {intentos}/{max_intentos} fallido al conectar con RabbitMQ: {e}")
            if intentos < max_intentos:
                logging.info(f"Reintentando en {tiempo_espera} segundos...")
                time.sleep(tiempo_espera)
    
    logging.error("No se pudo establecer conexión con RabbitMQ después de varios intentos")
    return None

# Configurar intercambios y colas necesarios
def setup_rabbitmq():
    """Configura los intercambios y colas necesarios en RabbitMQ"""
    try:
        conexion = conectar_a_rabbitmq()
        if not conexion:
            logging.error("No se pudo configurar RabbitMQ")
            return False
            
        canal = conexion.channel()
        
        # Configurar exchange
        canal.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='direct', durable=True)
        
        # Configurar colas
        canal.queue_declare(queue=QUEUE_SOLICITUDES, durable=True)
        canal.queue_declare(queue=QUEUE_RESPUESTAS, durable=True)
        canal.queue_declare(queue=QUEUE_PETICIONES_IA, durable=True)
        canal.queue_declare(queue=QUEUE_SCRAPED_URLS, durable=True)
        
        # Vincular colas a exchange
        canal.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_SOLICITUDES, routing_key=QUEUE_SOLICITUDES)
        canal.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_RESPUESTAS, routing_key=QUEUE_RESPUESTAS)
        # No es necesario vincular QUEUE_PETICIONES_IA al exchange 'formularios' si se va a usar de forma directa
        # o con otro exchange específico. Por ahora, la dejaremos sin vincular a este exchange.
        
        conexion.close()
        logging.info("RabbitMQ configurado correctamente")
        return True
    except Exception as e:
        logging.error(f"Error al configurar RabbitMQ: {e}")
        return False

# Función para consumir mensajes de una cola
def configurar_consumidor(canal, cola, callback):
    canal.queue_declare(queue=cola, durable=True)
    canal.basic_qos(prefetch_count=1)
    canal.basic_consume(queue=cola, on_message_callback=callback)
    logging.info(f"Consumidor configurado para la cola: {cola}")

# Función para enviar mensajes a la cola de peticiones de IA
def enviar_a_peticiones_ia(mensaje):
    """Envía un mensaje a la cola de peticiones de IA."""
    try:
        conexion = pika.BlockingConnection(get_connection_params())
        canal = conexion.channel()

        # Declarar la cola (asegura que exista)
        canal.queue_declare(queue=QUEUE_PETICIONES_IA, durable=True)

        # Publicar el mensaje directamente a la cola
        canal.basic_publish(
            exchange='', # Publicación directa a la cola
            routing_key=QUEUE_PETICIONES_IA,
            body=mensaje if isinstance(mensaje, str) else json.dumps(mensaje),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Hacer que el mensaje sea persistente
                content_type='application/json'
            )
        )
        logging.info(f"Mensaje enviado a RabbitMQ ({QUEUE_PETICIONES_IA}): {mensaje}")
        conexion.close()
        return True
    except Exception as e:
        logging.error(f"Error al enviar mensaje a {QUEUE_PETICIONES_IA}: {e}")
        return False

# Función para enviar mensajes a la cola de URLs scrapeadas
def enviar_a_scraped_urls(mensaje):
    """Envía un mensaje a la cola de URLs scrapeadas."""
    try:
        conexion = pika.BlockingConnection(get_connection_params())
        canal = conexion.channel()

        # Declarar la cola (asegura que exista)
        # La declaración ya se hace en setup_rabbitmq, pero es bueno tenerla aquí por si acaso
        # y para mantener consistencia con otras funciones de envío.
        canal.queue_declare(queue=QUEUE_SCRAPED_URLS, durable=True)

        # Publicar el mensaje directamente a la cola
        canal.basic_publish(
            exchange='', # Publicación directa a la cola
            routing_key=QUEUE_SCRAPED_URLS,
            body=mensaje if isinstance(mensaje, str) else json.dumps(mensaje),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Hacer que el mensaje sea persistente
                content_type='application/json'
            )
        )
        logging.info(f"Mensaje enviado a RabbitMQ ({QUEUE_SCRAPED_URLS}): {mensaje}")
        conexion.close()
        return True
    except Exception as e:
        logging.error(f"Error al enviar mensaje a {QUEUE_SCRAPED_URLS}: {e}")
        return False