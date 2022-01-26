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
        logger.info("Отправлено сообщение")


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
            logger.info(dvmn_response)
            if dvmn_response["status"] == "found":
                payload = {"timestamp": dvmn_response["last_attempt_timestamp"]}
                messages = dvmn_response["new_attempts"]
                send_message(tg_chat, bot, messages)
                logger.info(messages)
            elif dvmn_response["status"] == "timeout":
                payload = {"timestamp": dvmn_response["timestamp_to_request"]}
                logger.info(
                    "Таймаут, перезапуск с меткой- {0}".format(
                        dvmn_response["timestamp_to_request"]
                    )
                )

        except requests.exceptions.ReadTimeout:
            logger.exception("Перезапуск")
        except requests.exceptions.ConnectionError:
            time.sleep(10)
            logger.exception("Нет соединения, переподключение.")


def main():
    logging.basicConfig(filename="bot.log", level=logging.INFO)
    dotenv.load_dotenv()
    dvmn_token = os.environ["DVMN_TOKEN"]
    tg_token = os.environ["TG_TOKEN"]
    tg_chat = os.environ["TG_CHAT"]
    bot = telegram.Bot(token=tg_token)
    get_reviews(dvmn_token, tg_chat, bot)


if __name__ == "__main__":
    main()
