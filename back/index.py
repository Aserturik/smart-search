from flask import Flask, request, jsonify, Response
import uuid
import requests

app = Flask(__name__)

@app.route('/recomendarProductos', methods=['POST'])
def recomendar_productos():
    user_id = str(uuid.uuid4())
    solicitud = f"Solicitud recibida para usuario {user_id}"
    return jsonify({
        'id_usuario': user_id,
        'solicitud': solicitud
    })

@app.route('/recomendarProductos', defaults={'path': ''}, methods=['GET'])
@app.route('/recomendarProductos/<path:path>', methods=['GET'])
def recomendar_productos_front(path):
    # Proxy cualquier ruta al frontend
    try:
        url = f'http://front:5173/{path}'
        resp = requests.get(url)
        return Response(resp.content, status=resp.status_code, content_type=resp.headers.get('Content-Type'))
    except Exception as e:
        return f"Error al conectar con el frontend: {e}", 502

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
