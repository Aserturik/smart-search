from flask import Flask, jsonify
from flask_cors import CORS
import logging
from database_utils import get_db_connection

app = Flask(__name__)
CORS(app)

@app.route('/formulary/<int:user_id>', methods=['GET'])
def get_user_form_data(user_id):
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Error de conexión a la base de datos'}), 500

        cursor = conn.cursor()

        # Consulta para obtener la información del usuario y su formulario
        query = """
            SELECT 
                u.id as usuario_id,
                u.nombreUsuario,
                u.edad,
                t.motivoCompra,
                t.fuenteInformacion,
                t.temasDeInteres,
                t.comprasNoNecesarias,
                t.importanciaMarca,
                t.probarNuevosProductos,
                t.aspiraciones,
                t.nivelSocial,
                t.tiempoLibre,
                t.identidad,
                t.tendencias,
                s.id as solicitud_id,
                s.comentarioSolicitud
            FROM usuarios u
            LEFT JOIN solicitudes s ON u.id = s.userId
            LEFT JOIN tests t ON s.testsId = t.id
            WHERE u.id = %s
            ORDER BY s.id DESC
            LIMIT 1
        """
        
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()

        if not result:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        # Modificamos la consulta de URLs para usar el ID de solicitud específico
        urls_query = """
            SELECT ue.url, ue.fecha_creacion
            FROM urls_encontradas ue
            WHERE ue.solicitud_id = %s
            ORDER BY ue.fecha_creacion DESC
        """
        
        # Usamos el ID de solicitud específico
        cursor.execute(urls_query, (result[14],))  # result[14] es solicitud_id
        urls = [{"url": row[0], "fecha": row[1].isoformat()} for row in cursor.fetchall()]

        # Para debugging
        logging.info(f"URLs encontradas para solicitud {result[14]}: {urls}")

        response = {
            'usuario': {
                'id': result[0],
                'nombre': result[1],
                'edad': result[2]
            },
            'formulario': {
                'motivoCompra': result[3],
                'fuenteInformacion': result[4],
                'temasDeInteres': result[5],
                'comprasNoNecesarias': result[6],
                'importanciaMarca': result[7],
                'probarNuevosProductos': result[8],
                'aspiraciones': result[9],
                'nivelSocial': result[10],
                'tiempoLibre': result[11],
                'identidad': result[12],
                'tendencias': result[13]
            },
            'solicitud': {
                'id': result[14],
                'comentario': result[15],
                'urls': urls
            }
        }

        # Para debugging
        logging.info(f"Respuesta completa: {response}")

        return jsonify(response)

    except Exception as e:
        logging.error(f"Error al obtener datos del usuario: {e}")
        return jsonify({'error': f'Error del servidor: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)