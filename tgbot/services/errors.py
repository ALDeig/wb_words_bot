class ErrorBadRequestMPStats(Exception):
    pass


class ErrorAuthenticationMPStats(Exception):
    pass


class WBAuthorizedError(Exception):
    """Ошибка авторизации в личном кабинете WB"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class WBUpdateNameError(Exception):
    """Ошибка при изменении имени в карточке WB"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)