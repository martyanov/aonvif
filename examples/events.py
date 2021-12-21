import asyncio
import datetime as dt
import logging

import pytz

import onvif


logging.getLogger('zeep').setLevel(logging.DEBUG)


async def run():
    mycam = onvif.ONVIFCamera(
        '192.168.3.10',
        80,
        'hass',
        'peek4boo',
        wsdl_dir='/home/jane/onvif/wsdl',
    )
    await mycam.update_xaddrs()

    if not await mycam.create_pullpoint_subscription():
        print('PullPoint not supported')
        return

    event_service = mycam.get_service('events')
    properties = await event_service.GetEventProperties()
    print(properties)
    capabilities = await event_service.GetServiceCapabilities()
    print(capabilities)

    pullpoint = mycam.create_pullpoint_service()
    await pullpoint.SetSynchronizationPoint()
    req = pullpoint.create_type('PullMessages')
    req.MessageLimit = 100
    req.Timeout = dt.timedelta(seconds=30)
    messages = await pullpoint.PullMessages(req)
    print(messages)

    subscription = mycam.create_subscription_service('PullPointSubscription')
    req = subscription.zeep_client.get_element('ns5:Renew')
    req.TerminationTime = str(dt.datetime.now(pytz.UTC) + dt.timedelta(minutes=10))
    termination_time = (dt.datetime.now(pytz.UTC) + dt.timedelta(minutes=10)).isoformat()
    await subscription.Renew(termination_time)
    await subscription.Unsubscribe()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
