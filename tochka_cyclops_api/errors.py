from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Type

import requests

from .utils import AttrDict 

__all__: tuple[str, ...] = ("BaseError", "ConnectionError", "BadResponse", "ApiError")


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
    # Может быть словарем и строкой
    meta: Any = None
    # Иногда возвращается это поле в виде словаря
    data: Any = None
    # Некоторые методы API возвращают еще и егора, те да там конструкция вида: {"error": {"error": ...}} (масло масляное)
    error: Any = None
    # На случай если будут добавлены еще какие-то поля
    kwargs: field(default_factory=dict) = None

    @classmethod
    def raise_if_error(cls: Type[ApiError], response: AttrDict) -> None:
        if "error" in response:
            raise cls(
                **{k: kwargs.pop(k) for k in response.error if k in cls.__match_args__},
                kwargs=response.error,
            )

    # 4418: This operation is impossible with the current status of the deal; meta: 'in_process'
    def __str__(self) -> str:
        rv = [f"{self.code}: {self.message}"]
        for prop in ["meta", "data", "error"]:
            if val := getattr(self, prop):
                rv.append(f"{prop}: {val!r}")
        return "; ".join(rv)
