# Echonet Lite

This package provides an [Echonet](http://echonet.jp/english/) Lite
middleware module for Python3.  The current implementation only
provides quite limited functions to implement Echonet Lite server and
client.

[Echonet Lite specification](http://echonet.jp/spec_en/) is available
from the Echonet web site.


## Programming an Echonet Lite Node

### Server Node

A simple temperature server code is included in the examples directory
as ``examples/server-temp.py``.

```python
import struct

from echonetlite.interfaces import monitor
from echonetlite import middleware
from echonetlite.protocol import *

class MyTemperature(middleware.NodeSuperObject):
    def __init__(self, eoj):
        super(MyTemperature, self).__init__(eoj=eoj)
        # self.property[EPC_MANUFACTURE_CODE] = ...
        self._add_property(EPC_TEMPERATURE, [0,0])
        self.get_property_map += [
            EPC_TEMPERATURE]

        monitor.schedule_loopingcall(
            1,
            self._update_temperature)

    def _update_temperature(self):
        # update temperature value here
        val = 270
        self._properties[EPC_TEMPERATURE] = struct.pack('!h', val)

# Create local devices
profile = middleware.NodeProfile()
# profile.property[EPC_MANUFACTURE_CODE] = ...
# profile.property[EPC_IDENTIFICATION_NUMBER] = ...
temperature = MyTemperature(eoj=EOJ(clsgrp=CLSGRP_CODE['SENSOR'],
                                    cls=CLS_SE_CODE['TEMPERATURE'],
                                    instance_id=1))

# Start the Echonet Lite message loop
monitor.start(node_id='172.16.254.66',
              devices={str(profile.eoj): profile,
                       str(temperature.eoj): temperature})
```

A server (a local Echonet Lite device) should be defined as a subclass
of the ``middleware.NodeSuperObject`` class that handles some basic
requests required for all the Echonet Lite devices.

Since a temperature sensor device must provide the ``EPC_TEMPERATURE``
property, that property is created in the ``__init__()`` function.
Also, to respond the GET request from client nodes, the
``EPC_TEMPERATURE`` value is appended to the ``get_property_map``
variable.

The ``interfaces.monitor`` variable is the core instance of this
module.  It handles all the event loop and callback processing.  This
module used the [Twisted](https://twistedmatrix.com/) framework as its
underlying layer.

The ``interfaces.monitor.schedule_loopingcall()`` function registers a
function periodically called.  In this example, the
``_update_temperature()`` function that is meant to update the
internal temperature value is registered and called every second.

In the ``_update_temperature()`` function, the property value for the
``EPC_TEMPERATURE`` code is updated.  Based on the specification, the
temperature value is encoded into 2 bytes of data.

An Echonet Lite node must have one NodeProfile device.  The
``middleware.NodeProfile`` class provides a basic NodeProfile device
function.

Finally, by calling the ``monitor.start()`` function providing the
node IP address and device list, the Echonet Lite server that provides
two devices one is a NodeProfile device and the other is a temperature
sensor device starts working


### Client Node

A simple temperature client that can communication with the above
simple temperature server is included in the examples directory as
``examples/client-temp.py``.

```python
import struct

from echonetlite.interfaces import monitor
from echonetlite import middleware
from echonetlite.protocol import *

class Temperature(middleware.RemoteDevice):
    def __init__(self, eoj, node_id):
        super(Temperature, self).__init__(eoj=eoj)
        self._node_id = node_id
        monitor.schedule_loopingcall(
            10,
            self._request_temperature,
            from_device=controller,
            to_eoj=self.eoj,
            to_node_id=self._node_id)

        self.add_listener(EPC_TEMPERATURE,
                          self._on_did_receive_temperature)

    def _request_temperature(self, from_device, to_eoj, to_node_id):
        from_device.send(esv=ESV_CODE['GET'],
                         props=[Property(epc=EPC_TEMPERATURE),],
                         to_eoj=to_eoj,
                         to_node_id=to_node_id)

    def _on_did_receive_temperature(self, from_node_id, from_eoj,
                                    to_device, esv, prop):
        if esv not in ESV_RESPONSE_CODES:
            return
        (val,) = struct.unpack('!h', bytearray(prop.edt))
        print('Temperature is', val / 10)

class MyProfile(middleware.NodeProfile):
    def __init__(self, eoj=None):
        super(MyProfile, self).__init__(eoj=eoj)
        # profile.property[EPC_MANUFACTURE_CODE] = ...
        # profile.property[EPC_IDENTIFICATION_NUMBER] = ...

    def on_did_find_device(self, eoj, from_node_id):
        if (eoj.clsgrp == CLSGRP_CODE['SENSOR']
            and eoj.cls == CLS_SE_CODE['TEMPERATURE']):
            return Temperature(eoj, from_node_id)
        return None

profile = MyProfile()
controller = middleware.Controller(instance_id=1)

monitor.start(node_id='172.16.254.1',
              devices={str(profile.eoj): profile,
                       str(controller.eoj): controller})
```

The ``Temperature`` class is a placeholder to register functions to
request a temperature value and to receive its response.  In the
``__init__()`` function, two functions ``request_temperature``
and ``on_temperature`` are registered for these purposes.

When writing a client node, you need to handle new device discovery
case.  In the ``on_did_find_device()`` function, you will receive an
EOJ and node IP address when the middleware find a new device.  You
need to check the EOJ and create a new device entry (the
``Temperature`` class in this case).


## Code

The source code is available at
https://github.com/keiichishima/echonetlite

## Bug Reports

Please submit bug reports or patches through the GitHub interfaces.


## Author

Keiichi SHIMA
/ IIJ Innovation Institute Inc.
/ WIDE project
