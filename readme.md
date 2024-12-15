
# TG-Mark-All

## Overview

**TG-Mark-All** is a Telegram bot based on Python, designed to tag all members in a group using keywords like the bot's username, "@all," or "@everyone."

## Features

- **Start and Help Commands**: Initialize the bot and access a list of available commands.
- **Group Management**: View and manage groups where you have administrative privileges.
- **Member Tracking**: Monitor and display group members, including their activity status.
- **Automatic Inactive Member Removal**: Automatically remove members who have been inactive for a specified number of days.
- **Mass Mentioning**: Mention all group members using trigger words.
- **Manual Update**: Manually refresh the member list for your groups.
- **Database Integration**: Utilizes SQLite with SQLAlchemy for efficient data management.
- **Scheduled Tasks**: Uses APScheduler to handle periodic tasks like updating members and removing inactive users.


## Usage

Once the bot is running, you can interact with it using the following commands in Telegram. Ensure that the bot is added to your groups and has the necessary permissions to read and send messages.

### Available Commands

- **`/start`**: Initializes the bot and displays a welcome message.
- **`/help`**: Provides a list of available commands and their descriptions.
- **`/groups`**: Displays the groups where you have administrative privileges.
- **`/members <Group_ID>`**: Shows the list of members in the specified group.
- **`/set_expiration_days <Group_ID> <days>`**: Sets the number of days before inactive members are removed.
- **`/del_member <Telegram_ID> <Group_ID>`**: Removes a specific member from the group's database.
- **`/update`**: Manually updates the member list for all your groups.

## Install

Ниже представлена полная пошаговая инструкция по установке и настройке Telegram-бота **TG-Mark-All** на чистой системе Linux (Debian/Ubuntu). Инструкция включает установку всех необходимых пакетов, клонирование репозитория, настройку окружения и создание службы Systemd для автоматического запуска бота при старте системы.

---

## Шаг 1: Обновление системы

Сначала обновим список пакетов и установим обновления для текущих пакетов.

```bash
sudo apt update && sudo apt upgrade -y
```

## Шаг 2: Установка необходимых зависимостей

Установим все необходимые пакеты, включая Python 3, `pip`, `git` и другие зависимости.

```bash
sudo apt install -y python3 python3-pip python3-venv git
```

## Шаг 3: Клонирование репозитория бота

Перейдите в директорию, где вы хотите разместить файлы бота. Например, в `/opt`.

```bash
cd /opt
```

Клонируем репозиторий:

```bash
git clone https://github.com/MBudkin/TG-Mark-All.git
```

Перейдите в директорию проекта:

```bash
cd TG-Mark-All
```

## Шаг 4: Создание виртуального окружения и установка зависимостей

Создадим виртуальное окружение для изоляции зависимостей проекта.

```bash
python3 -m venv venv
```

Активируем виртуальное окружение:

```bash
source venv/bin/activate
```

Установим необходимые пакеты из `requirements.txt`:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Шаг 5: Настройка конфигурационных файлов

### 5.1 Создание файла `.env`

Создайте файл `.env` в корневой директории проекта:

```bash
nano .env
```

Вставьте следующее содержимое, заменив `YOUR_BOT_TOKEN` на токен вашего Telegram-бота:

```env
# .env

# Токен вашего Telegram бота
BOT_TOKEN=YOUR_BOT_TOKEN

# Часовой пояс для планировщика (например, Europe/Moscow)
TIMEZONE=Europe/Moscow

# Другие настройки можно добавить здесь
```

Сохраните файл и выйдите из редактора (`Ctrl + O`, затем `Ctrl + X` в nano).

### 5.2 Проверка и настройка других файлов

Убедитесь, что файлы `bot.py`, `models.py` и другие необходимые файлы находятся в директории проекта и настроены правильно. Если вы клонировали репозиторий, это должно быть выполнено автоматически.

## Шаг 6: Тестовый запуск бота

Прежде чем настраивать службу Systemd, протестируйте запуск бота вручную.

Убедитесь, что виртуальное окружение активировано:

```bash
source venv/bin/activate
```

Запустите бота:

```bash
python3 bot.py
```

Если бот запускается без ошибок, можно перейти к следующему шагу. Для остановки бота нажмите `Ctrl + C`.

## Шаг 7: Создание службы Systemd для автоматического запуска бота

### 7.1 Создание файла службы

Создайте файл службы Systemd. Для этого используем текстовый редактор, например, `nano`.

```bash
sudo nano /etc/systemd/system/tg-mark-all.service
```

