# Checklist de Lineamientos - TurboMessage

Fuente: `Lineamientos_Omega.pdf`

## 1) Alcance general

- [ ] TurboMessage replica la funcionalidad de un servidor de e-mails con las restricciones indicadas.
- [ ] Casi todas las comunicaciones del sistema se implementan usando **gRPC** y **Protocol Buffers**.
- [ ] **Django** se usa solo para exponer/consumir servicios gRPC (front-end).
- [ ] La GUI de usuario se implementa como pagina web en Django.
- [ ] Todas las vistas de usuario se implementan con **templates de Django**.

## 2) Restricciones de arquitectura

- [ ] No se usan modelos de Django para la logica/persistencia del sistema.
- [ ] La persistencia se implementa con archivos o base de datos externos al ORM de Django.

## 3) Usuarios y autenticacion

- [ ] Un usuario puede registrarse persistentemente con nombre de usuario y contrasena.
- [ ] Un usuario puede iniciar sesion con sus credenciales.
- [ ] Cada usuario tiene un identificador alfanumerico unico para ser contactado.

## 4) Correo: composicion y estructura

- [ ] Un usuario puede escribir correo a otro usuario existente.
- [ ] Todo correo tiene: identificador, tema, un emisor, un destinatario y cuerpo de mensaje.
- [ ] El identificador del correo lo autogenera el servidor.
- [ ] No se permiten archivos adjuntos.

## 5) Bandejas (entrada/salida)

- [ ] La bandeja de entrada de un usuario no puede tener mas de 5 correos.
- [ ] Si el receptor tiene entrada llena, el emisor recibe mensaje de error.
- [ ] La bandeja de salida de un usuario no puede tener mas de 5 correos.
- [ ] Un usuario puede leer cualquier correo de su bandeja de entrada y salida.
- [ ] Un usuario puede borrar cualquier correo de su bandeja de entrada y salida.

## 6) Estados del correo

- [ ] El correo maneja estados `no leido` y `leido`.
- [ ] Los estados son persistentes (archivo o base de datos).
- [ ] Al leer por primera vez un correo, su estado cambia automaticamente a `leido`.
- [ ] No existe otra forma de cambiar el estado de un correo.

## 7) Persistencia y entrega asincrona

- [ ] Los correos enviados son persistentes (salvo que el receptor los borre).
- [ ] El receptor no necesita estar en linea para que se entregue eventualmente el mensaje.
- [ ] El emisor puede enviar mensajes aunque el receptor no este conectado.
- [ ] Al conectarse, un usuario puede recibir mensajes enviados en su ausencia (si hay espacio en entrada).
- [ ] Clientes pueden abrir/cerrar arbitrariamente sin perder informacion persistente.

## 8) Reglas de envio/recepcion

- [ ] Para enviar un e-mail, el usuario receptor debe existir.
- [ ] Un usuario puede enviar `k` mensajes a cualquier usuario existente.
- [ ] Un usuario puede recibir `q` mensajes de cualquier usuario existente si tiene espacio.

## 9) Concurrencia y robustez

- [ ] El sistema atiende a `n` usuarios concurrentemente.
- [ ] No existen condiciones de carrera.

## 10) Usabilidad de interfaz

- [ ] La estetica de la GUI no es criterio de evaluacion.
- [ ] La GUI es usable y sin errores que afecten la interaccion.

## 11) Entregables

- [ ] Se entrega todo el codigo fuente.
- [ ] Se entrega documento de descripcion del proyecto (maximo 2 paginas).
- [ ] Formato del documento: Arial 11, interlineado simple, margenes de 2.5 cm.
- [ ] El documento incluye:
- [ ] Introduccion breve.
- [ ] Descripcion de la arquitectura del sistema.
- [ ] Conclusiones breves.

## 12) Evaluacion y fecha limite

- [ ] Equipo de 1 a 2 personas.
- [ ] Valor total del proyecto: 2 puntos de calificacion final.
- [ ] 1.8 puntos: ejecucion con requerimientos completos.
- [ ] 0.2 puntos: calidad y presentacion de documentacion.
- [ ] Fecha limite de entrega: **martes 12 de mayo de 2026**, a la hora de clase.
- [ ] Penalizacion: 20% menos por cada dia natural de retraso.
- [ ] Entregar despues de la hora implica automaticamente un dia de retraso.
