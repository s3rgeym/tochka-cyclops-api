from __future__ import annotations

import collections
import re
from typing import Any, Type


def camel_to_snake(name: str) -> str:
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


class AttrDict(dict):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.__dict__ = self

    @classmethod
    def _from_value(cls: Type[AttrDict], v: Any) -> Any:
        return (
            cls.from_dict(v)
            if isinstance(v, dict)
            else list(map(cls._from_value, v))
            if isinstance(v, collections.abc.Sequence)
            and not isinstance(v, (str, bytes))
            else v
        )

    @classmethod
    def from_dict(cls: Type[AttrDict], d: dict) -> AttrDict:
        return cls({k: cls._from_value(v) for k, v in d.items()})
