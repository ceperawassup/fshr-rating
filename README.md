# 📊 fshr-rating-tracker

Система отслеживания и сравнения рейтингов ФШР юных шахматисток (2015–2017 г.р.).  
Помогает тренерам и родителям видеть прогресс, сравнивать с соперницами и анализировать личные встречи.

## 🎯 Возможности
- Импорт списков игроков из XLSX‑файлов (расширенный поиск ratings.ruchess.ru)
- Хранение истории рейтингов (классика, быстрые, блиц + ФИДЕ)
- Гибкая система тегов: `szfo`, `szfo_25_class`, `rf_26_blitz` и любые другие
- Учёт личных встреч (результаты по контролям) с отображением в таблице 🟢🟡🔴
- Расчёт **Δ** (дельты) относительно стартового рейтинга на конкретном турнире
- Цветовая индикация роста / падения рейтинга
- Фильтрация по тегам, году рождения, контролю

## 📁 Структура проекта
fsfr-rating-tracker/
├── ratings.db # база SQLite (не в Git)
├── config.py # настройки: ID дочери, даты турниров, пороги
├── import_list.py # первичный импорт всех игроков из XLSX
├── update_ratings.py # обновление рейтингов из нового XLSX
├── add_tag.py # добавить тег игрокам по списку ID
├── add_match.py # добавить личную встречу
├── import_start_snapshot.py # импорт стартовых рейтингов турнира
├── viewer.py # просмотр и сравнение (основной инструмент)
├── requirements.txt
├── README.md
└── .gitignore

## ⚙️ Установка и настройка
1. Клонируйте репозиторий:
    git clone git@github.com:ceperawassup/fsfr-rating-tracker.git
    cd fsfr-rating-tracker

2. Создайте виртуальное окружение и установите зависимости:
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
3. Скачайте XLSX‑файл с сайта ratings.ruchess.ru (расширенный поиск: пол – жен, год рождения 2015‑2017).
Поместите его в папку проекта и выполните первоначальный импорт:
    python import_list.py
4. При необходимости добавьте теги (турниры, регионы) и личные встречи – см. примеры ниже.
## 🚀 Использование
# Импорт стартовых рейтингов турнира
    python import_start_snapshot.py файл.xlsx ГГГГ-ММ-ДД {classic,rapid,blitz}
Скрипт ожидает XLSX с колонками: Ном. | Имя | ИН | Рейт.Нац. | Клуб/Город
(первые две строки – заголовки, данные с 3‑й).
Пример:
python import_start_snapshot.py rf_26_blitz_start.xlsx 2026-02-03 blitz

# Добавление тегов по списку ID
    python add_tag.py имя_тега файл_с_id.txt
Файл должен содержать по одному ФШР ID на строку. Теги можно комбинировать (через запятую).
Пример:
python add_tag.py szfo_25_class id_szfo_class.txt
# Добавление личной встречи
    python add_match.py ID_соперницы {classic,rapid,blitz} {win,draw,loss} [--date ГГГГ-ММ-ДД] [--tournament "Название"]
Пример:
python add_match.py 485118 classic win --date 2026-04-15 --tournament "СЗФО 2026"
# Просмотр и анализ – viewer.py
    python viewer.py [--tag ТЕГ] [--birth ГОД] [--sort ПОЛЕ] [--top N] [--fide] [--delta-tag ТЕГ_ДЕЛЬТЫ]
# Основные параметры viewer.py
Параметр	Описание
--tag	Фильтр по тегу (можно несколько через запятую, например --tag szfo,rf_26_class)
--birth	Год рождения или диапазон (2016 или 2015-2016)
--sort	Поле сортировки: classic_fshr, rapid_fshr, blitz_fshr
--top	Показать только N первых строк
--fide	Показать также рейтинг ФИДЕ
--delta-tag	Тег турнира, для которого рассчитать Δ (отклонение от стартового рейтинга). Дата турнира берётся из config.py
# Примеры
# Все девочки СЗФО по классике, с дельтой относительно турнира
    python viewer.py --tag szfo --sort classic_fshr --delta-tag szfo_25_class
# Топ‑10 России 2016 г.р. по блицу с приростом
    python viewer.py --tag rf_26_blitz --birth 2016 --sort blitz_fshr --delta-tag rf_26_blitz --top 10
# Участницы классики РФ с отображением рейтинга ФИДЕ
    python viewer.py --tag rf_26_class --sort classic_fshr --fide
# Параметры import_start_snapshot.py
Параметр	Описание
filename	Путь к XLSX‑файлу
date	Дата турнира (ГГГГ-ММ-ДД)
control	Контроль: classic, rapid, blitz
# Параметры add_match.py
Параметр	Обязательный	Описание
player_id	да	ФШР ID соперницы
control	да	classic, rapid, blitz
result	да	win, draw, loss
--date	нет	Дата встречи (ГГГГ-ММ-ДД)
--tournament	нет	Название турнира
# Параметры add_tag.py
Параметр	Описание
tag	Название тега (например, szfo_25_class)
ids_file	Файл со списком ФШР ID (по одному на строку)
## 📌 Примечания
База данных ratings.db и все XLSX/CSV файлы добавлены в .gitignore и не попадают в репозиторий.

Для расчёта Δ необходимо предварительно добавить даты турниров в config.py в словарь TOURNAMENT_DATES.

Цветной вывод работает в терминалах с поддержкой ANSI (Linux, macOS, Windows Terminal).

## 👤 Автор
ceperawassup – системный администратор, шахматный энтузиаст, отец юной шахматистки.
