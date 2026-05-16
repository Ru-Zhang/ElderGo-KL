"""Structured route planning errors for elder-friendly API responses."""

from __future__ import annotations


class RouteUnavailableError(Exception):
    """Raised when no transit route can be recommended."""

    def __init__(self, code: str, message: str, *, departure_time: str | None = None) -> None:
        self.code = code
        self.message = message
        self.departure_time = departure_time
        super().__init__(message)

    def to_detail(self) -> dict[str, str]:
        detail: dict[str, str] = {"code": self.code, "message": self.message}
        if self.departure_time:
            detail["departure_time"] = self.departure_time
        return detail
