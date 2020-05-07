"""Initialize onvif."""
import zeep

from onvif.client import ONVIFService, ONVIFCamera, SERVICES
from onvif.exceptions import (
    ONVIFError,
    ERR_ONVIF_UNKNOWN,
    ERR_ONVIF_PROTOCOL,
    ERR_ONVIF_WSDL,
    ERR_ONVIF_BUILD,
)


def zeep_pythonvalue(self, xmlvalue):
    """Monkey patch zeep."""
    return xmlvalue


# pylint: disable=no-member
zeep.xsd.simple.AnySimpleType.pythonvalue = zeep_pythonvalue

__all__ = (
    "ONVIFService",
    "ONVIFCamera",
    "ONVIFError",
    "ERR_ONVIF_UNKNOWN",
    "ERR_ONVIF_PROTOCOL",
    "ERR_ONVIF_WSDL",
    "ERR_ONVIF_BUILD",
    "SERVICES",
)
