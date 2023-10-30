# Tochka API v2 aka Cyclops API Library for Python

[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tochka-cyclops-api)]() [![PyPI - Version](https://img.shields.io/pypi/v/tochka-cyclops-api)]() [![PyPI - Downloads](https://img.shields.io/pypi/dm/tochka-cyclops-api)]() [![Total Downloads](https://static.pepy.tech/badge/tochka-cyclops-api)]()

Ставьте звезды, суки бесполезные! Мне от ваших 100 установок в первый день НИКАКОЙ ПОЛЬЗЫ

> Unofficial Python Library for Tochka API

Неофициальная библиотека на Python для работы с АПИ Точка Банка (я его предпочитаю называть Дрочка банком). [Документация туть](https://api.tochka.com/static/v1/tender-docs/cyclops/main/index.html).

* Работает через JSONRPC.
* Может грузить документы.
* Содержит магию "Лунной призмы" 🪄 💫 ✨

Установка:

```bash
pip install tochka-cyclops-api

# Если текущая версия падает с ошибкой, установите предыдущую
pip install tochka-cyclops-api==0.3.0

# или так
poetry add tochka-cyclops-api

poetry add git+https://github.com/s3rgeym/tochka-cyclops-api.git

git clone https://github.com/s3rgeym/tochka-cyclops-api.git
cd tochka-cyclops-api
# что-то правим
poetry install --no-dev
```

Поддержка asyncio пока не планируется, но за звезду и донат в пару тысяч оперативно добавлю.

В эпоху Docker использовать версии Python, отличные от последних — моветон, поэтому поддержка более старых точно не планируется.

Использование:

```python
from tochka_cyclops_api import ApiTochka, ApiError

api = ApiTochka(
    base_url='<API_URL>',
    sign_system='<SIGN_SYSTEM>',
    sign_thumbprint='<SIGN_THUMBPRINT>',
    pkey_data=open('/path/to/rsaprivkey.pem').read(),
)

# Методы генерируются динамически. Вызов несуществующих атрибутов инстанса ApiTochka преобразуется в запросы к API.
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

    * camelCase преобразуется в snake_case: identificationPayment,
      IdentificationPayment и identification_payment равнозначны.
    * Вместо именованных параметров можно передать словарь.
    * Если словарь и именованные параметры передаются вместе, то они мержатся,
      причем именованные параметры перезапишут элементы словаря.

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

    # Вместо словаря при парсинге объектов используется AttrDict,
    # который позволяет к полям обращаться как к атрибутам, а не только по индексу
    print(rv.virtual_accounts[0])
except ApiError as ex:
    if ex.code == '4411':
        print('Аккаунт не найден')
  ...


rv = api.upload_document(
    'beneficiary',
    # можно передать любой объект, имеющий метод read, например, `requests.get('https://target/path/to/file.pdf')`,
    # но тогда придется указать content_type
    open('/path/to/offer.pdf', 'rb'),
    beneficiary_id='...',
    document_type='contract_offer',
    # Эти параметры можно опустить, они сгенерируются автоматически
    document_date='2023-11-12',
    document_number='12345',
)

print(rv.document_id)  # cyclops-231020230621590-98a669e2-859b-44ac-9831-4a964ac7e49b
```

Запуск тестов:

```bash
poetry run python -m unittest
```

Все мыслимые права защищены _в натуре_ (с) 2023.
