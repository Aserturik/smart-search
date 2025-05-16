import { Client } from '@stomp/stompjs';

// Configuración para comunicación directa con RabbitMQ mediante WebSTOMP
const isInDocker = window.location.hostname !== 'localhost';
// Usamos el HOST del navegador ya que necesitamos conectarnos desde el cliente (no desde el contenedor)
const RABBITMQ_HOST = window.location.hostname;
const RABBITMQ_PORT = 15674;  // Puerto de WebSTOMP
const RABBITMQ_WS_URL = `ws://${RABBITMQ_HOST}:${RABBITMQ_PORT}/ws`;

// Configuración de colas
const QUEUE_SOLICITUDES = 'solicitudes';
const QUEUE_RESPUESTAS = 'respuestas';

// Para depuración
console.log(`Entorno Docker: ${isInDocker}`);
console.log(`Hostname: ${window.location.hostname}`);
console.log(`WebSocket URL: ${RABBITMQ_WS_URL}`);

// Para el modo de simulación cuando RabbitMQ no está disponible
let mockMode = false;
let mockId = 1;

class RabbitMQService {
  constructor() {
    this.client = null;
    this.connected = false;
    this.messageCallbacks = new Map();
    this.connectionAttempts = 0;
    this.maxConnectionAttempts = 3;
    this.mockMode = false;
  }

  // Conectar con RabbitMQ mediante WebSTOMP
  connect() {
    return new Promise((resolve, reject) => {
      if (this.connected) {
        console.log('Ya conectado a RabbitMQ');
        resolve();
        return;
      }

      // Si ya estamos en modo simulación, no intentamos conectar
      if (mockMode) {
        console.log('Funcionando en modo simulación (sin conexión RabbitMQ)');
        resolve();
        return;
      }

      console.log(`Intentando conectar con RabbitMQ via WebSTOMP: ${RABBITMQ_WS_URL}`);
      
      if (this.connectionAttempts >= this.maxConnectionAttempts) {
        console.warn(`Se alcanzó el máximo de intentos (${this.maxConnectionAttempts}), activando modo simulación`);
        this._activateMockMode();
        resolve();
        return;
      }
      
      this.connectionAttempts++;

      try {
        this.client = new Client({
          brokerURL: RABBITMQ_WS_URL,
          connectHeaders: {
            login: 'guest',
            passcode: 'guest',
          },
          debug: function (str) {
            console.log('STOMP: ' + str);
          },
          reconnectDelay: 5000,
          heartbeatIncoming: 4000,
          heartbeatOutgoing: 4000,
        });

        this.client.onConnect = () => {
          console.log('Conectado a RabbitMQ via WebSTOMP');
          this.connected = true;
          this.connectionAttempts = 0;
          
          // Suscribirse a la cola de respuestas
          this._subscribeToResponses();
          
          resolve();
        };

        this.client.onStompError = (frame) => {
          console.error('Error de STOMP:', frame.headers['message']);
          console.error('Detalles adicionales:', frame.body);
          
          // Intentar reconectar si no superamos el límite
          if (this.connectionAttempts < this.maxConnectionAttempts) {
            console.log(`Reintentando conexión... ${this.connectionAttempts}/${this.maxConnectionAttempts}`);
            setTimeout(() => {
              this.connect().then(resolve).catch(reject);
            }, 2000);
          } else {
            // Activar modo simulación como fallback
            this._activateMockMode();
            resolve();
          }
        };

        this.client.onWebSocketError = (event) => {
          console.error('Error de WebSocket:', event);
          console.error('Detalles del error de WebSocket:');
          console.error('- URL:', RABBITMQ_WS_URL);
          console.error('- Host:', RABBITMQ_HOST);
          console.error('- Puerto:', RABBITMQ_PORT);
          
          // Intentar reconectar si no superamos el límite
          if (this.connectionAttempts < this.maxConnectionAttempts) {
            console.log(`Reintentando conexión... ${this.connectionAttempts}/${this.maxConnectionAttempts}`);
            setTimeout(() => {
              this.connect().then(resolve).catch(reject);
            }, 2000);
          } else {
            // Activar modo simulación como fallback
            this._activateMockMode();
            resolve();
          }
        };

        this.client.activate();
        
        // Establecer un timeout por si la conexión falla sin emitir errores
        setTimeout(() => {
          if (!this.connected && !mockMode) {
            console.warn('Timeout de conexión a RabbitMQ');
            
            // Intentar reconectar si no superamos el límite
            if (this.connectionAttempts < this.maxConnectionAttempts) {
              console.log(`Reintentando conexión... ${this.connectionAttempts}/${this.maxConnectionAttempts}`);
              setTimeout(() => {
                // Limpiar el cliente actual
                if (this.client) {
                  try {
                    this.client.deactivate();
                  } catch (e) {
                    console.error('Error al desactivar cliente:', e);
                  }
                  this.client = null;
                }
                
                this.connect().then(resolve).catch(reject);
              }, 2000);
            } else {
              console.warn('Activando modo simulación después de múltiples intentos');
              this._activateMockMode();
              resolve();
            }
          }
        }, 5000);
      } catch (error) {
        console.error('Error al crear cliente STOMP:', error);
        
        // Intentar reconectar si no superamos el límite
        if (this.connectionAttempts < this.maxConnectionAttempts) {
          console.log(`Reintentando conexión... ${this.connectionAttempts}/${this.maxConnectionAttempts}`);
          setTimeout(() => {
            this.connect().then(resolve).catch(reject);
          }, 2000);
        } else {
          // Activar modo simulación como fallback
          this._activateMockMode();
          resolve();
        }
      }
    });
  }

