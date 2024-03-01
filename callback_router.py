import calendar
import datetime
import logging

import aiogram
import pytz
from aiogram import Router, F, types, Dispatcher
from aiogram.enums import ContentType
from aiogram.filters.callback_data import CallbackData
import time
import config
import keyboards
import methods
import routers
from config import months
import sqlite3
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc
from aiogram.types import InlineKeyboardMarkup
from factories import *
from methods import galochka_date_change, send_testing_message

router = Router()
con = sqlite3.connect("database.db", timeout=30)
cursor = con.cursor()
await_time = False


@router.callback_query(DateCallbackFactory.filter(F.action == "set_date"))
async def send_random_value(callback: types.CallbackQuery, callback_data: DateCallbackFactory):
    return_keyboard = callback.message.reply_markup
    cursor.execute(f"UPDATE users_data set test_status=1, await_time=1 where user_id={callback.from_user.id}")
    con.commit()
    return_keyboard = galochka_date_change(callback=callback, callback_data=callback_data,
                                           return_keyboard=return_keyboard)
    try:
        await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[]))
        await callback.message.edit_text(text=f"Дата выполнения задания: {callback_data.day}.{callback_data.month}"
                                              f".{callback_data.year}")
    except Exception:
        print("Клавиатура не изменена")
    await callback.message.answer(f"Выберите удобное время  🕗"
                                  f"\nИли напишите своё время", reply_markup=keyboards.get_times(callback))
    await callback.answer()


@router.callback_query(F.data == "nothing")
async def nothing(callback: types.CallbackQuery):
    await callback.answer()


@router.callback_query(DateCallbackFactory.filter(F.action == "month"))
async def month(callback: types.CallbackQuery, callback_data: DateCallbackFactory):
    try:
        await callback.message.edit_reply_markup(reply_markup=keyboards.get_calendar(year=callback_data.year,
                                                                                     month=callback_data.month,
                                                                                     message=callback))
    except Exception:
        logging.error("Month select error")
    await callback.answer()


# @router.callback_query(TimeCallbackFactory.filter(F.action == "times"))
# async def times(callback: types.CallbackQuery, callback_data: TimeCallbackFactory):
#     return_keyboard = callback.message.reply_markup
#     # for row in range(len(callback.message.reply_markup.inline_keyboard)):
#     #     for data in range(len(callback.message.reply_markup.inline_keyboard[row])):
#     #         # if callback.message.reply_markup.inline_keyboard[row][data].text == "✅":
#     #         #     return_keyboard.inline_keyboard[row][data].text = str(caldr[row-1][data])
#     #
#     #         if callback.message.reply_markup.inline_keyboard[row][data].text == f"{callback_data.hour}:{callback_data.minute}0":
#     #             print("Edited", callback.message.reply_markup.inline_keyboard[row][data].text, callback_data.hour,
#     #                   callback_data.minute)
#     #             user_config = (f"{callback_data.hour}:{callback_data.minute}0", callback.from_user.id)
#     #             cursor.execute("UPDATE users_data SET time=? WHERE user_id=?", user_config)
#     #             con.commit()
#     #             return_keyboard.inline_keyboard[row][data].text = "✅"
#     cursor.execute(f"SELECT time FROM users_data WHERE user_id = {callback.from_user.id}")
#     row = cursor.fetchall()
#     return_keyboard = galochka_time_change(callback, callback_data, return_keyboard, row[0][0])
#     try:
#         await callback.message.edit_reply_markup(reply_markup=return_keyboard)
#         await callback.answer()
#     except Exception:
#         print("eroro")


