# Smart Search - Sistema Inteligente de Recomendación de Productos

Smart Search es una aplicación web diseñada para ofrecer recomendaciones de productos personalizadas basadas en las preferencias y necesidades del usuario, utilizando un modelo de lenguaje grande (LLM) para el análisis inteligente.

## Arquitectura General

El sistema utiliza una arquitectura de microservicios orquestada mediante Docker Compose. Los componentes principales son:

*   **Frontend (`front/`)**: Interfaz de usuario desarrollada en React (con Vite) donde los usuarios ingresan su información y preferencias.
*   **Backend (`back/`)**: API desarrollada en Flask (Python) que gestiona la lógica de negocio, la comunicación con la base de datos y el message broker.
*   **Base de Datos (`Postgres/`)**: PostgreSQL para almacenar datos de usuarios, tests y solicitudes.
*   **Message Broker (`rabbitmq`)**: RabbitMQ para gestionar colas de mensajes y permitir el procesamiento asíncrono de las solicitudes de recomendación.
*   **Motor de IA (`ai_service/`)**: Servicio Flask (Python) que actúa como proxy a una API externa de modelos de lenguaje (OpenRouter). Ejecuta el modelo especificado en las solicitudes (ej. `qwen/qwen-72b-chat`) utilizando una API key almacenada en `ai_service/.env`. Es responsable de generar las recomendaciones.
*   **Reverse Proxy (`traefik`)**: Traefik para gestionar el enrutamiento de red y potencialmente SSL (actualmente solo configurado para su propio dashboard).
*   **Scraper (`scraper/`)**: Componente planeado para la recolección de datos de productos (actualmente no implementado).

## Tecnologías Utilizadas

*   **Frontend**: React, Vite, JavaScript
*   **Backend**: Flask (Python), Requests, Psycopg2 (PostgreSQL Adapter), Pika (RabbitMQ Adapter)
*   **Base de Datos**: PostgreSQL
*   **Message Broker**: RabbitMQ
*   **IA**: Flask (Python) como proxy, API de OpenRouter (ej. Modelo `qwen/qwen-72b-chat`)
*   **Orquestación**: Docker, Docker Compose
*   **Reverse Proxy**: Traefik

## Cómo Empezar

### Prerrequisitos

*   Docker instalado ([https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/))
*   Docker Compose instalado ([https://docs.docker.com/compose/install/](https://docs.docker.com/compose/install/))

### Levantando la Aplicación

1.  **Clona el repositorio (si aplica).**
2.  **Navega al directorio raíz del proyecto.**
3.  **Construye e inicia todos los servicios usando Docker Compose:**
    ```bash
    docker-compose up -d --build
    ```
    *Nota: El servicio `ai_service` y un consumidor de RabbitMQ para interactuar con él necesitan ser añadidos al `docker-compose.yml` y creados para una funcionalidad completa.*

### Puertos Expuestos (configuración actual en `docker-compose.yml`):

*   **Traefik HTTP**: `80` (mapeado al puerto `80` del host)
*   **Traefik Dashboard**: `8080` (mapeado al puerto `8080` del host) - Accede vía `http://localhost:8080/dashboard/`
*   **RabbitMQ Management UI**: `15672` (mapeado al puerto `15672` del host) - Accede vía `http://localhost:15672/` (user: guest, pass: guest)
*   **PostgreSQL**: `5432` (mapeado al puerto `5432` del host)
*   **Frontend (directo, si se ejecuta localmente fuera de Docker o si Traefik no lo enruta)**: `5173`
*   **Backend (directo, si se ejecuta localmente fuera de Docker o si Traefik no lo enruta)**: `5000`
*   **AI Service (Flask Proxy)**: `5001` (expuesto internamente por el contenedor, se accederá a través de Docker networking)

## Estructura de Directorios

```
.
├── Postgres/         # Configuración y Dockerfile para PostgreSQL
├── back/             # Código fuente y Dockerfile del backend Flask
├── front/            # Código fuente y Dockerfile del frontend React
├── ai_service/       # Dockerfile y aplicación Flask para el proxy a la API de IA (requiere .env con OPENROUTER_API_KEY)
├── scraper/          # Placeholder para el servicio de scraping (Dockerfile vacío)
├── .git/             # Repositorio Git
├── docker-compose.yml # Archivo de orquestación de Docker Compose
└── README.md         # Este archivo
```

## Flujo de Recomendación de Productos (Previsto)

1.  El usuario accede al **Frontend** y completa un formulario/test con sus preferencias.
2.  El Frontend envía la información al **Backend**.
3.  El Backend guarda los datos en la base de datos **PostgreSQL**.
4.  El Backend publica un mensaje con los datos del usuario/test en una cola de **RabbitMQ**.
5.  Un servicio **Consumidor de RabbitMQ** (por implementar) toma el mensaje de la cola.
6.  Este consumidor envía los datos al servicio **`ai_service`** (el proxy Flask).
7.  El `ai_service` reenvía la solicitud a la API de OpenRouter, la cual procesa la información y devuelve una respuesta con la recomendación.
8.  El consumidor recibe la recomendación y la almacena o la presenta al usuario (este último paso necesita definición).

## Mejoras y Pasos Futuros Clave

*   **Integrar `ai_service` en `docker-compose.yml`**: Añadir el servicio `ai_service` para que se inicie con `docker-compose up`.
*   **Implementar Consumidor de RabbitMQ**: Crear un servicio que consuma mensajes de RabbitMQ, interactúe con la API del `ai_service`, y gestione las recomendaciones.
*   **Definir/Crear Esquema Completo de BD**: Asegurar que el directorio `Postgres/` contenga los scripts para inicializar todas las tablas necesarias (incluyendo una para `recomendaciones`).
*   **Configurar Traefik para Servicios**: Modificar `docker-compose.yml` para que Traefik enrute el tráfico a `front` y `back` usando etiquetas (`labels`).
*   **Desarrollar el `scraper`**: Implementar la lógica del scraper y su Dockerfile, y añadirlo a `docker-compose.yml` si es necesario.
*   **Clarificar Entrega de Recomendaciones**: Definir e implementar cómo el usuario final accede a las recomendaciones.
*   **Gestión de Secretos**: Utilizar archivos `.env` para gestionar credenciales y configuraciones sensibles en `docker-compose.yml`.
*   **Healthchecks**: Añadir healthchecks robustos para `front` y `back` en `docker-compose.yml`.
*   **Documentación Detallada**: Expandir la documentación para cada servicio. 