# Guia_Proyecto_Unificada.md

## 1) Objetivo del proyecto

TurboMessage es un sistema de mensajeria tipo e-mail con estas decisiones centrales:

- **Front-end:** Django (vistas y controladores web).
- **Contrato y transporte:** gRPC + Protocol Buffers.
- **Logica y persistencia:** servidor gRPC en Python + SQLite.

La arquitectura separa claramente GUI (Django) de negocio (gRPC server).

## 2) Front-end (Django)

### Estructura

- `django_ui/django_ui/`: proyecto Django (settings/urls/asgi/wsgi).
- `django_ui/turbomessage/`: app principal.
- `django_ui/turbomessage/views.py`: controladores y flujo web.
- `django_ui/turbomessage/grpc_client.py`: puente con gRPC.
- `django_ui/turbomessage/templates/turbomessage/`: templates (`index`, `auth_form`, `compose`, `email_detail`, `base`).

### Navegacion y paginas

- `/` redireccion inteligente segun sesion.
- `/register/`, `/login/`, `/logout/`.
- `/mailbox/` (pagina principal `index.html`).
- `/compose/`.
- `/email/<id>/` y `/email/<id>/delete/`.

### Funcionalidad

- Registro/login.
- Sesion de usuario (cookies firmadas).
- Listado de correos y separacion visual inbox/outbox.
- Envio, lectura y borrado de correos.
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

- Alta y autenticacion de usuarios.
- Envio de correo entre usuarios existentes.
- Listado de correos visibles por usuario.
- Lectura de correo (marca `is_read` al receptor).
- Borrado por propietario.

### Concurrencia y persistencia

- SQLite en archivo.
- `BEGIN IMMEDIATE` en operaciones criticas.
- lock de escritura para evitar condiciones de carrera en operaciones de capacidad y mutacion.

## 5) Flujo integral (front -> proto -> back)

1. Vista Django recibe accion del usuario.
2. `views.py` llama `grpc_client.py`.
3. Cliente serializa request protobuf y hace RPC.
4. `server.py` delega a `storage.py`.
5. `storage.py` aplica reglas, persiste y devuelve resultado.
6. `server.py` responde `*Reply`.
7. Django renderiza template con feedback.

## 6) Cumplimiento de lineamientos y rubrica

### Requerimientos funcionales cubiertos

- Registro persistente de usuarios (username/password). Solucion: RPC `Register` + insercion en SQLite.
- Login de usuarios. Solucion: RPC `Login` + validacion de credenciales en `storage.py`.
- Identificador alfanumerico unico por usuario. Solucion: generacion de `user_id` con formato `[username]@turbo.com` y llave unica.
- Envio de correo solo a usuario existente. Solucion: `SendEmail` valida existencia de emisor y receptor antes de insertar.
- Correo con id, tema, emisor, destinatario y cuerpo. Solucion: tabla `emails` + `id` autoincremental en SQLite.
- Sin adjuntos. Solucion: el contrato protobuf no define campos de archivo.
- Lectura y borrado de correos. Solucion: RPCs `ReadEmail` y `DeleteEmail` con validacion de ownership.
- Estado `no leido/leido` persistente y cambio al leer. Solucion: campo `is_read` y actualizacion en primera lectura del receptor.
- Persistencia de mensajes y entrega asincrona (usuario receptor puede estar desconectado). Solucion: almacenamiento permanente en SQLite y consulta diferida con `ListEmails`.

### Reglas de capacidad

- Inbox maximo 5 correos. Solucion: conteo previo de inbox en `send_email` y rechazo transaccional.
- Outbox maximo 5 correos. Solucion: conteo previo de outbox en `send_email` y rechazo transaccional.
- Error al emisor si inbox de receptor esta llena. Solucion: `IdReply.result` retorna `ok=false` y mensaje descriptivo.

### Arquitectura/restricciones

- Comunicacion principal via gRPC + protobuf. Solucion: flujo app web -> `grpc_client.py` -> `TurboMessageService`.
- Django usado como front-end y consumidor gRPC. Solucion: controladores en `views.py` sin logica de negocio profunda.
- Sin uso del ORM/modelos Django para logica/persistencia central. Solucion: persistencia exclusiva en `grpc_server/storage.py` con `sqlite3`.

### Concurrencia

- Atencion a usuarios concurrentes con control transaccional y lock en servidor. Solucion: `BEGIN IMMEDIATE` + `RLock`.
- Mitigacion de condiciones de carrera en operaciones criticas. Solucion: serializacion de escrituras y commits atomicos.

### Rubrica y entrega (lineamientos)

- Equipo de 1 a 2 personas. Solucion: organizacion de trabajo modular por capas (front/proto/back).
- Peso total del proyecto: 2 puntos (1.8 funcional + 0.2 documentacion). Solucion: trazabilidad tecnica y documentos de soporte.
- Fecha limite: martes 12 de mayo de 2026 a la hora de clase. Solucion: guia de despliegue y ejecucion reproducible.
- Penalizacion: 20% por dia natural; despues de la hora cuenta como 1 dia. Solucion: validacion temprana y control de versiones por hitos.

## 7) Arranque rapido

1. Activar entorno e instalar dependencias:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "Django>=5.0,<6.0" "grpcio>=1.65.0" "grpcio-tools>=1.65.0" "protobuf>=5.0.0"
```

2. Generar stubs (ya se encontraran en `grpc_server/generated/`):

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

1. Deten el servidor gRPC.
2. Elimina el archivo de base de datos:

```bash
rm grpc_server/data/turbomessage.db
```

3. Arranca de nuevo el servidor gRPC (`python -m grpc_server.server`).
