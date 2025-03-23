# URL Shortener API

Простой API-сервис для сокращения ссылок. Поддерживает регистрацию пользователей, генерацию коротких ссылок, статистику по переходам и управление своими ссылками.

## Описание API

### Аутентификация
- `POST /auth/register` — регистрация пользователя.
- `POST /auth/login` — получение JWT токена.

### Работа со ссылками
- `POST /links/shorten` — создание короткой ссылки.
- `GET /{short_code}` — переход по короткой ссылке.
- `GET /links/{short_code}/stats` — получение статистики по ссылке.
- `PUT /links/{short_code}` — обновление оригинального URL.
- `DELETE /links/{short_code}` — удаление ссылки.
- `GET /links/search?original_url=...` — поиск ссылки по оригинальному URL.
- `GET /links/expired` — просмотр всех истёкших ссылок.
- `DELETE /links/cleanup?days=N` — удаление неиспользуемых ссылок старше N дней.

### Авторизация
Для защищённых эндпоинтов используется JWT токен (Bearer).  
Полученный токен необходимо указать в Swagger UI через кнопку "Authorize" или передавать в заголовке:

```
Authorization: Bearer <your_token>
```

## Примеры запросов

### Регистрация пользователя
```json
POST /auth/register
{
  "email": "test@example.com",
  "password": "qwerty123"
}
```

### Логин
```json
POST /auth/login
username: test@example.com
password: qwerty123
```

### Создание ссылки
```json
POST /links/shorten
{
  "original_url": "https://example.com",
  "custom_alias": "example123",
  "expires_at": "2025-03-01T23:59:59"
}
```

## Инструкция по запуску

### 1. Клонирование репозитория
```bash
git clone https://github.com/your-username/url-shortener.git
cd url-shortener
```

### 2. Установка зависимостей
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Настройка окружения

Создайте `.env` файл в корне и укажите:

```
DATABASE_URL=<url>
REDIS_URL=<url>
SECRET_KEY=<key>
```

### 4. Создание таблиц (через Alembic)
```bash
alembic upgrade head
```

### 5. Запуск приложения
```bash
uvicorn app.main:app --reload
```

Приложение будет доступно по адресу:
```
http://127.0.0.1:8000/docs
```