#!/usr/bin/env python
# -*- coding: utf-8 -*-

import echonetlite
from echonetlite.protocol import *

class Node(object):
    def __init__(self, node_id, devices):
        # _node_id: a layer 3 address string
        self._node_id = node_id
        # _devices: a dict with key as str(eoj), value as Device()
        self._devices = devices

    @property
    def node_id(self):
        return self._node_id

    @property
    def devices(self):
        return self._devices

    def __str__(self):
        s = 'Node ID: {0}'.format(self._node_id)
        for d in self._devices.values():
            s += ', ' + str(d)
        return s

    def get_profile(self):
        profile = None
        for (_, d) in self._devices.items():
            if (d.eoj.clsgrp == CLSGRP_CODE['PROFILE']
                and d.eoj.cls == CLS_CODE['PROFILE']['PROFILE']):
                profile = d
                break
        return profile

    def add_device(self, device):
        self._devices[str(device.eoj)] = device

    def get_device(self, eoj):
        if str(eoj) in self._devices:
            return self._devices[str(eoj)]
        return None

    def remove_device(self, eoj):
        if str(eoj) in self._devices:
            del self._devices[str(eoj)]


class Device(object):
    def __init__(self, eoj=None):
        self._eoj = eoj
        self._properties = {}
        self._listeners = {}

    @property
    def eoj(self):
        return self._eoj

    @property
    def properties(self):
        return self._properties

    @property
    def listeners(self):
        return self._listeners

    def __str__(self):
        s = 'EOJ: {0}'.format(str(self._eoj))
        for epc, edt in self._properties.items():
            s += ', EPC: {0:#04x}, EDT:'.format(epc)
            for dt in edt:
                s += ' {0:02x}'.format(dt)
        return s

    def add_listener(self, epc, func):
        key = self._eoj.clsgrp << 16 | self._eoj.cls << 8 | epc
        self._listeners[key] = func

    def remove_listener(self, epc):
        key = self._eoj.clsgrp << 16 | self._eoj.cls << 8 | epc
        del self._listeners[key]


class RemoteDevice(Device):
    pass


class LocalDevice(Device):
    def __init__(self, eoj=None):
        super(LocalDevice, self).__init__(eoj)
        self._status_change_property_map = []
        self._set_property_map = []
        self._get_property_map = []

    def _add_property(self, epc, edt):
        self._properties[epc] = edt

    def _get_property(self, epc):
        if epc in self._properties:
            return self._properties[epc]
        return None

    def _remove_property(self, epc):
        del self._properties[epc]

    @property
    def status_change_property_map(self):
        return self._status_change_property_map

    @status_change_property_map.setter
    def status_change_property_map(self, prop_map):
        self._status_change_property_map = prop_map
        self._properties[EPC_STATUS_CHANGE_PROPERTY_MAP] = [
            len(self._status_change_property_map)] + self._status_change_property_map

    @property
    def set_property_map(self):
        return self._set_property_map

    @set_property_map.setter
    def set_property_map(self, prop_map):
        self._set_property_map = prop_map
        self._properties[EPC_SET_PROPERTY_MAP] = [
            len(self._set_property_map)] + self._set_property_map

    @property
    def get_property_map(self):
        return self._get_property_map

    @get_property_map.setter
    def get_property_map(self, prop_map):
        self._get_property_map = prop_map
        self._properties[EPC_GET_PROPERTY_MAP] = [
            len(self._get_property_map)] + self._get_property_map

    def send(self, esv, props, to_eoj, to_node_id=None):
        msg = Message()
        msg.seoj = self._eoj
        msg.deoj = to_eoj
        msg.esv = esv
        msg.properties = props
        msg.opc = len(props)
        echonetlite.interfaces.monitor.send(msg, to_node_id)

    def _build_response_props(self, msg, from_node):
        res_props = []
        if (msg.esv == ESV_CODE['GET']
            or msg.esv == ESV_CODE['INF_REQ']
            or msg.esv == ESV_CODE['INFC']):
            for p in msg.properties:
                if p.epc not in self._get_property_map:
                    # XXX error
                    #print('EPC {0:#x} does not exist'.format(p.epc))
                    continue
                res_props.append(Property(epc=p.epc,
                                          edt=self._properties[p.epc]))
        if (msg.esv == ESV_CODE['SETI']
            or msg.esv == ESV_CODE['SETC']):
            for p in msg.properties:
                if p.epc not in self._set_property_map:
                    # XXX error
                    #print('EPC {0:#x} is not writable'.format(p.epc))
                    continue
                self._properties[p.epc] = p.edt
                if msg.esv == ESV_CODE['SETC']:
                    res_props.append(Property(epc=p.epc,
                                              edt=self._properties[p.epc]))

        return res_props

    def on_did_receive_request(self, msg, from_node):
        props = self._build_response_props(msg, from_node)
        esv = None
        if msg.esv == ESV_CODE['SETC']:
            esv = ESV_CODE['SET_RES']
        elif msg.esv == ESV_CODE['GET']:
            esv = ESV_CODE['GET_RES']
        elif msg.esv == ESV_CODE['INF_REQ']:
            esv = ESV_CODE['INF']
        elif msg.esv == ESV_CODE['INFC']:
            esv = ESV_CODE['INFC_RES']
        elif msg.esv == ESV_CODE['SETGET']:
            esv = ESV_CODE['SETGET_RES']

        if len(props) == 0:
            # XXX
            return

        if esv is not None:
            self.send(esv, props, msg.seoj, from_node.node_id)

    def _process_response(self, msg, from_node):
        pass

    def on_did_receive_response(self, msg, from_node):
        self._process_response(msg, from_node)

    def on_did_receive_error(self, msg, from_node):
        pass


