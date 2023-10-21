from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Type

import requests

__all__ = ("BaseError", "ConnectionError", "BadResponse", "ApiError")


class BaseError(Exception):
    pass


class ConnectionError(BaseError):
    pass


@dataclass(frozen=True)
class BadResponse(BaseError):
    status: int
    reason: str

    @classmethod
    def from_response(
        cls: Type[BadResponse], response: requests.Response
    ) -> BadResponse:
        return cls(status=response.status_code, reason=response.reason)

    def __str__(self) -> str:
        return f"{self.status}: {self.reason}"


@dataclass(frozen=True)
class ApiError(BaseError):
    code: str
    message: str
    meta: Any = None
    data: Any = None
    error: Any = None

    @classmethod
    def raise_if_error(cls: Type[ApiError], response: dict) -> None:
        if "error" in response:
            raise cls(**response["error"])

    def __str__(self) -> str:
        rv = [f"{self.code}: {self.message}"]
        for prop in ["meta", "data", "error"]:
            if val := getattr(self, prop):
                rv.append(f"{prop}: {val!r}")
        return "; ".join(rv)