Вставьте следующее содержимое, заменив пути в соответствии с вашим расположением проекта (предполагается, что проект находится в `/opt/TG-Mark-All`):

```ini
[Unit]
Description=TG-Mark-All Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/TG-Mark-All
Environment="PATH=/opt/TG-Mark-All/venv/bin"
ExecStart=/opt/TG-Mark-All/venv/bin/python3 bot.py
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

**Пояснения к параметрам:**

- **Description**: Описание службы.
- **After**: Зависимость от сетевых служб.
- **User**: Пользователь, от имени которого будет запускаться служба (в данном случае `root`).
- **WorkingDirectory**: Рабочая директория проекта.
- **Environment**: Указание пути к виртуальному окружению.
- **ExecStart**: Команда для запуска бота.
- **Restart** и **RestartSec**: Автоматический перезапуск службы при сбое.
- **WantedBy**: Определяет, когда служба должна быть запущена.

Сохраните файл и выйдите из редактора (`Ctrl + O`, затем `Ctrl + X` в nano).

### 7.2 Перезагрузка демонa Systemd и запуск службы

Перезагрузим демон Systemd, чтобы он распознал новую службу.

```bash
sudo systemctl daemon-reload
```

Запустим службу:

```bash
sudo systemctl start tg-mark-all.service
```

Проверим статус службы:

```bash
sudo systemctl status tg-mark-all.service
```

Вы должны увидеть что-то похожее на:

```
● tg-mark-all.service - TG-Mark-All Telegram Bot
     Loaded: loaded (/etc/systemd/system/tg-mark-all.service; enabled; vendor preset: enabled)
     Active: active (running) since ...
   Main PID: 12345 (python3)
      Tasks: 3 (limit: 4915)
     Memory: 50.0M
     CGroup: /system.slice/tg-mark-all.service
             └─12345 /opt/TG-Mark-All/venv/bin/python3 bot.py
```

### 7.3 Автозапуск службы при старте системы

Включим автозапуск службы при загрузке системы:

```bash
sudo systemctl enable tg-mark-all.service
```

## Шаг 8: Управление службой

### 8.1 Остановка службы

```bash
sudo systemctl stop tg-mark-all.service
```

### 8.2 Перезапуск службы

```bash
sudo systemctl restart tg-mark-all.service
```

### 8.3 Просмотр логов службы

Для просмотра логов бота используйте `journalctl`:

```bash
sudo journalctl -u tg-mark-all.service -f
```

Флаг `-f` позволяет следить за логами в реальном времени.

## Шаг 9: Дополнительные рекомендации

### 9.1 Обновление кода бота

Если вы вносите изменения в код бота или обновляете репозиторий, выполните следующие шаги:

1. Остановите службу:

    ```bash
    sudo systemctl stop tg-mark-all.service
    ```

2. Перейдите в директорию проекта и обновите код:

    ```bash
    cd /opt/TG-Mark-All
    git pull origin main
    ```

3. Установите новые зависимости (если они появились):

    ```bash
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
    ```

4. Запустите службу снова:

    ```bash
    sudo systemctl start tg-mark-all.service
    ```

### 9.2 Безопасность

Хотя вы запускаете бота от имени `root`, рекомендуется создать отдельного пользователя для запуска бота для повышения безопасности.

Создайте пользователя `tgbot`:

```bash
sudo adduser --system --no-create-home tgbot
```

Измените файл службы `/etc/systemd/system/tg-mark-all.service`, заменив `User=root` на `User=tgbot` и установив соответствующие права на директорию проекта:

```bash
sudo chown -R tgbot:tgbot /opt/TG-Mark-All
```

Отредактируйте файл службы:

```bash
sudo nano /etc/systemd/system/tg-mark-all.service
```

Измените строку `User=root` на `User=tgbot`.

Сохраните файл, перезагрузите демон и перезапустите службу:

```bash
sudo systemctl daemon-reload
sudo systemctl restart tg-mark-all.service
```

## Шаг 10: Проверка работы бота

Убедитесь, что бот работает корректно:

1. Откройте Telegram и найдите вашего бота.
2. Отправьте команду `/start` и убедитесь, что бот отвечает приветственным сообщением.
3. Проверьте функциональность бота в группах, где он добавлен.

---

Поздравляю! Вы успешно установили и настроили Telegram-бота **TG-Mark-All** на вашей системе Linux. Теперь бот будет автоматически запускаться при каждом старте системы и работать в фоновом режиме. Не забывайте периодически проверять логи службы для отслеживания состояния бота и возможных ошибок.
