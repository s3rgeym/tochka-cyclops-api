from __future__ import annotations

import base64
import io
import json
import mimetypes
import re
import sys
import uuid
from dataclasses import KW_ONLY, dataclass
from functools import cached_property
from types import SimpleNamespace
from typing import Any, BinaryIO, Literal, Optional, Type, Union
from urllib.parse import urljoin

import OpenSSL
import requests
from OpenSSL import crypto


class BaseError(Exception):
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


def camel_to_snake(name: str) -> str:
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


DocumentMimeTypes = Literal[
    "application/pdf",
    "image/gif",
    "image/jpeg",
    "image/pjpeg",
    "image/png",
    "image/tiff",
    "image/x-tiff",
    "image/bmp",
    "image/x-windows-bmp",
    "image/x-ms-bmp",
    "image/ms-bmp",
    "image/x-bmp",
]


@dataclass
class ApiTochka:
    """See: <https://api.tochka.com/static/v1/tender-docs/cyclops/main/index.html>"""

    _: KW_ONLY
    sign_system: str
    sign_thumbprint: str
    pkey_data: Union[str, bytes]
    pkey_passphrase: Optional[bytes] = None
    session: Optional[requests.Session] = None
    base_url: str = "https://api.tochka.com/api/v1/cyclops"
    timeout: float = 15.0
    user_agent: str = (
        "Mozilla/5.0 (+https://github.com/s3rgeym/tochka-cyclops-api"
        f"; Python/{'.'.join(map(str, sys.version_info[:3]))})"
    )

    @cached_property
    def pkey(self) -> crypto.PKey:
        return crypto.load_privatekey(
            crypto.FILETYPE_PEM,
            self.pkey_data,
            self.pkey_passphrase,
        )

    def default_session(self) -> requests.Session:
        s = requests.session()
        s.headers.update({"Accept": "application/json"})
        return s

    def __post_init__(self) -> None:
        self.session = self.session or self.default_session()

    def _get_full_url(self, endpoint: str) -> str:
        return urljoin(self.base_url.rstrip("/") + "/", endpoint.lstrip("/"))

    def request(
        self,
        endpoint: str,
        data: Union[str, bytes, io.IOBase],
        query_params: dict | None = None,
        content_type: str = "application/json",
    ) -> Any:
        if callable(getattr(data, "read", None)):
            data = data.read()
        if not isinstance(data, bytes):
            data = data.encode()
        sign_data = OpenSSL.crypto.sign(self.pkey, data, "sha256")
        sign_data = base64.b64encode(sign_data).decode()
        headers = {
            "sign-data": sign_data,
            "sign-thumbprint": self.sign_thumbprint,
            "sign-system": self.sign_system,
            "Content-Type": content_type,
            "User-Agent": self.user_agent,
        }
        resp = self.session.post(
            self._get_full_url(endpoint),
            data=data,
            params=query_params,
            headers=headers,
            timeout=self.timeout,
        )
        try:
            # Позволяет использовать rv.foo.bar вместо rv['foo']['bar']
            # rv = resp.json(object_hook=lambda x: SimpleNamespace(**x))
            rv = resp.json(object_hook=AttrDict)
        except requests.JSONDecodeError as ex:
            raise BadResponse.from_response(response=resp) from ex
        ApiError.raise_if_error(rv)
        return rv

    @staticmethod
    def _generate_id() -> str:
        return str(uuid.uuid4())

    def jsonrpc_call(
        self,
        method: str,
        params: dict | None = None,
        endpoint: str | None = None,
        **kw: Any,
    ) -> Any:
        params = dict(params or {})
        params.update(kw)

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self._generate_id(),
        }

        data = json.dumps(payload)

        res = self.request(endpoint or "/v2/jsonrpc", data)
        assert res["id"] == payload["id"]
        return res["result"]

    def __getattr__(self, name: str) -> Any:
        if not name.startswith("_"):

            def fn(*args: Any, **kwargs: Any) -> Any:
                return self.jsonrpc_call(camel_to_snake(name), *args, **kwargs)

            fn.__name__ = name
            return fn
        raise AttributeError(name)

    __call__ = jsonrpc_call

    # https://api.tochka.com/static/v1/tender-docs/cyclops/main/upload_document.html#upload-document
    def upload_document(
        self,
        kind: Literal["beneficiary", "deal"],
        data: BinaryIO | bytes,
        params: dict | None = None,
        content_type: DocumentMimeTypes | None = None,
        **kwargs: Any,
    ) -> dict:
        params = dict(params or {})
        params.update(kwargs)
        if not content_type:
            if not isinstance(data, io.IOBase):
                raise ValueError("you must specify content_type for raw data")
            content_type, _ = mimetypes.guess_type(data.name)
        return self.request(
            f"upload_document/{kind}", data, params, content_type
        )


class AttrDict(dict):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.__dict__ = self
