from werkzeug.exceptions import HTTPException


class DeviceNotFound(HTTPException):
    code = 441
    description = "<p>The device doesn't exist</p>"
    _name = "Device Not Found"

    @HTTPException.name.getter
    def name(self):
        return self._name

    def __init__(self, description=None):
        """Surcharge."""
        HTTPException.__init__(self, description)


class ActionNotFound(HTTPException):
    code = 442
    description = "<p>The Action doesn't exist</p>"
    _name = "Action Not Found"

    @HTTPException.name.getter
    def name(self):
        return self._name

    def __init__(self, description=None):
        """Surcharge."""
        HTTPException.__init__(self, description)


class TagNotFound(HTTPException):
    code = 443
    description = "<p>Tag unrecognized</p>"
    _name = "Tag Not Found"

    @HTTPException.name.getter
    def name(self):
        return self._name

    def __init__(self, description=None):
        """Surcharge."""
        HTTPException.__init__(self, description)


class CheckPointError(HTTPException):
    code = 444
    description = "Checkpoint error"
    _name = "Check point error"

    @HTTPException.name.getter
    def name(self):
        return self._name

    def __init__(self, description=None):
        """Surcharge."""
        HTTPException.__init__(self, description)


class SectorError(HTTPException):
    code = 445
    description = "<p>Activity sector error</p>"
    _name = "Sector not found"

    @HTTPException.name.getter
    def name(self):
        return self._name

    def __init__(self, description=None):
        """Surcharge."""
        HTTPException.__init__(self, description)
