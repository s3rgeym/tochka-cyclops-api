from __future__ import annotations

import base64
import datetime
import io
import json
import mimetypes
import sys
import time
import uuid
from dataclasses import KW_ONLY, dataclass
from functools import cached_property
from typing import Any, BinaryIO, Literal
from urllib.parse import urljoin

import requests
from OpenSSL import crypto

from .errors import *
from .utils import AttrDict, camel_to_snake

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
    pkey_data: bytes | str
    pkey_passphrase: bytes | str | None = None
    session: requests.Session | None = None
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
        s.headers.update({
            "Accept": "application/json",
        })
        return s

    def __post_init__(self) -> None:
        self.session = self.session or self.default_session()

    def _get_full_url(self, endpoint: str) -> str:
        return urljoin(self.base_url.rstrip("/") + "/", endpoint.lstrip("/"))

    def request(
        self,
        endpoint: str,
        data: str | bytes | io.IOBase,
        query_params: dict | None = None,
        content_type: str = "application/json",
    ) -> Any:
        if callable(getattr(data, "read", None)):
            data = data.read()
        if not isinstance(data, bytes):
            data = data.encode()
        sign_data = crypto.sign(self.pkey, data, "sha256")
        sign_data = base64.b64encode(sign_data).decode()
        headers = {
            "sign-data": sign_data,
            "sign-thumbprint": self.sign_thumbprint,
            "sign-system": self.sign_system,
            "Content-Type": content_type,
            "User-Agent": self.user_agent,
        }
        try:
            resp = self.session.post(
                self._get_full_url(endpoint),
                data=data,
                params=query_params,
                headers=headers,
                timeout=self.timeout,
            )
            # Позволяет использовать rv.foo.bar вместо rv['foo']['bar']
            # rv = resp.json(object_hook=lambda x: SimpleNamespace(**x))
            rv = resp.json(object_hook=AttrDict)
        except requests.JSONDecodeError as e:
            raise BadResponse.from_response(response=resp) from e
        except requests.RequestException as e:
            raise ConnectionError(
                f"Request failed due connection error: {e}"
            ) from e
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
        **kwargs: Any,
    ) -> Any:
        params = dict(params or {}, **kwargs)
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self._generate_id(),
        }
        data = json.dumps(payload, default=str)
        res = self.request(endpoint or "/v2/jsonrpc", data)
        assert res.id == payload["id"]
        return res.result

    def __getattr__(self, name: str) -> Any:
        if not name.startswith("_"):

            def fn(*args: Any, **kwargs: Any) -> Any:
                return self.jsonrpc_call(camel_to_snake(name), *args, **kwargs)

            fn.__name__ = name
            return fn
        raise AttributeError(name)

    __call__ = jsonrpc_call  # <ApiTochka>('method', params)

    # https://api.tochka.com/static/v1/tender-docs/cyclops/main/upload_document.html#upload-document
    def upload_document(
        self,
        kind: Literal["beneficiary", "deal"],
        data: BinaryIO | bytes,
        params: dict | None = None,
        *,
        document_type: str,
        document_number: str | int | None = None,
        document_date: datetime.datetime | datetime.date | str | None = None,
        content_type: DocumentMimeTypes | None = None,
        **kwargs: Any,
    ) -> dict:
        if document_number is None:
            document_number = time.time_ns()
        if document_date is None:
            document_date = datetime.datetime.now()
        if isinstance(document_date, (datetime.date, datetime.datetime)):
            document_date = document_date.strftime("%Y-%m-%d")
        params = dict(
            params or {},   
            document_date=document_date,
            document_number=str(document_number),
            document_type=document_type,
            **kwargs,
        )
        if not content_type:
            # if not isinstance(data, io.IOBase):
            if not hasattr(data, "name"):
                raise ValueError("you must specify content_type for raw data")
            content_type, _ = mimetypes.guess_type(data.name)
        return self.request(
            f"/upload_document/{kind}", data, params, content_type
        )
