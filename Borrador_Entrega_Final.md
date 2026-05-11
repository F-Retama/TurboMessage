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

## Cumplimiento de requerimientos principales

- Registro persistente de usuarios con username/password. Solucion aplicada: RPC `Register` e insercion en SQLite.
- Inicio de sesion por credenciales. Solucion aplicada: RPC `Login` con validacion directa de usuario y password.
- ID alfanumerico unico por usuario. Solucion aplicada: generacion de `user_id` con formato `[username]@turbo.com` y restriccion unica.
- Envio de correo solo a usuarios existentes. Solucion aplicada: `SendEmail` valida emisor y receptor antes de persistir.
- Correo con identificador autogenerado, tema, emisor, receptor y cuerpo. Solucion aplicada: tabla `emails` con `id` autoincremental y campos obligatorios.
- Sin soporte de adjuntos. Solucion aplicada: contrato protobuf sin campos de archivos.
- Lectura y borrado de correos por usuario. Solucion aplicada: RPCs `ReadEmail` y `DeleteEmail` con control por `user_id`.
- Estado de correo `no leido/leido` persistente y cambio automatico en la primera lectura del receptor. Solucion aplicada: campo `is_read` actualizado en lectura.
- Persistencia de mensajes para entrega asincrona (receptor no necesita estar conectado para recibir despues). Solucion aplicada: almacenamiento permanente en SQLite + `ListEmails`.
- Limites de capacidad: inbox maximo 5, outbox maximo 5. Solucion aplicada: validaciones de conteo previas al insert en `storage.py`.
- Error cuando se intenta enviar a una inbox llena. Solucion aplicada: respuesta `IdReply` con `result.ok=false` y mensaje de rechazo.
- Operacion concurrente con mitigacion de condiciones de carrera en operaciones criticas. Solucion aplicada: `BEGIN IMMEDIATE` y lock de escritura.
- Uso de Django solo como front-end/consumidor gRPC, sin usar ORM para negocio central. Solucion aplicada: controladores web en Django y logica/persistencia en backend gRPC.

## Conclusiones

El proyecto consolida una implementacion coherente con enfoque de sistemas distribuidos: contrato claro, servicios remotos y persistencia controlada por backend. La solucion mantiene simplicidad operativa en frontend y concentra la complejidad en la capa gRPC, lo cual facilita trazabilidad, pruebas y evolucion futura. Como siguientes pasos naturales, se recomienda ampliar pruebas automatizadas de integracion y concurrencia, y preparar el documento final con el formato solicitado (Arial 11, interlineado simple, margenes de 2.5 cm).
