class NotUpdates(Exception):
    """Вызывается в случае, если нет обновлений по проверке дз."""

    pass


class NotFirstApiException(Exception):
    """Вызывается при не первом появлении ошибки с API."""

    pass


class MessageException(Exception):
    """Вызывается при проблемах с отправкой сообщений."""

    pass


class UncorrectStatus(Exception):
    """Вызывается при проблемах с отправкой сообщений."""

    pass
