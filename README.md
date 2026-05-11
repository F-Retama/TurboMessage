# TurboMessage

## Resumen

TurboMessage es un sistema de mensajeria tipo e-mail con arquitectura distribuida en tres capas:

- Front-end web en Django.
- Contrato de servicios en gRPC + Protocol Buffers.
- Logica de negocio y persistencia en servidor gRPC con SQLite.

La aplicacion web opera como cliente de servicios gRPC; la logica central no se implementa con ORM de Django.

## Estructura del repositorio

```text
.
|-- django_ui/
|   |-- django_ui/        # proyecto Django
|   `-- turbomessage/     # app Django (vistas, cliente gRPC, templates)
|-- proto/
|   `-- turbomessage.proto
|-- grpc_server/
|   |-- server.py         # servidor gRPC ejecutable
|   |-- storage.py        # reglas de negocio + SQLite
|   `-- generated/        # stubs protobuf/gRPC
`-- requirements.txt
```

## Flujo de arquitectura (front -> proto -> back)

1. La vista Django recibe la accion del usuario.
2. El controlador (`views.py`) invoca `grpc_client.py`.
3. El cliente serializa requests del contrato `proto/turbomessage.proto`.
4. `grpc_server/server.py` procesa RPCs y delega a `storage.py`.
5. `storage.py` aplica reglas, persiste en SQLite y devuelve resultados.
6. El servidor responde `*Reply`; Django renderiza feedback en templates.

## Cobertura de requerimientos (sintesis)

- Registro/login persistente: `Register` y `Login` sobre SQLite.
- ID unico de usuario: generado con `uuid`.
- Envio valido solo a usuario existente: validacion previa en `SendEmail`.
- Correo con id, tema, emisor, receptor y cuerpo: entidad `Email` y tabla `emails`.
- Sin adjuntos: contrato protobuf sin campos de archivo.
- Lectura/borrado: `ReadEmail` y `DeleteEmail` con control por `user_id`.
- Estado no leido/leido: campo `is_read` persistente con cambio al leer.
- Entrega asincrona: persistencia en SQLite y consulta diferida con `ListEmails`.
- Capacidad inbox/outbox (maximo 5): conteos previos y rechazo transaccional.
- Error por inbox llena: respuesta `IdReply` con `result.ok=false`.
- Concurrencia: `BEGIN IMMEDIATE` + lock de escritura en operaciones criticas.

## Setup y ejecucion

1. Entorno e instalacion:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "Django>=5.0,<6.0" "grpcio>=1.65.0" "grpcio-tools>=1.65.0" "protobuf>=5.0.0"
```

2. Generacion de stubs:

```bash
python -m grpc_tools.protoc \
  -I proto \
  --python_out=grpc_server/generated \
  --grpc_python_out=grpc_server/generated \
  proto/turbomessage.proto
```

3. Arranque del backend gRPC (puerto `36933`):

```bash
python -m grpc_server.server
```

4. Arranque del frontend Django:

```bash
cd django_ui
python manage.py runserver 0.0.0.0:8000
```

5. Acceso web:

- `http://localhost:8000/`
