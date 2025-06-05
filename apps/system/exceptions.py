class TokenExpiredException(Exception):
    def __init__(self, message="Token expired"):
        self.message = message
        super().__init__(self.message)
