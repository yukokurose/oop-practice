# Design.pro

ПР № 2.1. Главная, регистрация и вход в личный кабинет.

ПР № 2.2. Выход, создание заявки, список своих заявок с фильтром и удаление новой заявки.

## Запуск

```powershell
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8089
```

[Главная](http://localhost:8089/) · [Админка](http://localhost:8089/superadmin/)

Для локальной проверки админки выполни `python manage.py create_demo_admin`.
Логин и пароль из ТЗ — `admin` и `admin`.

Тесты — `python manage.py test`.
