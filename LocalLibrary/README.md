# LocalLibrary

ПР № 1.1. Каталог местной библиотеки на Django и SQLite. [Туториал MDN](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Server-side/Django).

## Запуск в PowerShell

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe manage.py migrate
& .\.venv\Scripts\python.exe manage.py seed_catalog
& .\.venv\Scripts\python.exe manage.py runserver
```

[Каталог](http://127.0.0.1:8000/) · [Админка](http://127.0.0.1:8000/admin/)

Для входа в админку сначала создай учётную запись командой `& .\.venv\Scripts\python.exe manage.py createsuperuser`.
