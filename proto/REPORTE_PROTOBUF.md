# Protobuf de TurboMessage

## Estructura

El contrato esta hecho para que el cliente sea muy ligero y la complejidad viva en el servidor gRPC.

- Requests simples con tipos basicos (`string`, `int64`, `bool`).
- Responses reciclables (`Result` + wrappers) para mantener consistencia.
- Un solo servicio (`TurboMessageService`) con operaciones directas del dominio.

## Piezas del contrato

- `AuthRequest`: login/registro.
- `SendEmailRequest`: envio de correo.
- `ListEmailsRequest`: listar correos de un usuario.
- `EmailActionRequest`: leer o borrar un correo por `user_id` y `email_id`.
- `Email`: entidad de correo intercambiada.
- `Result`: estado comun (`ok`, `message`).
- Wrappers de respuesta: `UserResponse`, `IdResponse`, `EmailResponse`, `EmailsResponse`, `EmptyResponse`.

## Flujo cliente-servidor (version final)

1. Django envia requests gRPC con datos minimos.
2. El servidor valida reglas de negocio (usuarios, limites, estados, ownership).
3. El servidor persiste en base de datos.
4. El servidor responde con el wrapper adecuado y `Result`.
5. Django interpreta `Result` y muestra la vista correspondiente.
