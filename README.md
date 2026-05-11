# Proyecto Omega - TurboMessage

Implementacion de un sistema simple de mensajeria estilo e-mail llamado **TurboMessage**.

## Stack tecnologico

- **Back-end de logica de negocio:** gRPC + Protocol Buffers
- **Front-end web:** Django (solo para exponer/consumir servicios gRPC y renderizar templates)
- **Persistencia:** archivos o base de datos (sin modelos de Django)


## Estructura inicial

```text
.
|-- grpc_server/
|   |-- app.py
|   |-- db/
|   |-- repositories/
|   |-- services/
|   `-- generated/
|-- django_ui/
|   |-- turbo_ui/
|   `-- apps/mailbox/
|-- proto/
|-- scripts/
```

## Persistencia en base de datos

- Se usara SQLite desde el backend gRPC con `sqlite3` nativo de Python.
- Django queda solo como front-end y cliente gRPC.
- No se usaran modelos ni ORM de Django.


## Despliegue
