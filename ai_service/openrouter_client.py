import os
import requests
import json
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
YOUR_SITE_URL = os.getenv("YOUR_SITE_URL", "http://localhost:5173")
YOUR_SITE_NAME = os.getenv("YOUR_SITE_NAME", "Smart Search")

DEFAULT_MODEL = "qwen/qwen3-235b-a22b"

def get_openrouter_headers():
    if not OPENROUTER_API_KEY:
        logging.error("OPENROUTER_API_KEY no está configurada.")
        raise ValueError("OPENROUTER_API_KEY no está configurada.")
    return {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": YOUR_SITE_URL,
        "X-Title": YOUR_SITE_NAME,
    }

def call_openrouter_api_for_prompt(prompt: str):
    """Llama a la API de OpenRouter con un prompt específico para la generación de búsquedas."""
    try:
        headers = get_openrouter_headers()
        payload = {
            "model": DEFAULT_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            # "temperature": 0.7, # Opcional
            # "max_tokens": 150,  # Opcional
        }
        
        logging.debug(f"Enviando petición a OpenRouter (prompt): {json.dumps(payload)}")
        response = requests.post(OPENROUTER_API_URL, headers=headers, data=json.dumps(payload), timeout=60)
        response.raise_for_status()
        response_json = response.json()
        logging.debug(f"Respuesta recibida de OpenRouter (prompt): {response_json}")
        
        ia_message_content_str = response_json.get('choices', [{}])[0].get('message', {}).get('content')
        if not ia_message_content_str:
            logging.warning("No se encontró contenido en la respuesta de la IA o formato inesperado.")
            return None
        return ia_message_content_str

    except requests.exceptions.HTTPError as http_err:
        logging.error(f"Error HTTP al contactar OpenRouter: {http_err} - {http_err.response.text if http_err.response else 'No response text'}")
        # Reintentar es manejado por RabbitMQ, aquí solo retornamos None o levantamos la excepción
        raise # Re-levantar para que el consumidor de RabbitMQ pueda decidir si reencolar
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Error de red o conexión al contactar OpenRouter: {req_err}")
        raise # Re-levantar para que el consumidor de RabbitMQ pueda decidir si reencolar
    except ValueError as val_err: # Por ejemplo, si la API key no está configurada
        logging.error(f"Error de configuración: {val_err}")
        raise # No se puede continuar sin API key
    except Exception as e:
        logging.error(f"Error inesperado al llamar a OpenRouter API: {e}", exc_info=True)
        raise # Re-levantar para manejo genérico

def proxy_openrouter_request(incoming_data: dict):
    """Actúa como proxy para la API de OpenRouter, reenviando la solicitud y respuesta."""
    try:
        headers = get_openrouter_headers()
        model = incoming_data.get("model")
        messages = incoming_data.get("messages")

        if not model or not messages:
            return {"error": "Faltan los campos 'model' o 'messages' en el request body"}, 400

        data_to_send = {
            "model": model,
            "messages": messages
        }
        
        optional_params = ["temperature", "top_p", "max_tokens", "stream", "stop", "frequency_penalty", "presence_penalty", "seed"]
        for param in optional_params:
            if param in incoming_data:
                data_to_send[param] = incoming_data[param]

        logging.debug(f"Enviando a OpenRouter (proxy): {json.dumps(data_to_send)}")
        
        response = requests.post(OPENROUTER_API_URL, headers=headers, data=json.dumps(data_to_send), stream=True)
        response.raise_for_status()
        return response # Se devuelve el objeto response para streaming si es necesario

    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error en proxy: {http_err} - {http_err.response.text if http_err.response else 'No response text'}")
        # Devolver el error original de OpenRouter si es posible
        error_details = http_err.response.text if http_err.response else "Error en la comunicación con la API de IA"
        status_code = http_err.response.status_code if http_err.response is not None else 500
        return {"error": "Error en la comunicación con la API de IA", "details": error_details}, status_code
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request error en proxy: {req_err}")
        return {"error": "Error de red o configuración al contactar la API de IA"}, 503
    except ValueError as val_err: # API Key no configurada
        logging.error(f"Error de configuración en proxy: {val_err}")
        return {"error": str(val_err)}, 500
    except Exception as e:
        logging.error(f"Ocurrió un error inesperado en proxy: {e}", exc_info=True)
        return {"error": f"Ocurrió un error inesperado: {str(e)}"}, 500 