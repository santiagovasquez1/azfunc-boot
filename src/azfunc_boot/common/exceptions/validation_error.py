class ValidationError(Exception):
    def __init__(self, message="Error de validación de datos"):
        super().__init__(message)