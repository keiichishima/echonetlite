import argparse
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

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--self-node', dest='self_node', required=True,
                        help='IP address of this node')
    args = parser.parse_args()

    profile = MyProfile()
    controller = middleware.Controller(instance_id=1)

    monitor.start(node_id=args.self_node,
                  devices={str(profile.eoj): profile,
                           str(controller.eoj): controller})
