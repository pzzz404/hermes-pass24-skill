# PASS24 skill for Hermes

Скилл Hermes для заказа автомобильных пропусков в [PASS24.online](https://pass24.online) через Telegram. Пользователь отправляет заявку текстом или голосовым сообщением; Hermes распознаёт номер и марку автомобиля, оформляет пропуск в PASS24.online и возвращает результат в чат.

> Этот репозиторий реализует действие PASS24 внутри Hermes. Telegram, голосовые сообщения и диалог с пользователем обслуживает Hermes; скилл не подключается к Telegram напрямую.

## Как это работает

```text
Заявка текстом или голосом в Telegram → Hermes → PASS24 skill → PASS24.online
```

Hermes распознаёт намерение пользователя и номер автомобиля, после чего вызывает CLI с локальным защищённым файлом конфигурации. CLI возвращает JSON; Hermes интерпретирует результат и сообщает пользователю, что пропуск оформлен либо почему оформление не удалось.

## Возможности

- Создать разовый автомобильный пропуск на текущий день.
- Получить список сегодняшних пропусков.
- Отменить пропуск по ID.
- Получить `address_id`, `tenant_id` и тип транспорта из истории PASS24.

## Установка для Hermes

Установите зависимости в среде, из которой Hermes будет вызывать коннектор:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Создайте локальный закрытый файл конфигурации вне репозитория, например `/secure/path/pass24.env`:

```dotenv
PASS24_PHONE=+7XXXXXXXXXX
PASS24_PASSWORD=your_password_here
PASS24_ADDRESS_ID=0
PASS24_TENANT_ID=0
PASS24_VEHICLE_TYPE=404
```

Не сохраняйте этот файл в Git, не передавайте его агенту в тексте сообщений и не включайте в логи. Шаблон переменных находится в [`.env.example`](.env.example).

## Вызовы CLI

Hermes вызывает команды от имени локального процесса:

```bash
PASS24_ENV_FILE=/secure/path/pass24.env python -m bot.cli create "А123ВО77 Toyota"
PASS24_ENV_FILE=/secure/path/pass24.env python -m bot.cli list
PASS24_ENV_FILE=/secure/path/pass24.env python -m bot.cli cancel 12345
PASS24_ENV_FILE=/secure/path/pass24.env python -m bot.cli discover
```

Ответ всегда JSON. Hermes должен передавать в `create` уже распознанные номер и марку; обработка голоса и Telegram-взаимодействие остаются исключительно на стороне Hermes.

## Конфигурация

| Переменная | Назначение |
|---|---|
| `PASS24_BASE_URL` | URL мобильного API; обычно оставьте значение из шаблона. |
| `PASS24_PHONE` | Номер телефона для входа; отправляется API как `email`. |
| `PASS24_PASSWORD` | Пароль от аккаунта PASS24. |
| `PASS24_ADDRESS_ID` | ID адреса; `0` позволяет получить его через `discover`. |
| `PASS24_TENANT_ID` | ID профиля жильца; `0` позволяет получить его через `discover`. |
| `PASS24_VEHICLE_TYPE` | Тип транспортного средства; по умолчанию `404`. |

### Особенность авторизации PASS24

В API поле логина называется `email`, но для авторизации в него нужно передать номер телефона, используемый в приложении PASS24:

```text
email = номер телефона PASS24
password = пароль PASS24
```

Поэтому `PASS24_PHONE` содержит телефон, а не адрес электронной почты. Это соответствие реализовано в [`bot/api.py`](bot/api.py).

## Безопасность и приватность

- В публикуемый репозиторий не входят токены, пароли, номера телефонов, chat ID и история пропусков.
- `.env`, `.env.*`, кэш и журналы исключены правилами [`.gitignore`](.gitignore).
- Не передавайте секреты через аргументы командной строки: используйте только `PASS24_ENV_FILE`.
- Проект является неофициальной интеграцией и работает от имени авторизованного пользователя PASS24.

## Проверка установки

```bash
.venv/bin/python -m compileall bot
.venv/bin/python -m bot.cli --help
```

## Известное ограничение TLS

Мобильный API PASS24 на момент разработки имел сертификат, который не проходил стандартную проверку. Поэтому клиент временно использует `verify=False`. Это снижает защиту канала: используйте интеграцию только в доверенной сети и проверьте состояние API перед эксплуатацией.

## Лицензия

[MIT](LICENSE).

---

## English

A Hermes skill for ordering PASS24.online vehicle passes through Telegram. A user sends a text or voice request, Hermes recognises the vehicle details, invokes the local PASS24 CLI, and replies with the result.

This repository implements the PASS24 action inside Hermes. It is **not** a Telegram bot: Hermes owns all messaging and speech-to-text, then invokes `bot.cli` locally and receives JSON in return.

The PASS24 login API calls its login property `email`, but its value must be the account phone number. Keep all credentials in a local file referenced by `PASS24_ENV_FILE`; never commit it.
