"""gRPC server implementation for TurboMessage."""

from __future__ import annotations

from concurrent import futures
from pathlib import Path
import sys

import grpc

from grpc_server.storage import Storage

GENERATED_DIR = Path(__file__).resolve().parent / "generated"
if str(GENERATED_DIR) not in sys.path:
    sys.path.insert(0, str(GENERATED_DIR))

import turbomessage_pb2  # type: ignore  # noqa: E402
import turbomessage_pb2_grpc  # type: ignore  # noqa: E402

DEFAULT_GRPC_PORT = 36933


class TurboMessageService(turbomessage_pb2_grpc.TurboMessageServiceServicer):
    def __init__(self, storage: Storage) -> None:
        self.storage = storage

    @staticmethod
    def _result(ok: bool, message: str) -> turbomessage_pb2.Result:
        return turbomessage_pb2.Result(ok=ok, message=message)

    @staticmethod
    def _email_message(email: dict) -> turbomessage_pb2.Email:
        return turbomessage_pb2.Email(
            id=int(email["id"]),
            sender_id=str(email["sender_id"]),
            recipient_id=str(email["recipient_id"]),
            subject=str(email["subject"]),
            body=str(email["body"]),
            is_read=bool(email["is_read"]),
        )

    def Register(self, request, context):  # noqa: N802 (gRPC naming)
        ok, message, user_id = self.storage.register(request.username, request.password)
        return turbomessage_pb2.UserReply(
            result=self._result(ok, message),
            user_id=user_id if ok else "",
        )

    def Login(self, request, context):  # noqa: N802
        ok, message, user_id = self.storage.login(request.username, request.password)
        return turbomessage_pb2.UserReply(
            result=self._result(ok, message),
            user_id=user_id if ok else "",
        )

    def SendEmail(self, request, context):  # noqa: N802
        ok, message, email_id = self.storage.send_email(
            request.sender_id,
            request.recipient_id,
            request.subject,
            request.body,
        )
        return turbomessage_pb2.IdReply(
            result=self._result(ok, message),
            id=email_id if ok else 0,
        )

    def ListEmails(self, request, context):  # noqa: N802
        ok, message, emails = self.storage.list_emails(request.user_id)
        return turbomessage_pb2.EmailsReply(
            result=self._result(ok, message),
            emails=[self._email_message(email) for email in emails],
        )

    def ReadEmail(self, request, context):  # noqa: N802
        ok, message, email = self.storage.read_email(request.user_id, request.email_id)
        return turbomessage_pb2.EmailReply(
            result=self._result(ok, message),
            email=self._email_message(email) if ok and email else turbomessage_pb2.Email(),
        )

    def DeleteEmail(self, request, context):  # noqa: N802
        ok, message = self.storage.delete_email(request.user_id, request.email_id)
        return turbomessage_pb2.EmptyReply(result=self._result(ok, message))


def serve(host: str = "0.0.0.0", port: int = DEFAULT_GRPC_PORT) -> grpc.Server:
    storage = Storage()
    storage.init_db()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=33))
    turbomessage_pb2_grpc.add_TurboMessageServiceServicer_to_server(
        TurboMessageService(storage),
        server,
    )
    server.add_insecure_port(f"{host}:{port}")
    server.start()
    return server


def main() -> None:
    server = serve(host="0.0.0.0", port=DEFAULT_GRPC_PORT)
    print(f"TurboMessage gRPC server running on 0.0.0.0:{DEFAULT_GRPC_PORT}")
    server.wait_for_termination()


if __name__ == "__main__":
    main()
