import os
import pika
import logging
import time
import json
import requests

# Import openrouter_client correctly
import openrouter_client

# Configuración de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Configuración RabbitMQ
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.environ.get("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.environ.get("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.environ.get("RABBITMQ_PASS", "guest")
QUEUE_PETICIONES_IA = "peticiones_ia"
SCRAPPER_PETICIONES_QUEUE = os.environ.get(
    "SCRAPPER_PETICIONES_QUEUE", "scrapper_peticiones_queue"
)  # Nueva cola


def get_connection_params():
    """Obtiene los parámetros de conexión a RabbitMQ"""
    return pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS),
        heartbeat=600,
        blocked_connection_timeout=300,
    )


def conectar_a_rabbitmq(max_intentos=5, tiempo_espera=5):
    intentos = 0
    while intentos < max_intentos:
        try:
            conexion = pika.BlockingConnection(get_connection_params())
            logging.info("Conexión establecida con RabbitMQ")
            return conexion
        except Exception as e:
            intentos += 1
            logging.error(
                f"Intento {intentos}/{max_intentos} fallido al conectar con RabbitMQ: {e}"
            )
            if intentos < max_intentos:
                logging.info(f"Reintentando en {tiempo_espera} segundos...")
                time.sleep(tiempo_espera)
    logging.error(
        "No se pudo establecer conexión con RabbitMQ después de varios intentos"
    )
    return None


def procesar_peticion_ia_callback(ch, method, properties, body):
    try:
        data_usuario = json.loads(body.decode())
        # Extraer el ID de usuario del mensaje
        user_id = data_usuario.get('id_usuario') or data_usuario.get('usuario', {}).get('id')
        
        if not user_id:
            logging.error("No se encontró ID de usuario en el mensaje")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return
            
        logging.info(f"Recibida petición de IA para usuario: {user_id}")

        prompt = f"""Analiza el siguiente perfil de usuario y genera entre 10 y 12 términos de búsqueda altamente relevantes y específicos para una tienda online. Enfócate especialmente en palabras clave concretas relacionadas con marcas, productos o intereses explícitos del usuario. Utiliza el lenguaje exacto que un usuario escribiría en un buscador, priorizando términos cortos y accionables como 'cámara nikon', 'sony alpha', 'cámara para paisajes', etc.

Perfil del usuario: data{json.dumps(data_usuario)}.

Responde únicamente con un array JSON de strings. Ejemplo de formato exacto de respuesta: ["cámara nikon", "sony alpha 7", "ofertas cámaras canon"]. No incluyas ningún texto adicional, explicaciones ni markdown, solo el array JSON."""

        ia_message_content_str = openrouter_client.call_openrouter_api_for_prompt(
            prompt
        )

        if not ia_message_content_str:
            logging.warning(
                f"No se recibió contenido de la IA para usuario: {user_id}. Reintentando mensaje."
            )
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            return

        try:
            lista_busquedas = json.loads(ia_message_content_str)
            if not isinstance(lista_busquedas, list):
                raise ValueError("El contenido de la IA no es una lista JSON.")
            logging.info(
                f"Lista de búsquedas obtenida para {user_id}: {lista_busquedas}"
            )
        except json.JSONDecodeError as e:
            logging.error(
                f"Error al decodificar JSON de IA para {user_id}: {ia_message_content_str}. Error: {e}. Mensaje no será reencolado."
            )
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return
        except (
            ValueError
        ) as e:  # Captura el ValueError de la verificación de isinstance
            logging.error(
                f"Error en formato de contenido de IA para {user_id}: {ia_message_content_str}. Error: {e}. Mensaje no será reencolado."
            )
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        # Preparar mensaje para el scraper
        mensaje_para_scraper = {
            'user_id': user_id,  # Usar el ID extraído
            'busquedas': lista_busquedas
        }

        try:
            # Publicar en la cola del scraper
            # Asegurarse de que la cola existe (declararla aquí también es una buena práctica, aunque el consumidor también lo hará)
            ch.queue_declare(queue=SCRAPPER_PETICIONES_QUEUE, durable=True)
            ch.basic_publish(
                exchange="",
                routing_key=SCRAPPER_PETICIONES_QUEUE,
                body=json.dumps(mensaje_para_scraper),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Hacer el mensaje persistente
                ),
            )
            logging.info(
                f"Mensaje con búsquedas para usuario {user_id} enviado a {SCRAPPER_PETICIONES_QUEUE}: {mensaje_para_scraper}"
            )
        except Exception as pub_err:
            logging.error(
                f"Error al publicar mensaje en {SCRAPPER_PETICIONES_QUEUE} para {user_id}: {pub_err}. El mensaje original de IA será reencolado para no perder la petición."
            )
            # Reencolar el mensaje original de IA si falla la publicación al scraper
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            return

        ch.basic_ack(delivery_tag=method.delivery_tag)
        logging.info(
            f"Petición de IA procesada y ack enviada para usuario: {user_id}"
        )

    except (
        ValueError
    ) as val_err:  # Captura el ValueError de openrouter_client (ej. API Key) o json.loads
        # Distinguir si el error es por API key o por otra cosa podría ser útil aquí
        if "OPENROUTER_API_KEY" in str(val_err):
            logging.critical(
                f"Error crítico de configuración con OpenRouter (procesando usuario {user_id}): {val_err}. El mensaje no será reencolado. Revisar configuración."
            )
        else:
            logging.error(
                f"ValueError durante el procesamiento para {user_id}: {val_err}. Mensaje no será reencolado."
            )
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except (
        requests.exceptions.HTTPError,
        requests.exceptions.RequestException,
    ) as req_err:
        # Errores de comunicación con OpenRouter (ya logueados en openrouter_client)
        logging.warning(
            f"Error de comunicación con OpenRouter (procesando usuario {user_id}): {req_err}. Mensaje será reencolado."
        )
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    except (
        json.JSONDecodeError
    ) as e:  # Error al decodificar el body del mensaje de RabbitMQ
        logging.error(
            f"Error al decodificar JSON de RabbitMQ: {body.decode()}. Error: {e}. Mensaje no será reencolado."
        )
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        logging.error(
            f"Error inesperado al procesar petición de IA para {user_id}: {e}",
            exc_info=True,
        )
        ch.basic_nack(
            delivery_tag=method.delivery_tag, requeue=True
        )  # Reintentar para errores desconocidos


