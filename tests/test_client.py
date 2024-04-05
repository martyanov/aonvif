import pytest

import aonvif
import aonvif.client


def test_client_handle_errors():
    @aonvif.client.handle_errors
    def maybe_raise(r=False):
        if r:
            raise Exception('oops')

        return 'ok'

    assert maybe_raise() == 'ok'

    with pytest.raises(
        aonvif.ONVIFError,
        match='oops',
    ):
        maybe_raise(True)


def test_client_set_capabilies_with_invalid_capabilities_type():
    with pytest.raises(
        RuntimeError,
        match='Capabilities type must be dictionary',
    ):
        client = aonvif.ONVIFCamera(
            'testhost',
            80,
            'username',
            'password',
        )
        client.set_capabilities(
            capabilities=[
                {
                    'Media': {
                        'XAddr': 'http://localhost/path',
                    },
                },
            ],
        )


def test_client_set_capabilities_with_invalid_capabilities_key_type():
    with pytest.raises(
        RuntimeError,
        match='Capabilities key type must be string',
    ):
        client = aonvif.ONVIFCamera(
            'testhost',
            80,
            'username',
            'password',
        )
        client.set_capabilities(
            capabilities={
                tuple('Media'): {
                    'XAddr': 'http://localhost/path',
                },
            },
        )


def test_client_set_capabilities_with_invalid_capability_type():
    with pytest.raises(
        RuntimeError,
        match='Capability type must be dictionary',
    ):
        client = aonvif.ONVIFCamera(
            'testhost',
            80,
            'username',
            'password',
        )
        client.set_capabilities(
            capabilities={
                'Media': ['XAddr', 'http://localhost/path'],
            },
        )


def test_client_set_capabilities_with_missing_xaddr():
    with pytest.raises(
        RuntimeError,
        match='Capability XAddr type must be string',
    ):
        client = aonvif.ONVIFCamera(
            'testhost',
            80,
            'username',
            'password',
        )
        client.set_capabilities(
            capabilities={
                'Media': {
                    'RTPMulticast': True,
                },
            },
        )


def test_client_set_capabilities_with_invalid_xaddr_type():
    with pytest.raises(
        RuntimeError,
        match='Capability XAddr type must be string',
    ):
        client = aonvif.ONVIFCamera(
            'testhost',
            80,
            'username',
            'password',
        )
        client.set_capabilities(
            capabilities={
                'Media': {
                    'XAddr': True,
                },
            },
        )


@pytest.fixture
def mocked_device_mgmt_service(mocker):
    mocked_service = mocker.AsyncMock()
    mocked_service.GetCapabilities.return_value = {
        'Analytics': {
            'XAddr': 'http://testhost/onvif/analytics_service',
            'RuleSupport': True,
            'AnalyticsModuleSupport': True,
            '_value_1': None,
            '_attr_1': None,
        },
        'Events': {
            'XAddr': 'http://testhost/onvif/event_service',
            'WSSubscriptionPolicySupport': True,
            'WSPullPointSupport': True,
            'WSPausableSubscriptionManagerInterfaceSupport': False,
            '_value_1': None,
            '_attr_1': None,
        },
        'PTZ': {
            'XAddr': 'http://testhost/onvif/ptz_service',
            '_value_1': None,
            '_attr_1': None,
        },
    }

    return mocked_service


@pytest.mark.asyncio
async def test_client_update_xaddrs(mocker, mocked_device_mgmt_service):
    client = aonvif.ONVIFCamera(
        'testhost',
        80,
        'username',
        'password',
    )
    mocker.patch.object(
        client,
        'create_devicemgmt_service',
        return_value=mocked_device_mgmt_service,
    )

    await client.update_xaddrs()

    assert client._xaddrs == {
        'http://www.onvif.org/ver20/ptz/wsdl': 'http://testhost/onvif/ptz_service',
        'http://www.onvif.org/ver10/events/wsdl': 'http://testhost/onvif/event_service',
        'http://www.onvif.org/ver20/analytics/wsdl': 'http://testhost/onvif/analytics_service',
    }
    mocked_device_mgmt_service.GetCapabilities.assert_awaited_once_with({'Category': 'All'})


@pytest.mark.asyncio
async def test_client_update_xaddrs_with_custom_capabilities(
    mocker,
    mocked_device_mgmt_service,
):
    client = aonvif.ONVIFCamera(
        'testhost',
        80,
        'username',
        'password',
    )
    client.set_capabilities(
        capabilities={
            'Imaging': {
                'XAddr': 'http://testhost/onvif/imaging_service',
            },
        },
    )

    mocker.patch.object(
        client,
        'create_devicemgmt_service',
        return_value=mocked_device_mgmt_service,
    )

    await client.update_xaddrs()

    assert client._xaddrs == {
        'http://www.onvif.org/ver20/imaging/wsdl': 'http://testhost/onvif/imaging_service',
    }
    mocked_device_mgmt_service.GetCapabilities.assert_not_awaited()
