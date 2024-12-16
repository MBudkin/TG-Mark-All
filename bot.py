# bot.py
import logging
import os
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler,
    filters, ChatMemberHandler
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Group, Member
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import datetime
import pytz
from dotenv import load_dotenv

# Загрузка конфигураций из .env файла
load_dotenv()

# Получение настроек из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
TIMEZONE = os.getenv('TIMEZONE', 'UTC')

# Проверка наличия обязательных конфигураций
if not BOT_TOKEN:
    raise ValueError("Отсутствует токен бота (BOT_TOKEN) в конфигурационном файле .env.")

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Создание базы данных
engine = create_engine('sqlite:///bot.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Часовой пояс для планировщика
try:
    TIMEZONE = pytz.timezone(TIMEZONE)
except pytz.UnknownTimeZoneError:
    logger.warning(f"Неизвестный часовой пояс '{TIMEZONE}'. Используется UTC.")
    TIMEZONE = pytz.utc

# Глобальный список триггерных слов
TRIGGER_WORDS = []

async def get_bot_username(bot):
    """
    Получает уникальное имя бота.
    """
    try:
        me = await bot.get_me()
        return f"@{me.username}" if me.username else ""
    except Exception as e:
        logger.error(f"Ошибка при получении имени бота: {e}")
        return ""

async def is_user_admin(bot, chat_id, user_id):
    """
    Проверяет, является ли пользователь администратором или создателем чата.

    :param bot: Экземпляр бота
    :param chat_id: ID чата (группы)
    :param user_id: ID пользователя
    :return: True, если пользователь администратор или создатель, иначе False
    """
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in ['administrator', 'creator']
    except Exception as e:
        logger.error(f"Ошибка при проверке статуса администратора для пользователя {user_id} в чате {chat_id}: {e}")
        return False

# Функция старта
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TRIGGER_WORDS
    bot = context.bot
    bot_username = await get_bot_username(bot)
    if not bot_username:
        await update.message.reply_text("Не удалось определить имя бота. Пожалуйста, убедитесь, что бот имеет username.")
        return

    # Добавляем в список триггеров имя бота, @all и @everyone
    TRIGGER_WORDS = [bot_username.lower(), "@all", "@everyone"]

    start_message = (
        "Привет!\n"
        "Я бот для упоминания всех участников группы.\n\n"
        f"Бот {bot_username} помогает упоминать всех участников группы при использовании {', '.join(TRIGGER_WORDS)}.\n\n"
        f"Как использовать {bot_username}:\n"
        "- Добавьте бота в группу.\n"
        "- Убедитесь, что бот имеет права читать сообщения и отправлять сообщения.\n"
        f"- Введите {', '.join(TRIGGER_WORDS)} в сообщении, чтобы бот упомянул всех участников."
    )
    await update.message.reply_text(start_message)

# Обработка команды /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != 'private':
        await update.message.reply_text("Эта команда доступна только в личном чате с ботом.")
        return  # Игнорировать команды вне личного чата

    help_text = (
        "Команды бота:\n"
        "/start - Запустить бота и показать приветственное сообщение\n"
        "/help - Показать справку\n"
        "/groups - Показать группы, где вы администратор\n"
        "/members <Group_ID> - Показать список участников группы\n"
        "/set_expiration_days <Group_ID> <дней> - Установить дни до удаления неактивных участников из базы\n"
        "/del_member <Telegram_ID> <Group_ID> - Удалить участника из базы данных\n"
        "/update - Обновить список участников вручную по всем группам\n"
    )
    await update.message.reply_text(help_text)

# Обработка команды /groups
async def groups_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != 'private':
        await update.message.reply_text("Эта команда доступна только в личном чате с ботом.")
        return  # Игнорировать команды вне личного чата

    user_id = update.effective_user.id
    bot = context.bot

    session = Session()
    try:
        groups = session.query(Group).all()
        admin_groups = []
        for group in groups:
            is_admin = await is_user_admin(bot, group.telegram_id, user_id)
            if is_admin:
                admin_groups.append(group)

        if not admin_groups:
            await update.message.reply_text("Вы не являетесь администратором ни одной группы.")
            return

        message_lines = ["<b>Ваши группы:</b>"]
        for group in admin_groups:
            message_lines.append(f"<b>ID:</b> <code>{group.telegram_id}</code> | <b>Название:</b> {group.name or 'Без названия'}")

        message_text = "\n".join(message_lines)
        await update.message.reply_text(message_text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Ошибка при выполнении команды /groups: {e}")
        await update.message.reply_text("Произошла ошибка при получении списка групп.")
    finally:
        session.close()

# Обработка команды /members <Group_ID>
async def members_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != 'private':
        await update.message.reply_text("Эта команда доступна только в личном чате с ботом.")
        return  # Игнорировать команды вне личного чата

    if len(context.args) != 1:
        await update.message.reply_text("Использование: /members <Group_ID>")
        return

    try:
        group_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Неверный формат Group_ID. Пожалуйста, введите числовой ID группы.")
        return

    user_id = update.effective_user.id
    bot = context.bot

    session = Session()
    try:
        group = session.query(Group).filter(Group.telegram_id == group_id).first()
        if not group:
            await update.message.reply_text("Группа с таким ID не найдена в базе данных.")
            return

        # Проверка, является ли пользователь администратором этой группы
        is_admin = await is_user_admin(bot, group.telegram_id, user_id)
        if not is_admin:
            await update.message.reply_text("Вы не являетесь администратором этой группы.")
            return

        members = session.query(Member).filter(Member.group_id == group.id).all()
        if not members:
            await update.message.reply_text("В базе данных нет участников этой группы.")
            return

        message_lines = [f"<b>Список участников группы '{group.name or 'Без названия'}':</b>"]
        now = datetime.datetime.utcnow()
        for member in members:
            last_active = member.last_active.strftime('%Y-%m-%d %H:%M:%S UTC')
            days_since_last_active = (now - member.last_active).days
            expiration_days = group.expiration_days
            days_until_deletion = max(expiration_days - days_since_last_active, 0)
            username = f"@{member.username}" if member.username else "Не указан"
            member_info = (
                f"<b>ID:</b> <code>{member.telegram_id}</code>\n"
                f"<b>Имя:</b> {member.full_name or 'Без имени'}\n"
                f"<b>Username:</b> {username}\n"
                f"<b>Последняя активность:</b> {last_active}\n"
                f"<b>Дней до удаления из базы:</b> {days_until_deletion}"
            )
            message_lines.append("\n---\n" + member_info)

        message_text = "\n".join(message_lines)
        # Разбиваем на части при необходимости
        if len(message_text) > 4096:
            for chunk in [message_text[i:i+4000] for i in range(0, len(message_text), 4000)]:
                await update.message.reply_text(chunk, parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(message_text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Ошибка при выполнении команды /members: {e}")
        await update.message.reply_text("Произошла ошибка при получении списка участников.")
    finally:
        session.close()

# Обработка команды /set_expiration_days <Group_ID> <дней>
async def set_expiration_days_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != 'private':
        await update.message.reply_text("Эта команда доступна только в личном чате с ботом.")
        return  # Игнорировать команды вне личного чата

    if len(context.args) != 2:
        await update.message.reply_text("Использование: /set_expiration_days <Group_ID> <дней>")
        return

    try:
        group_id = int(context.args[0])
        new_days = int(context.args[1])
        if new_days <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректные числовые значения для Group_ID и дней (положительное число).")
        return

    user_id = update.effective_user.id
    bot = context.bot

    session = Session()
    try:
        group = session.query(Group).filter(Group.telegram_id == group_id).first()
        if not group:
            await update.message.reply_text("Группа с таким ID не найдена в базе данных.")
            return

        # Проверка, является ли пользователь администратором этой группы
        is_admin = await is_user_admin(bot, group.telegram_id, user_id)
        if not is_admin:
            await update.message.reply_text("Вы не являетесь администратором этой группы.")
            return

        old_days = group.expiration_days
        group.expiration_days = new_days
        session.commit()

        await update.message.reply_text(
            f"Количество дней до удаления участников из базы успешно изменено с {old_days} на {new_days} дней для группы '{group.name or 'Без названия'}'."
        )
    except Exception as e:
        logger.error(f"Ошибка при выполнении команды /set_expiration_days: {e}")
        await update.message.reply_text("Произошла ошибка при установке дней до удаления из базы.")
    finally:
        session.close()

# Обработка команды /del_member <Telegram_ID> <Group_ID>
async def del_member_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != 'private':
        await update.message.reply_text("Эта команда доступна только в личном чате с ботом.")
        return  # Игнорировать команды вне личного чата

    if len(context.args) != 2:
        await update.message.reply_text("Использование: /del_member <Telegram_ID> <Group_ID>")
        return

    try:
        target_id = int(context.args[0])
        group_id = int(context.args[1])
    except ValueError:
        await update.message.reply_text("Неверный формат. Пожалуйста, введите числовые значения для Telegram_ID и Group_ID.")
        return

    user_id = update.effective_user.id
    bot = context.bot

    session = Session()
    try:
        group = session.query(Group).filter(Group.telegram_id == group_id).first()
        if not group:
            await update.message.reply_text("Группа с таким ID не найдена в базе данных.")
            return

        # Проверка, является ли пользователь администратором этой группы
        is_admin = await is_user_admin(bot, group.telegram_id, user_id)
        if not is_admin:
            await update.message.reply_text("Вы не являетесь администратором этой группы.")
            return

        member = session.query(Member).filter(Member.telegram_id == target_id, Member.group_id == group.id).first()
        if not member:
            await update.message.reply_text(f"Участник с ID <code>{target_id}</code> не найден в группе '{group.name or 'Без названия'}'.")
            return

        session.delete(member)
        session.commit()
        await update.message.reply_text(
            f"Участник {member.full_name or 'без имени'} (ID: <code>{target_id}</code>) успешно удалён из группы '{group.name or 'Без названия'}'.",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Ошибка при выполнении команды /del_member: {e}")
        await update.message.reply_text("Произошла ошибка при удалении участника из базы.")
    finally:
        session.close()

# Обработка команды /update
async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != 'private':
        await update.message.reply_text("Эта команда доступна только в личном чате с ботом.")
        return  # Игнорировать команды вне личного чата

    user_id = update.effective_user.id
    bot = context.bot

    session = Session()
    try:
        groups = session.query(Group).all()
        admin_groups = []
        for group in groups:
            is_admin = await is_user_admin(bot, group.telegram_id, user_id)
            if is_admin:
                admin_groups.append(group)

        if not admin_groups:
            await update.message.reply_text("Вы не являетесь администратором ни одной группы.")
            return

        await update.message.reply_text("Начинаю обновление участников для ваших групп...")

        for group in admin_groups:
            try:
                # Исправляем метод: теперь get_chat_member_count
                members_count = await bot.get_chat_member_count(chat_id=group.telegram_id)

                if members_count > 200:
                    logger.info(f"Группа {group.telegram_id} слишком большая для ручного обновления.")
                    await update.message.reply_text(f"Группа '{group.name or 'Без названия'}' слишком большая для ручного обновления.")
                    continue

                # Получаем всех участников группы
                members = []
                async for member in bot.get_chat_members(chat_id=group.telegram_id):
                    members.append(member.user)

                active_ids = set()
                for user in members:
                    active_ids.add(user.id)
                    db_member = session.query(Member).filter(Member.telegram_id == user.id, Member.group_id == group.id).first()
                    if not db_member:
                        db_member = Member(
                            telegram_id=user.id,
                            username=user.username,
                            first_name=user.first_name,
                            last_name=user.last_name,
                            full_name=f"{user.first_name or ''} {user.last_name or ''}".strip(),
                            last_active=datetime.datetime.utcnow(),
                            group=group
                        )
                        session.add(db_member)
                    else:
                        db_member.username = user.username
                        db_member.first_name = user.first_name
                        db_member.last_name = user.last_name
                        db_member.full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
                        db_member.last_active = datetime.datetime.utcnow()
                session.commit()

                # Удаление неактивных участников из базы
                deleted = session.query(Member).filter(
                    Member.group_id == group.id,
                    Member.telegram_id.notin_(active_ids)
                ).delete(synchronize_session=False)
                if deleted:
                    logger.info(f"Удалено {deleted} неактивных участников из группы {group.telegram_id}.")
                    await update.message.reply_text(f"Удалено {deleted} неактивных участников из группы '{group.name or 'Без названия'}'.")
                else:
                    await update.message.reply_text(f"В группе '{group.name or 'Без названия'}' нет неактивных участников для удаления из базы.")
                session.commit()
            except AttributeError as ae:
                logger.error(f"Ошибка при обновлении группы {group.telegram_id}: {ae}")
                await update.message.reply_text(f"Произошла ошибка при обновлении группы '{group.name or 'Без названия'}'. Проверьте права бота.")
            except Exception as e:
                logger.error(f"Ошибка при обновлении группы {group.telegram_id}: {e}")
                await update.message.reply_text(f"Произошла ошибка при обновлении группы '{group.name or 'Без названия'}'.")
    
        await update.message.reply_text("Обновление участников завершено.")
    except Exception as e:
        logger.error(f"Ошибка при выполнении команды /update: {e}")
        await update.message.reply_text("Произошла ошибка при обновлении участников.")
    finally:
        session.close()

# Обработка сообщений для отслеживания участников и реакции на триггеры
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if message.chat.type not in ['group', 'supergroup']:
        return  # Игнорировать личные сообщения

    session = Session()
    try:
        # Получение или создание записи группы
        group = session.query(Group).filter(Group.telegram_id == message.chat.id).first()
        if not group:
            group = Group(telegram_id=message.chat.id, name=message.chat.title)
            session.add(group)
            session.commit()

        # Обновление информации об отправителе
        user = message.from_user
        member = session.query(Member).filter(Member.telegram_id == user.id, Member.group_id == group.id).first()
        if not member:
            member = Member(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                full_name=f"{user.first_name or ''} {user.last_name or ''}".strip(),
                last_active=datetime.datetime.utcnow(),
                group=group
            )
            session.add(member)
        else:
            member.username = user.username
            member.first_name = user.first_name
            member.last_name = user.last_name
            member.full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
            member.last_active = datetime.datetime.utcnow()
        session.commit()

        # Проверяем наличие любого триггерного слова
        if not TRIGGER_WORDS:
            # Если список триггерных слов еще не инициализирован, получаем имя бота
            bot = context.bot
            bot_username = await get_bot_username(bot)
            if bot_username:
                TRIGGER_WORDS.extend([bot_username.lower(), "@all", "@everyone"])
            else:
                logger.warning("Не удалось инициализировать триггерные слова из-за отсутствия имени бота.")

        text_lower = message.text.lower()
        if any(trigger in text_lower for trigger in TRIGGER_WORDS):
            members = session.query(Member).filter(Member.group_id == group.id).all()
            if not members:
                await message.reply_text("Нет участников для упоминания.")
                return

            mentions = []
            for m in members:
                if m.username:
                    mentions.append(f"@{m.username}")
                else:
                    mentions.append(f"[{m.full_name or 'User'}](tg://user?id={m.telegram_id})")
            mention_text = ', '.join(mentions)
            await message.reply_text(mention_text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
    finally:
        session.close()

# Обработчик обновлений участников
async def chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.chat_member
    user = result.new_chat_member.user
    chat = update.effective_chat

    session = Session()
    try:
        group = session.query(Group).filter(Group.telegram_id == chat.id).first()
        if not group:
            group = Group(telegram_id=chat.id, name=chat.title)
            session.add(group)
            session.commit()

        if result.new_chat_member.status in ['member', 'administrator', 'creator']:
            # Добавление или обновление участника
            member = session.query(Member).filter(Member.telegram_id == user.id, Member.group_id == group.id).first()
            if not member:
                member = Member(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    full_name=f"{user.first_name or ''} {user.last_name or ''}".strip(),
                    last_active=datetime.datetime.utcnow(),
                    group=group
                )
                session.add(member)
            else:
                member.username = user.username
                member.first_name = user.first_name
                member.last_name = user.last_name
                member.full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
                member.last_active = datetime.datetime.utcnow()
            session.commit()
        else:
            # Удаление участника
            session.query(Member).filter(Member.telegram_id == user.id, Member.group_id == group.id).delete()
            session.commit()
    except Exception as e:
        logger.error(f"Ошибка при обновлении участника: {e}")
    finally:
        session.close()

# Функция удаления неактивных участников из базы с учетом expiration_days
def remove_inactive_members():
    session = Session()
    try:
        groups = session.query(Group).all()
        now = datetime.datetime.utcnow()
        total_deleted = 0

        for group in groups:
            cutoff_date = now - datetime.timedelta(days=group.expiration_days)
            inactive_members = session.query(Member).filter(
                Member.group_id == group.id,
                Member.last_active < cutoff_date
            ).all()

            for member in inactive_members:
                logger.info(f"Удаление неактивного участника: {member.full_name} (ID: {member.telegram_id}) из группы ID: {group.telegram_id}")
                session.delete(member)
                total_deleted += 1

        session.commit()
        if total_deleted:
            logger.info(f"Удалено {total_deleted} неактивных участников из всех групп.")
    except Exception as e:
        logger.error(f"Ошибка при удалении неактивных участников из базы: {e}")
    finally:
        session.close()

# Функция обновления участников группы (оптимизирована для минимизации API-запросов)
async def update_members(application_bot):
    session = Session()
    try:
        # Получаем все группы из базы данных
        groups = session.query(Group).all()
        for group in groups:
            try:
                # Получаем количество участников в группе
                members_count = await application_bot.get_chat_member_count(chat_id=group.telegram_id)

                # Ограничение для небольших групп
                # Для больших групп рекомендуется полагаться на события обновления участников
                if members_count > 200:
                    logger.info(f"Группа {group.telegram_id} слишком большая для ручного обновления.")
                    continue

                # Получаем всех участников группы
                members = []
                async for member in application_bot.get_chat_members(chat_id=group.telegram_id):
                    members.append(member.user)

                active_ids = set()
                for user in members:
                    active_ids.add(user.id)
                    db_member = session.query(Member).filter(Member.telegram_id == user.id, Member.group_id == group.id).first()
                    if not db_member:
                        db_member = Member(
                            telegram_id=user.id,
                            username=user.username,
                            first_name=user.first_name,
                            last_name=user.last_name,
                            full_name=f"{user.first_name or ''} {user.last_name or ''}".strip(),
                            last_active=datetime.datetime.utcnow(),
                            group=group
                        )
                        session.add(db_member)
                    else:
                        db_member.username = user.username
                        db_member.first_name = user.first_name
                        db_member.last_name = user.last_name
                        db_member.full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
                        db_member.last_active = datetime.datetime.utcnow()
                session.commit()

                # Удаление неактивных участников из базы
                deleted = session.query(Member).filter(
                    Member.group_id == group.id,
                    Member.telegram_id.notin_(active_ids)
                ).delete(synchronize_session=False)
                if deleted:
                    logger.info(f"Удалено {deleted} неактивных участников из группы {group.telegram_id}.")
                session.commit()
            except AttributeError as ae:
                logger.error(f"Ошибка при обновлении группы {group.telegram_id}: {ae}")
            except Exception as e:
                logger.error(f"Ошибка при обновлении группы {group.telegram_id}: {e}")
    except Exception as e:
        logger.error(f"Ошибка при обновлении участников: {e}")
    finally:
        session.close()

# Планировщик задач
def start_scheduler(application):
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(
        update_members,
        IntervalTrigger(hours=24, timezone=TIMEZONE),  # Ежедневно
        args=[application.bot],
        id='update_members_job',
        replace_existing=True
    )
    scheduler.add_job(
        remove_inactive_members,
        IntervalTrigger(days=1, timezone=TIMEZONE),  # Ежедневно
        id='remove_inactive_members_job',
        replace_existing=True
    )
    scheduler.start()
    logger.info("Планировщик задач запущен.")

# Основная функция запуска бота
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("groups", groups_command))
    application.add_handler(CommandHandler("members", members_command))
    application.add_handler(CommandHandler("set_expiration_days", set_expiration_days_command))
    application.add_handler(CommandHandler("del_member", del_member_command))
    application.add_handler(CommandHandler("update", update_command))

    # Обработчик сообщений для отслеживания участников и реакции на триггеры
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Обработчик обновлений участников
    application.add_handler(ChatMemberHandler(chat_member_update, ChatMemberHandler.CHAT_MEMBER))

    # Планировщик задач
    start_scheduler(application)

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()