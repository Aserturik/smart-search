from dotenv import load_dotenv
load_dotenv() # Called first to load .env variables

import os
import logging

# Initial debug print, happens immediately after load_dotenv()
# Using print here to ensure it appears regardless of logging config state
print(f"DEBUG PRINT (app.py top): OPENROUTER_API_KEY from .env: {os.getenv('OPENROUTER_API_KEY')}")

from flask import Flask, request, jsonify
import threading
import requests # Keep for Response object if needed by Flask

# Importaciones de los nuevos módulos
import rabbitmq_client
import openrouter_client

# Configure logging (can be done after load_dotenv if logging config might come from .env)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Log the API key again using the configured logger for confirmation
logging.info(f"DEBUG LOGGING (app.py after imports): OPENROUTER_API_KEY from .env: {os.getenv('OPENROUTER_API_KEY')}")

app = Flask(__name__)

# Las configuraciones de API y RabbitMQ se han movido a sus respectivos módulos.

@app.route('/health')
def health_check():
    # Considerar verificar la conectividad con RabbitMQ si es crítico
    # rabbitmq_status = rabbitmq_client.check_rabbitmq_connection()
    # if rabbitmq_status:
    #     return jsonify({"status": "healthy", "rabbitmq_connection": "ok"}), 200
    # else:
    #     return jsonify({"status": "unhealthy", "rabbitmq_connection": "failed"}), 503
    return jsonify({"status": "healthy"}), 200

@app.route('/api/v1/chat/completions', methods=['POST'])
def proxy_openrouter_endpoint():
    try:
        incoming_data = request.json
        if not incoming_data:
            return jsonify({"error": "Request body debe ser JSON"}), 400

        # Llamada a la función del openrouter_client
        response_data = openrouter_client.proxy_openrouter_request(incoming_data)

        if isinstance(response_data, tuple) and len(response_data) == 2 and isinstance(response_data[0], dict):
            # Es un error formateado como (dict_error, status_code)
            return jsonify(response_data[0]), response_data[1]
        elif isinstance(response_data, requests.Response):
            # Es una respuesta de OpenRouter, potencialmente para streaming
            if 'chunked' in response_data.headers.get('Transfer-Encoding', '').lower():
                def generate():
                    for chunk in response_data.iter_content(chunk_size=8192):
                        yield chunk
                return app.response_class(generate(), content_type=response_data.headers['Content-Type'], status=response_data.status_code)
            else:
                return jsonify(response_data.json()), response_data.status_code
        else:
            # Caso inesperado
            logging.error(f"Respuesta inesperada del proxy_openrouter_request: {response_data}")
            return jsonify({"error": "Respuesta inesperada del servicio de IA"}), 500

    except Exception as e:
        # Este es un catch-all más genérico si proxy_openrouter_request mismo levanta una excepción no manejada por él
        logging.error(f"Error inesperado en el endpoint proxy_openrouter: {e}", exc_info=True)
        return jsonify({"error": f"Ocurrió un error inesperado en el servidor: {str(e)}"}), 500


if __name__ == '__main__':
    # Iniciar el consumidor de RabbitMQ en un hilo separado
    thread_consumidor = threading.Thread(
        target=rabbitmq_client.iniciar_consumidor_ia,
        daemon=True
    )
    thread_consumidor.start()
    
    app.run(host='0.0.0.0', port=5001, debug=False) # debug=False para producción 