from cgitb import text
from plistlib import FMT_BINARY
import time
import dotenv
import os
import requests
import telegram
import logging


logger = logging.getLogger("logger")




def send_message(tg_chat, bot, messages):
    for message in messages:
        if message["is_negative"]:
            result = "\nК сожалению, в работе нашлись ошибки."
        else:
            result = (
                "\nПреподавателю всё понравилось, можно приступать к следубщему уроку!"
            )
        bot.send_message(
            text=f"""Преподаватель проверил работу - "{message["lesson_title"]}"!\n{message["lesson_url"]}
        {result}""",
            chat_id=tg_chat,
        )
        logger.info("Отправлено сообщение с результатом проверки работы!")


def get_reviews(dvmn_token, tg_chat, bot):
    payload = None
    while True:
        try:
            response = requests.get(
                "https://dvmn.org/api/long_polling/",
                headers={"Authorization": dvmn_token},
                params=payload,
                timeout=140,
            )
            response.raise_for_status()
            dvmn_response = response.json()
            logger.info('Получен ответ от dvmn.org')
            if dvmn_response["status"] == "found":
                payload = {"timestamp": dvmn_response["last_attempt_timestamp"]}
                messages = dvmn_response["new_attempts"]
                logger.info('Найден новый результат проверки!')
                send_message(tg_chat, bot, messages)
            elif dvmn_response["status"] == "timeout":
                payload = {"timestamp": dvmn_response["timestamp_to_request"]}
                logger.info(
                    "Таймаут, перезапуск с меткой- {0}".format(
                        dvmn_response["timestamp_to_request"]
                    )
                )

        except requests.exceptions.ReadTimeout:
            logger.exception("Перезапуск по таймауту.", exc_info=False)

        except requests.exceptions.ConnectionError:
            time.sleep(10)
            logger.exception("Нет соединения с сетью, переподключение.", exc_info=False)


def main():
    formatter = logging.Formatter("%(asctime)s - %(module)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s")
    logger.setLevel('INFO')
    dotenv.load_dotenv()
    dvmn_token = os.environ["DVMN_TOKEN"]
    tg_token = os.environ["TG_TOKEN"]
    tg_chat = os.environ["TG_CHAT"]
    bot = telegram.Bot(token=tg_token)
    class MyLogsHandler(logging.Handler):
        def emit(self, record):
            log_entry = self.format(record)
            bot.send_message(chat_id=tg_chat, text=log_entry)
    tg_logger = MyLogsHandler()
    tg_logger.setLevel(logging.INFO)
    tg_logger.setFormatter(formatter)
    logger.addHandler(tg_logger)
    logger.info('Бот запущен')
    get_reviews(dvmn_token, tg_chat, bot)


if __name__ == "__main__":
    main()
