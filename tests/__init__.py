import json
import unittest

from tochka_cyclops_api import ApiError
from tochka_cyclops_api.utils import AttrDict


class Test(unittest.TestCase):
    def test_attr_dict(self) -> None:
        res = AttrDict.from_dict({"users": [{"id": 42, "name": "John Carmak"}]})
        self.assertEqual(res.users[0].id, 42)
        self.assertEqual(res.users[0].name, "John Carmak")

    def test_error_string(self) -> None:
        with self.assertRaises(ApiError) as ctx:
            res = AttrDict.from_dict(
                {
                    "error": {
                        "code": "-10001",
                        "message": "an exception has occurred",
                        "meta": "bad name",
                    }
                }
            )
            ApiError.raise_if_error(res)
        self.assertEqual(
            str(ctx.exception),
            "-10001: an exception has occurred; meta: 'bad name'",
        )
