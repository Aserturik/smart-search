import { useState, useEffect } from 'react'
import './App.css'
import rabbitmqService from './services/rabbitmq'
import Microlink from '@microlink/react'
import styled from 'styled-components'

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
  const [isLoading, setIsLoading] = useState(false)
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
        // Aquí podrías verificar data.user_id si fuera necesario para filtrar
        // Por ahora, simplemente añadimos las URLs recibidas
        // Para evitar duplicados si el componente se re-renderiza o el mensaje llega varias veces:
        setScrapedUrls(prevUrls => {
          const newUrls = data.urls.filter(url => !prevUrls.includes(url));
          return [...prevUrls, ...newUrls];
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
    e.preventDefault()
    setIsLoading(true);
    setMensaje('Enviando formulario...');
    
    try {
      console.log('Enviando formulario a través de RabbitMQ:', formData);
      
      // Actualizar información de depuración
      setDebugInfo(prevDebug => ({
        ...prevDebug,
        lastRequest: formData,
        requestTime: new Date().toISOString()
      }));
      
      // Enviar los datos a través de RabbitMQ
      await rabbitmqService.sendMessage(formData);
      console.log('Formulario enviado, esperando respuesta...');
      
    } catch (error) {
      console.error('Error al enviar formulario:', error);
      setIsLoading(false);
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
      
      {/* Área de información de depuración */}
      <div className="debug-info" style={{ marginTop: '2rem', padding: '1rem', background: '#f5f5f5', borderRadius: '4px' }}>
        <details>
          <summary>Información de depuración</summary>
          <pre style={{ whiteSpace: 'pre-wrap', overflowX: 'auto' }}>
            {JSON.stringify(debugInfo, null, 2)}
          </pre>
        </details>
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
