# Guia_Proyecto_Unificada.md

## 1) Objetivo del proyecto

TurboMessage es un sistema de mensajería tipo e-mail con estas decisiones centrales:

- **Front-end:** Django (vistas y controladores web).
- **Contrato y transporte:** gRPC + Protocol Buffers.
- **Lógica y persistencia:** servidor gRPC en Python + SQLite.

La arquitectura separa claramente GUI (Django) de negocio (gRPC server).

## 2) Front-end (Django)

### Estructura

- `django_ui/django_ui/`: proyecto Django (settings/urls/asgi/wsgi).
- `django_ui/turbomessage/`: app principal.
- `django_ui/turbomessage/views.py`: controladores y flujo web.
- `django_ui/turbomessage/grpc_client.py`: puente con gRPC.
- `django_ui/turbomessage/templates/turbomessage/`: templates (`index`, `auth_form`, `compose`, `email_detail`, `base`).

### Navegación y páginas

- `/` redirección inteligente según sesión.
- `/register/`, `/login/`, `/logout/`.
- `/mailbox/` (pagina principal `index.html`).
- `/compose/`.
- `/email/<id>/` y `/email/<id>/delete/`.

### Funcionalidad

- Registro/login.
- Sesión de usuario (cookies firmadas).
- Listado de correos y separación visual inbox/outbox.
- Envío, lectura y borrado de correos.
- Mensajes flash de estado.

## 3) Proto (contrato gRPC)

Archivo: `proto/turbomessage.proto`.

### Servicio unico

`TurboMessageService` expone:

- `Register(AuthRequest) -> UserReply`
- `Login(AuthRequest) -> UserReply`
- `SendEmail(SendEmailRequest) -> IdReply`
- `ListEmails(ListEmailsRequest) -> EmailsReply`
- `ReadEmail(EmailActionRequest) -> EmailReply`
- `DeleteEmail(EmailActionRequest) -> EmptyReply`

### Mensajes clave

- Requests minimos (`AuthRequest`, `SendEmailRequest`, `ListEmailsRequest`, `EmailActionRequest`).
- Entidad `Email`.
- `Result` + wrappers `*Reply` para respuestas consistentes.

## 4) Back-end (gRPC + SQLite)

### Estructura

- `grpc_server/server.py`: servidor ejecutable y handlers RPC.
- `grpc_server/storage.py`: reglas de negocio + persistencia + concurrencia.
- `grpc_server/generated/`: stubs generados.

### Funcionalidad del servidor

- Alta y autenticación de usuarios.
- Envío de correo entre usuarios existentes.
- Listado de correos visibles por usuario.
- Lectura de correo (marca `is_read` al receptor).
- Borrado por propietario.

### Concurrencia y persistencia

- SQLite en archivo.
- `BEGIN IMMEDIATE` en operaciones críticas.
- lock de escritura para evitar condiciones de carrera en operaciones de capacidad y mutacion.

## 5) Flujo integral (front -> proto -> back)

1. Vista Django recibe acción del usuario.
2. `views.py` llama `grpc_client.py`.
3. Cliente serializa request protobuf y hace RPC.
4. `server.py` delega a `storage.py`.
5. `storage.py` aplica reglas, persiste y devuelve resultado.
6. `server.py` responde `*Reply`.
7. Django renderiza template con feedback.

### 5.1) Registro de usuario y persistencia (paso a paso)

Este flujo explica cómo los tres componentes interactúan para cumplir el lineamiento de registro persistente:

1. El usuario completa el formulario en `/register/`; `views.py` valida que haya username y password.
2. `grpc_client.py` construye `AuthRequest` y llama a `Register` vía gRPC.
3. `server.py` recibe el RPC y delega la operación a `storage.register`.
4. `storage.register` abre conexión SQLite, inicia `BEGIN IMMEDIATE`, genera `user_id` con formato `username@turbo.com` e inserta en `users`.
5. Si el username ya existe, SQLite dispara `IntegrityError`, se revierte la transacción y se regresa un error claro.
6. El `UserReply` vuelve a Django; si `ok=true`, se guardan `tm_user_id` y `tm_username` en sesión y el usuario entra a su bandeja.

### 5.2) Envío de correo y validaciones

Este flujo resume cómo se cumplen los lineamientos de envío y capacidad:

1. El usuario entra a `/compose/` y Django valida que destinatario, tema y cuerpo existan.
2. `grpc_client.py` envía `SendEmailRequest` con `sender_id`, `recipient_id`, `subject` y `body`.
3. `storage.send_email` abre transacción, valida que emisor y receptor existan y revisa límites de inbox/outbox.
4. Si todo es válido, inserta el correo en `emails` y devuelve un `IdReply` con el id autogenerado.
5. Django muestra el resultado con un mensaje flash y regresa a la bandeja.

