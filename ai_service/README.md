# AI Service - Smart Search

Servicio de procesamiento de IA que utiliza OpenRouter para generar términos de búsqueda personalizados.

## Estructura

ai_service/
├── app.py              # API Flask y healthcheck
├── rabbitmq_client.py  # Cliente RabbitMQ
├── openrouter_client.py # Cliente OpenRouter
├── requirements.txt    # Dependencias
└── Dockerfile         # Configuración de contenedor

## Funcionalidades

1. **API REST (`app.py`)**
   - Endpoint de healthcheck
   - Proxy para OpenRouter API
   - Gestión de configuración

2. **Procesamiento de IA**
   - Análisis de perfiles de usuario
   - Generación de términos de búsqueda
   - Comunicación con OpenRouter

## Tecnologías usadas

- Python 3.11
- Flask
- RabbitMQ (pika)
- OpenRouter API

## Configuración

Requiere un archivo `.env` con:
```env
OPENROUTER_API_KEY=tu_api_key_aqui
```

Variables de entorno adicionales:
- `RABBITMQ_HOST`: Host de RabbitMQ
- `RABBITMQ_PORT`: Puerto de RabbitMQ
- `FLASK_APP`: Aplicación Flask
- `FLASK_RUN_HOST`: Host de Flask
- `PYTHONUNBUFFERED`: Configuración de Python

## Colas RabbitMQ

- `peticiones_ia`: Recibe perfiles de usuario
- `scrapper_peticiones_queue`: Envía términos de búsqueda

## API Endpoints

- `GET /health`: Healthcheck del servicio
- `POST /api/v1/chat/completions`: Proxy para OpenRouter