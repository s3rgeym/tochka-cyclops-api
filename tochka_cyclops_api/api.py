from __future__ import annotations

import base64
import datetime
import io
import json
import logging
import mimetypes
import sys
import time
import uuid
from dataclasses import KW_ONLY, dataclass
from functools import cached_property
from os import getenv
from typing import Any, BinaryIO, Literal
from urllib.parse import urljoin
from urllib.request import getproxies

import requests
from OpenSSL import crypto

from .constants import (
    ERROR_RESPONSE_KEY,
    KEBAB_PACKAGE_NAME,
    RESULT_RESPONSE_KEY,
)
from .errors import *
from .utils import AttrDict, camel_to_snake

logger = logging.getLogger(__package__)

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


ProxiesDict = dict[str, str]
SYSTEM_PROXIES: ProxiesDict = getproxies()

# TODO: генерация методов для автодополнения
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
    jsonrpc_endpoint: str = "/v2/jsonrpc"
    upload_document_endpoint: str = "/upload_document/{kind}"
    timeout: float = 15.0
    user_agent: str = (
        f"Mozilla/5.0 ({KEBAB_PACKAGE_NAME} +https://github.com/s3rgeym/{KEBAB_PACKAGE_NAME}"
        f"; Python/{'.'.join(map(str, sys.version_info[:3]))})"
    )

    @cached_property
    def pkey(self) -> crypto.PKey:
        return crypto.load_privatekey(
            crypto.FILETYPE_PEM,
            self.pkey_data,
            self.pkey_passphrase,
        )

    # @cached_property
    # def get_proxies(self) -> ProxiesDict:
    #     rv = {}
    #     for end in ['', 's']:
    #         key = 'http' + end
    #         if val := getenv(key.upper() + '_PROXY'):
    #             rv[key] = val
    #     return rv

    def default_session(self) -> requests.Session:
        s = requests.session()
        s.headers.update(
            {
                "Accept": "application/json;charset=UTF-8",
            }
        )
        return s

    def __post_init__(self) -> None:
        self.session = self.session or self.default_session()

    def _get_full_url(self, endpoint: str) -> str:
        return urljoin(self.base_url.rstrip("/") + "/", endpoint.lstrip("/"))

    def _sign_data(self, data: bytes) -> str:
        return base64.b64encode(crypto.sign(self.pkey, data, "sha256")).decode()

    def _retry_request(
        self,
        url: str,
        data: str | bytes,
        headers: dict[str, str],
        query_params: dict | None,
        tries: int,
    ) -> AttrDict:
        while tries:
            try:
                resp = self.session.post(
                    url,
                    data=data,
                    params=query_params,
                    headers=headers,
                    timeout=self.timeout,
                    proxies=SYSTEM_PROXIES,
                )
                # Позволяет использовать rv.foo.bar вместо rv['foo']['bar']
                # rv = resp.json(object_hook=lambda x: SimpleNamespace(**x))
                return resp.json(object_hook=AttrDict)
            except requests.Timeout:
                tries -= 1
            except requests.JSONDecodeError as e:
                raise BadResponse.from_response(response=resp) from e
            except requests.RequestException as e:
                raise ConnectionError(
                    f"Request failed due connection error: {e}"
                ) from e
        raise MaximumRetriesExceeded()

    def _request(
        self,
        endpoint: str,
        data: str | bytes | io.IOBase,
        query_params: dict | None = None,
        content_type: str = "application/json",
        tries: int = 1,  # если указать -1, то будет выполняться до победного
    ) -> AttrDict:
        if callable(getattr(data, "read", None)):
            data = data.read()
        if not isinstance(data, bytes):
            data = data.encode()
        assert type(data) is bytes
        assert content_type
        headers = {
            "sign-data": self._sign_data(data),
            "sign-thumbprint": self.sign_thumbprint,
            "sign-system": self.sign_system,
            "Content-Type": content_type,
            "User-Agent": self.user_agent,
        }
        rv = self._retry_request(
            url=self._get_full_url(endpoint),
            data=data,
            headers=headers,
            query_params=query_params,
            tries=tries,
        )
        ApiError.raise_if_error(rv)
        return rv

    @staticmethod
    def _generate_id() -> str:
        return str(uuid.uuid4())

    def jsonrpc_call(
        self,
        method: str,
        params: dict | None = None,
        *,
        tries: int = 1,
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
        logger.debug("JSON Request Body: %r", data)
        res = self._request(self.jsonrpc_endpoint, data, tries=tries)
        assert res.id == payload["id"]
        return res[RESULT_RESPONSE_KEY]

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
        tries: int = 1,
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
        return self._request(
            self.upload_document_endpoint.format(kind=kind),
            data,
            params,
            content_type,
            tries=tries,
        )
