aonvif
======

.. start-inclusion-marker-do-not-remove

.. image:: https://github.com/martyanov/aonvif/workflows/CI/badge.svg?event=push
   :alt: Build Status
   :target: https://github.com/martyanov/aonvif/actions?query=event%3Apush+branch%3Amaster+workflow%3ACI

.. image:: https://codecov.io/gh/martyanov/aonvif/coverage.svg?branch=master
   :alt: Coverage report
   :target: https://codecov.io/gh/martyanov/aonvif/branch/master

.. image:: https://img.shields.io/pypi/v/aonvif.svg
   :alt: PyPI Version
   :target: https://pypi.python.org/pypi/aonvif

.. image:: https://img.shields.io/pypi/pyversions/aonvif.svg
   :alt: Supported Python Versions
   :target: https://pypi.python.org/pypi/aonvif

.. image:: https://img.shields.io/pypi/l/aonvif.svg
   :alt: License
   :target: https://pypi.python.org/pypi/aonvif

ONVIF asynchronous client implementation in Python.

Installation
------------

.. code:: bash

    $ python -m pip install aonvif

Getting Started
---------------

Initialize an ONVIFCamera instance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    from onvif import ONVIFCamera
    mycam = ONVIFCamera('192.168.0.2', 80, 'user', 'passwd', '/etc/onvif/wsdl/')
    await mycam.update_xaddrs()

Now, an ONVIFCamera instance is available. By default, a devicemgmt service is also available if everything is OK.

So, all operations defined in the WSDL document::

/etc/onvif/wsdl/devicemgmt.wsdl

are available.

Get information from your camera
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

    # Get Hostname
    resp = await mycam.devicemgmt.GetHostname()
    print 'My camera`s hostname: ' + str(resp.Name)

    # Get system date and time
    dt = await mycam.devicemgmt.GetSystemDateAndTime()
    tz = dt.TimeZone
    year = dt.UTCDateTime.Date.Year
    hour = dt.UTCDateTime.Time.Hour

Configure (Control) your camera
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To configure your camera, there are two ways to pass parameters to service methods.

**Dict**

This is the simpler way::

    params = {'Name': 'NewHostName'}
    await device_service.SetHostname(params)

**Type Instance**

This is the recommended way. Type instance will raise an
exception if you set an invalid (or non-existent) parameter.

::

    params = mycam.devicemgmt.create_type('SetHostname')
    params.Hostname = 'NewHostName'
    await mycam.devicemgmt.SetHostname(params)

    time_params = mycam.devicemgmt.create_type('SetSystemDateAndTime')
    time_params.DateTimeType = 'Manual'
    time_params.DaylightSavings = True
    time_params.TimeZone.TZ = 'CST-8:00:00'
    time_params.UTCDateTime.Date.Year = 2014
    time_params.UTCDateTime.Date.Month = 12
    time_params.UTCDateTime.Date.Day = 3
    time_params.UTCDateTime.Time.Hour = 9
    time_params.UTCDateTime.Time.Minute = 36
    time_params.UTCDateTime.Time.Second = 11
    await mycam.devicemgmt.SetSystemDateAndTime(time_params)

Use other services
~~~~~~~~~~~~~~~~~~
ONVIF protocol has defined many services.
You can find all the services and operations `here <https://www.onvif.org/onvif/ver20/util/operationIndex.html>`_.
ONVIFCamera has support methods to create new services::

    # Create ptz service
    ptz_service = mycam.create_ptz_service()
    # Get ptz configuration
    await mycam.ptz.GetConfiguration()
    # Another way
    # await ptz_service.GetConfiguration()

Or create an unofficial service::

    xaddr = 'http://192.168.0.3:8888/onvif/yourservice'
    yourservice = mycam.create_onvif_service('service.wsdl', xaddr, 'yourservice')
    await yourservice.SomeOperation()
    # Another way
    # await mycam.yourservice.SomeOperation()

ONVIF CLI
---------
python-onvif also provides a command line interactive interface: onvif-cli.
onvif-cli is installed automatically.

Single command example
~~~~~~~~~~~~~~~~~~~~~~

::

    $ onvif-cli devicemgmt GetHostname --user 'admin' --password '12345' --host '192.168.0.112' --port 80
    True: {'FromDHCP': True, 'Name': hision}
    $ onvif-cli devicemgmt SetHostname "{'Name': 'NewerHostname'}" --user 'admin' --password '12345' --host '192.168.0.112' --port 80
    True: {}

Interactive mode
~~~~~~~~~~~~~~~~

::

    $ onvif-cli -u 'admin' -a '12345' --host '192.168.0.112' --port 80 --wsdl /etc/onvif/wsdl/
    ONVIF >>> cmd
    analytics   devicemgmt  events      imaging     media       ptz
    ONVIF >>> cmd devicemgmt GetWsdlUrl
    True: http://www.onvif.org/
    ONVIF >>> cmd devicemgmt SetHostname {'Name': 'NewHostname'}
    ONVIF >>> cmd devicemgmt GetHostname
    True: {'Name': 'NewHostName'}
    ONVIF >>> cmd devicemgmt SomeOperation
    False: No Operation: SomeOperation

NOTE: Tab completion is supported for interactive mode.

Batch mode
~~~~~~~~~~

::

    $ vim batchcmds
    $ cat batchcmds
    cmd devicemgmt GetWsdlUrl
    cmd devicemgmt SetHostname {'Name': 'NewHostname', 'FromDHCP': True}
    cmd devicemgmt GetHostname
    $ onvif-cli --host 192.168.0.112 -u admin -a 12345 -w /etc/onvif/wsdl/ < batchcmds
    ONVIF >>> True: http://www.onvif.org/
    ONVIF >>> True: {}
    ONVIF >>> True: {'FromDHCP': False, 'Name': NewHostname}

References
----------

* `Operations Index <https://www.onvif.org/onvif/ver20/util/operationIndex.html>`_

* `ONVIF Specifications <https://www.onvif.org/profiles-add-ons-specifications/>`_
