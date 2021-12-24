import datetime
import logging
import os
import typing

import zeep.cache
import zeep.client
import zeep.exceptions
import zeep.helpers
import zeep.proxy
import zeep.transports
import zeep.wsse.username

from . import exceptions
from . import wsdl


logger = logging.getLogger('aonvif')
logging.basicConfig(level=logging.INFO)
logging.getLogger('zeep.client').setLevel(logging.CRITICAL)


def handle_errors(func):
    """Ensure methods to raise an ONVIFError when something was wrong."""

    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise exceptions.ONVIFError(e)

    return wrapped


class UsernameToken(zeep.wsse.username.UsernameToken):
    """UsernameDigestToken class, with a time drift parameter that can be adjusted.

    This allows authentication on cameras without being time synchronized.
    Please note that using NTP on both end is the recommended solution,
    this should only be used in 'safe' environments.
    """

    def __init__(
        self,
        username: str,
        password: str,
        device_time_drift: typing.Optional[datetime.timedelta] = None,
        **kwargs,
    ):
        super().__init__(username, password, **kwargs)
        self._device_time_drift = device_time_drift

    def apply(self, envelope, headers):
        old_created = self.created
        if self.created is None:
            self.created = datetime.datetime.utcnow()

        if self._device_time_drift is not None:
            self.created += self._device_time_drift

        result = super().apply(envelope, headers)

        self.created = old_created

        return result


