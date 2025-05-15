import os
import requests
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

app = Flask(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Puedes cambiar estos si quieres que tu sitio aparezca en los rankings de OpenRouter
YOUR_SITE_URL = "http://localhost:5173" # Ejemplo, podría ser la URL de tu frontend
YOUR_SITE_NAME = "Smart Search"

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
    app.run(host='0.0.0.0', port=5001, debug=True) # Puerto diferente al backend principal 