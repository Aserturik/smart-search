import pika
import logging

# Configuración de RabbitMQ
RABBITMQ_HOST = 'rabbitmq'  # Nombre del servicio RabbitMQ en docker-compose
RABBITMQ_QUEUE = 'recomendaciones'

# Función para enviar mensajes a RabbitMQ
def enviar_a_rabbitmq(mensaje):
    try:
        # Conexión a RabbitMQ
        conexion = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        canal = conexion.channel()

        # Declarar la cola (asegura que exista)
        canal.queue_declare(queue=RABBITMQ_QUEUE, durable=True)

        # Publicar el mensaje
        canal.basic_publish(
            exchange='',
            routing_key=RABBITMQ_QUEUE,
            body=mensaje,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Hacer que el mensaje sea persistente
            )
        )
        logging.info(f"Mensaje enviado a RabbitMQ: {mensaje}")
        conexion.close()
    except Exception as e:
        logging.error(f"Error al enviar mensaje a RabbitMQ: {e}")