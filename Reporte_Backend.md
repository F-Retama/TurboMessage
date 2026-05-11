# Reporte_Backend.md

Este backend implementa **toda la logica de negocio** de TurboMessage usando solo:

- gRPC + Protocol Buffers (API)
- SQLite (persistencia)
- Python (servidor)

Django no participa aqui en reglas de negocio; solo consumira estos RPCs desde el frontend.

## Estructura del backend

- `grpc_server/server.py`: punto de arranque y servidor ejecutable; implementa las RPCs del contrato `proto/turbomessage.proto`.
- `grpc_server/storage.py`: concentrador de reglas de negocio + acceso a SQLite.
- `grpc_server/generated/`: stubs gRPC generados desde protobuf.

Arranque:

```bash
python -m grpc_server.server
```


## Flujo de conexion

1. `server.py` levanta el servidor gRPC.
2. `server.py` recibe requests protobuf y llama `Storage`.
3. `storage.py` valida reglas, ejecuta transacciones SQLite y devuelve resultado.
4. `server.py` convierte el resultado a los mensajes protobuf de respuesta.

## Generacion de codigo protobuf

Se genera desde `proto/turbomessage.proto` hacia `grpc_server/generated/` con:

```bash
python -m grpc_tools.protoc \
  -I proto \
  --python_out=grpc_server/generated \
  --grpc_python_out=grpc_server/generated \
  proto/turbomessage.proto
```

## Dependencias del backend

- `grpcio`
- `grpcio-tools` (solo para generar stubs)
- `protobuf`
- `sqlite3` (stdlib de Python)

## Funcionalidades del servidor y cumplimiento de requerimientos

RPCs implementadas:

- `Register`: alta persistente de usuarios.
- `Login`: autenticacion basica por username/password.
- `SendEmail`: envio entre usuarios existentes.
- `ListEmails`: consulta de correos visibles del usuario.
- `ReadEmail`: lectura de correo (marca `is_read` en receptor).
- `DeleteEmail`: borrado por propietario (emisor/receptor).

Requerimientos globales que cubre este backend:

- Persistencia de usuarios/correos en base de datos.
- Regla de maximo 5 correos en inbox y 5 en outbox.
- Error cuando el receptor tiene inbox llena.
- Estado `no leido/leido` persistente y cambio automatico al leer.
- Envio/recepcion asincrona por almacenamiento persistente.
- Concurrencia basica: transacciones `BEGIN IMMEDIATE` + lock de escritura para evitar condiciones de carrera en operaciones criticas.
- Sin modelos de Django para negocio/persistencia.