class MemoryCache(zeep.cache.Base):
    """Simple in-memory caching using dict lookup.

    We can store entries indefinitely, as we know that WSDL files
    can not change.

    We use `url` as stated by `zeep.cache.Base` interface to overcome
    possible issues if keyword arguments are used, but actually it is
    always a file path.
    """

    # Dictionary for storing cache entries
    _cache: typing.Dict[str, bytes] = {}

    def add(self, url: str, content: bytes) -> None:
        logger.debug(f'Caching contents of {url!r}')

        if not isinstance(content, (str, bytes)):
            raise TypeError(
                f'a bytes-like object is required, not {type(content).__name__!r}',
            )

        self._cache[url] = content

    def get(self, url: str) -> typing.Optional[bytes]:
        content = self._cache.get(url)
        if content is not None:
            logger.debug(f'Cache HIT for {url!r}')
            return content

        logger.debug(f'Cache MISS for {url!r}')

        return None


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
    """

    @handle_errors
    def __init__(
        self,
        xaddr: str,
        username: str,
        password: str,
        url: str,
        binding_name: str,
        use_token_digest: bool = True,
        device_time_drift: typing.Optional[datetime.timedelta] = None,
    ):
        self.url = url
        self.xaddr = xaddr

        # Create security token
        wsse = UsernameToken(
            username,
            password,
            device_time_drift=device_time_drift,
            use_digest=use_token_digest,
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
            transport=zeep.transports.AsyncTransport(cache=MemoryCache()),
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
    @handle_errors
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

            @handle_errors
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
    """Implemention ONVIF compliant device.

    This class integrates ONVIF services.

    :param host: Camera host.
    :param port: Camera port.
    :param username: Camera username.
    :param password: Camera user password.
    :param use_token_digest: Use password digest for WSSE authentication.
    :param adjust_time: Allows authentication on cameras without being time synchronized.
                        NOTE: Please note that using NTP on both end is the recommended
                        solution, this should only be used in "safe" environments.
                        Also, this cannot be used on AXIS camera, as every request is
                        authenticated, contrary to ONVIF standard.
    """
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        use_token_digest: bool = True,
        adjust_time: bool = False,
    ):
        # TODO: Handle case-sensivity
        os.environ.pop('http_proxy', None)
        os.environ.pop('https_proxy', None)

        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._use_token_digest = use_token_digest
        self._adjust_time = adjust_time

        # Time drift for a device to overcome clock synchronization
        self._device_time_drift = None

        # Known xaddrs
        self._xaddrs = {}

        # Currently initialized services
        self._services = {}

        self.to_dict = ONVIFService.to_dict

    async def update_xaddrs(self):
        """Update xaddrs for services."""

        # Create devicemgmt service
        devicemgmt = self.create_devicemgmt_service()

        # If time adjusting needed, calculate drift
        if self._adjust_time:
            device_time = (await devicemgmt.GetSystemDateAndTime()).UTCDateTime
            device_dt = datetime.datetime(
                device_time.Date.Year,
                device_time.Date.Month,
                device_time.Date.Day,
                device_time.Time.Hour,
                device_time.Time.Minute,
                device_time.Time.Second,
            )
            self._device_time_drift = device_dt - datetime.datetime.utcnow()

        # Get XAddr of services on the device
        self._xaddrs = {}
        capabilities = await devicemgmt.GetCapabilities({'Category': 'All'})
        for name in capabilities:
            capability = capabilities[name]
            try:
                if name.lower() in wsdl.SERVICES and capability is not None:
                    namespace = wsdl.SERVICES[name.lower()]['ns']
                    self._xaddrs[namespace] = capability['XAddr']
            except Exception:
                logger.exception(f'Unexpected service type: {name!r}')

    async def close(self):
        """Release all previously initialized services."""

        for service in self._services.values():
            await service.close()

    def get_definition(self, name, port_type=None):
        """Return xaddr and wsdl of specified service.

        :param name: Service name for which the definition requested.
        """

        # Check if the service is supported
        if name not in wsdl.SERVICES:
            raise exceptions.ONVIFError(f'Unknown service: {name!r}')

        wsdl_file = wsdl.SERVICES[name]['wsdl']
        namespace = wsdl.SERVICES[name]['ns']
        binding = wsdl.SERVICES[name]['binding']

        binding_name = f'{{{namespace}}}{binding}'

        if port_type:
            namespace += '/' + port_type

        # TODO: Cache or load asynchronously
        wsdl_path = str(wsdl.WSDL_DIR / wsdl_file)

        # XAddr for devicemgmt is fixed
        if name == 'devicemgmt':
            host = self._host
            # If scheme is missing, then treat the scheme as http://
            if not self._host.startswith('http://') or not self._host.startswith('https://'):
                host = f'http://{self._host}'

            xaddr = f'{host}:{self._port}/onvif/device_service'
            return xaddr, wsdl_path, binding_name

        # Get XAddr
        xaddr = self._xaddrs.get(namespace)
        if not xaddr:
            raise exceptions.ONVIFError(f"Device doesn't support service: {name!r}")

        return xaddr, wsdl_path, binding_name

    def create_onvif_service(
        self,
        name: str,
        port_type: typing.Optional[str] = None,
    ) -> ONVIFService:
        """Create ONVIF service and update service registry.

        :param name: Service name that should be initialized.
        """

        # Normalize provided service name
        name = name.lower()

        # Get the service definition
        xaddr, wsdl_file, binding_name = self.get_definition(name, port_type)

        # Try to get the requested service from registry,
        # don't recreate a service if the XAddr remains the same,
        # the XAddr can change when a new PullPointSubscription is created
        service = self._services.get(binding_name)
        if service and service.xaddr == xaddr:
            return service

        # Create a fresh service
        service = ONVIFService(
            xaddr,
            self._username,
            self._password,
            wsdl_file,
            binding_name,
            use_token_digest=self._use_token_digest,
            device_time_drift=self._device_time_drift,
        )

        # Store the newly created service for further reuse
        self._services[binding_name] = service

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

    def create_subscription_service(
        self,
        port_type:
        typing.Optional[str] = None,
    ) -> ONVIFService:
        """Create subscription service."""
        return self.create_onvif_service(
            'subscription',
            port_type=port_type,
        )

    async def create_pullpoint_subscription(self):
        """Create a pullpoint subscription."""
        try:
            events = self.create_events_service()
            pullpoint = await events.CreatePullPointSubscription()

            self._xaddrs[
                'http://www.onvif.org/ver10/events/wsdl/PullPointSubscription',
            ] = pullpoint.SubscriptionReference.Address._value_1
        except zeep.exceptions.Fault:
            return False
        return True
