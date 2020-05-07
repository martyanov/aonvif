# -*- coding: utf-8 -*-
import asyncio
import datetime
import logging

from onvif import ONVIFCamera
from zeep.exceptions import Fault

logging.getLogger("zeep").setLevel(logging.DEBUG)


async def run():
    mycam = ONVIFCamera("192.168.3.14", 80, "admin", "admin")
    await mycam.update_xaddrs()

    if not await mycam.create_pullpoint_subscription():
        print("PullPoint not supported")
        return

    event_service = mycam.get_service("events")
    properties = await event_service.GetEventProperties()
    print(properties)
    capabilities = await event_service.GetServiceCapabilities()
    print(capabilities)

    pullpoint = mycam.create_pullpoint_service()
    await pullpoint.SetSynchronizationPoint()
    req = pullpoint.create_type("PullMessages")
    req.MessageLimit = 100
    req.Timeout = datetime.timedelta(seconds=30)
    messages = await pullpoint.PullMessages(req)
    print(messages)

    subscription = mycam.create_subscription_service("PullPointSubscription")
    await subscription.Unsubscribe()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
