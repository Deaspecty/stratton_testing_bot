import datetime
import logging
import coloredlogs
import pytz
import tzlocal
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import methods
from methods import exist_datetime, send_testing_message
import config
from config import con
import keyboards

router = Router()
# con = sqlite3.connect("database.db", timeout=30)
cursor = con.cursor(buffered=True)
coloredlogs.install()


@router.message(Command("start"))
async def start(message: Message):
    await message.answer(
        f"Приветствую @{message.from_user.username}🙂🤝🏼 "
        f"\nЯ бот компании Stratton.kz"
        f"\nПомогу тебе получить практическое задание 👇",
        reply_markup=keyboards.main_actions(message=message, add_remove_exam=exist_datetime(message.from_user.id))
    )


@router.message(F.text == "Главная")
async def start(message: Message):
    await message.answer(
        f"Приветствую @{message.from_user.username}🙂🤝🏼 "
        f"\nЯ бот компании Stratton.kz"
        f"\nПомогу тебе получить практическое задание 👇",
        reply_markup=keyboards.main_actions(message=message, add_remove_exam=exist_datetime(message.from_user.id))
    )


@router.message(F.text == "Подробная информация")
async def info(message: Message):
    await message.answer(
        f"🏬  Компания Stratton.kz"
        f"\n"
        f"\n🤖  Мы разрабатываем чат-боты Telegram для бизнеса. Наши боты сделаны не на конструкторах, а пишутся с нуля."
        f"\n"
        f"\n🤖  Мы разрабатываем чат-боты Instagram для бизнеса. Автоматизируйте общение с клиентами и улучшайте "
        f"продажи в Instagram. Просто и удобно."
        f"\n"
        f"\n🤖  Роботизация бизнес-процессов избавляет от рутины и выгорания сотрудников, повышает точность и "
        f"скорость выполнения операций."
        f"\n"
        f"\n📈  Повысьте узнаваемость своих услуг и продуктов с помощью удобного сайта.",
        reply_markup=keyboards.main_actions(message=message, add_remove_exam=exist_datetime(message.from_user.id))
    )


@router.message(F.text == "Контакты")
async def info(message: Message):
    await message.answer(
        f"Для связи с нами пишите ✍️"
        f"\n@strattonautomation",
        reply_markup=keyboards.main_actions(message=message, add_remove_exam=exist_datetime(message.from_user.id))
    )


@router.message(F.text == "Записаться на тестирование")
async def info(message: Message):
    if methods.get_test_status(message) in [1, None]:
        today = datetime.datetime.now()
        await message.answer(
            f"Выберите удобную дату: 📅",
            reply_markup=keyboards.get_calendar(today.year, today.month, message)
        )
        # except Exception:
        #     print("Error 4444")
    elif methods.get_test_status(message) in [2, 3, 4]:
        await message.answer("Нельзя перезаписать начавшееся тестирование. ❌")
    elif methods.get_test_status(message) in [5, 6]:
        await message.answer(
            f"Тестирование было пройдено."
            f"\n"
            f"\nПо вопросам пересдачи пишите ✍️"
            f"\n@strattonautomation",
        )


@router.message(F.text == "Юху")
async def info(message: Message):
    await message.answer(
        f"Юхууу",
        reply_markup=keyboards.main_actions(message=message, add_remove_exam=exist_datetime(message.from_user.id))
    )


@router.message(F.text == "Отменить тестирование")
async def add_remove_exam(message: Message):
    try:
        if methods.get_test_status(message) == 1:
            cursor.execute(f"UPDATE users_data SET date=NULL, time=NULL, test_status=NULL "
                           f"WHERE user_id={message.from_user.id}")
            con.commit()
            return await message.answer(text="Ваше тестирование удалено. ❌",
                                        reply_markup=keyboards.main_actions(message=message,
                                                                            add_remove_exam=exist_datetime(
                                                                                message.from_user.id)))
        elif methods.get_test_status(message) in [2, 3, 4]:
            return await message.answer(text="Нельзя отменить начавшееся тестирование. ❌",
                                        reply_markup=keyboards.main_actions(message=message,
                                                                            add_remove_exam=exist_datetime(
                                                                                message.from_user.id)))
        elif methods.get_test_status(message) in [5, 6]:
            return await message.answer(text="Нельзя отменить пройденное тестирование. ❌",
                                        reply_markup=keyboards.main_actions(message=message,
                                                                            add_remove_exam=exist_datetime(
                                                                                message.from_user.id)))
    except Exception:
        return await message.answer(text="Не удалось удалить тестирование.",
                                    reply_markup=keyboards.main_actions(message=message, add_remove_exam=exist_datetime(
                                        message.from_user.id)))


