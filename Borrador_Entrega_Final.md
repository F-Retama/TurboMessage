# Borrador_Entrega_Final

## Introduccion

TurboMessage es una aplicacion de mensajeria tipo e-mail desarrollada para cumplir un conjunto de lineamientos academicos enfocados en arquitectura distribuida y separacion de responsabilidades. El sistema implementa una interfaz web en Django para la interaccion con el usuario y un servidor gRPC que concentra la logica de negocio, persistencia y control de concurrencia. Esta separacion permite mantener una GUI simple y una capa de servicios robusta, cumpliendo la restriccion de no usar el ORM de Django para la logica central.

## Arquitectura del sistema

La arquitectura se divide en tres capas:

1. **Capa de presentacion (Django)**
- Proyecto Django: `django_ui/django_ui`.
- App principal: `django_ui/turbomessage`.
- Funciones: registro, login, bandeja principal, redaccion, lectura y borrado.
- La app web no aplica reglas de negocio profundas; delega operaciones al servidor gRPC.

2. **Capa de contrato (Protocol Buffers)**
- Archivo: `proto/turbomessage.proto`.
- Servicio unico: `TurboMessageService`.
- Operaciones RPC: `Register`, `Login`, `SendEmail`, `ListEmails`, `ReadEmail`, `DeleteEmail`.
- Respuestas estandarizadas con `Result` + wrappers `*Reply`.

3. **Capa de negocio y datos (gRPC + SQLite)**
- Servidor: `grpc_server/server.py` (arranque ejecutable).
- Logica/persistencia: `grpc_server/storage.py`.
- Base de datos: SQLite en archivo.
- Mecanismo de concurrencia: transacciones `BEGIN IMMEDIATE` y lock de escritura para proteger operaciones criticas.

### Flujo operativo

1. Usuario interactua con una vista Django.
2. `views.py` invoca `grpc_client.py`.
3. Cliente gRPC serializa request protobuf y llama al backend en el puerto `36933`.
4. `server.py` procesa RPC y delega a `storage.py`.
5. `storage.py` aplica reglas, persiste en SQLite y devuelve resultado.
6. `server.py` responde `*Reply` y Django renderiza resultado al usuario.

### Registro y persistencia de usuarios

El registro es el caso mas representativo del flujo distribuido porque cruza las tres capas y deja evidencia persistente:

1. El usuario llena el formulario `/register/` y Django valida que los campos no esten vacios.
2. El cliente gRPC crea un `AuthRequest` y envia `Register` al servidor.
3. El servidor gRPC delega a `storage.register`, que abre transaccion, genera `user_id` con formato `username@turbo.com` e inserta en SQLite.
4. Si el username ya existe, la base de datos rechaza la operacion y se responde con error controlado.
5. El frontend recibe `UserReply`; si es exitoso, guarda el `user_id` en sesion y redirige a la bandeja.

### Envio de correos y validaciones

El envio aplica reglas funcionales y de capacidad desde el backend:

1. El usuario escribe un correo en `/compose/` y Django valida los campos obligatorios.
2. El cliente gRPC envia `SendEmailRequest` con emisor, receptor, tema y cuerpo.
3. `storage.send_email` valida existencia de usuarios y limites de inbox/outbox dentro de una transaccion.
4. Si es valido, se inserta en `emails` y se regresa un `IdReply` con el id autogenerado.
5. Django muestra el resultado al usuario y vuelve a la bandeja.

### Listado, lectura y borrado

El manejo de bandejas y acciones sobre correos sigue este flujo:

1. `/mailbox/` llama `ListEmails` para traer correos visibles del usuario.
2. Django separa inbox/outbox segun `recipient_id` y `sender_id`.
3. `ReadEmail` valida acceso y marca `is_read` si el receptor abre el correo por primera vez.
4. `DeleteEmail` marca eliminaciones por usuario y elimina fisicamente cuando ambos lo borran.

## Cumplimiento de requerimientos principales

- Registro persistente de usuarios con username/password. Se logra con `Register`, que escribe en SQLite bajo transaccion.
- Inicio de sesion por credenciales. `Login` valida contra la tabla `users` y devuelve `user_id` para la sesion.
- ID alfanumerico unico por usuario. Se forma como `[username]@turbo.com` y se protege con restriccion unica.
- Envio de correo solo a usuarios existentes. `SendEmail` valida existencia de emisor y receptor antes de insertar.
- Correo con identificador autogenerado, tema, emisor, receptor y cuerpo. La tabla `emails` define `id` autoincremental y campos obligatorios.
- Sin soporte de adjuntos. El contrato protobuf no expone campos de archivos.
- Lectura y borrado de correos por usuario. `ReadEmail` y `DeleteEmail` validan ownership y responden segun el usuario.
- Estado de correo `no leido/leido` persistente. `is_read` cambia al primer acceso del receptor.
- Persistencia de mensajes y entrega asincrona. Los correos quedan en SQLite y se consultan con `ListEmails`.
- Limites de capacidad (inbox/outbox maximo 5). `storage.py` cuenta antes de insertar y rechaza si excede.
- Error al enviar a inbox llena. `IdReply` retorna `ok=false` con mensaje descriptivo.
- Operacion concurrente controlada. `BEGIN IMMEDIATE` y `RLock` serializan escrituras criticas.
- Django solo como front-end gRPC. La logica de negocio vive en el backend y el ORM no se usa.

## Conclusiones

El proyecto consolida una implementacion coherente con enfoque de sistemas distribuidos: contrato claro, servicios remotos y persistencia controlada por backend. La solucion mantiene simplicidad operativa en frontend y concentra la complejidad en la capa gRPC, lo cual facilita trazabilidad, pruebas y evolucion futura. Como siguientes pasos naturales, se recomienda ampliar pruebas automatizadas de integracion y concurrencia, y preparar el documento final con el formato solicitado (Arial 11, interlineado simple, margenes de 2.5 cm).
