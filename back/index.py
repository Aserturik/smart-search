from flask import Flask, request, jsonify, Response
import uuid
import requests
import logging  # Importamos logging para configurar el nivel de log
from flask_cors import CORS

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

@app.route('/recomendar-productos', methods=['POST'])
def recomendar_productos():
    data = request.json
    nombre = data.get('nombre', 'Usuario Anónimo')
    respuesta = data.get('respuesta', 'Sin respuesta')
    user_id = str(uuid.uuid4())
    
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