@router.message(Command("remake"))
async def start(message: Message):
    try:
        if config.DEV_MODE:
            cursor.execute(f"DELETE FROM users_data")
            con.commit()
            logging.info("DB remaked")
            await message.answer(text="АНИГИЛЯЦИЯ УСПЕШНА",
                                 reply_markup=keyboards.main_actions(message=message, add_remove_exam=exist_datetime(
                                     message.from_user.id)))
    except Exception:
        logging.error("Remake error")


@router.message(F.video)
async def video(message: Message):
    if methods.get_test_status(message) in [2, 3]:
        cursor.execute(f"SELECT date, time FROM users_data WHERE user_id = {message.from_user.id}")
        row_db = cursor.fetchall()
        date_to = datetime.datetime.strptime(row_db[0][0].split(" ")[0] + " " + row_db[0][1], '%Y-%m-%d %H:%M')
        now = datetime.datetime.now()
        video_format = message.video.mime_type.lower()
        print(video_format)
        if message.video.duration > 40:
            return await message.reply("Извините, видео должно быть не более 40 секунд. 🕗")
        print("Видео весит = ", message.video.file_size)
        if message.video.file_size > 10485760:  # 10 МБ в байтах
            return await message.reply("Извините, видео должно весить не более 10МБ. 💾")
        if not (video_format in ["video/mp4", "video/quicktime"]):
            return await message.reply("Извините, формат видео недопустим. Только видео с расширением .mov или .mp4 ")
        if date_to < now < date_to + config.exam_times["duration"]:  # or config.DEV_MODE:
            await message.send_copy(message.from_user.id,
                                    reply_markup=keyboards.keyboard_is_exam_complete(from_who=0,
                                                                                     sender=message.from_user.id))
            con.commit()
    elif methods.get_test_status(message) in [5, 6]:
        await message.answer("Вы отправили видео не в срок! ⌛️")
    elif methods.get_test_status(message) == 4:
        await message.answer("Вы уже отправили тестирование! ❌")


@router.message(F.text)
async def format_time(message: Message):
    cursor.execute(f"select test_status from users_data where user_id={message.from_user.id}")
    if methods.get_test_status(message) == 1:
        for time_format in ["%H:%M", "%H %M", "%H-%M", "%H.%M"]:
            try:
                time = datetime.datetime.strptime(message.text, time_format)
                await methods.appoint_test(message, time)
            except ValueError:
                pass
    elif methods.get_test_status(message) in [2, 3]:
        print("WHAT?  ", " " in "@ asdbot")
        if (message.text.startswith("@") and message.text.endswith("bot") and not (" " in message.text)) or \
                (message.text.startswith("https://t.me/") and message.text.endswith("bot") and
                 not (" " in message.text)):
            cursor.execute(f"SELECT date, time FROM users_data WHERE user_id = {message.from_user.id}")
            row_db = cursor.fetchall()
            date_to = datetime.datetime.strptime(row_db[0][0].split(" ")[0] + " " + row_db[0][1], '%Y-%m-%d %H:%M')
            now = datetime.datetime.now()
            if date_to < now < date_to + config.exam_times["duration"]:  # or config.DEV_MODE:
                await message.send_copy(message.from_user.id,
                                        reply_markup=keyboards.keyboard_is_exam_complete(from_who=0,
                                                                                         sender=message.from_user.id))

        else:
            return await message.reply("Это не похоже на ссылку на бота.")
    elif methods.get_test_status(message) == 4:
        await message.answer("Вы уже отправили тестирование! ❌")
