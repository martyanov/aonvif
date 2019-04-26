# -*- coding: utf-8 -*-
import asyncio
from onvif import ONVIFCamera
__author__ = 'vahid'


async def run():
    mycam = ONVIFCamera('192.168.3.7', 80, 'hass', 'peek4boo') #, no_cache=True)
    await mycam.update_xaddrs()
    event_service = mycam.create_events_service()
    properties = await event_service.GetEventProperties()
    print(properties)
    
    pullpoint = mycam.create_pullpoint_service()
    req = pullpoint.create_type('PullMessages')
    req.MessageLimit=100
    req.Timeout = 30
    messages = await pullpoint.PullMessages(req)
    print(messages)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
