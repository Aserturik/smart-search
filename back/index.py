from flask import Flask
import logging  # Importamos logging para configurar el nivel de log
from flask_cors import CORS
from routes import register_routes  # Importamos la función que registra las rutas

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

# Registrar las rutas desde el módulo routes
register_routes(app)

# Mensaje de inicio para verificar que el logger funciona
app.logger.info("Flask backend iniciado - Listo para recibir solicitudes")
print("SERVIDOR FLASK INICIADO", flush=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
