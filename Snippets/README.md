# Snippets

ПР № 3.1. API для фрагментов кода на Django REST framework с подсветкой синтаксиса.

## Локальный запуск

Из папки `Snippets` в PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py createsuperuser
.\.venv\Scripts\python manage.py runserver 8090
```

Открой [API](http://127.0.0.1:8090/). Для создания и редактирования сниппетов используй кнопку входа в интерфейсе.

| Адрес | Назначение |
| --- | --- |
| `/` | Корень API |
| `/snippets/` | Список и создание сниппетов |
| `/snippets/<id>/` | Просмотр, изменение и удаление сниппета |
| `/snippets/<id>/highlight/` | HTML с подсветкой кода |
| `/users/`, `/users/<id>/` | Пользователи и ссылки на их сниппеты |

Гость может читать сниппеты. Вошедший пользователь может создавать сниппеты, а редактировать и удалять их может владелец.

Тесты запускаются командой `python manage.py test` из активированного окружения.

## PythonAnywhere

В Bash-консоли клонируй репозиторий и подготовь окружение. Замени `username` в домене на своё имя.

```bash
git clone https://github.com/yukokurose/oop-practice.git
cd ~/oop-practice/Snippets
python3.12 -m venv ~/.virtualenvs/snippets
source ~/.virtualenvs/snippets/bin/activate
python -m pip install -r requirements.txt
umask 077
python -c 'import secrets; print(secrets.token_urlsafe(64))' > ~/.snippets-secret
export SNIPPETS_SECRET_KEY="$(cat ~/.snippets-secret)"
export SNIPPETS_DEBUG=0
export SNIPPETS_ALLOWED_HOSTS=username.pythonanywhere.com
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

Во вкладке **Web** создай приложение через **Manual configuration**, выбери Python 3.12 и укажи virtualenv `/home/username/.virtualenvs/snippets`. В WSGI-файл добавь:

```python
import os
import sys
from pathlib import Path

home = Path("/home/username")
sys.path.insert(0, str(home / "oop-practice" / "Snippets"))
os.environ["DJANGO_SETTINGS_MODULE"] = "tutorial.settings"
os.environ["SNIPPETS_DEBUG"] = "0"
os.environ["SNIPPETS_SECRET_KEY"] = (home / ".snippets-secret").read_text().strip()
os.environ["SNIPPETS_ALLOWED_HOSTS"] = "username.pythonanywhere.com"

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
```

В **Static files** добавь URL `/static/` и папку `/home/username/oop-practice/Snippets/staticfiles`. Включи **Force HTTPS**, нажми **Reload** и открой свой домен через HTTPS.
