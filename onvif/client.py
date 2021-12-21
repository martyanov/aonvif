import datetime
import logging
import os.path

import zeep.client
import zeep.exceptions
import zeep.helpers
import zeep.proxy
import zeep.wsse.username

from . import exceptions
from . import wsdl


logger = logging.getLogger('onvif')
logging.basicConfig(level=logging.INFO)
logging.getLogger('zeep.client').setLevel(logging.CRITICAL)


def safe_func(func):
    """Ensure methods to raise an ONVIFError when something was wrong."""

    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise exceptions.ONVIFError(e)

    return wrapped


class UsernameDigestTokenDtDiff(zeep.wsse.username.UsernameToken):
    """UsernameDigestToken class, with a time offset parameter that can be adjusted.

    This allows authentication on cameras without being time synchronized.
    Please note that using NTP on both end is the recommended solution,
    this should only be used in "safe" environments.
    """

    def __init__(self, user, passw, dt_diff=None, **kwargs):
        super().__init__(user, passw, **kwargs)
        # Date/time difference in datetime.timedelta
        self.dt_diff = dt_diff

    def apply(self, envelope, headers):
        old_created = self.created
        if self.created is None:
            self.created = datetime.datetime.utcnow()
        if self.dt_diff is not None:
            self.created += self.dt_diff
        result = super().apply(envelope, headers)
        self.created = old_created
        return result


class ONVIFService:
    """Python Implemention for ONVIF Service.

    Services List:
        Analytics
        DeviceIO
        DeviceMgmt
        Events
        Imaging
        Media
        Notification
        PTZ
        PullPointSubscription
        Receiver
        Recording
        Replay
        Search
        Subscription

    There are two ways to pass parameter to services methods
    1. Dict
        params = {'Name': 'NewHostName'}
        device_service.SetHostname(params)
    2. Type Instance
        params = device_service.create_type('SetHostname')
        params.Hostname = 'NewHostName'
        device_service.SetHostname(params)

    >>> from onvif import ONVIFService
    >>> device_service = ONVIFService('http://192.168.0.112/onvif/device_service',
    ...                           'admin', 'foscam',
    ...                           '/etc/onvif/wsdl/devicemgmt.wsdl')
    >>> ret = device_service.GetHostname()
    >>> print ret.FromDHCP
    >>> print ret.Name
    >>> device_service.SetHostname(dict(Name='newhostname'))
    >>> ret = device_service.GetSystemDateAndTime()
    >>> print ret.DaylightSavings
    >>> print ret.TimeZone
    >>> dict_ret = device_service.to_dict(ret)
    >>> print dict_ret['TimeZone']
    """

    @safe_func
    def __init__(
        self,
        xaddr,
        user,
        passwd,
        url,
        binding_name,
        encrypt=True,
        dt_diff=None,
    ):
        if not os.path.isfile(url):
            raise exceptions.ONVIFError(f"{url!r} doesn't exist!")

        self.url = url
        self.xaddr = xaddr

        # Create security token
        wsse = UsernameDigestTokenDtDiff(
            user, passwd, dt_diff=dt_diff, use_digest=encrypt,
        )

        # Client settings
        settings = zeep.client.Settings()
        settings.strict = False
        settings.xml_huge_tree = True

        # Create client
        self._client = zeep.client.AsyncClient(
            wsdl=url,
            wsse=wsse,
            settings=settings,
        )

        # Create service proxy, it's a workaround as zeep still
        # doesn't support AsyncServiceProxy for AsyncClient
        binding = self._client.wsdl.bindings.get(binding_name)
        if binding is None:
            raise exceptions.ONVIFError(f'Binding was not found: {binding_name!r}')

        self._service_proxy = zeep.proxy.AsyncServiceProxy(
            self._client,
            binding,
            address=self.xaddr,
        )

        # Set soap header for authentication
        self.user = user
        self.passwd = passwd
        # Indicate wether password digest is needed
        self.encrypt = encrypt
        self.dt_diff = dt_diff

        namespace = binding_name[binding_name.find('{') + 1: binding_name.find('}')]
        available_ns = self._client.namespaces
        active_ns = (
            list(available_ns.keys())[list(available_ns.values()).index(namespace)]
            or 'ns0'
        )
        self.create_type = lambda x: self._client.get_element(active_ns + ':' + x)()

    async def close(self):
        """Close the transport session."""
        if self._client:
            await self._client.transport.aclose()

    @staticmethod
    @safe_func
    def to_dict(zeepobject):
        """Convert a WSDL Type instance into a dictionary."""
        return {} if zeepobject is None else zeep.helpers.serialize_object(zeepobject)

    def __getattr__(self, name):
        """Call the real ONVIF Service operations.

        See the official wsdl definition for the
        APIs detail(API name, request parameters,
        response parameters, parameter types, etc...)
        """

        def service_wrapper(func):
            """Wrap service call."""

            @safe_func
            def wrapped(params=None):
                def call(params=None):
                    if params is None:
                        params = {}
                    else:
                        params = ONVIFService.to_dict(params)
                    try:
                        ret = func(**params)
                    except TypeError:
                        ret = func(params)
                    return ret

                return call(params)

            return wrapped

        builtin = name.startswith('__') and name.endswith('__')
        if builtin:
            return self.__dict__[name]

        return service_wrapper(getattr(self._service_proxy, name))


