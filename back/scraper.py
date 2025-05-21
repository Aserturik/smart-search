import requests
from bs4 import BeautifulSoup
import os
import logging
import pika
import json
import time
import sys
from rabbitmq_utils import enviar_a_scraped_urls, QUEUE_SCRAPED_URLS
from database_utils import get_db_connection, init_db_connection_pool

# Configure logging con más detalles
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# RabbitMQ Configuration (similar to ai_service)
RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_PORT = int(os.environ.get('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.environ.get('RABBITMQ_USER', 'guest')
RABBITMQ_PASS = os.environ.get('RABBITMQ_PASS', 'guest')
SCRAPPER_PETICIONES_QUEUE = os.environ.get('SCRAPPER_PETICIONES_QUEUE', 'scrapper_peticiones_queue')
MAX_PRODUCTS_PER_SEARCH_DEFAULT = int(os.environ.get('MAX_PRODUCTS_PER_SEARCH', 3))

def get_rabbitmq_connection_params():
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
            conexion = pika.BlockingConnection(get_rabbitmq_connection_params())
            logger.info("Scraper: Conexión establecida con RabbitMQ")
            return conexion
        except Exception as e:
            intentos += 1
            logger.error(f"Scraper: Intento {intentos}/{max_intentos} fallido al conectar con RabbitMQ: {e}")
            if intentos < max_intentos:
                logger.info(f"Scraper: Reintentando en {tiempo_espera} segundos...")
                time.sleep(tiempo_espera)
    logger.error("Scraper: No se pudo establecer conexión con RabbitMQ después de varios intentos")
    return None

def construir_url(response):
    busqueda = response.lower().replace(" ", "-").replace(",", "")
    
    # Construir la URL
    base_url = "https://listado.mercadolibre.com.co"
    url = f"{base_url}/{busqueda}"
    return url

def scrape_mercadolibre_colombia(search_queries_obj, max_products_per_search=5):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    all_product_links = {"urls": []}
    
    if "busquedas" not in search_queries_obj or not isinstance(search_queries_obj["busquedas"], list):
        logger.error("Invalid input format. Expected {'busquedas': ['query1', 'query2', ...]}")
        return all_product_links

    for busqueda_texto in search_queries_obj["busquedas"]:
        logger.info(f"Starting scrape for: {busqueda_texto}")
        url = construir_url(busqueda_texto)
        logger.info(f"Generated URL: {url}")
        
        product_links_for_current_search = []
        current_page = 1
        retries = 3 # Max retries per page

        while len(product_links_for_current_search) < max_products_per_search:
            page_url = f"{url}_Desde_{(current_page - 1) * 50 + 1}" if current_page > 1 else url
            
            attempt = 0
            response = None
            while attempt < retries:
                try:
                    response = requests.get(page_url, headers=headers, timeout=10)
                    response.raise_for_status() # Raises an HTTPError for bad responses (4XX or 5XX)
                    break 
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Error accessing page {page_url} (Attempt {attempt + 1}/{retries}): {e}")
                    attempt += 1
                    if attempt == retries:
                        logger.error(f"Failed to access page {page_url} after {retries} attempts.")
                        # Optionally, you might want to break the outer loop or skip this search query
                        break # Break from retry loop, go to next search or stop

            if response is None or response.status_code != 200:
                # If all retries failed, or an unexpected status code after successful connection
                break # Stop processing this search query

            soup = BeautifulSoup(response.text, "html.parser")
            items = soup.find_all("a", href=True)
            
            found_new_link_on_page = False
            for item in items:
                link = item.get("href")
                if link and "articulo.mercadolibre.com.co" in link and len(product_links_for_current_search) < max_products_per_search:
                    if link not in all_product_links["urls"] and link not in product_links_for_current_search:
                        product_links_for_current_search.append(link)
                        all_product_links["urls"].append(link)
                        found_new_link_on_page = True
                if len(product_links_for_current_search) >= max_products_per_search:
                    break
            
            if len(product_links_for_current_search) >= max_products_per_search:
                logger.info(f"Reached max products ({max_products_per_search}) for '{busqueda_texto}'.")
                break

            # Check for next page
            # MercadoLibre's "Siguiente" button might be within a specific element, e.g., <li class="andes-pagination__button andes-pagination__button--next">
            # Or it might be a direct <a> tag with title "Siguiente" or text "Siguiente"
            next_page_indicators = soup.find_all("a", title="Siguiente")
            if not next_page_indicators:
                 # Fallback: find by text if title not present or varies
                next_page_indicators = [a for a in soup.find_all("a") if a.get_text(strip=True) == "Siguiente"]

            if not next_page_indicators or not next_page_indicators[0].get("href"):
                logger.info(f"No 'Next' page found for '{busqueda_texto}' on page {current_page}. Reached end of results for this search or page structure changed.")
                break # No next page link found

            if not found_new_link_on_page and current_page > 1: # Avoid breaking on first page if it's empty for some reason
                 logger.info(f"No new links found on page {current_page} for '{busqueda_texto}'. Assuming end of relevant results.")
                 break
            
            current_page += 1
            # Optional: Add a small delay to be polite to the server
            # import time
            # time.sleep(1) 

        logger.info(f"Found {len(product_links_for_current_search)} links for '{busqueda_texto}'.")

    logger.info(f"Scraping finished. Total unique URLs collected: {len(all_product_links['urls'])}")
    logger.info(f"Collected URLs: {all_product_links}")
    return all_product_links

def procesar_peticion_scraping_callback(ch, method, properties, body):
    """Procesa un mensaje de la cola de peticiones de scraping."""
    user_id_log = 'ID no especificado'
    try:
        mensaje = json.loads(body.decode())
        user_id_log = mensaje.get('user_id', 'ID no especificado')
        logger.info(f"Scraper: Recibida petición de scraping para usuario: {user_id_log} con datos: {mensaje}")

        if 'busquedas' not in mensaje or not isinstance(mensaje['busquedas'], list):
            logger.error(f"Scraper: Formato de mensaje inválido para {user_id_log}. Esperado {{'busquedas': [...]}}. Mensaje: {mensaje}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False) # No reencolar, mensaje erróneo
            return

        # Crear el objeto esperado por scrape_mercadolibre_colombia
        search_queries_obj = {"busquedas": mensaje['busquedas']}
        max_products = mensaje.get('max_products_per_search', MAX_PRODUCTS_PER_SEARCH_DEFAULT)

        logger.info(f"Scraper: Iniciando scraping para {user_id_log} con {len(search_queries_obj['busquedas'])} búsquedas, max_products: {max_products}.")
        
        # Aquí se llama a la función de scraping existente
        # La función scrape_mercadolibre_colombia ya loguea sus resultados.
        scraped_data = scrape_mercadolibre_colombia(search_queries_obj, max_products_per_search=max_products)

        # Podrías enviar `scraped_data` a otra cola o base de datos aquí si es necesario.
        # Por ahora, solo confirmamos el procesamiento.
        logger.info(f"Scraper: Scraping completado para {user_id_log}. URLs obtenidas: {len(scraped_data.get('urls', []))}")

        # Enviar las URLs scrapeadas a la nueva cola para el frontend
        if scraped_data.get('urls'):
            payload_urls = {
                'user_id': user_id_log, # Aunque el frontend no lo use actualmente para esto, es buena práctica incluirlo
                'urls': scraped_data['urls']
            }
            if enviar_a_scraped_urls(payload_urls):
                logger.info(f"Scraper: URLs enviadas a {QUEUE_SCRAPED_URLS} para usuario {user_id_log}")
            else:
                logger.error(f"Scraper: Error al enviar URLs a {QUEUE_SCRAPED_URLS} para usuario {user_id_log}")

            # Guardar URLs en la base de datos
            try:
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    
                    # Convertir user_id_log a entero
                    user_id = int(user_id_log)
                    
                    # Obtener el ID de la solicitud más reciente
                    cursor.execute("""
                        SELECT id 
                        FROM solicitudes 
                        WHERE userId = %s 
                        ORDER BY id DESC 
                        LIMIT 1
                    """, (user_id,))
                    
                    solicitud_id = cursor.fetchone()
                    
                    if solicitud_id:
                        logger.info(f"Encontrada solicitud {solicitud_id[0]} para usuario {user_id}")
                        
                        # Primero eliminar URLs existentes para esta solicitud
                        cursor.execute("""
                            DELETE FROM urls_encontradas 
                            WHERE solicitud_id = %s
                        """, (solicitud_id[0],))
                        
                        # Insertar las nuevas URLs
                        for url in scraped_data['urls']:
                            cursor.execute("""
                                INSERT INTO urls_encontradas (solicitud_id, url)
                                VALUES (%s, %s)
                            """, (solicitud_id[0], url))
                        
                        conn.commit()
                        logger.info(f"Se guardaron {len(scraped_data['urls'])} URLs para la solicitud {solicitud_id[0]}")
                    else:
                        logger.error(f"No se encontró solicitud para el usuario {user_id}")
            except ValueError as e:
                logger.error(f"Error al convertir user_id: {user_id_log} - {e}")
            except Exception as e:
                logger.error(f"Error al guardar URLs: {e}")
                if conn:
                    conn.rollback()
            finally:
                if conn:
                    conn.close()

        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info(f"Scraper: Petición de scraping procesada y ack enviada para usuario: {user_id_log}")

    except json.JSONDecodeError as e:
        logger.error(f"Scraper: Error al decodificar JSON de RabbitMQ para {user_id_log}: {body.decode()}. Error: {e}. Mensaje no será reencolado.")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        logger.error(f"Scraper: Error inesperado al procesar petición de scraping para {user_id_log}: {e}", exc_info=True)
        # Reencolar con precaución, podría ser un error persistente en el mensaje o en el scraper
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True) 

def iniciar_consumidor_scraper():
    """Inicia el consumidor de RabbitMQ para la cola de peticiones de scraping."""
    logger.info(f"Scraper: Preparando para iniciar consumidor de {SCRAPPER_PETICIONES_QUEUE}...")
    while True:
        conexion = conectar_a_rabbitmq()
        if conexion:
            try:
                canal = conexion.channel()
                # Declarar la cola como durable, igual que el productor
                canal.queue_declare(queue=SCRAPPER_PETICIONES_QUEUE, durable=True)
                canal.basic_qos(prefetch_count=1) # Procesar un mensaje a la vez
                
                canal.basic_consume(queue=SCRAPPER_PETICIONES_QUEUE, on_message_callback=procesar_peticion_scraping_callback)
                
                logger.info(f"Scraper: Consumidor de {SCRAPPER_PETICIONES_QUEUE} iniciado. Esperando mensajes...")
                canal.start_consuming()
            except pika.exceptions.StreamLostError as e:
                logger.warning(f"Scraper: Se perdió la conexión con RabbitMQ (StreamLostError): {e}. Reintentando...")
            except pika.exceptions.AMQPConnectionError as e:
                logger.warning(f"Scraper: Error de conexión AMQP: {e}. Reintentando...")
            except Exception as e:
                logger.error(f"Scraper: Error inesperado en el consumidor: {e}. Reintentando...", exc_info=True)
            finally:
                if conexion and not conexion.is_closed:
                    try:
                        conexion.close()
                        logger.info("Scraper: Conexión RabbitMQ cerrada limpiamente.")
                    except Exception as close_err:
                        logger.error(f"Scraper: Error al cerrar la conexión RabbitMQ: {close_err}")
                logger.info("Scraper: Intentando reconectar consumidor RabbitMQ en 10 segundos.")
                time.sleep(10)
        else:
            logger.warning("Scraper: No se pudo conectar a RabbitMQ para iniciar consumidor. Reintentando en 10 segundos.")
            time.sleep(10)

def main():
    """Función principal que inicia el servicio"""
    try:
        # Inicializar la conexión a la base de datos
        if not init_db_connection_pool():
            logger.error("No se pudo inicializar el pool de conexiones a la base de datos")
            sys.exit(1)
            
        logger.info("Iniciando servicio de Scraper...")
        iniciar_consumidor_scraper()
    except Exception as e:
        logger.error(f"Error crítico al iniciar el servicio: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()