# Domjudge tool web

Domjudge 線上程式評分系統輔助工具 網頁版

## 當前功能

- 帳號管理
- 題庫管理
    - 題目打包(.zip)

## 安裝

### 準備

#### Windows

- Git for Windows(Git Bash)
- Python 3.8
    - [pipenv](https://pipenv.pypa.io/en/latest/)
    
```bash
$ py -m pip install -U pipenv
or 
$ python -m pip install -U pipenv
```

#### MacOS/Linux

- Git
- Python 3.8
    - [pipenv](https://pipenv.pypa.io/en/latest/)

### 使用

> Windows open Git Bash
> MacOS/Linux open terminal
```bash
$ git clone https://github.com/ntub/domjudge-tool-web.git
```

```bash
$ cd domjudge-tool-web
$ pipenv install --dev
# Create new python venv and install python packages
$ py -m pipenv install --dev
# for Windows
$ python -m pipenv install --dev

```

```bash
$ pipenv shell
# active virtualenv
$ py -m pipenv shell
# for Windows
$ python -m pipenv shell

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

(venv)$ python manage.py runserver
# Control + C can exit
(venv)$ winpty python manage.py runserver
# for Windows git bash
```

#### Web GUI

1. Open [http://localhost:8000/admin/](http://localhost:8000/admin/) from browser
2. Login your super user account

## Feature

- 線上網頁服務
- 匯入帳號功能