def iniciar_consumidor_ia():
    """Inicia el consumidor de RabbitMQ para la cola de peticiones_ia."""
    logging.info(f"Preparando para iniciar consumidor de {QUEUE_PETICIONES_IA}...")
    # La función call_openrouter_api_for_prompt ya no se pasa como argumento directamente aquí,
    # ya que procesar_peticion_ia_callback la importa y usa directamente.
    while True:
        conexion = conectar_a_rabbitmq()
        if conexion:
            try:
                canal = conexion.channel()
                canal.queue_declare(queue=QUEUE_PETICIONES_IA, durable=True)
                canal.basic_qos(prefetch_count=1)

                # El callback ahora usa directamente openrouter_client.call_openrouter_api_for_prompt
                canal.basic_consume(
                    queue=QUEUE_PETICIONES_IA,
                    on_message_callback=procesar_peticion_ia_callback,
                )

                logging.info(
                    f"Consumidor de {QUEUE_PETICIONES_IA} iniciado. Esperando mensajes..."
                )
                canal.start_consuming()
            except pika.exceptions.StreamLostError as e:
                logging.warning(
                    f"Se perdió la conexión con RabbitMQ (StreamLostError): {e}. Reintentando..."
                )
            except pika.exceptions.AMQPConnectionError as e:
                logging.warning(f"Error de conexión AMQP: {e}. Reintentando...")
            except Exception as e:
                logging.error(
                    f"Error inesperado en el consumidor de IA: {e}. Reintentando...",
                    exc_info=True,
                )
            finally:
                if conexion and not conexion.is_closed:
                    try:
                        conexion.close()
                        logging.info("Conexión RabbitMQ cerrada limpiamente.")
                    except Exception as close_err:
                        logging.error(
                            f"Error al cerrar la conexión RabbitMQ: {close_err}"
                        )
                logging.info(
                    "Intentando reconectar consumidor RabbitMQ en 10 segundos."
                )
                time.sleep(10)
        else:
            logging.warning(
                "No se pudo conectar a RabbitMQ para iniciar consumidor IA. Reintentando en 10 segundos."
            )
            time.sleep(10)
