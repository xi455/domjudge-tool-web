# Domjudge Tool

Domjudge 線上程式評分系統輔助工具 網頁版

## 當前功能

- 帳號管理
- 題庫管理
    - 題目打包(.zip)
- 線上網頁服務

## 安裝

### 準備

#### Windows

- Git for Windows(Git Bash)
- Python 3.8
    - [pipenv](https://pipenv.pypa.io/en/latest/)
    
```bash
$ python -m pip install -U pipenv
```

#### MacOS/Linux

- Git
- Python 3.8
    - [pipenv](https://pipenv.pypa.io/en/latest/)

### 使用

#### Online Service

[__https://hackmd.io/@biz-pg/domjudge-tool-web__](https://hackmd.io/@biz-pg/domjudge-tool-web)

#### Local Service

> Windows open Git Bash

> Mac OS/Linux open terminal
```bash
$ git clone https://github.com/ntub/domjudge-tool-web.git
```

```bash
$ cd domjudge-tool-web
$ pipenv install --dev
# Create new python venv and install python packages

# for Windows
$ python -m pipenv install --dev

```

```bash
$ pipenv shell
# active virtualenv

# for Windows
$ python -m pipenv shell

$ cp src/core/.env.example src/core/.env
$ vi src/core/.env
#SECRET_KEY=key-here
#DEBUG=on
#ALLOWED_HOSTS=*,
#DATABASE_URL=sqlite:///sqlite.db
#DJANGO_SUPERUSER_USERNAME=admin
#DJANGO_SUPERUSER_PASSWORD=admin-password

(venv)$ cd src

(venv)$ python manage.py migrate
# init local database and create db tables

(venv)$ python manage.py loaddata -i ./fixtures/groups.json
# loading init db data

(venv)$ python manage.py createsuperuser
# 使用者名稱: admin
# 電子信箱: superuser@mail.com
# Password: ***************
# Password (again): ***************
# Bypass password validation and create user anyway? [y/N]: y
# Superuser created successfully.
```

Run Server

```bash
(venv)$ cd src

(venv)$ python manage.py runserver
# Control + C can exit
(venv)$ winpty python manage.py runserver
# for Windows git bash
```

#### Web GUI

1. Open [http://localhost:8000/admin/](http://localhost:8000/admin/) from browser
2. Login your superuser account

## Feature

- 匯入帳號功能
