import { useState } from 'react'
import './App.css'

function App() {
  const [nombre, setNombre] = useState('')
  const [respuesta, setRespuesta] = useState('')
  const [userId, setUserId] = useState('')
  const [mensaje, setMensaje] = useState('')

  const enviarFormulario = async (e) => {
    e.preventDefault()
    
    try {
      const response = await fetch('http://localhost:5000/recomendar-productos', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          nombre: nombre,
          respuesta: respuesta
        })
      })
      
      const data = await response.json()
      setUserId(data.id_usuario)
      setMensaje('Formulario enviado correctamente')
    } catch (error) {
      setMensaje('Error al enviar el formulario: ' + error.message)
    }
  }

  return (
    <>
      <h1>Bienvenido a Smart Search</h1>
      <p>Cuestionario de personalidad</p>
      
      <form onSubmit={enviarFormulario}>
        <div>
          <label htmlFor="nombre">Nombre:</label>
          <input 
            type="text" 
            id="nombre" 
            value={nombre} 
            onChange={(e) => setNombre(e.target.value)}
            required
          />
        </div>
        
        <div>
          <label htmlFor="respuesta">Respuesta:</label>
          <input 
            type="text" 
            id="respuesta" 
            value={respuesta} 
            onChange={(e) => setRespuesta(e.target.value)}
            required
          />
        </div>
        
        <button type="submit">Enviar</button>
      </form>
      
      {userId && (
        <div>
          <p>ID de Usuario recibido: {userId}</p>
        </div>
      )}
      
      {mensaje && <p>{mensaje}</p>}
    </>
  )
}

export default App