class ProfileSuperObject(LocalDevice):
    def __init__(self, eoj=None):
        super(ProfileSuperObject, self).__init__(eoj)
        # Vendor code
        self._properties[EPC_MANUFACTURE_CODE] = [0,0,0]
        # Status change announcement property map
        self.status_change_property_map = []
        # Set property map
        self.set_property_map = []
        # Get property map
        self.get_property_map = [
            EPC_MANUFACTURE_CODE,
            EPC_STATUS_CHANGE_PROPERTY_MAP,
            EPC_SET_PROPERTY_MAP,
            EPC_GET_PROPERTY_MAP
        ]

    def _process_response(self, msg, from_node):
        super(ProfileSuperObject, self)._process_response(msg, from_node)


class NodeProfile(ProfileSuperObject):
    def __init__(self, eoj=None):
        super(NodeProfile, self).__init__(eoj)
        if eoj is None:
            self._eoj = EOJ(CLSGRP_CODE['PROFILE'],
                            CLS_PR_CODE['PROFILE'],
                            INSTANCE_PR_NORMAL)

        # Operating status
        self._properties[EPC_OPERATING_STATUS] = [EDT_OPERATING_STATUS_BOOTING]
        # Echonet Lite protocol version
        self._properties[EPC_VERSION_INFORMATION] = PROTOCOL_VERSION
        # Identification number
        self._properties[EPC_IDENTIFICATION_NUMBER] = [0xfe] + self._properties[EPC_MANUFACTURE_CODE] + [0] * 13
        # Get property map
        self.get_property_map += [
            EPC_OPERATING_STATUS,
            EPC_VERSION_INFORMATION,
            EPC_IDENTIFICATION_NUMBER,
            EPC_NUM_SELF_NODE_INSTANCES,
            EPC_NUM_SELF_NODE_CLASSES,
            EPC_INSTANCE_LIST_NOTIFICATION,
            EPC_SELF_NODE_INSTANCE_LIST_S,
            EPC_SELF_NODE_CLASS_LIST_S]

        # Discover nodes just after booting,
        echonetlite.interfaces.monitor.schedule_call(
            0, self._request_operating_status)
        # and discover any new devices on the link every 60 seconds.
        echonetlite.interfaces.monitor.schedule_loopingcall(
            60, self._request_operating_status)

    def update_device_numbers(self, devices):
        grpcls_set = set()
        instance_set = set()
        instance_set_wo_profile = set()
        for (_, d) in devices.items():
            grpcls = (d.eoj.clsgrp << 8 | d.eoj.cls)
            grpcls_set.add(grpcls)
            if (d.eoj.clsgrp == CLSGRP_CODE['PROFILE']
                and d.eoj.cls == CLS_PR_CODE['PROFILE']):
                instance_set.add(d.eoj.eoj)
            else:
                instance_set.add(d.eoj.eoj)
                instance_set_wo_profile.add(d.eoj.eoj)
        self._properties[EPC_NUM_SELF_NODE_INSTANCES] = [
            (len(instance_set_wo_profile) >> 16) & 0xff,
            (len(instance_set_wo_profile) >> 8) & 0xff,
            len(instance_set_wo_profile) & 0xff
        ]
        self._properties[EPC_NUM_SELF_NODE_CLASSES] = [
            (len(grpcls_set) >> 8) & 0xff,
            len(grpcls_set) & 0xff
        ]
        instances_data_wo_profile = []
        for i in instance_set_wo_profile:
            instances_data_wo_profile += [(i >> 16) & 0xff,
                                          (i >> 8) & 0xff,
                                          i & 0xff]
        instances_data = []
        for i in instance_set:
            instances_data += [(i >> 16) & 0xff,
                               (i >> 8) & 0xff,
                               i & 0xff]
        grpclses_data = []
        for gc in grpcls_set:
            grpclses_data += [(gc >> 8) & 0xff, gc & 0xff]
        self._properties[EPC_INSTANCE_LIST_NOTIFICATION] = (
            [len(instance_set_wo_profile) & 0xff]
            + instances_data_wo_profile)
        self._properties[EPC_SELF_NODE_INSTANCE_LIST_S] = (
            [len(instance_set) & 0xff]
            + instances_data)
        self._properties[EPC_SELF_NODE_CLASS_LIST_S] = (
            [len(grpcls_set) ] + grpclses_data)

    def _request_operating_status(self):
        self.send(esv=ESV_CODE['INF_REQ'],
                  props=[Property(epc=EPC_OPERATING_STATUS),],
                  to_eoj=EOJ(CLSGRP_CODE['PROFILE'],
                             CLS_PR_CODE['PROFILE'],
                             INSTANCE_PR_NORMAL))

    def _on_did_receive_operating_status_response(self, from_node_id,
                                                  from_eoj, esv, prop):
        if (prop.pdc == 1
            and prop.edt[0] == EDT_OPERATING_STATUS_BOOTING):
            self.send(esv=ESV_CODE['GET'],
                         props=[Property(epc=EPC_SELF_NODE_INSTANCE_LIST_S),],
                         to_eoj=from_eoj,
                         to_node_id=from_node_id)

    def _on_did_receive_instance_list_s_response(self, from_node_id,
                                                 from_eoj, esv, prop):
        if prop.pdc == 0:
            return
        (ndevices,) = struct.unpack('!B', bytearray(prop.edt[0:1]))
        for idx in range(ndevices):
            (g,c,i) = struct.unpack('!BBB', bytearray(prop.edt[
                idx * 3 + 1:idx * 3 + 4]))
            eoj = EOJ(g, c, i)
            if str(eoj) in echonetlite.interfaces.monitor.nodes[from_node_id].devices:
                # already listed
                continue
            device = self.on_did_find_device(eoj, from_node_id)
            if device is None:
                device = self._on_did_find_device_default(eoj, from_node_id)
            echonetlite.interfaces.monitor.nodes[from_node_id].add_device(device)

    def on_did_find_device(self, eoj, from_node_id):
        return None

    def _on_did_find_device_default(self, eoj, from_node_id):
        return Device(eoj=eoj)

    def _process_response(self, msg, from_node):
        super(NodeProfile, self)._process_response(msg, from_node)

        from_node_id = from_node.node_id
        from_eoj = msg.seoj
        esv = msg.esv
        for prop in msg.properties:
            if prop.epc == EPC_OPERATING_STATUS:
                self._on_did_receive_operating_status_response(
                    from_node_id, from_eoj, esv, prop)
            elif prop.epc == EPC_SELF_NODE_INSTANCE_LIST_S:
                self._on_did_receive_instance_list_s_response(
                    from_node_id, from_eoj, esv, prop)


