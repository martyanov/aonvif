#!/usr/bin/python

import unittest

import onvif


CAM_HOST = '172.20.9.84'
CAM_PORT = 80
CAM_USER = 'root'
CAM_PASS = 'password'

DEBUG = False


def log(ret):
    if DEBUG:
        print(ret)


class TestDevice(unittest.TestCase):

    # Class level cam. Run this test more efficiently..
    cam = onvif.ONVIFCamera(CAM_HOST, CAM_PORT, CAM_USER, CAM_PASS)

    # ***************** Test Capabilities ***************************
    def test_wsd_url(self):
        self.cam.devicemgmt.GetWsdlUrl()

    def test_get_services(self):
        """Returns a cllection of the devices services.

        Aand possibly their available capabilities.
        """
        params = {'IncludeCapability': True}
        self.cam.devicemgmt.GetServices(params)
        params = self.cam.devicemgmt.create_type('GetServices')
        params.IncludeCapability = False
        self.cam.devicemgmt.GetServices(params)

    def test_get_service_capabilities(self):
        """Returns the capabilities of the devce service."""
        ret = self.cam.devicemgmt.GetServiceCapabilities()
        ret.Network.IPFilter

    def test_get_capabilities(self):
        """Probides a backward compatible interface for the base capabilities."""
        categorys = ['PTZ', 'Media', 'Imaging',
                     'Device', 'Analytics', 'Events']
        self.cam.devicemgmt.GetCapabilities()
        for category in categorys:
            self.cam.devicemgmt.GetCapabilities({'Category': category})

        with self.assertRaises(onvif.ONVIFError):
            self.cam.devicemgmt.GetCapabilities({'Category': 'unknown'})

    def test_get_hostname(self):
        """Get the hostname from a device."""
        self.cam.devicemgmt.GetHostname()

    def test_set_hostname(self):
        """Set the hostname on a device.

        A device shall accept strings formated according to
        RFC 1123 section 2.1 or alternatively to RFC 952,
        other string shall be considered as invalid strings
        """
        pre_host_name = self.cam.devicemgmt.GetHostname()

        self.cam.devicemgmt.SetHostname({'Name': 'testHostName'})
        self.assertEqual(self.cam.devicemgmt.GetHostname().Name, 'testHostName')

        self.cam.devicemgmt.SetHostname({'Name': pre_host_name.Name})

    def test_set_hostname_from_dhcp(self):
        """Controls whether the hostname shall be retrieved from DHCP."""
        ret = self.cam.devicemgmt.SetHostnameFromDHCP({'FromDHCP': False})
        self.assertTrue(isinstance(ret, bool))

    def test_get_dns(self):
        """Gets the DNS setting from a device."""
        ret = self.cam.devicemgmt.GetDNS()
        self.assertTrue(hasattr(ret, 'FromDHCP'))
        if not ret.FromDHCP and len(ret.DNSManual) > 0:
            log(ret.DNSManual[0].Type)
            log(ret.DNSManual[0].IPv4Address)

    def test_set_dns(self):
        """Set the DNS settings on a device."""
        self.cam.devicemgmt.SetDNS({'FromDHCP': False})

    def test_get_ntp(self):
        """Get the NTP settings from a device."""
        ret = self.cam.devicemgmt.GetNTP()
        if ret.FromDHCP:
            self.assertTrue(hasattr(ret, 'NTPManual'))
            log(ret.NTPManual)

    def test_set_ntp(self):
        """Set the NTP setting."""
        self.cam.devicemgmt.SetNTP({'FromDHCP': False})

    def test_get_dynamic_dns(self):
        """Get the dynamic DNS setting."""
        ret = self.cam.devicemgmt.GetDynamicDNS()
        log(ret)

    def test_set_dynamic_dns(self):
        """Set the dynamic DNS settings on a device."""
        self.cam.devicemgmt.GetDynamicDNS()
        self.cam.devicemgmt.SetDynamicDNS({'Type': 'NoUpdate', 'Name': None, 'TTL': None})


if __name__ == '__main__':
    unittest.main()
