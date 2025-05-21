import { useState, useEffect } from 'react'
import './App.css'
import rabbitmqService from './services/rabbitmq'
import Microlink from '@microlink/react'
import styled from 'styled-components'

// Componente para el círculo de carga
const LoadingSpinner = styled.div`
  display: inline-block;
  width: 80px;
  height: 80px;
  margin: 20px auto;
  border: 6px solid rgba(0, 0, 0, 0.1);
  border-left-color: #3498db;
  border-radius: 50%;
  animation: rotate 1s linear infinite;
  
  @keyframes rotate {
    to {
      transform: rotate(360deg);
    }
  }
`;

// Contenedor para el spinner centrado
const LoadingContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin: 30px auto;
  padding: 30px;
  background-color: #34495e;
  border-radius: 8px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  text-align: center;
  max-width: 400px;
  
  p {
    margin-top: 15px;
    color: #ecf0f1;
    font-size: 16px;
    font-weight: 500;
  }
`;

function App() {
  const [formData, setFormData] = useState({
    nombreUsuario: '',
    edad: '',
    motivoCompra: '',
    fuenteInformacion: '',
    temasDeInteres: '',
    comprasNoNecesarias: '',
    importanciaMarca: '',
    probarNuevosProductos: '',
    aspiraciones: '',
    nivelSocial: '',
    tiempoLibre: '',
    identidad: '',
    tendencias: '',
    comentarioSolicitud: ''
  })
  
  const [userId, setUserId] = useState('')
  const [mensaje, setMensaje] = useState('')
  const [isLoading, setIsLoading] = useState(false) // Estado para controlar la carga
  const [connectionStatus, setConnectionStatus] = useState('Conectando...')
  const [debugInfo, setDebugInfo] = useState({})
  const [scrapedUrls, setScrapedUrls] = useState([]);

  // Conectar a RabbitMQ al cargar el componente
  useEffect(() => {
    console.log('Iniciando conexión con RabbitMQ...');
    setMensaje('Conectando a RabbitMQ...');
    
    // Conectar al servicio de RabbitMQ
    rabbitmqService.connect()
      .then(() => {
        console.log('Conectado a RabbitMQ desde React');
        setConnectionStatus('Conectado');
        setMensaje('Listo para enviar formulario');
        
        // Recopilar información de depuración
        setDebugInfo({
          timestamp: new Date().toISOString(),
          hostname: window.location.hostname,
          port: window.location.port,
          protocol: window.location.protocol,
          isInDocker: window.location.hostname !== 'localhost',
          mockMode: !!rabbitmqService.mockMode
        });
        
        // Configurar el listener para respuestas
        const unsubscribe = rabbitmqService.onResponse((data) => {
          console.log('Respuesta recibida:', data);
          setIsLoading(false);
          
          if (data.error) {
            setMensaje('Error: ' + data.error);
          } else {
            setUserId(data.id_usuario);
            setMensaje(data.mensaje || 'Formulario enviado correctamente');
          }
        });
        
        // Limpiar al desmontar
        return () => {
          unsubscribe();
          rabbitmqService.disconnect();
        };
      })
      .catch(error => {
        console.error('Error al conectar con RabbitMQ:', error);
        setConnectionStatus('Error de conexión');
        setMensaje('Error de conexión a RabbitMQ: ' + error.message);
      });
  }, []);

  // Iniciar manejo de respuestas al cargar el componente
  useEffect(() => {
    console.log('Configurando manejo de respuestas de RabbitMQ');
    
    // Configurar el listener para respuestas de RabbitMQ
    const unsubscribe = rabbitmqService.onResponse((data) => {
      console.log('Respuesta recibida del backend:', data);
      setIsLoading(false);
      
      if (data.error) {
        setMensaje('Error: ' + data.error);
      } else {
        setUserId(data.id_usuario || '');
        setMensaje(data.mensaje || 'Formulario procesado correctamente');
      }
      
      // Actualizar información de depuración
      setDebugInfo(prevDebug => ({
        ...prevDebug,
        lastResponse: data,
        responseTime: new Date().toISOString()
      }));
    });
    
    // Establecer información de depuración inicial
    setDebugInfo({
      appStartTime: new Date().toISOString(),
      userAgent: navigator.userAgent,
      platform: navigator.platform,
      windowLocation: window.location.href
    });
    
    // Limpiar al desmontar el componente
    return () => {
      console.log('Limpiando manejadores de respuestas');
      unsubscribe();
    };
  }, []);

  // Efecto para manejar URLs scrapeadas
  useEffect(() => {
    console.log('Configurando listener para URLs scrapeadas');
    const unsubscribeUrls = rabbitmqService.onScrapedUrls((data) => {
      console.log('URLs scrapeadas recibidas en App.jsx:', data);
      if (data && data.urls && Array.isArray(data.urls)) {
        setScrapedUrls(prevUrls => {
          const newUrls = data.urls.filter(url => !prevUrls.includes(url));
          const combinedUrls = [...prevUrls, ...newUrls];
          
          // Si recibimos URLs, podemos desactivar el estado de carga
          // Solo si hay al menos una URL (para evitar falsos positivos)
          if (newUrls.length > 0) {
            console.log('URLs recibidas, desactivando estado de carga');
            setIsLoading(false);
          }
          
          return combinedUrls;
        });
      } else {
        console.warn('Formato de URLs scrapeadas inesperado:', data);
      }
    });

    return () => {
      console.log('Limpiando listener de URLs scrapeadas');
      unsubscribeUrls();
    };
  }, []); // Dependencias vacías para que se ejecute solo al montar/desmontar

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prevState => ({
      ...prevState,
      [name]: value
    }))
  }

  const enviarFormulario = async (e) => {
    e.preventDefault();
    
    // Primero establecemos el estado de carga a true y limpiamos las URLs
    setIsLoading(true);
    setScrapedUrls([]);
    setMensaje('Enviando formulario...');
    
    // Registramos el estado actual para verificar
    console.log('Estado isLoading al iniciar envío:', true);
    
    try {
      console.log('Enviando formulario a través de RabbitMQ:', formData);
      
      // Actualizar información de depuración
      setDebugInfo(prevDebug => ({
        ...prevDebug,
        lastRequest: formData,
        requestTime: new Date().toISOString(),
        isLoadingOnRequest: true // Registrar que isLoading es true durante la solicitud
      }));
      
      // Enviar los datos a través de RabbitMQ
      await rabbitmqService.sendMessage(formData);
      console.log('Formulario enviado, esperando respuesta...');
      console.log('Estado isLoading después de enviar:', isLoading);
      
      // Importante: NO cambiamos isLoading a false aquí
      // setIsLoading se ejecutará cuando llegue la respuesta (en el efecto onResponse)
    } catch (error) {
      console.error('Error al enviar formulario:', error);
      setIsLoading(false); // En caso de error, desactivamos el estado de carga
      setMensaje(`Error al enviar el formulario: ${error.message || 'Error desconocido'}`);
      
      // Actualizar información de depuración
      setDebugInfo(prevDebug => ({
        ...prevDebug,
        lastError: error.message,
        errorTime: new Date().toISOString()
      }));
    }
  }

  return (
    <div className="container">
      <h1>Bienvenido a Smart Search</h1>
      <p>Cuestionario de personalidad para recomendaciones de productos</p>
      
      <div className="connection-status">
        Estado: {connectionStatus}
      </div>
      
      <form onSubmit={enviarFormulario} className="form-container">
        <h2>Información Personal</h2>
        <div className="form-group">
          <label htmlFor="nombreUsuario">Nombre completo:</label>
          <input 
            type="text" 
            id="nombreUsuario" 
            name="nombreUsuario"
            value={formData.nombreUsuario} 
            onChange={handleChange}
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="edad">Edad:</label>
          <input 
            type="number" 
            id="edad" 
            name="edad"
            value={formData.edad} 
            onChange={handleChange}
            required
          />
        </div>
        
        <h2>Hábitos de Compra</h2>
        
        <div className="form-group">
          <label htmlFor="motivoCompra">¿Qué te impulsa principalmente a comprar un producto?</label>
          <select 
            id="motivoCompra" 
            name="motivoCompra"
            value={formData.motivoCompra} 
            onChange={handleChange}
            required
          >
            <option value="">Selecciona una opción</option>
            <option value="Precio">Precio</option>
            <option value="Calidad">Calidad</option>
            <option value="Marca">Marca</option>
            <option value="Novedad o moda">Novedad o moda</option>
            <option value="Necesidad">Necesidad</option>
            <option value="Otros">Otros</option>
          </select>
        </div>
        
        <div className="form-group">
          <label htmlFor="fuenteInformacion">¿Dónde buscas información sobre productos antes de comprar?</label>
          <select 
            id="fuenteInformacion" 
            name="fuenteInformacion"
            value={formData.fuenteInformacion} 
            onChange={handleChange}
            required
          >
            <option value="">Selecciona una opción</option>
            <option value="Redes sociales">Redes sociales</option>
            <option value="Amigos">Amigos</option>
            <option value="Publicidad">Publicidad</option>
            <option value="Otros">Otros</option>
          </select>
        </div>
        
        <div className="form-group">
          <label htmlFor="temasDeInteres">¿Cuál es tu tema de mayor interés?</label>
          <select 
            id="temasDeInteres" 
            name="temasDeInteres"
            value={formData.temasDeInteres} 
            onChange={handleChange}
            required
          >
            <option value="">Selecciona una opción</option>
            <option value="Entretenimiento">Entretenimiento</option>
            <option value="Tecnología">Tecnología</option>
            <option value="Moda">Moda</option>
            <option value="Deportes">Deportes</option>
            <option value="Ecología">Ecología</option>
            <option value="Noticias y actualidad">Noticias y actualidad</option>
            <option value="Otros">Otros</option>
          </select>
        </div>
        
        <div className="form-group">
          <label htmlFor="comprasNoNecesarias">¿Con qué frecuencia realizas compras que no son necesarias?</label>
          <select 
            id="comprasNoNecesarias" 
            name="comprasNoNecesarias"
            value={formData.comprasNoNecesarias} 
            onChange={handleChange}
            required
          >
            <option value="">Selecciona una opción</option>
            <option value="Nunca">Nunca</option>
            <option value="Rara vez">Rara vez</option>
            <option value="A veces">A veces</option>
            <option value="Frecuentemente">Frecuentemente</option>
            <option value="Cuando hay ofertas">Cuando hay ofertas</option>
            <option value="Cuando llama la atención">Cuando llama la atención</option>
          </select>
        </div>
        
        <div className="form-group">
          <label htmlFor="importanciaMarca">¿Qué importancia le das a la marca de un producto?</label>
          <select 
            id="importanciaMarca" 
            name="importanciaMarca"
            value={formData.importanciaMarca} 
            onChange={handleChange}
            required
          >
            <option value="">Selecciona una opción</option>
            <option value="Nada importante">Nada importante</option>
            <option value="Poco importante">Poco importante</option>
            <option value="Algo importante">Algo importante</option>
            <option value="Muy importante">Muy importante</option>
            <option value="Extremadamente importante">Extremadamente importante</option>
          </select>
        </div>
        
        <div className="form-group">
          <label htmlFor="probarNuevosProductos">¿Te gusta probar productos nuevos?</label>
          <select 
            id="probarNuevosProductos" 
            name="probarNuevosProductos"
            value={formData.probarNuevosProductos} 
            onChange={handleChange}
            required
          >
            <option value="">Selecciona una opción</option>
            <option value="Le gusta">Me gusta</option>
            <option value="Solo si es necesario">Solo si es necesario</option>
            <option value="No le da importancia">No le doy importancia</option>
            <option value="Prefiere lo conocido">Prefiero lo conocido</option>
          </select>
        </div>
        
        <h2>Estilo de Vida</h2>
        
        <div className="form-group">
          <label htmlFor="aspiraciones">¿Cuál es tu principal aspiración en este momento?</label>
          <select 
            id="aspiraciones" 
            name="aspiraciones"
            value={formData.aspiraciones} 
            onChange={handleChange}
            required
          >
            <option value="">Selecciona una opción</option>
            <option value="Estabilidad financiera">Estabilidad financiera</option>
            <option value="Crecimiento personal">Crecimiento personal</option>
            <option value="Diversión">Diversión</option>
            <option value="Trabajo">Trabajo</option>
            <option value="Estudio">Estudio</option>
            <option value="Status social">Status social</option>
            <option value="Otros">Otros</option>
          </select>
        </div>
        
        <div className="form-group">
          <label htmlFor="nivelSocial">¿Te consideras una persona social?</label>
          <select 
            id="nivelSocial" 
            name="nivelSocial"
            value={formData.nivelSocial} 
            onChange={handleChange}
            required
          >
            <option value="">Selecciona una opción</option>
            <option value="Altamente social">Altamente social</option>
            <option value="Algo social">Algo social</option>
            <option value="Poco social">Poco social</option>
            <option value="No social">No social</option>
          </select>
        </div>
        
        <div className="form-group">
          <label htmlFor="tiempoLibre">¿Cuánto tiempo libre tienes?</label>
          <select 
            id="tiempoLibre" 
            name="tiempoLibre"
            value={formData.tiempoLibre} 
            onChange={handleChange}
            required
          >
            <option value="">Selecciona una opción</option>
            <option value="Poco tiempo libre">Poco tiempo libre</option>
            <option value="Tiempo libre moderado">Tiempo libre moderado</option>
            <option value="Mucho tiempo libre">Mucho tiempo libre</option>
          </select>
        </div>
        
        <div className="form-group">
          <label htmlFor="identidad">¿Crees que tus compras definen tu personalidad?</label>
          <select 
            id="identidad" 
            name="identidad"
            value={formData.identidad} 
            onChange={handleChange}
            required
          >
            <option value="">Selecciona una opción</option>
            <option value="Totalmente">Totalmente</option>
            <option value="A veces">A veces</option>
            <option value="No lo creo">No lo creo</option>
            <option value="No">No</option>
          </select>
        </div>
        
        <div className="form-group">
          <label htmlFor="tendencias">¿Sueles seguir las tendencias actuales?</label>
          <select 
            id="tendencias" 
            name="tendencias"
            value={formData.tendencias} 
            onChange={handleChange}
            required
          >
            <option value="">Selecciona una opción</option>
            <option value="Siempre">Siempre</option>
            <option value="A veces">A veces</option>
            <option value="No siempre">No siempre</option>
            <option value="No">No</option>
          </select>
        </div>
        
        <div className="form-group">
          <label htmlFor="comentarioSolicitud">¿Qué tipo de productos estás buscando?</label>
          <textarea 
            id="comentarioSolicitud" 
            name="comentarioSolicitud"
            value={formData.comentarioSolicitud} 
            onChange={handleChange}
            placeholder="Ejemplo: Busco productos para el hogar, elementos de deporte, etc."
            rows="3"
            required
          />
        </div>
        
        <button type="submit" className="submit-button" disabled={isLoading}>
          {isLoading ? 'Enviando...' : 'Enviar Formulario'}
        </button>
      </form>
      
      {userId && (
        <div className="success-message">
          <p>¡Gracias por completar el cuestionario!</p>
          <p>ID de Usuario: {userId}</p>
        </div>
      )}
      
      {mensaje && <p className="message">{mensaje}</p>}
      
      {/* Componente de círculo de carga */}
      {isLoading && scrapedUrls.length === 0 && (
        <LoadingContainer>
          <LoadingSpinner />
          <p>Buscando productos recomendados para ti...</p>
        </LoadingContainer>
      )}
      
      {/* Componente de depuración - Solo visible durante desarrollo */}
      <div style={{margin: '20px 0', padding: '10px', border: '1px solid #ccc', borderRadius: '5px', backgroundColor: '#f9f9f9'}}>
        <h3>Estado de depuración:</h3>
        <p>isLoading: {isLoading ? 'true' : 'false'}</p>
        <p>scrapedUrls.length: {scrapedUrls.length}</p>
        <p>¿Debería mostrar spinner? {(isLoading && scrapedUrls.length === 0) ? 'SÍ' : 'NO'}</p>
        <button 
          onClick={() => {
            console.log('Forzando isLoading a true');
            setIsLoading(true);
            console.log('isLoading después de set:', isLoading);
          }}
          style={{marginRight: '10px'}}
        >
          Forzar isLoading=true
        </button>
        <button onClick={() => setScrapedUrls([])}>
          Limpiar URLs
        </button>
      </div>
    
      {/* Sección para mostrar URLs scrapeadas */}
      {scrapedUrls.length > 0 && (
        <div className="scraped-urls-container">
          <h2>Enlaces de Productos Encontrados:</h2>
          <div className="microlink-cards-wrapper">
            {scrapedUrls.map((url, index) => (
              <Microlink key={index} url={url} size="large" media={['image', 'logo']} style={{ marginBottom: '20px' }} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default App
