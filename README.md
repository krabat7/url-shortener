# URL Shortener API

Простой API-сервис для сокращения ссылок. Поддерживает регистрацию пользователей, генерацию коротких ссылок, статистику по переходам и управление своими ссылками.

## Демо

Сервис развернут на Render:
**[https://url-shortener-4an4.onrender.com/docs](https://url-shortener-4an4.onrender.com/docs)**

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

---

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
  "expires_at": "2025-12-31T23:59:59"
}
```

---

## Инструкция по запуску локально

### 1. Клонирование репозитория
```bash
git clone https://github.com/your-username/url-shortener.git
cd url-shortener
```

### 2. Установка зависимостей
```bash
python -m venv venv
source venv/bin/activate  # или Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Настройка окружения

Создайте `.env` файл в корне и укажите:

```
DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
```

### 4. Инициализация БД
```bash
alembic upgrade head
```

### 5. Запуск приложения
```bash
uvicorn app.main:app --reload
```

Документация будет доступна по адресу:
```
http://127.0.0.1:8000/docs
```

---

## Структура базы данных

**Таблица `users`**
- `id` — уникальный идентификатор пользователя
- `email` — почта пользователя (уникальна)
- `hashed_password` — захешированный пароль

**Таблица `links`**
- `id` — уникальный идентификатор ссылки
- `original_url` — оригинальный длинный URL
- `short_code` — сгенерированный или пользовательский короткий код (уникален)
- `created_at` — дата создания ссылки
- `expires_at` — дата, после которой ссылка считается истекшей
- `click_count` — количество переходов по ссылке
- `last_click` — дата последнего перехода
- `user_id` — внешний ключ на таблицу `users`, связывает ссылку с её владельцем