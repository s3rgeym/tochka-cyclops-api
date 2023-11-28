from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Type

import requests

from .constants import ERROR_RESPONSE_KEY
from .utils import AttrDict

__all__: tuple[str, ...] = (
    "Error",
    "BaseError",
    "ConnectionError",
    "MaximumRetriesExceeded",
    "BadResponse",
    "ApiError",
)


class Error(Exception):
    error_message: str = "An unexcpected error has occurred"

    def __init__(self, error_message: str | None = None):
        self.error_message = error_message or self.error_message
        super().__init__(str(self))

    def __str__(self) -> str:
        return (
            self.error_message()
            if callable(self.error_message)
            else self.error_message
        )


BaseError = Error


class ConnectionError(Error):
    pass


class MaximumRetriesExceeded(ConnectionError):
    error_message = "Maximum connection retries exceeded"


@dataclass(frozen=True)
class BadResponse(Error):
    status: int
    reason: str

    @classmethod
    def from_response(
        cls: Type[BadResponse], response: requests.Response
    ) -> BadResponse:
        return cls(status=response.status_code, reason=response.reason)

    @property
    def error_message(self) -> str:
        return f"{self.status}: {self.reason}"


@dataclass(frozen=True)
class ApiError(Error):
    code: str
    message: str
    # Может быть словарем и строкой
    meta: Any = None
    # Иногда возвращается это поле в виде словаря
    data: Any = None
    # Некоторые методы API возвращают еще и егора, те да там конструкция вида: {"error": {"error": ...}} (масло масляное)
    error: Any = None
    # На случай если будут добавлены еще какие-то поля
    rest: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def raise_if_error(cls: Type[ApiError], response: AttrDict) -> None:
        if ERROR_RESPONSE_KEY in response:
            d = deepcopy(response[ERROR_RESPONSE_KEY])
            # for i in d приведет к ошибке dictionary changed size during iteration
            raise cls(
                **{
                    i: d.pop(i)
                    for i in response[ERROR_RESPONSE_KEY]
                    if i in cls.__match_args__
                },
                rest=d,
            )

    # 4418: This operation is impossible with the current status of the deal; meta: 'in_process'
    @property
    def error_message(self) -> str:
        return "; ".join(
            [
                f"{self.code}: {self.message}",
                *(
                    f"{k}: {self.__dict__[k]!r}"
                    for k in (set(self.__dict__) - {"code", "message"})
                    if self.__dict__[k]
                ),
            ]
        )
