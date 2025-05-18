# Smart Search - Sistema Inteligente de Recomendación de Productos

Smart Search es una aplicación web diseñada para ofrecer recomendaciones de productos personalizadas basadas en las preferencias y necesidades del usuario, utilizando un modelo de lenguaje grande (LLM) para el análisis inteligente y un scraper para la obtención de datos de productos.

**Repositorio del Proyecto:** [https://github.com/Aserturik/smart-search](https://github.com/Aserturik/smart-search)

## Arquitectura General

El sistema utiliza una arquitectura de microservicios orquestada mediante Docker Compose, con un fuerte énfasis en el procesamiento asíncrono a través de RabbitMQ. Los componentes principales son:

*   **Frontend (`front/`)**: Interfaz de usuario (asumido React con Vite) donde los usuarios ingresan su información. Se comunica con el backend y otros componentes principalmente a través de RabbitMQ.
*   **Backend (`back/`)**: Este servicio NO es una API Flask tradicional como podría sugerir la configuración de Docker Compose. En su lugar, utiliza Supervisor para ejecutar dos procesos Python independientes:
    *   **Procesador de Solicitudes (`index.py`)**: Un consumidor de RabbitMQ que escucha la cola `solicitudes`. Procesa los datos del usuario, los guarda en PostgreSQL y luego envía un mensaje a la cola `peticiones_ia` para iniciar el análisis de IA. También envía mensajes de estado a la cola `respuestas`.
    *   **Scraper (`scraper.py`)**: Un consumidor de RabbitMQ que escucha la cola `scrapper_peticiones_queue`. Al recibir una lista de términos de búsqueda (provenientes del servicio de IA), realiza scraping en MercadoLibre Colombia y envía las URLs de los productos encontrados a la cola `scraped_urls_queue`.
*   **Base de Datos (`Postgres/`)**: PostgreSQL para almacenar datos de usuarios, tests y solicitudes.
*   **Message Broker (`rabbitmq`)**: RabbitMQ para gestionar la comunicación asíncrona entre los diferentes servicios a través de varias colas dedicadas.
*   **Servicio de IA (`ai_service/`)**: Este servicio consta de dos partes principales:
    *   **Aplicación Flask (`app.py`)**: Proporciona un endpoint `/health` y un proxy directo a la API de OpenRouter (`/api/v1/chat/completions`). Carga la API key desde un archivo `.env` en su directorio.
    *   **Consumidor de IA (`rabbitmq_client.py`)**: Se ejecuta en un hilo separado dentro del mismo contenedor. Escucha la cola `peticiones_ia`, procesa la solicitud del usuario utilizando el `openrouter_client.py` para interactuar con el LLM (ej. `qwen/qwen-72b-chat`), y luego envía los términos de búsqueda generados por la IA a la cola `scrapper_peticiones_queue`.
*   **Reverse Proxy (`traefik`)**: Traefik para gestionar el enrutamiento de red (actualmente configurado principalmente para su propio dashboard).

## Tecnologías Utilizadas

*   **Frontend**: React, Vite, JavaScript (asumido, basado en `docker-compose.yml`)
*   **Backend (`back/` workers)**: Python, Pika (RabbitMQ Adapter), Psycopg2 (PostgreSQL Adapter), Requests, BeautifulSoup4 (para el scraper)
*   **Base de Datos**: PostgreSQL
*   **Message Broker**: RabbitMQ
*   **Servicio de IA (`ai_service/`)**: Flask (Python), Pika (RabbitMQ Adapter), Requests, API de OpenRouter (ej. Modelo `qwen/qwen-72b-chat`)
*   **Orquestación**: Docker, Docker Compose
*   **Gestión de Procesos (en `back/`)**: Supervisor
*   **Reverse Proxy**: Traefik

## Cómo Empezar

### Prerrequisitos

*   Docker instalado ([https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/))
*   Docker Compose instalado ([https://docs.docker.com/compose/install/](https://docs.docker.com/compose/install/))
*   **Crear archivo `.env` en `ai_service/`**: Este archivo debe contener la variable `OPENROUTER_API_KEY` con tu clave de API para OpenRouter. Ejemplo:
    ```env
    # ai_service/.env
    OPENROUTER_API_KEY="tu_api_key_aqui"
    ```

### Levantando la Aplicación

1.  **Clona el repositorio (si aplica).**
2.  **Asegúrate de haber creado el archivo `ai_service/.env` como se describe arriba.**
3.  **Navega al directorio raíz del proyecto.**
4.  **Construye e inicia todos los servicios usando Docker Compose:**
    ```bash
    docker-compose up -d --build
    ```

### Puertos Expuestos (configuración actual en `docker-compose.yml`):

*   **Traefik HTTP**: `80` (mapeado al puerto `80` del host)
*   **Traefik Dashboard**: `8080` (mapeado al puerto `8080` del host) - Accede vía `http://localhost:8080/dashboard/`
*   **RabbitMQ Management UI**: `15672` (mapeado al puerto `15672` del host) - Accede vía `http://localhost:15672/` (user: guest, pass: guest)
*   **PostgreSQL**: `5432` (mapeado al puerto `5432` del host)
*   **Frontend (directo, si se ejecuta localmente fuera de Docker o si Traefik no lo enruta)**: `5173`
*   **Backend (directo, si se ejecuta localmente fuera de Docker o si Traefik no lo enruta)**: `5000` (Nota: El servicio `back` actualmente no ejecuta una API Flask en este puerto; ejecuta workers de RabbitMQ. Esta configuración de puerto podría ser un remanente).
*   **AI Service (Flask Proxy & Health)**: `5001` (expuesto por el contenedor, accesible para health checks o proxy directo).

## Estructura de Directorios

```
.
├── Postgres/         # Configuración y Dockerfile para PostgreSQL
├── back/             # Lógica de los workers de backend (procesador de solicitudes, scraper), Dockerfile y config de Supervisor
├── front/            # Código fuente y Dockerfile del frontend React
├── ai_service/       # Aplicación Flask para proxy de IA y consumidor de RabbitMQ, Dockerfile (requiere .env con OPENROUTER_API_KEY)
├── rabbitmq/         # Configuración de plugins para RabbitMQ
├── docker-compose.yml # Archivo de orquestación de Docker Compose
└── README.md         # Este archivo
```

## Flujo de Recomendación de Productos

1.  El **Frontend** recopila la información del usuario y la envía como un mensaje a la cola `solicitudes` de RabbitMQ.
2.  El worker **Procesador de Solicitudes (`back/index.py`)** consume el mensaje de `solicitudes`.
    *   Guarda los datos del usuario y el test en la base de datos **PostgreSQL**.
    *   Envía un mensaje de confirmación/estado a la cola `respuestas` (que el Frontend puede escuchar).
    *   Publica un mensaje con el perfil del usuario en la cola `peticiones_ia`.
3.  El **Consumidor de IA (`ai_service/rabbitmq_client.py`)** consume el mensaje de `peticiones_ia`.
    *   Prepara un prompt y utiliza el `openrouter_client.py` para consultar el modelo de lenguaje grande (LLM) a través de OpenRouter.
    *   El LLM devuelve una lista de términos de búsqueda relevantes.
    *   El Consumidor de IA publica estos términos de búsqueda en la cola `scrapper_peticiones_queue`.
4.  El worker **Scraper (`back/scraper.py`)** consume el mensaje de `scrapper_peticiones_queue`.
    *   Utiliza los términos de búsqueda para realizar scraping en MercadoLibre Colombia.
    *   Recopila una lista de URLs de productos.
    *   Publica las URLs scrapeadas en la cola `scraped_urls_queue`.
5.  El **Frontend** consume los mensajes de la cola `scraped_urls_queue` para mostrar las recomendaciones de productos al usuario. También puede escuchar la cola `respuestas` para feedback del proceso de solicitud inicial.

## Mejoras y Pasos Futuros Clave

*   **Clarificar/Corregir Configuración del Servicio `back`**:
    *   El `docker-compose.yml` define el servicio `back` como si fuera una aplicación Flask en el puerto 5000 (`FLASK_APP=index.py`), pero `index.py` es un worker de RabbitMQ. Esta configuración es confusa. Si no hay una API Flask en `back/`, se debería eliminar la exposición del puerto 5000 y las variables de entorno `FLASK_APP` y `FLASK_ENV`.
    *   Si se pretende tener una API REST en el backend además de los workers, debería ser un proceso separado o `index.py` debería ser refactorizado.
*   **Definir/Crear Esquema Completo de BD**: Asegurar que el directorio `Postgres/` contenga los scripts para inicializar todas las tablas necesarias (incluyendo una para `recomendaciones` si se planea almacenar las URLs scrapeadas de forma persistente).
*   **Configurar Traefik para Servicios**: Modificar `docker-compose.yml` para que Traefik enrute el tráfico a `front` y `ai_service` (si se desea exponer su API proxy) usando etiquetas (`labels`). Actualmente, `traefik.enable=false` para la mayoría de los servicios.
*   **Gestión de Secretos Avanzada**: Considerar el uso de Docker secrets o Vault para la `OPENROUTER_API_KEY` y credenciales de base de datos/RabbitMQ, en lugar de solo archivos `.env` o valores por defecto.
*   **Healthchecks Robustos**:
    *   Añadir healthchecks para `front` y `back` (workers) en `docker-compose.yml`. El healthcheck del `back` podría verificar la conexión a RabbitMQ y PostgreSQL.
    *   Mejorar el healthcheck del `ai_service` para que también verifique la conexión a RabbitMQ o incluso la disponibilidad de OpenRouter (con cuidado de no exceder cuotas).
*   **Documentación Detallada por Servicio**: Expandir la documentación interna de cada servicio/módulo.
*   **Manejo de Errores y Resiliencia**: Mejorar el manejo de errores en los consumidores de RabbitMQ (políticas de reintento, colas de mensajes fallidos - dead-letter queues).
*   **Testing**: Implementar tests unitarios e de integración para los diferentes componentes.
*   **Frontend-Backend Sincronización**: Detallar más cómo el frontend gestiona la naturaleza asíncrona de las recomendaciones (e.g., cómo notifica al usuario cuando las URLs están listas).