class ONVIFCamera:
    """Python Implemention ONVIF compliant device.

    This class integrates onvif services.

    adjust_time parameter allows authentication on cameras without being time synchronized.
    Please note that using NTP on both end is the recommended solution,
    this should only be used in "safe" environments.
    Also, this cannot be used on AXIS camera, as every request is authenticated,
    contrary to ONVIF standard.

    >>> from onvif import ONVIFCamera
    >>> mycam = ONVIFCamera('192.168.0.112', 80, 'admin', '12345')
    >>> mycam.devicemgmt.GetServices(False)
    >>> media_service = mycam.create_media_service()
    >>> ptz_service = mycam.create_ptz_service()
    # Get PTZ Configuration:
    >>> mycam.ptz.GetConfiguration()
    # Another way:
    >>> ptz_service.GetConfiguration()
    """
    def __init__(
        self,
        host,
        port,
        user,
        passwd,
        wsdl_dir=None,
        encrypt=True,
        adjust_time=False,
    ):
        # TODO: Handle case-sensivity
        os.environ.pop('http_proxy', None)
        os.environ.pop('https_proxy', None)
        self.host = host
        self.port = int(port)
        self.user = user
        self.passwd = passwd
        self.wsdl_dir = wsdl_dir
        self.encrypt = encrypt
        self.adjust_time = adjust_time
        self.dt_diff = None
        self.xaddrs = {}

        # Active service client container
        self.services = {}

        self.to_dict = ONVIFService.to_dict

        # TODO: Better to handle with pathlib
        if self.wsdl_dir is None:
            self.wsdl_dir = os.path.join(os.path.dirname(__file__), 'wsdl')

    async def update_xaddrs(self):
        """Update xaddrs for services."""
        self.dt_diff = None
        devicemgmt = self.create_devicemgmt_service()
        if self.adjust_time:
            sys_date = await devicemgmt.GetSystemDateAndTime()
            cdate = sys_date.UTCDateTime
            cam_date = datetime.datetime(
                cdate.Date.Year,
                cdate.Date.Month,
                cdate.Date.Day,
                cdate.Time.Hour,
                cdate.Time.Minute,
                cdate.Time.Second,
            )
            self.dt_diff = cam_date - datetime.datetime.utcnow()

        # Get XAddr of services on the device
        self.xaddrs = {}
        capabilities = await devicemgmt.GetCapabilities({'Category': 'All'})
        for name in capabilities:
            capability = capabilities[name]
            try:
                if name.lower() in wsdl.SERVICES and capability is not None:
                    namespace = wsdl.SERVICES[name.lower()]['ns']
                    self.xaddrs[namespace] = capability['XAddr']
            except Exception:
                logger.exception('Unexpected service type')

    async def create_pullpoint_subscription(self):
        """Create a pullpoint subscription."""
        try:
            events = self.create_events_service()
            pullpoint = await events.CreatePullPointSubscription()

            self.xaddrs[
                'http://www.onvif.org/ver10/events/wsdl/PullPointSubscription',
            ] = pullpoint.SubscriptionReference.Address._value_1
        except zeep.exceptions.Fault:
            return False
        return True

    async def close(self):
        """Close all transports."""

        for service in self.services.values():
            await service.close()

    def get_definition(self, name, port_type=None):
        """Return xaddr and wsdl of specified service."""

        # Check if the service is supported
        if name not in wsdl.SERVICES:
            raise exceptions.ONVIFError(f'Unknown service {name!r}')

        wsdl_file = wsdl.SERVICES[name]['wsdl']
        namespace = wsdl.SERVICES[name]['ns']
        binding = wsdl.SERVICES[name]['binding']

        binding_name = f'{{{namespace}}}{binding}'

        if port_type:
            namespace += '/' + port_type

        # TODO: Cache or load asynchronously
        wsdlpath = os.path.join(self.wsdl_dir, wsdl_file)
        if not os.path.isfile(wsdlpath):
            raise exceptions.ONVIFError(f'No such file: {wsdlpath!r}')

        # XAddr for devicemgmt is fixed
        if name == 'devicemgmt':
            host = self.host
            # If scheme is missing, then treat the scheme as http://
            if not self.host.startswith('http://') or not self.host.startswith('https://'):
                host = f'http://{self.host}'

            xaddr = f'{host}:{self.port}/onvif/device_service'
            return xaddr, wsdlpath, binding_name

        # Get other XAddr
        xaddr = self.xaddrs.get(namespace)
        if not xaddr:
            raise exceptions.ONVIFError(f"Device doesn't support service: {name!r}")

        return xaddr, wsdlpath, binding_name

    def create_onvif_service(self, name, port_type=None) -> ONVIFService:
        """Create ONVIF service and update service registry."""

        name = name.lower()
        xaddr, wsdl_file, binding_name = self.get_definition(name, port_type)

        # Don't re-create bindings if the xaddr remains the same,
        # the xaddr can change when a new PullPointSubscription is created
        binding = self.services.get(binding_name)
        if binding and binding.xaddr == xaddr:
            return binding

        service = ONVIFService(
            xaddr,
            self.user,
            self.passwd,
            wsdl_file,
            binding_name,
            encrypt=self.encrypt,
            dt_diff=self.dt_diff,
        )

        self.services[binding_name] = service

        return service

    def create_analytics_service(self) -> ONVIFService:
        """Create analytics service."""
        return self.create_onvif_service('analytics')

    def create_deviceio_service(self) -> ONVIFService:
        """Create deviceio service."""
        return self.create_onvif_service('deviceio')

    def create_devicemgmt_service(self) -> ONVIFService:
        """Create devicemgmt service."""
        return self.create_onvif_service('devicemgmt')

    def create_events_service(self) -> ONVIFService:
        """Create events service."""
        return self.create_onvif_service('events')

    def create_imaging_service(self) -> ONVIFService:
        """Create imaging service."""
        return self.create_onvif_service('imaging')

    def create_media_service(self) -> ONVIFService:
        """Create meida service."""
        return self.create_onvif_service('media')

    def create_notification_service(self) -> ONVIFService:
        """Create notification service."""
        return self.create_onvif_service('notification')

    def create_ptz_service(self) -> ONVIFService:
        """Create ptz service."""
        return self.create_onvif_service('ptz')

    def create_pullpoint_service(self) -> ONVIFService:
        """Create pullpoint service."""
        return self.create_onvif_service(
            'pullpoint',
            port_type='PullPointSubscription',
        )

    def create_receiver_service(self) -> ONVIFService:
        """Create receiver service."""
        return self.create_onvif_service('receiver')

    def create_recording_service(self) -> ONVIFService:
        """Create recording service."""
        return self.create_onvif_service('recording')

    def create_replay_service(self) -> ONVIFService:
        """Create replay service."""
        return self.create_onvif_service('replay')

    def create_search_service(self) -> ONVIFService:
        """Create search service."""
        return self.create_onvif_service('search')

    def create_subscription_service(self, port_type=None) -> ONVIFService:
        """Create subscription service."""
        return self.create_onvif_service(
            'subscription',
            port_type=port_type,
        )
