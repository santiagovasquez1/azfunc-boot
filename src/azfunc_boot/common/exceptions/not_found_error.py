class NotFoundError(Exception):
    def __init__(self, message="Recurso no encontrado"):
        super().__init__(message)