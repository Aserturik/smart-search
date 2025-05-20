# Frontend Service - Smart Search

Interfaz de usuario para el sistema de recomendación de productos.

## Estructura

front/
├── src/
│   ├── App.jsx           # Componente principal
│   ├── services/
│   │   └── rabbitmq.js   # Cliente RabbitMQ WebSTOMP
│   ├── main.jsx         # Punto de entrada
│   └── styles/          # Estilos CSS
├── package.json        # Dependencias y scripts
├── vite.config.js     # Configuración de Vite
└── Dockerfile         # Configuración de contenedor

## Características

- Formulario de perfil de usuario
- Conexión WebSocket con RabbitMQ
- Visualización de productos recomendados
- Interfaz responsiva
- Tarjetas de producto con Microlink

## Tecnologías usadas

- React 19
- Vite
- WebSTOMP (RabbitMQ)
- Styled Components
- Microlink React

## Configuración

El servicio se configura a través de variables de entorno:
- `RABBITMQ_HOST`: Host para WebSocket
- `RABBITMQ_PORT`: Puerto WebSocket (15674)
- `NODE_ENV`: Entorno de desarrollo
- `VITE_DEV_SERVER_HOST`: Host del servidor de desarrollo
- `VITE_DEV_SERVER_PORT`: Puerto del servidor (5173)
