CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nombreUsuario VARCHAR(100) NOT NULL,
    edad INT NOT NULL,
    correo VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE tests (
    id SERIAL PRIMARY KEY,
    motivoCompra VARCHAR(100) NOT NULL, -- Motivos que impulsan a comprar algo (Precio, Calidad, Marca, novedad o moda, necesidad, otros)
    fuenteInformacion VARCHAR(100) NOT NULL, -- Fuentes de información (Redes sociales, amigos, publicidad, otros)
    temasDeInteres VARCHAR(100) NOT NULL, -- Temas de interés (Entretenimiento, tecnología, moda, deportes, ecologia, noticias y actualidad, otros)
    comprasNoNecesarias VARCHAR(100) NOT NULL, -- Frecuencia de compras no necesarias (Nunca, Rara vez, A veces, Frecuentemente, cuando hay ofertas, cuando llama la atención)
    importanciaMarca VARCHAR(100) NOT NULL, -- Importancia de la marca de un producto (Nada importante, Poco importante, Algo importante, Muy importante, Extremadamente importante)
    probarNuevosProductos VARCHAR(100) NOT NULL, -- Le gusta probar productos nuevos? (Le gusta, solo si es necesario, no le da importancia, prefiere lo conocido)
    aspiraciones VARCHAR(100) NOT NULL, -- Aspiraciones (Estabilidad financiera, crecimiento personal, diversion, trabajo, estudio, status social, otros)
    nivelSocial VARCHAR(100) NOT NULL, -- Se considera una persona sociale (altamente social, algo social, poco social, no social)
    tiempoLibre VARCHAR(100) NOT NULL, -- Tiempo libre (poco tiempo libre, tiempo libre moderado, mucho tiempo libre)
    identidad VARCHAR(100) NOT NULL, -- tus compras definen tu personalidad? (totalmente, a veces, no lo creo, no)
    tendencias VARCHAR(100) NOT NULL -- Sueles seguir las tendencias actuales? (siempre, a veces, no siempre, no)
);

CREATE TABLE solicitudes (
    id SERIAL PRIMARY KEY,
    userId INT NOT NULL,
    testsId INT NOT NULL,
    comentarioSolicitud VARCHAR(255), -- Comentario de que busca, ejemplo: busco productos para el hogar, elementos de deporte, etc.
    CONSTRAINT fk_user FOREIGN KEY (userId) REFERENCES usuarios (id) ON DELETE CASCADE,
    CONSTRAINT fk_test FOREIGN KEY (testsId) REFERENCES tests (id) ON DELETE CASCADE
);

-- Insertar datos en la tabla usuarios
INSERT INTO usuarios (nombreUsuario, edad, correo) VALUES
('Juan Pérez', 30, 'juan.perez@example.com'),
('María López', 25, 'maria.lopez@example.com'),
('Carlos Gómez', 35, 'carlos.gomez@example.com');

-- Insertar datos en la tabla tests
INSERT INTO tests (motivoCompra, fuenteInformacion, temasDeInteres, comprasNoNecesarias, importanciaMarca, probarNuevosProductos, aspiraciones, nivelSocial, tiempoLibre, identidad, tendencias) VALUES
('Precio', 'Redes sociales', 'Tecnología', 'A veces', 'Muy importante', 'Le gusta', 'Crecimiento personal', 'Algo social', 'Tiempo libre moderado', 'A veces', 'Siempre'),
('Calidad', 'Amigos', 'Deportes', 'Frecuentemente', 'Extremadamente importante', 'Solo si es necesario', 'Diversión', 'Altamente social', 'Mucho tiempo libre', 'Totalmente', 'A veces'),
('Marca', 'Publicidad', 'Moda', 'Rara vez', 'Algo importante', 'Prefiere lo conocido', 'Estabilidad financiera', 'Poco social', 'Poco tiempo libre', 'No lo creo', 'No');

-- Insertar datos en la tabla solicitudes
INSERT INTO solicitudes (userId, testsId, comentarioSolicitud) VALUES
(1, 1, 'Busco productos tecnológicos de calidad'),
(2, 2, 'Interesada en ropa deportiva y accesorios'),
(3, 3, 'Busco ofertas en productos para el hogar');