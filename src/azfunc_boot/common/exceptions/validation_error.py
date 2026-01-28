class ValidationError(Exception):
    def __init__(self, message="Data validation error"):
        super().__init__(message)