from zeep.exceptions import Fault  # noqa: F401
from zeep.exceptions import ValidationError  # noqa: F401


class ONVIFError(Exception):
    """Base type for all ONVIF errors."""
