import json
import unittest

from tochka_cyclops_api import ApiError
from tochka_cyclops_api.utils import AttrDict


class Test(unittest.TestCase):
    def test_error_string(self) -> None:
        with self.assertRaises(ApiError) as ctx:
            res = json.loads(
                """{
                "error": {
                    "code": "-10001",
                    "message": "an exception has occurred",
                    "meta": "bad name"
                }
            }""",
                object_hook=AttrDict,
            )
            ApiError.raise_if_error(res)
        self.assertEqual(
            str(ctx.exception),
            "-10001: an exception has occurred; meta: 'bad name'",
        )
