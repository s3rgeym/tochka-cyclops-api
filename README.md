# Tochka API v2 aka Cyclops API Library for Python

[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tochka-cyclops-api)]() [![PyPI - Version](https://img.shields.io/pypi/v/tochka-cyclops-api)]() [![PyPI - Downloads](https://img.shields.io/pypi/dm/tochka_cyclops_api)]()

Ставьте звезды, суки бесполезные! Мне от ваших 100 установок в первый день НИКАКОЙ ПОЛЬЗЫ

> Unofficial Python Library for Tochka API

Неофициальная библиотека на Python для работы с АПИ Точка Банка (я его предпочитаю называть дрочка банком). [Документация туть](https://api.tochka.com/static/v1/tender-docs/cyclops/main/index.html).

* Работает через JSONRPC.
* Может грузить документы.

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

# Вызов методов
try:
  """
  Отправит запрос с таким телом:

  {
    "id": "0d6a26ea-84f0-4be2-9999-b46edc9b59b6",
    "jsonrpc": "2.0",
    "method": "identification_payment",
    "params": {
      "payment_id": "cyclops-b9eabfd7-eead-4940-a6b1-4654850664f5",
      "owners":[{
        "virtual_account": "859b645a-ebb8-4f91-8b05-b433c85dc662",
        "amount": 1000
      }]
    }
  }

  * camelCase преобразуется в snake_case: identificationPayment, IdentificationPayment и identification_payment равнозначны.
  * Вместо именованных параметров можно передать словарь.
  * Если словарь и именованные параметры передаются вместе, то они мержатся, причем именованные параметры перезаписывают соотв элементы словаря.

  Результат будет примерно таким:

  {
    "virtual_accounts": [{
      "code": "859b645a-ebb8-4f91-8b05-b433c85dc662",
      "cash": 1000
    }]
  }
  """
  res = api.identificationPayment(payment_id="cyclops-b9eabfd7-eead-4940-a6b1-4654850664f5", owners=[{
      "virtual_account": "859b645a-ebb8-4f91-8b05-b433c85dc662",
      "amount": 1000
  }])
except ApiError as ex:
  if ex.code == '4411':
    print('Аккаунт не найден')
  ...
```

Все мыслимые права защищены _в натуре_ (с) 2023.
