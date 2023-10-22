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
    rest: field(default_factory=dict) = None

    @classmethod
    def raise_if_error(cls: Type[ApiError], response: AttrDict) -> None:
        if "error" in response:
            d = dict(response.error)
            raise cls(**{i: d.pop(i) for i in d if i in cls.__match_args__}, rest=d)

    # 4418: This operation is impossible with the current status of the deal; meta: 'in_process'
    def __str__(self) -> str:
        rv = [f"{self.code}: {self.message}"]
        for k in ['meta', 'data', 'error']:
            if v := getattr(self, k):
                rv.append(f"{k}: {v!r}")
        return "; ".join(rv)