  _subscribeToResponses() {
    if (!this.connected || !this.client) {
      console.error('No conectado a RabbitMQ, no se puede suscribir a respuestas');
      return;
    }

    try {
      // En WebSTOMP, la cola debe tener el prefijo /queue/
      const queueDestination = `/queue/${QUEUE_RESPUESTAS}`;
      
      console.log(`Suscribiéndose a cola de respuestas: ${queueDestination}`);
      
      this.client.subscribe(queueDestination, (message) => {
        try {
          const data = JSON.parse(message.body);
          console.log('Respuesta recibida de RabbitMQ:', data);
          this._processResponse(data);
        } catch (e) {
          console.error('Error al procesar respuesta:', e);
        }
      });
      
      console.log('Suscripción a cola de respuestas completada');
    } catch (error) {
      console.error('Error al suscribirse a cola de respuestas:', error);
    }
  }

  // Enviar mensaje a través de RabbitMQ directamente por WebSTOMP
  async sendMessage(data) {
    if (mockMode) {
      return this._handleMockResponse(data);
    }

    if (!this.connected) {
      try {
        await this.connect();
      } catch (error) {
        console.error('Error al conectar con RabbitMQ:', error);
        this._activateMockMode();
        return this._handleMockResponse(data);
      }
    }

    if (!this.connected || !this.client) {
      console.warn('No conectado a RabbitMQ después de intentar conectar, activando modo simulación');
      this._activateMockMode();
      return this._handleMockResponse(data);
    }

    try {
      console.log(`Enviando formulario a RabbitMQ: ${JSON.stringify(data)}`);
      
      // En WebSTOMP, la cola debe tener el prefijo /queue/
      const queueDestination = `/queue/${QUEUE_SOLICITUDES}`;
      
      this.client.publish({
        destination: queueDestination,
        body: JSON.stringify(data),
        headers: { 'content-type': 'application/json' }
      });
      
      console.log(`Formulario enviado a la cola ${queueDestination}`);
      
      return {
        success: true,
        mensaje: 'Formulario enviado, esperando respuesta...'
      };
    } catch (error) {
      console.error('Error al enviar mensaje a RabbitMQ:', error);
      
      // Si hay un error, activamos el modo simulación
      if (!mockMode) {
        console.log('Activando modo simulación debido a error de comunicación');
        this._activateMockMode();
        return this._handleMockResponse(data);
      }
      
      throw error;
    }
  }

  _handleMockResponse(data) {
    return new Promise((resolve) => {
      setTimeout(() => {
        console.log('Modo simulación: Generando respuesta simulada');
        
        const mockResponse = {
          id_usuario: mockId++,
          nombre: data.nombreUsuario || 'Usuario Simulado',
          mensaje: `Hola ${data.nombreUsuario || 'Usuario'}, tu información ha sido registrada correctamente (SIMULADO).`
        };
        
        this._processResponse(mockResponse);
        resolve(mockResponse);
      }, 1000);
    });
  }

  _activateMockMode() {
    console.log('Activando modo simulación');
    mockMode = true;
    this.mockMode = true;
    
    // Desactivar cliente STOMP si existe
    if (this.client) {
      try {
        this.client.deactivate();
      } catch (e) {
        console.error('Error al desactivar cliente STOMP:', e);
      }
      this.client = null;
    }
    
    this.connected = false;
  }

  disconnect() {
    if (this.client && this.connected) {
      try {
        this.client.deactivate();
        console.log('Desconectado de RabbitMQ');
      } catch (e) {
        console.error('Error al desconectar de RabbitMQ:', e);
      }
      this.client = null;
      this.connected = false;
    }
  }

  _processResponse(data) {
    console.log('Procesando respuesta:', data);
    const callbacks = this.messageCallbacks.get('respuesta') || [];
    
    callbacks.forEach(callback => {
      try {
        callback(data);
      } catch (e) {
        console.error('Error en callback de respuesta:', e);
      }
    });
  }

  onResponse(callback) {
    if (!this.messageCallbacks.has('respuesta')) {
      this.messageCallbacks.set('respuesta', []);
    }
    
    this.messageCallbacks.get('respuesta').push(callback);
    
    return () => {
      const callbacks = this.messageCallbacks.get('respuesta') || [];
      const index = callbacks.indexOf(callback);
      if (index !== -1) {
        callbacks.splice(index, 1);
      }
    };
  }
}

// Instancia singleton
const rabbitmqService = new RabbitMQService();

export default rabbitmqService; 