### 5.3) Listado, lectura y borrado de correos

Este flujo explica cómo se consultan y administran los mensajes:

1. `/mailbox/` llama `ListEmails` y el backend retorna todos los correos visibles del usuario.
2. Django separa inbox/outbox según `recipient_id` y `sender_id` para la presentación.
3. Al abrir un correo, `ReadEmail` valida ownership y marca `is_read` si el receptor lo lee por primera vez.
4. Al borrar, `DeleteEmail` marca eliminaciones por emisor o receptor y solo borra físicamente si ambos lo hicieron.

## 6) Cumplimiento de lineamientos y rúbrica

### Requerimientos funcionales cubiertos

- Registro persistente de usuarios (username/password). Se resuelve con `Register`, que valida datos en Django y persiste en SQLite vía `storage.register`.
- Login de usuarios. `Login` busca credenciales en `storage.py` y regresa `user_id` para iniciar sesión en Django.
- Identificador alfanumérico único por usuario. Se genera con el formato `[username]@turbo.com` y la tabla `users` aplica unicidad.
- Envío de correo solo a usuario existente. `SendEmail` verifica emisor/receptor en SQLite antes de insertar.
- Correo con id, tema, emisor, destinatario y cuerpo. Se almacena en la tabla `emails` con `id` autoincremental.
- Sin adjuntos. El contrato protobuf no define campos de archivo, lo que bloquea esa funcionalidad.
- Lectura y borrado de correos. `ReadEmail` y `DeleteEmail` validan ownership en el backend antes de responder.
- Estado `no leído/leído` persistente y cambio al leer. `is_read` se actualiza solo cuando el receptor abre el correo.
- Persistencia de mensajes y entrega asíncrona. `ListEmails` consulta SQLite y entrega lo que haya aunque el receptor estuviera desconectado.

### Reglas de capacidad

- Inbox máximo 5 correos. Solución: conteo previo de inbox en `send_email` y rechazo transaccional.
- Outbox máximo 5 correos. Solución: conteo previo de outbox en `send_email` y rechazo transaccional.
- Error al emisor si inbox de receptor esta llena. Solucion: `IdReply.result` retorna `ok=false` y mensaje descriptivo.

### Arquitectura/restricciones

- Comunicación principal vía gRPC + protobuf. Solución: flujo app web -> `grpc_client.py` -> `TurboMessageService`.
- Django usado como front-end y consumidor gRPC. Solución: controladores en `views.py` sin lógica de negocio profunda.
- Sin uso del ORM/modelos Django para lógica/persistencia central. Solución: persistencia exclusiva en `grpc_server/storage.py` con `sqlite3`.

### Concurrencia

- Atención a usuarios concurrentes con control transaccional y lock en servidor. Solución: `BEGIN IMMEDIATE` + `RLock`.
- Mitigación de condiciones de carrera en operaciones críticas. Solución: serialización de escrituras y commits atómicos.

### Rubrica y entrega (lineamientos)

- Equipo de 1 a 2 personas. Solucion: organizacion de trabajo modular por capas (front/proto/back).
- Peso total del proyecto: 2 puntos (1.8 funcional + 0.2 documentación). Solución: trazabilidad técnica y documentos de soporte.
- Fecha límite: martes 12 de mayo de 2026 a la hora de clase. Solución: guía de despliegue y ejecución reproducible.
- Penalización: 20% por día natural; después de la hora cuenta como 1 día. Solución: validación temprana y control de versiones por hitos.

## 7) Arranque rápido

1. Activar entorno e instalar dependencias:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "Django>=5.0,<6.0" "grpcio>=1.65.0" "grpcio-tools>=1.65.0" "protobuf>=5.0.0"
```

2. Generar stubs (ya se encontrarán en `grpc_server/generated/`):

```bash
python -m grpc_tools.protoc \
  -I proto \
  --python_out=grpc_server/generated \
  --grpc_python_out=grpc_server/generated \
  proto/turbomessage.proto
```

3. Levantar backend gRPC (puerto `36933`):

```bash
python -m grpc_server.server
```

4. Levantar frontend Django:

```bash
cd django_ui
python manage.py runserver 0.0.0.0:8000
```

5. Abrir `http://localhost:8000/`.

## 8) Purgar base de datos

Si necesitas reiniciar por completo los usuarios y correos, borra el archivo SQLite y deja que el servidor lo regenere:

1. Detén el servidor gRPC.
2. Elimina el archivo de base de datos:

```bash
rm grpc_server/data/turbomessage.db
```

3. Arranca de nuevo el servidor gRPC (`python -m grpc_server.server`).
