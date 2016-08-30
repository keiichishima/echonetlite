# Echonet Lite

This package provides an [Echonet](http://echonet.jp/english/) Lite
middleware module for Python3.  The current implementation only
provides quite limited functions to implement Echonet Lite server and
client.

[The base specification](http://echonet.jp/spec_en/) is available from
the Echonet web site.


## Creating a Echonet Lite Node

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
        self._add_property(EPC_TEMPERATURE, [0,0])
        self.get_property_map += [
            EPC_TEMPERATURE]

        monitor.schedule_loopingcall(
            1,
            self._update_temperature)

    def _update_temperature(self):
        # update temperature value here
        val = 270
        self.properties[EPC_TEMPERATURE] = struct.pack('!h', val)

# Create local devices
profile = middleware.NodeProfile()
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
