# Backend Service - Smart Search

Este servicio maneja el procesamiento de solicitudes de usuarios y el scraping de productos.

## Estructura

back/
├── index.py           # Worker principal para procesar solicitudes
├── scraper.py        # Worker para scraping de productos
├── database_utils.py # Utilidades para conexión a PostgreSQL
├── rabbitmq_utils.py # Utilidades para conexión a RabbitMQ
├── requirements.txt  # Dependencias del servicio
├── supervisor.conf   # Configuración de supervisord
└── Dockerfile       # Configuración de contenedor

## Funcionalidades

1. **Procesamiento de Solicitudes (`index.py`)**
   - Recibe datos de usuarios desde RabbitMQ
   - Almacena información en PostgreSQL
   - Envía perfiles a la cola de IA

2. **Scraping de Productos (`scraper.py`)**
   - Escucha términos de búsqueda desde RabbitMQ
   - Realiza scraping en MercadoLibre
   - Envía URLs encontradas al frontend

## Tecnologías

- Python 3.11
- PostgreSQL (psycopg2)
- RabbitMQ (pika)
- BeautifulSoup4 (scraping)
- Supervisor (gestión de procesos)

## Configuración

El servicio se configura a través de variables de entorno:
- `RABBITMQ_HOST`: Host de RabbitMQ (default: "rabbitmq")
- `RABBITMQ_PORT`: Puerto de RabbitMQ (default: 5672)
- `POSTGRES_HOST`: Host de PostgreSQL
- `POSTGRES_DB`: Nombre de la base de datos
- `POSTGRES_USER`: Usuario de PostgreSQL
- `POSTGRES_PASSWORD`: Contraseña de PostgreSQL

## Colas RabbitMQ

- `solicitudes`: Recibe datos de formularios
- `respuestas`: Envía confirmaciones al frontend
- `peticiones_ia`: Envía perfiles al servicio de IA
- `scrapper_peticiones_queue`: Recibe términos de búsqueda
- `scraped_urls_queue`: Envía URLs encontradas