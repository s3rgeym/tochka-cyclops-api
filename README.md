# Tochka API v2 aka Cyclops API

[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tochka-cyclops-api)]() [![PyPI - Downloads](https://img.shields.io/pypi/dm/tochka_cyclops_api)]()

Ставьте звезды, суки бесполезные! Мне от ваших 100 установок в первый день НИКАКОЙ ПОЛЬЗЫ

Неофициальная библиотека на Python для работы с АПИ Точка Банка (я его предпочитаю называть дрочка банком). [Документация](https://api.tochka.com/static/v1/tender-docs/cyclops/main/index.html).

Установка:

```bash
pip install tochka-cyclops-api
```

Поддержка asyncio пока не планируется, но за звезду и донат в пару тысяч оперативно добавлю.

Использование:

```python
from tochka_cyclops_api import ApiTochka, ApiError

api = ApiTochka(
  base_url=API_TOCHKA_BASE_URL,
  sign_system=API_TOCHKA_SIGN_SYSTEM,
  sign_thumbprint=API_TOCHKA_SIGN_THUMBPRINT,
  pkey_data=API_TOCHKA_PKEY_DATA,
)

# Вызовы
# Вернет словарь (поле result) либо бросит ошибку ApiError (у ошибок есть code str)
try:
  # Все три примера вызовут один и тот же метод с теми же параметрами
  res = api.meth_name(foo='bar', baz=42)
  res = api.methName({'foo': 'bar'}, baz=42)
  res = api.jsonrpc_call('MethName', {'foo': 'bar', 'baz': 42})
except ApiError as ex:
  if ex.code == '1234':
    do_smthn()
```
