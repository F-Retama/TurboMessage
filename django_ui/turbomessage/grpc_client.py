"""gRPC client wrapper used by Django controllers."""

from __future__ import annotations

import os
from pathlib import Path
import sys

import grpc

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GENERATED_DIR = PROJECT_ROOT / "grpc_server" / "generated"
if str(GENERATED_DIR) not in sys.path:
    sys.path.insert(0, str(GENERATED_DIR))

import turbomessage_pb2  # type: ignore  # noqa: E402
import turbomessage_pb2_grpc  # type: ignore  # noqa: E402


class TurboMessageClient:
    def __init__(self, target: str | None = None) -> None:
        self.target = target or os.getenv("TURBOMESSAGE_GRPC_TARGET", "localhost:36933")

    @staticmethod
    def _rpc_error_message(exc: grpc.RpcError) -> str:
        details = exc.details()
        return details if details else f"gRPC error: {exc.code().name}"

    def register(self, username: str, password: str) -> turbomessage_pb2.UserReply:
        try:
            with grpc.insecure_channel(self.target) as channel:
                stub = turbomessage_pb2_grpc.TurboMessageServiceStub(channel)
                return stub.Register(
                    turbomessage_pb2.AuthRequest(username=username, password=password)
                )
        except grpc.RpcError as exc:
            return turbomessage_pb2.UserReply(
                result=turbomessage_pb2.Result(
                    ok=False,
                    message=self._rpc_error_message(exc),
                ),
                user_id="",
            )

    def login(self, username: str, password: str) -> turbomessage_pb2.UserReply:
        try:
            with grpc.insecure_channel(self.target) as channel:
                stub = turbomessage_pb2_grpc.TurboMessageServiceStub(channel)
                return stub.Login(
                    turbomessage_pb2.AuthRequest(username=username, password=password)
                )
        except grpc.RpcError as exc:
            return turbomessage_pb2.UserReply(
                result=turbomessage_pb2.Result(
                    ok=False,
                    message=self._rpc_error_message(exc),
                ),
                user_id="",
            )

    def send_email(
        self, sender_id: str, recipient_id: str, subject: str, body: str
    ) -> turbomessage_pb2.IdReply:
        try:
            with grpc.insecure_channel(self.target) as channel:
                stub = turbomessage_pb2_grpc.TurboMessageServiceStub(channel)
                return stub.SendEmail(
                    turbomessage_pb2.SendEmailRequest(
                        sender_id=sender_id,
                        recipient_id=recipient_id,
                        subject=subject,
                        body=body,
                    )
                )
        except grpc.RpcError as exc:
            return turbomessage_pb2.IdReply(
                result=turbomessage_pb2.Result(
                    ok=False,
                    message=self._rpc_error_message(exc),
                ),
                id=0,
            )

    def list_emails(self, user_id: str) -> turbomessage_pb2.EmailsReply:
        try:
            with grpc.insecure_channel(self.target) as channel:
                stub = turbomessage_pb2_grpc.TurboMessageServiceStub(channel)
                return stub.ListEmails(turbomessage_pb2.ListEmailsRequest(user_id=user_id))
        except grpc.RpcError as exc:
            return turbomessage_pb2.EmailsReply(
                result=turbomessage_pb2.Result(
                    ok=False,
                    message=self._rpc_error_message(exc),
                ),
                emails=[],
            )

    def read_email(self, user_id: str, email_id: int) -> turbomessage_pb2.EmailReply:
        try:
            with grpc.insecure_channel(self.target) as channel:
                stub = turbomessage_pb2_grpc.TurboMessageServiceStub(channel)
                return stub.ReadEmail(
                    turbomessage_pb2.EmailActionRequest(user_id=user_id, email_id=email_id)
                )
        except grpc.RpcError as exc:
            return turbomessage_pb2.EmailReply(
                result=turbomessage_pb2.Result(
                    ok=False,
                    message=self._rpc_error_message(exc),
                ),
                email=turbomessage_pb2.Email(),
            )

    def delete_email(self, user_id: str, email_id: int) -> turbomessage_pb2.EmptyReply:
        try:
            with grpc.insecure_channel(self.target) as channel:
                stub = turbomessage_pb2_grpc.TurboMessageServiceStub(channel)
                return stub.DeleteEmail(
                    turbomessage_pb2.EmailActionRequest(user_id=user_id, email_id=email_id)
                )
        except grpc.RpcError as exc:
            return turbomessage_pb2.EmptyReply(
                result=turbomessage_pb2.Result(
                    ok=False,
                    message=self._rpc_error_message(exc),
                )
            )