@router.callback_query(TimeCallbackFactory.filter(F.action == "times"))
async def times(callback: types.CallbackQuery, callback_data: TimeCallbackFactory):
    return_keyboard = keyboards.get_times(callback)
    correct_time = f"{callback_data.hour}:{callback_data.minute}0"
    # correct_time = f"20:24"
    user_config = (correct_time, callback.from_user.id)
    cursor.execute("UPDATE users_data SET time=? WHERE user_id=?", user_config)
    con.commit()
    for row in range(len(callback.message.reply_markup.inline_keyboard)):
        for data in range(len(callback.message.reply_markup.inline_keyboard[row])):
            # if callback.message.reply_markup.inline_keyboard[row][data].text == "✅":
            #     return_keyboard.inline_keyboard[row][data].text = str(caldr[row-1][data])

            if callback.message.reply_markup.inline_keyboard[row] \
                    [data].text == f"{callback_data.hour}:{callback_data.minute}0":
                print("Edited", callback.message.reply_markup.inline_keyboard[row][data].text, callback_data.hour,
                      callback_data.minute)
                cursor.execute("UPDATE users_data SET time=?, test_status=1 WHERE user_id=?",
                               (f"{callback_data.hour}:{callback_data.minute}0", callback.from_user.id))
                con.commit()
                cursor.execute(f"SELECT date, time FROM users_data WHERE user_id = {callback.from_user.id}")
                row_db = cursor.fetchall()
                if row_db != [] and row_db[0][0] is not None and row_db[0][1] is not None:
                    date_to = datetime.datetime.strptime(row_db[0][0].split(" ")[0] + " " + row_db[0][1] +
                                                         ":00", '%Y-%m-%d %H:%M:%S')
                else:
                    print("No datetime in database")
                    return callback.message.answer(text="Произошла ошибка")
                if config.DEV_MODE:
                    date_now = datetime.datetime.now()
                    date_to = datetime.datetime(year=date_now.year, month=date_now.month, day=date_now.day,
                                                hour=date_now.hour, minute=date_now.minute)
                    date_to += datetime.timedelta(minutes=1)
                    timed = datetime.time(hour=date_to.hour, minute=date_to.minute).strftime("%H:%M")
                    cursor.execute(f"update users_data set date=?, time=?"
                                   f" where user_id={callback.from_user.id}",
                                   (date_to, f"{timed}"))
                    con.commit()

                scheduler = AsyncIOScheduler(timezone="Asia/Almaty")
                try:
                    scheduler.remove_all_jobs()
                    scheduler.shutdown()
                except:
                    print("schedulers shutdown error")
                scheduler.add_job(send_testing_message, trigger='date', run_date=date_to,
                                  kwargs={"callback": callback})
                scheduler.add_job(send_testing_message, trigger='date',
                                  run_date=str(date_to + config.exam_times["send_notification"]),
                                  kwargs={"callback": callback})
                scheduler.add_job(send_testing_message, trigger='date', run_date=str(date_to +
                                                                                     config.exam_times["duration"]),
                                  kwargs={"callback": callback})
                scheduler.start()

                return_keyboard.inline_keyboard[row][data].text = "✅"
    try:
        await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[]))
        await callback.message.edit_text(text=f"Вы выбрали время: {callback_data.hour}:{callback_data.minute}0")
    except Exception:
        print("keyboard not modified")
    cursor.execute(f"SELECT date, time FROM users_data WHERE user_id = {callback.from_user.id}")
    row_db = cursor.fetchall()
    await callback.answer()
    dates = row_db[0][0].split(' ')[0].split('-')
    date = f"{dates[2]}.{dates[1]}.{dates[0]}"
    await callback.message.answer(text="Ура! Вы назначили себе задание! 🙂"
                                       "\n"
                                       f"\nДата: {date}"
                                       f"\nВремя: {row_db[0][1]}"
                                       "\nВремя на выполнение: 4 часа"
                                       "\n"
                                       "\nТеперь ожидайте задание 🙂",
                                  reply_markup=keyboards.main_actions(message=callback, add_remove_exam=
                                  routers.exist_datetime(callback.from_user.id)))


@router.callback_query(F.data == "back_to_date")
async def month(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[]))
    await callback.message.edit_text(text="Вы вернулись назад  ◀️")
    await callback.message.answer(
        f"Выберите удобную дату  📅",
        reply_markup=keyboards.get_calendar(2024, 2, callback)
    )
    await callback.answer()


@router.message(F.text)
async def format_time(message: types.Message):
    cursor.execute(f"select test_status from users_data where user_id={message.from_user.id}")
    if methods.is_status_active(message, remove_none=True):
        time = datetime.datetime.strptime(message.text, "%H:%M")
        cursor.execute(f"UPDATE users_data SET time='{time.strftime('%H:%M')}', test_status=1 WHERE user_id={message.from_user.id}")
        con.commit()
        cursor.execute(f"SELECT date, time FROM users_data WHERE user_id = {message.from_user.id}")
        row_db = cursor.fetchone()
        print(row_db)
        if row_db != [] and row_db[0][0] is not None and row_db[0][1] is not None:
            date_to = datetime.datetime.strptime(row_db[0].split(" ")[0] + " " + time.strftime('%H:%M'), '%Y-%m-%d %H:%M')
        scheduler = AsyncIOScheduler(timezone="Asia/Almaty")
        try:
            scheduler.remove_all_jobs()
            scheduler.shutdown()
        except:
            print("schedulers shutdown error")
        scheduler.add_job(send_testing_message, trigger='date', run_date=date_to,
                          kwargs={"message": message})
        scheduler.add_job(send_testing_message, trigger='date',
                          run_date=str(date_to + config.exam_times["send_notification"]),
                          kwargs={"message": message})
        scheduler.add_job(send_testing_message, trigger='date', run_date=str(date_to +
                                                                             config.exam_times["duration"]),
                          kwargs={"message": message})
        scheduler.start()
        cursor.execute(f"SELECT date, time FROM users_data WHERE user_id = {message.from_user.id}")
        row_db = cursor.fetchall()
        dates = row_db[0][0].split(' ')[0].split('-')
        date = f"{dates[2]}.{dates[1]}.{dates[0]}"
        await message.answer(text="Ура! Вы назначили себе задание! 🙂"
                                  "\n"
                                  f"\nДата: {date}"
                                  f"\nВремя: {row_db[0][1]}"
                                  "\nВремя на выполнение: 4 часа"
                                  "\n"
                                  "\nТеперь ожидайте задание 🙂",
                             reply_markup=keyboards.main_actions(message=message,
                                                                 add_remove_exam=
                                                                 routers.exist_datetime(message.from_user.id)))