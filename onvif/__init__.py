from onvif.client import ONVIFService, ONVIFCamera, SERVICES
from onvif.exceptions import ONVIFError, ERR_ONVIF_UNKNOWN, \
        ERR_ONVIF_PROTOCOL, ERR_ONVIF_WSDL, ERR_ONVIF_BUILD
#from onvif import cli
import zeep

# Monkey patch zeep
def zeep_pythonvalue(self, xmlvalue):
        return xmlvalue
# pylint: disable=no-member
zeep.xsd.simple.AnySimpleType.pythonvalue = zeep_pythonvalue

__all__ = ( 'ONVIFService', 'ONVIFCamera', 'ONVIFError',
            'ERR_ONVIF_UNKNOWN', 'ERR_ONVIF_PROTOCOL',
            'ERR_ONVIF_WSDL', 'ERR_ONVIF_BUILD',
            'SERVICES'#, 'cli'
           )
