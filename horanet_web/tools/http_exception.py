from werkzeug.exceptions import HTTPException


class ApplicationError(HTTPException):
    code = 440
    description = "<p>Application error</p>"
    _name = "Application Error"

    @HTTPException.name.getter
    def name(self):
        return self._name

    def __init__(self, description=None):
        """Surcharge."""
        HTTPException.__init__(self, description)
