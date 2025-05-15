import { useState } from 'react'
import './App.css'

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

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prevState => ({
      ...prevState,
      [name]: value
    }))
  }

  const enviarFormulario = async (e) => {
    e.preventDefault()
    
    try {
      const response = await fetch('http://localhost:5000/recomendar-productos', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      })
      
      const data = await response.json()
      if (data.error) {
        setMensaje('Error: ' + data.error)
      } else {
        setUserId(data.id_usuario)
        setMensaje(data.mensaje || 'Formulario enviado correctamente')
      }
    } catch (error) {
      setMensaje('Error al enviar el formulario: ' + error.message)
    }
  }

  return (
    <div className="container">
      <h1>Bienvenido a Smart Search</h1>
      <p>Cuestionario de personalidad para recomendaciones de productos</p>
      
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
        
        <button type="submit" className="submit-button">Enviar Formulario</button>
      </form>
      
      {userId && (
        <div className="success-message">
          <p>¡Gracias por completar el cuestionario!</p>
          <p>ID de Usuario: {userId}</p>
        </div>
      )}
      
      {mensaje && <p className="message">{mensaje}</p>}
    </div>
  )
}

export default App
