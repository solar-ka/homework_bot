import logging
import os
import time
import sys

import requests
import telegram
from dotenv import load_dotenv
from exceptions import NotFirstApiException, NotUpdates, MessageException

load_dotenv()
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
    handlers=[logging.StreamHandler(sys.stdout)],
)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет сообщение."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except MessageException as error:
        logging.error(f'Ошибка при отправке сообщения: {error}')
    else:
        logging.info(f'Бот отправил сообщение: "{message}"')


def get_api_answer(current_timestamp):
    """Делает запрос к API яндекс-практикума."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=params)
    count_exeptions = 0
    if homework_statuses.status_code != 200:
        count_exeptions += 1
        if count_exeptions != 1:
            raise NotFirstApiException(
                'Ошибка при запросе к основному API: ',
                f'status_code={homework_statuses.status_code}'
            )
        else:
            raise Exception(
                'Ошибка при запросе к основному API: ',
                f'status_code={homework_statuses.status_code}'
            )
    else:
        logging.info(f'Выполнен запрос к API с параметрами: {params} ')
        return homework_statuses.json()


def check_response(response):
    """Проверяет, что ответ API содержит ключ homeworks."""
    if not isinstance(response, dict):
        raise TypeError(f'response не является словарём: response={response}')
    else:
        homeworks = response.get('homeworks')
    if homeworks is None:
        raise KeyError('Ответ API не содержит ключа "homeworks"')
    elif not isinstance(homeworks, list):
        raise TypeError(
            f'homeworks не является списком: homeworks={homeworks}'
        )
    else:
        logging.info('Ответ API содержит ключ homeworks')
        return homeworks


def parse_status(homework):
    """Определяет статус проверки конкретной домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_name is None:
        raise KeyError(
            'Домашняя работа не содержит необходимого ключа homework_name'
        )
    if homework_status is None:
        raise KeyError(
            'Домашняя работа не содержит необходимого ключа homework_status'
        )
    else:
        logging.info(
            'Домашняя работа содержит необходимые ключи: ',
            f'homework_name={homework_name}, homework_status={homework_status}'
        )
        if homework_status not in HOMEWORK_STATUSES:
            raise Exception(
                'Статус проверки работы не соответствует ожиданиям: ',
                f'неизвестный статус{homework_status}'
            )
        else:
            verdict = HOMEWORK_STATUSES[homework_status]
            logging.info(f'Изменился статус домашней работы: {verdict}')
            result = (
                f'Изменился статус проверки работы "{homework_name}".'
                + f'{verdict}'
            )
            return result


def check_tokens():
    """Проверяет наличие всех переменных окружения."""
    tokens_ok = True
    if not PRACTICUM_TOKEN:
        logging.critical('Отсутствует переменная окружения PRACTICUM_TOKEN')
        tokens_ok = False
    if not TELEGRAM_TOKEN:
        logging.critical('Отсутствует переменная окружения TELEGRAM_TOKEN')
        tokens_ok = False
    if not TELEGRAM_CHAT_ID:
        logging.critical('Отсутствует переменная окружения TELEGRAM_CHAT_ID')
        tokens_ok = False
    if not tokens_ok:
        logging.critical('Программа принудительно остановлена.')
    return tokens_ok


def main():
    """Основная логика работы бота."""
    if not check_tokens:
        sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response['current_date']
            homeworks = check_response(response)
            if len(homeworks) != 0:
                homework = homeworks[0]
                message = parse_status(homework)
            else:
                raise NotUpdates('Список обновлений домашних работ пустой')

        except (MessageException, NotFirstApiException) as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            time.sleep(RETRY_TIME)

        except NotUpdates as error:
            logging.debug(error)
            time.sleep(RETRY_TIME)

        except (TypeError, KeyError, Exception) as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            send_message(bot, message)
            time.sleep(RETRY_TIME)

        else:
            send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
