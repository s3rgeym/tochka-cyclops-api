# Tochka API v2 aka Cyclops API

Неофициальная библиотека на Python для работы с АПИ Точка Банка. [Документация](https://api.tochka.com/static/v1/tender-docs/cyclops/main/index.html).

Установка:

```bash
pip install tochka-cyclops-api
```

Поддержка asyncio пока не планируется, но за звезду и донат в пару тысяч оперативно добавлю.

Использование:

```python
from tochka_cyclops_api import ApiTochka

api = ApiTochka(
  base_url=API_TOCHKA_BASE_URL,
  sign_system=API_TOCHKA_SIGN_SYSTEM,
  sign_thumbprint=API_TOCHKA_SIGN_THUMBPRINT,
  pkey_data=API_TOCHKA_PKEY_DATA,
)

# Вызовы
# Все три примера вызовут один и тот же метод с теми же параметрами
api.meth_name(foo='bar', baz=42)
api.methName({'foo': 'bar'}, baz=42)
api.jsonrpc_call('MethName', {'foo': 'bar', 'baz': 42})
```