class NodeSuperObject(LocalDevice):
    def __init__(self, eoj=None):
        super(NodeSuperObject, self).__init__(eoj)

        # Operation status
        self._properties[EPC_OPERATING_STATUS] = [EDT_OPERATING_STATUS_BOOTING]
        # Installation location
        self._properties[EPC_INSTALLATION_LOCATION] = [
            EDT_INSTALLATION_LOCATION_NOT_SPECIFIED
        ]
        # Specification version
        self._properties[EPC_VERSION_INFORMATION] = APPENDIX_RELEASE
        # Fault status
        self._properties[EPC_FAULT_STATUS] = [EDT_FAULT_NOT_OCCURRED]
        # Manufcture code
        self._properties[EPC_MANUFACTURE_CODE] = [0,0,0]
        # Status change announcement property map
        self.status_change_property_map = []
        # Set property map
        self.set_property_map = []
        # Get property map
        self.get_property_map = [
            EPC_OPERATING_STATUS,
            EPC_INSTALLATION_LOCATION,
            EPC_VERSION_INFORMATION,
            EPC_FAULT_STATUS,
            EPC_MANUFACTURE_CODE,
            EPC_STATUS_CHANGE_PROPERTY_MAP,
            EPC_SET_PROPERTY_MAP,
            EPC_GET_PROPERTY_MAP,
        ]


class Controller(NodeSuperObject):
    def __init__(self, eoj=None, instance_id=1):
        super(Controller, self).__init__(eoj)
        if eoj is None:
            self._eoj = EOJ(CLSGRP_CODE['MANAGEMENT_OPERATION'],
                            CLS_MO_CODE['CONTROLLER'],
                            instance_id)
