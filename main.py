import dotenv
import os
import requests
import telegram
import logging


logging.basicConfig(filename="bot.log", level=logging.INFO)
logger = logging.getLogger('logger')


def send_message(tg_chat, bot, messages):
    for message in messages:
        if message["is_negative"]:
            result = "\nК сожалению, в работе нашлись ошибки."
        else:
            result = (
                "\nПреподавателю всё понравилось, можно приступать к следубщему уроку!"
            )
        bot.send_message(
            text="""Преподаватель проверил работу - "{0}"!\n{1}
        {2}""".format(
                message["lesson_title"], message["lesson_url"], result
            ),
            chat_id=tg_chat,
        )
        logger.info("Отправлено сообщение")


def get_reviews(dvmn_token, tg_chat, bot):
    payload = {"timestamp_to_request": ""}
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
            logger.info(response.json())
            if dvmn_response["status"] == "found":
                payload = {"timestamp": dvmn_response["last_attempt_timestamp"]}
                messages = dvmn_response["new_attempts"]
                send_message(tg_chat, bot, messages)
                logger.info(messages)
            elif dvmn_response["status"] == "timeout":
                payload = {"timestamp": dvmn_response["timestamp_to_request"]}
                logger.info("Таймаут, перезапуск с меткой- {0}".format(dvmn_response["timestamp_to_request"]))

        except requests.exceptions.ReadTimeout:
            logger.exception("Перезапуск")
        except requests.exceptions.ConnectionError:
            logger.exception("Нет соединения, переподключение.")


def main():
    dotenv.load_dotenv()
    dvmn_token = os.getenv("DVMN_TOKEN")
    tg_token = os.getenv("TG_TOKEN")
    tg_chat = os.getenv("TG_CHAT")
    bot = telegram.Bot(token=tg_token)
    get_reviews(dvmn_token, tg_chat, bot)


if __name__ == "__main__":
    main()
