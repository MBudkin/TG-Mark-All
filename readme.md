
# Telegram Group Management Bot

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Navigate to the Project Directory](#2-navigate-to-the-project-directory)
  - [3. Set Up a Virtual Environment](#3-set-up-a-virtual-environment)
  - [4. Install Dependencies](#4-install-dependencies)
- [Configuration](#configuration)
  - [1. Create a Telegram Bot](#1-create-a-telegram-bot)
  - [2. Set Up Environment Variables](#2-set-up-environment-variables)
- [Running the Bot](#running-the-bot)
- [Setting Up the Bot to Run on System Startup](#setting-up-the-bot-to-run-on-system-startup)
  - [1. Create a Systemd Service File](#1-create-a-systemd-service-file)
  - [2. Enable and Start the Service](#2-enable-and-start-the-service)
  - [3. Verify the Service Status](#3-verify-the-service-status)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Acknowledgements](#acknowledgements)

## Overview

The **Telegram Group Management Bot** is a Python-based Telegram bot designed to help administrators manage their Telegram groups efficiently. It offers functionalities such as tracking group members, managing inactive users, and facilitating mass mentions using trigger words like the bot's username, `@all`, or `@everyone`.

## Features

- **Start and Help Commands**: Initialize the bot and access a list of available commands.
- **Group Management**: View and manage groups where you have administrative privileges.
- **Member Tracking**: Monitor and display group members, including their activity status.
- **Automatic Inactive Member Removal**: Automatically remove members who have been inactive for a specified number of days.
- **Mass Mentioning**: Mention all group members using trigger words.
- **Manual Update**: Manually refresh the member list for your groups.
- **Database Integration**: Utilizes SQLite with SQLAlchemy for efficient data management.
- **Scheduled Tasks**: Uses APScheduler to handle periodic tasks like updating members and removing inactive users.

## Prerequisites

Before installing and running the bot, ensure that your system meets the following requirements:

- **Operating System**: Linux (Debian/Ubuntu recommended)
- **Python**: Version 3.7 or higher
- **Git**: For cloning the repository
- **Telegram Account**: To create and manage your bot

## Installation

Follow the steps below to install and set up the Telegram Group Management Bot on your Linux system.

### 1. Clone the Repository

First, clone the repository to your local machine using Git:

```bash
git clone https://github.com/MBudkin/TG-Mark-All.git
```

### 2. Navigate to the Project Directory

Change your current directory to the project's root directory:

```bash
cd TG-Mark-All
```

### 3. Set Up a Virtual Environment

It's recommended to use a Python virtual environment to manage dependencies. You can create and activate a virtual environment using the following commands:

```bash
# Create a virtual environment named 'venv'
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate
```

*After activation, your terminal prompt should be prefixed with `(venv)`.*

### 4. Install Dependencies

Install the required Python packages using `pip`:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This command installs all the packages listed in the `requirements.txt` file, including `python-dotenv` for environment variable management.

## Configuration

Proper configuration is essential for the bot to function correctly. Follow the steps below to configure your bot.

### 1. Create a Telegram Bot

If you haven't already created a Telegram bot, follow these steps:

1. **Open Telegram** and search for the [@BotFather](https://t.me/BotFather).
2. **Start a conversation** with BotFather by clicking the **Start** button.
3. **Create a new bot** by sending the command:

    ```
    /newbot
    ```

4. **Follow the prompts** to set a name and username for your bot.
5. **Receive your bot token**. This token is required for configuring the bot.

### 2. Set Up Environment Variables

Create a `.env` file in the project's root directory to store your configuration settings securely.

```bash
touch .env
```

Open the `.env` file using your preferred text editor and add the following configurations:

```dotenv
# .env

# Telegram Bot Token
BOT_TOKEN=your_telegram_bot_token_here

# Timezone for the scheduler (e.g., Europe/Moscow)
TIMEZONE=UTC

# (Optional) Additional configurations can be added here
```

*Replace `your_telegram_bot_token_here` with the token you received from BotFather.*

**Important:** Ensure that the `.env` file is included in your `.gitignore` to prevent sensitive information from being pushed to GitHub.

```gitignore
# .gitignore

# Virtual Environment
venv/
__pycache__/
*.pyc

# Environment Variables
.env
```

## Running the Bot

After completing the installation and configuration steps, you can run the bot using the following command:

```bash
python bot.py
```

If everything is set up correctly, the bot will start and begin listening for commands and messages in your Telegram groups.

## Setting Up the Bot to Run on System Startup

To ensure that your bot runs continuously and starts automatically when your Linux system boots, you can set it up as a **systemd** service. Follow the steps below to configure this.

### 1. Create a Systemd Service File

Create a service file for the bot. This file tells systemd how to manage the bot process.

```bash
sudo nano /etc/systemd/system/tg-mark-all.service
```

Add the following content to the file:

```ini
[Unit]
Description=Telegram Group Management Bot
After=network.target

[Service]
# Replace '/path/to/your/project' with the actual path where TG-Mark-All is located
WorkingDirectory=/path/to/your/project/TG-Mark-All
ExecStart=/path/to/your/project/TG-Mark-All/venv/bin/python bot.py
Restart=always
User=your_username
Environment=PATH=/path/to/your/project/TG-Mark-All/venv/bin
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

**Notes:**

- **WorkingDirectory**: The directory where your `bot.py` is located.
- **ExecStart**: The command to start the bot. Ensure it points to the Python interpreter inside your virtual environment.
- **User**: The system user that will run the bot. Replace `your_username` with your actual Linux username.
- **Environment=PATH**: Ensures that the service uses the Python interpreter from your virtual environment.
- **Environment=PYTHONUNBUFFERED=1**: Prevents Python from buffering stdout and stderr, useful for logging.

**Example:**

If your project is located at `/home/your_username/TG-Mark-All`, and your virtual environment is in `venv`, the service file would look like this:

```ini
[Unit]
Description=Telegram Group Management Bot
After=network.target

[Service]
WorkingDirectory=/home/your_username/TG-Mark-All
ExecStart=/home/your_username/TG-Mark-All/venv/bin/python bot.py
Restart=always
User=your_username
Environment=PATH=/home/your_username/TG-Mark-All/venv/bin
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

### 2. Enable and Start the Service

Reload systemd to recognize the new service, enable it to start on boot, and then start the service.

```bash
# Reload systemd to pick up the new service file
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable tg-mark-all.service

# Start the service immediately
sudo systemctl start tg-mark-all.service
```

### 3. Verify the Service Status

Check the status of your bot service to ensure it's running correctly.

```bash
sudo systemctl status tg-mark-all.service
```

You should see output indicating that the service is **active (running)**.

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

### Trigger Words for Mass Mentioning

In your Telegram groups, when any of the following trigger words are used in a message, the bot will mention all group members:

- **Bot's Username** (e.g., `@YourBotUsername`)
- **`@all`**
- **`@everyone`**

**Example:**

If your bot's username is `@GroupManagerBot`, sending a message like:

```
@GroupManagerBot
```

or

```
@all
```

or

```
@everyone
```

will prompt the bot to mention all members of the group.

## Troubleshooting

If you encounter issues while setting up or running the bot, consider the following steps:

1. **Check Service Status:**

   Ensure that the systemd service is running without errors.

   ```bash
   sudo systemctl status tg-mark-all.service
   ```

2. **View Logs:**

   Access the service logs to identify any runtime errors.

   ```bash
   journalctl -u tg-mark-all.service -f
   ```

3. **Verify Environment Variables:**

   Ensure that the `.env` file contains the correct `BOT_TOKEN` and `TIMEZONE`.

4. **Check Dependencies:**

   Make sure all Python dependencies are installed correctly.

   ```bash
   pip list
   ```

5. **Permissions:**

   Verify that the user running the service has the necessary permissions to access the project directory and execute the bot.

6. **Reinstall Dependencies:**

   Sometimes, reinstalling dependencies can resolve issues.

   ```bash
   pip install --upgrade --force-reinstall -r requirements.txt
   ```

## Contributing

Contributions are welcome! If you'd like to contribute to this project, please follow these steps:

1. **Fork the Repository**

2. **Create a New Branch**

   ```bash
   git checkout -b feature/YourFeatureName
   ```

3. **Commit Your Changes**

   ```bash
   git commit -m "Add some feature"
   ```

4. **Push to the Branch**

   ```bash
   git push origin feature/YourFeatureName
   ```

5. **Open a Pull Request**

   Describe your changes and submit a pull request for review.

## Acknowledgements

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - The library used for interacting with the Telegram Bot API.
- [SQLAlchemy](https://www.sqlalchemy.org/) - For ORM and database management.
- [APScheduler](https://apscheduler.readthedocs.io/en/stable/) - For scheduling periodic tasks.
- [python-dotenv](https://github.com/theskumar/python-dotenv) - For managing environment variables.

