# Proyecto Omega - TurboMessage

TurboMessage es un sistema simple de mensajeria tipo e-mail.

## Logica de alto nivel

- `proto/turbomessage.proto` define el contrato gRPC.
- `grpc_server/` implementa la logica de negocio y persistencia.
- `django_ui/` funciona como cliente web (templates + consumo gRPC).
- La persistencia se hace con SQLite desde el servidor gRPC.
- Django no usa ORM/modelos para la logica del dominio.

## Estructura actual

```text
.
|-- proto/
|   `-- turbomessage.proto
|-- grpc_server/
|-- django_ui/
`-- requirements.txt
```

## Setup local

1. Crear y activar entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Instalar librerias principales:

```bash
pip install "Django>=5.0,<6.0" "grpcio>=1.65.0" "grpcio-tools>=1.65.0" "protobuf>=5.0.0"
```

## Despliegue local (desarrollo)

```bash
# Terminal 1: backend gRPC
source .venv/bin/activate
python -m grpc_server.server

# Terminal 2: frontend Django
source .venv/bin/activate
cd django_ui
python manage.py runserver 0.0.0.0:8000
```

## Generacion de stubs gRPC

```bash
source .venv/bin/activate
python -m grpc_tools.protoc \
  -I proto \
  --python_out=grpc_server/generated \
  --grpc_python_out=grpc_server/generated \
  proto/turbomessage.proto
```
