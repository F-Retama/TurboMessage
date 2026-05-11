"""Thin gRPC client wrapper used by Django views."""


class TurboMessageClient:
    def __init__(self, target: str = "localhost:50051") -> None:
        self.target = target

    def health_status(self) -> str:
        # TODO: replace with a real gRPC ping/check call.
        return f"pending-connection:{self.target}"
