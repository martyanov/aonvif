# -*- coding: utf-8 -*-
import asyncio
from onvif import ONVIFCamera
from zeep.exceptions import Fault
__author__ = 'vahid'


async def run():
    mycam = ONVIFCamera('192.168.1.108', 80, 'admin', 'OneM0ment!', wsdl_dir='/home/jason/python-onvif-zeep-async/onvif/wsdl') #, no_cache=True)
    await mycam.update_xaddrs()
    print(mycam.xaddrs)

    media_service = mycam.create_media_service()
    profiles = await media_service.GetProfiles()
    # print(profiles)

    compatible_configurations = await media_service.GetCompatibleMetadataConfigurations(profiles[0].token)
    print(compatible_configurations)

    event_service = mycam.get_service('events')

    try:
        pullpoint = await event_service.CreatePullPointSubscription()
        print(pullpoint)
    except Fault as err:
        print(err)

    properties = await event_service.GetEventProperties()
    print(properties)
    capabilities = await event_service.GetServiceCapabilities()
    print(capabilities)
    
    pullpoint = mycam.create_pullpoint_service()
    req = pullpoint.create_type('PullMessages')
    req.MessageLimit=100
    req.Timeout = 30
    while True:
        messages = await pullpoint.PullMessages(req)
        print(messages)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
