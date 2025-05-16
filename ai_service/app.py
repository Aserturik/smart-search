import os
import requests
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import pika
import threading
import logging
import time

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Cargar variables de entorno desde .env
load_dotenv()

app = Flask(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Puedes cambiar estos si quieres que tu sitio aparezca en los rankings de OpenRouter
YOUR_SITE_URL = os.getenv("YOUR_SITE_URL", "http://localhost:5173")
YOUR_SITE_NAME = os.getenv("YOUR_SITE_NAME", "Smart Search")

# Configuración RabbitMQ
RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_PORT = int(os.environ.get('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.environ.get('RABBITMQ_USER', 'guest')
RABBITMQ_PASS = os.environ.get('RABBITMQ_PASS', 'guest')
QUEUE_PETICIONES_IA = 'peticiones_ia'


def get_connection_params():
    """Obtiene los parámetros de conexión a RabbitMQ"""
    return pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS),
        heartbeat=600,
        blocked_connection_timeout=300
    )

def conectar_a_rabbitmq(max_intentos=5, tiempo_espera=5):
    intentos = 0
    while intentos < max_intentos:
        try:
            conexion = pika.BlockingConnection(get_connection_params())
            logging.info("Conexión establecida con RabbitMQ para AI Service")
            return conexion
        except Exception as e:
            intentos += 1
            logging.error(f"Intento {intentos}/{max_intentos} fallido al conectar con RabbitMQ (AI Service): {e}")
            if intentos < max_intentos:
                logging.info(f"Reintentando en {tiempo_espera} segundos...")
                time.sleep(tiempo_espera)
    logging.error("No se pudo establecer conexión con RabbitMQ (AI Service) después de varios intentos")
    return None

def procesar_peticion_ia(ch, method, properties, body):
    """Procesa un mensaje de la cola de peticiones_ia."""
    try:
        data_usuario = json.loads(body.decode())
        logging.info(f"Recibida petición de IA para usuario: {data_usuario}")

        # Formato del prompt para qwen3, solicitando un array de strings como respuesta.
        prompt = f"Analiza el siguiente perfil de usuario: data{json.dumps(data_usuario)}. Basándote en este perfil, genera una lista de 10 a 12 términos de búsqueda relevantes para una tienda online. Debes responder ÚNICAMENTE con un array de strings en formato JSON. Por ejemplo, si los términos generados fueran 'ropa de moda para hombre' y 'ofertas de electrónica', tu respuesta DEBE ser exactamente así: [\\\"ropa de moda para hombre\\\", \\\"ofertas de electrónica\\\\\"]. NO incluyas ninguna otra explicación, texto adicional, o markdown, solo el array JSON."
        logging.info(f"Prompt para qwen3: {prompt}")

        if not OPENROUTER_API_KEY:
            logging.error("OPENROUTER_API_KEY no está configurada. No se puede llamar a la API.")
            # Nack y no reencolar si la configuración es incorrecta permanentemente
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": YOUR_SITE_URL, # Optional
            "X-Title": YOUR_SITE_NAME,    # Optional
        }

        payload = {
            "model": "qwen/qwen3-235b-a22b", # Model specified by user
            "messages": [
                {"role": "user", "content": prompt}
            ],
            # Podrías añadir otros parámetros como temperature, max_tokens si es necesario.
            # "temperature": 0.7,
            # "max_tokens": 150, 
        }
        
        logging.info(f"Enviando petición a OpenRouter: {json.dumps(payload)}")
        
        response = requests.post(OPENROUTER_API_URL, headers=headers, data=json.dumps(payload), timeout=60) # Added timeout
        response.raise_for_status()  # Lanza una excepción para códigos de estado HTTP 4xx/5xx

        response_json = response.json()
        logging.info(f"Respuesta recibida de OpenRouter: {response_json}")

        # Extraer el contenido del mensaje de la IA
        # Asumiendo que la respuesta de la IA es un string que representa una lista JSON
        ia_message_content_str = response_json.get('choices', [{}])[0].get('message', {}).get('content')
        
        if not ia_message_content_str:
            logging.error("No se encontró contenido en la respuesta de la IA o formato inesperado.")
            # Reencolar podría ser una opción si es un error transitorio de la IA
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True) 
            return
            
        # Convertir el string del contenido (que es una lista JSON) a una lista Python
        try:
            lista_busquedas = json.loads(ia_message_content_str)
            if not isinstance(lista_busquedas, list): # Verificar que sea una lista
                 raise ValueError("El contenido de la IA no es una lista JSON.")
            logging.info("\n")
            logging.info(f"Lista de búsquedas obtenida de qwen3: {lista_busquedas}")
            logging.info("\n")
        except json.JSONDecodeError as e:
            logging.error(f"Error al decodificar el contenido de la respuesta de la IA como JSON: {ia_message_content_str}. Error: {e}")
            # Probablemente no reencolar si el formato es consistentemente incorrecto
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False) 
            return
        except ValueError as e:
            logging.error(f"Error en el formato del contenido de la IA: {ia_message_content_str}. Error: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        # Aquí podrías procesar `lista_busquedas` y, si es necesario, enviar a otra cola.
        # Por ahora, solo registramos el resultado.

        ch.basic_ack(delivery_tag=method.delivery_tag)
        logging.info("Petición de IA procesada y ack enviada.")

    except requests.exceptions.HTTPError as http_err:
        logging.error(f"Error HTTP al contactar OpenRouter: {http_err} - {http_err.response.text if http_err.response else 'No response text'}")
        # Reencolar para errores de servidor (5xx) o rate limits (429)
        if http_err.response is not None and (500 <= http_err.response.status_code < 600 or http_err.response.status_code == 429):
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        else: # No reencolar para errores de cliente (4xx) que no sean rate limits
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except requests.exceptions.RequestException as req_err: # Timeout, ConnectionError, etc.
        logging.error(f"Error de red o conexión al contactar OpenRouter: {req_err}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True) # Reintentar para problemas de red
    except json.JSONDecodeError as e: # Error al decodificar el body del mensaje de RabbitMQ
        logging.error(f"Error al decodificar JSON de la petición de IA (mensaje de RabbitMQ): {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False) 
    except Exception as e:
        logging.error(f"Error inesperado al procesar petición de IA: {e}", exc_info=True)
        # Considerar si reencolar o no dependiendo del error, True es más seguro para errores desconocidos
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True) 

def iniciar_consumidor_ia():
    """Inicia el consumidor de RabbitMQ para la cola de peticiones_ia."""
    while True: # Bucle para reconexión automática
        conexion = conectar_a_rabbitmq()
        if conexion:
            try:
                canal = conexion.channel()
                canal.queue_declare(queue=QUEUE_PETICIONES_IA, durable=True)
                canal.basic_qos(prefetch_count=1) # Procesar un mensaje a la vez
                canal.basic_consume(queue=QUEUE_PETICIONES_IA, on_message_callback=procesar_peticion_ia)
                
                logging.info(f"Consumidor de {QUEUE_PETICIONES_IA} iniciado. Esperando mensajes...")
                canal.start_consuming()
            except pika.exceptions.StreamLostError as e:
                logging.error(f"Se perdió la conexión con RabbitMQ (StreamLostError): {e}. Reintentando...")
            except pika.exceptions.AMQPConnectionError as e:
                logging.error(f"Error de conexión AMQP (AI Service): {e}. Reintentando...")
            except Exception as e:
                logging.error(f"Error inesperado en el consumidor de IA: {e}. Reintentando...")
            finally:
                if conexion and not conexion.is_closed:
                    conexion.close()
                logging.info("Conexión RabbitMQ (AI Service) cerrada. Reintentando conexión en 10 segundos.")
                time.sleep(10) # Esperar antes de reintentar
        else:
            logging.info("No se pudo conectar a RabbitMQ para iniciar consumidor IA. Reintentando en 10 segundos.")
            time.sleep(10)


@app.route('/health')
def health_check():
    # TODO: Verificar también la conexión a RabbitMQ si es crítico para el health status
    return jsonify({"status": "healthy"}), 200

@app.route('/api/v1/chat/completions', methods=['POST'])
def proxy_openrouter():
    if not OPENROUTER_API_KEY:
        return jsonify({"error": "API key no configurada"}), 500

    try:
        incoming_data = request.json
        if not incoming_data:
            return jsonify({"error": "Request body debe ser JSON"}), 400

        model = incoming_data.get("model")
        messages = incoming_data.get("messages")

        if not model or not messages:
            return jsonify({"error": "Faltan los campos 'model' o 'messages' en el request body"}), 400

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": YOUR_SITE_URL,
            "X-Title": YOUR_SITE_NAME,
        }

        data_to_send = {
            "model": model,
            "messages": messages
        }
        
        # Permitir otros parámetros opcionales de la API de OpenRouter
        optional_params = ["temperature", "top_p", "max_tokens", "stream", "stop", "frequency_penalty", "presence_penalty", "seed"]
        for param in optional_params:
            if param in incoming_data:
                data_to_send[param] = incoming_data[param]

        app.logger.info(f"Enviando a OpenRouter: {json.dumps(data_to_send)}")

        response = requests.post(OPENROUTER_API_URL, headers=headers, data=json.dumps(data_to_send))
        response.raise_for_status()  # Lanza una excepción para códigos de estado HTTP 4xx/5xx

        # Si OpenRouter devuelve una respuesta en streaming (chunked), la pasamos tal cual.
        if 'chunked' in response.headers.get('Transfer-Encoding', '').lower():
            def generate():
                for chunk in response.iter_content(chunk_size=8192):
                    yield chunk
            return app.response_class(generate(), content_type=response.headers['Content-Type'])
        else:
            return jsonify(response.json()), response.status_code

    except requests.exceptions.HTTPError as http_err:
        app.logger.error(f"HTTP error occurred: {http_err} - {response.text}")
        return jsonify({"error": "Error en la comunicación con la API de IA", "details": response.text}), response.status_code
    except requests.exceptions.RequestException as req_err:
        app.logger.error(f"Request error occurred: {req_err}")
        return jsonify({"error": "Error de red o configuración al contactar la API de IA"}), 503
    except Exception as e:
        app.logger.error(f"Ocurrió un error inesperado: {e}")
        return jsonify({"error": f"Ocurrió un error inesperado: {str(e)}"}), 500

if __name__ == '__main__':
    # Iniciar el consumidor de RabbitMQ en un hilo separado
    thread_consumidor = threading.Thread(target=iniciar_consumidor_ia, daemon=True)
    thread_consumidor.start()
    
    app.run(host='0.0.0.0', port=5001, debug=True) # Puerto diferente al backend principal 