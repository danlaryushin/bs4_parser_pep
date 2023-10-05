![python](https://img.shields.io/badge/python-222324?style=for-the-badge&logo=python&logoColor=yellow)
![beautifulsoup4](https://img.shields.io/badge/beautifulsoup4-222324?style=for-the-badge&logo=jekyll&logoColor=)
![Prettytable](https://img.shields.io/badge/-Prettytable-222324?style=for-the-badge)
![Logging](https://img.shields.io/badge/-Logging-222324?style=for-the-badge)

# Проект парсинга PEP

## Описание проекта

Парсер имеет 4 режима работы:
- Whats New
- Latest Version
- Download
- PEP

## Перечень технологий
- Python
- BeautifulSoup4
- PrettyTable
- Logging

## Инструкции по запуску
Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/danlaryushin/bs4_parser_pep.git
```

```
cd bs4_parser_pep
```

Cоздать и активировать виртуальное окружение:

```
python -m venv env
```

```
source venv/Scripts/activate
```

Обновить менеджер пакетов pip и установить зависимости из файла requirements.txt:

```
python -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

## Примеры команд
Выведет справку по использованию
```
python main.py pep -h
```

Создаст csv файл с таблицей из двух колонок: «Статус» и «Количество»:
```
python main.py pep -o file
```

Выводит таблицу prettytable с тремя колонками: "Ссылка на документацию", "Версия", "Статус":
```
python main.py latest-versions -o pretty 
```

Выводит ссылки в консоль на нововведения в python:
```
python main.py whats-new
```

## Автор

[Даниил Ларюшин](https://github.com/danlaryushin)

