from flask import Flask, request, jsonify, Response
import uuid
import requests
import pika
import logging  # Importamos logging para configurar el nivel de log
from flask_cors import CORS
import json  # Importar json para convertir el mensaje a string

# Configurar el logger para que muestre todo en stdout
logging.basicConfig(
    level=logging.INFO,  # Nivel mínimo que se mostrará
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Enviar a stdout
    ]
)

app = Flask(__name__)
CORS(app)

# Asegurarse de que el logger de Flask muestre mensajes de INFO o más importantes
app.logger.setLevel(logging.INFO)

# Configuración de RabbitMQ
RABBITMQ_HOST = 'rabbitmq'  # Nombre del contenedor RabbitMQ en docker-compose
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
        app.logger.info(f"Mensaje enviado a RabbitMQ: {mensaje}")
        conexion.close()
    except Exception as e:
        app.logger.error(f"Error al enviar mensaje a RabbitMQ: {e}")

@app.route('/recomendar-productos', methods=['POST'])
def recomendar_productos():
    data = request.json
    nombre = data.get('nombre', 'Usuario Anónimo')
    respuesta = data.get('respuesta', 'Sin respuesta')
    user_id = str(uuid.uuid4())

    # Crear el mensaje para RabbitMQ
    mensaje = {
        'id_usuario': user_id,
        'nombre': nombre,
        'respuesta': respuesta
    }

    # Enviar el mensaje a RabbitMQ
    enviar_a_rabbitmq(json.dumps(mensaje))

    # Usar logger en lugar de print
    app.logger.info(f"Formulario recibido - Nombre: {nombre}, Respuesta: {respuesta}, ID: {user_id}")

    return jsonify({
        'id_usuario': user_id,
        'nombre': nombre,
        'respuesta': respuesta,
        'mensaje': f"Hola {nombre}, tu respuesta '{respuesta}' ha sido registrada."
    })



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

# Mensaje de inicio para verificar que el logger funciona
app.logger.info("Flask backend iniciado - Listo para recibir solicitudes")
print("SERVIDOR FLASK INICIADO", flush=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
