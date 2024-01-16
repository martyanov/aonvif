import datetime

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


def test_onvif_service_set_wsse(mocker):
    mocked_client = mocker.Mock(
        namespaces={
            'xsd': 'http://www.w3.org/2001/XMLSchema',
            'ns0': 'http://www.onvif.org/ver10/device/wsdl',
        },
    )
    mocker.patch('zeep.client.AsyncClient', return_value=mocked_client)
    mocker.patch('zeep.proxy.AsyncServiceProxy')
    onvif_service = aonvif.client.ONVIFService(
        'http://testhost',
        'test_username',
        'test_password',
        'http://testhost',
        '{http://www.onvif.org/ver10/device/wsdl}DeviceBinding',
    )

    onvif_service.set_wsse(
        'changed_username',
        'changed_password',
        use_token_digest=False,
        device_time_drift=datetime.timedelta(seconds=5),
    )

    wsse = onvif_service._client.wsse

    assert isinstance(wsse, aonvif.client.UsernameToken)
    assert wsse.username == 'changed_username'
    assert wsse.password == 'changed_password'
    assert wsse.use_digest is False
    assert wsse._device_time_drift == datetime.timedelta(seconds=5)
    assert wsse.zulu_timestamp is True


@pytest.mark.asyncio
async def test_onvif_camera_update_xaddrs(mocker):
    onvif_camera = aonvif.client.ONVIFCamera(
        host='testhost',
        port=99999,
        username='test',
        password='password',
    )
    devicemgmt = mocker.Mock()
    devicemgmt.GetCapabilities = mocker.AsyncMock(
        return_value={
            'Analytics': {
                'XAddr': 'http://testhost/onvif/Analytics',
             },
            'Events': {
                'XAddr': 'http://testhost/onvif/Events',
            },
        },
    )
    devicemgmt.GetSystemDateAndTime = mocker.AsyncMock()
    mocker.patch.object(onvif_camera, 'create_devicemgmt_service', return_value=devicemgmt)

    await onvif_camera.update_xaddrs()

    assert onvif_camera._xaddrs == {
        'http://www.onvif.org/ver20/analytics/wsdl': 'http://testhost/onvif/Analytics',
        'http://www.onvif.org/ver10/events/wsdl': 'http://testhost/onvif/Events',
    }
    devicemgmt.GetCapabilities.assert_awaited_once_with({'Category': 'All'})
    devicemgmt.GetSystemDateAndTime.assert_not_awaited()


@pytest.mark.asyncio
async def test_onvif_camera_update_xaddrs_with_adjust_time(mocker):
    onvif_camera = aonvif.client.ONVIFCamera(
        host='testhost',
        port=99999,
        username='test_user',
        password='password',
        adjust_time=True,
    )
    mocked_system_date_time = mocker.Mock(
        UTCDateTime=mocker.Mock(
            Date=mocker.Mock(
                Year=2023,
                Month=1,
                Day=2,
            ),
            Time=mocker.Mock(
                Hour=3,
                Minute=4,
                Second=5,
            ),
        ),
    )

    devicemgmt = mocker.Mock()
    devicemgmt.GetSystemDateAndTime = mocker.AsyncMock(return_value=mocked_system_date_time)
    devicemgmt.GetCapabilities = mocker.AsyncMock(return_value={})
    mocker.patch.object(onvif_camera, 'create_devicemgmt_service', return_value=devicemgmt)

    await onvif_camera.update_xaddrs()

    devicemgmt.GetSystemDateAndTime.assert_awaited_once_with()
    devicemgmt.set_wsse.assert_called_once_with(
        'test_user',
        'password',
        True,
        onvif_camera._device_time_drift,
    )
    assert isinstance(onvif_camera._device_time_drift, datetime.timedelta)
    devicemgmt.GetCapabilities.assert_awaited_once_with({'Category': 'All'})
    assert onvif_camera._xaddrs == {}
