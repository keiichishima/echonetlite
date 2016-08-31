#!/usr/bin/env python
# -*- coding: utf-8 -*-

import struct

PROTOCOL_VERSION = [ 1, 12, 0x01, 0x00]
APPENDIX_RELEASE = [0x00, 0x00, ord('H'), 0x00]

EHD1 = 0x10
EHD2_FMT1 = 0x81
EHD2_FMT2 = 0x82

def _code_to_desc(code_dict):
    desc_dict = {}
    for key in code_dict:
        desc_dict[code_dict[key]] = key
    return desc_dict

ESV_CODE = {
    'SETI_SNA':   0x50,
    'SETC_SNA':   0x51,
    'GET_SNA':    0x52,
    'INF_SNA':    0x53,
    'SETGET_SNA': 0x5e,
    'SETI':       0x60,
    'SETC':       0x61,
    'GET':        0x62,
    'INF_REQ':    0x63,
    'SETGET':     0x6e,
    'SET_RES':    0x71,
    'GET_RES':    0x72,
    'INF':        0x73,
    'INFC':       0x74,
    'INFC_RES':   0x7a,
    'SETGET_RES': 0x7e,
}
ESV_DESC = _code_to_desc(ESV_CODE)
ESV_REQUEST_CODES = (
    ESV_CODE['SETI'],
    ESV_CODE['SETC'],
    ESV_CODE['GET'],
    ESV_CODE['INF_REQ'],
    ESV_CODE['SETGET'],
    ESV_CODE['INF'],
)
ESV_RESPONSE_CODES = (
    ESV_CODE['SET_RES'],
    ESV_CODE['GET_RES'],
    ESV_CODE['INF'],
    ESV_CODE['INFC_RES'],
    ESV_CODE['SETGET_RES'],
)
ESV_ERROR_CODES = (
    ESV_CODE['SETI_SNA'],
    ESV_CODE['SETC_SNA'],
    ESV_CODE['GET_SNA'],
    ESV_CODE['INF_SNA'],
    ESV_CODE['SETGET_SNA'],
)

CLSGRP_CODE = {
    'SENSOR':               0x00,
    'AIR_CONDITIONER':      0x01,
    'HOUSING_FACILITIES':   0x02,
    'COOKING_HOUSEHOLD':    0x03,
    'HEALTH':               0x04,
    'MANAGEMENT_OPERATION': 0x05,
    'PROFILE':              0x0e, 
}
CLSGRP_DESC = _code_to_desc(CLSGRP_CODE)

CLS_SE_CODE = {
    'TEMPERATURE': 0x11,
}
CLS_AC_CODE = {}
CLS_HF_CODE = {
    'LV_ELECTRIC_ENERGY_METER': 0x88,
}
CLS_CH_CODE = {}
CLS_HE_CODE = {}
CLS_MO_CODE = {
    'CONTROLLER': 0xff,
}
CLS_PR_CODE = {
    'PROFILE': 0xf0,
}
CLS_CODE = {
    'SENSOR':               CLS_SE_CODE,
    'AIR_CONDITIONER':      CLS_AC_CODE,
    'HOUSING_FACILITIES':   CLS_HF_CODE,
    'COOKING_HOUSEHOLD':    CLS_CH_CODE,
    'HEALTH':               CLS_HE_CODE,
    'MANAGEMENT_OPERATION': CLS_MO_CODE,
    'PROFILE':              CLS_PR_CODE,
}
CLS_DESC = {
    CLSGRP_CODE['SENSOR']:               _code_to_desc(CLS_SE_CODE),
    CLSGRP_CODE['AIR_CONDITIONER']:      _code_to_desc(CLS_AC_CODE),
    CLSGRP_CODE['HOUSING_FACILITIES']:   _code_to_desc(CLS_HF_CODE),
    CLSGRP_CODE['COOKING_HOUSEHOLD']:    _code_to_desc(CLS_CH_CODE),
    CLSGRP_CODE['HEALTH']:               _code_to_desc(CLS_HE_CODE),
    CLSGRP_CODE['MANAGEMENT_OPERATION']: _code_to_desc(CLS_MO_CODE),
    CLSGRP_CODE['PROFILE']:              _code_to_desc(CLS_PR_CODE),
}

INSTANCE_PR_NORMAL   = 0x01
INSTANCE_PR_SENDONLY = 0x02
INSTANCE_ALL         = 0x00

# EPC codes for all nodes
EPC_OPERATING_STATUS           = 0x80
EDT_OPERATING_STATUS_BOOTING     = 0x30
EDT_OPERATING_STATUS_NOT_BOOTING = 0x31
EPC_INSTALLATION_LOCATION      = 0x81
EDT_INSTALLATION_LOCATION_NOT_SPECIFIED = 0x00
EPC_VERSION_INFORMATION        = 0x82
EPC_IDENTIFICATION_NUMBER      = 0x83
EPC_FAULT_STATUS               = 0x88
EDT_FAULT_OCCURRED             = 0x41
EDT_FAULT_NOT_OCCURRED         = 0x42
EPC_MANUFACTURE_CODE           = 0x8a
EPC_STATUS_CHANGE_PROPERTY_MAP = 0x9d
EPC_SET_PROPERTY_MAP           = 0x9e
EPC_GET_PROPERTY_MAP           = 0x9f

# EPC code for Node Profile class
EPC_NUM_SELF_NODE_INSTANCES    = 0xd3
EPC_NUM_SELF_NODE_CLASSES      = 0xd4
EPC_INSTANCE_LIST_NOTIFICATION = 0xd5
EPC_SELF_NODE_INSTANCE_LIST_S  = 0xd6
EPC_SELF_NODE_CLASS_LIST_S     = 0xd7

# EPC code for temperature sensor class
EPC_TEMPERATURE = 0xe0

# EPC code for Low-voltage smart electric enerty meter class
EPC_ELECTRIC_UNIT                = 0xe1
EPC_HISTORICAL_CUMULATIVE_NORMAL = 0xe2
EPC_INSTANTENEOUS_ELECTRIC       = 0xe7


class EOJ(object):
    def __init__(self, clsgrp=0, cls=0, instance_id=0, eoj=None):
        if eoj is None:
            self._eoj = ((clsgrp << 16)
                         | (cls << 8)
                         | instance_id)
        else:
            self._eoj = eoj

    @property
    def eoj(self):
        return self._eoj

    @property
    def clsgrp(self):
        return (self._eoj >> 16) & 0xff

    @property
    def cls(self):
        return (self._eoj >> 8) & 0xff

    @property
    def instance_id(self):
        return self._eoj & 0xff

    def __eq__(self, eoj):
        return self._eoj == int(eoj)

    def __int__(self):
        return self._eoj

    def __str__(self):
        if self.clsgrp in CLSGRP_DESC:
            s = '{0}'.format(CLSGRP_DESC[self.clsgrp])
        else:
            s = '{0:02x}'.format(self.clsgrp)
        if self.clsgrp in CLS_DESC and self.cls in CLS_DESC[self.clsgrp]:
            s += '.{0}'.format(CLS_DESC[self.clsgrp][self.cls])
        else:
            s += '.{0:02x}'.format(self.cls)
        s += '.{0:02x}'.format(self.instance_id)
        return s

    def is_clsgrp(self, clsgrp):
        return self.clsgrp == clsgrp

    def is_cls(self, cls):
        return self.cls == cls

    def is_all_instance(self):
        return self.instance_id == INS_ALL

class Message(object):
    def __init__(self, tid=None, seoj=None, deoj=None,
                 esv=None, opc=None, properties=None):
        self.tid = tid
        self.seoj = seoj
        self.deoj = deoj
        self.esv = esv
        self.opc = opc
        if properties is not None:
            self.properties = properties
        else:
            self.properties = []

    def __str__(self):
        s = ''
        if self.tid is not None:
            s += 'TID={0:#06x}'.format(self.tid)
        else:
            s += '(None)'
        s += ', SEOJ={0}({1:#08x})'.format(str(self.seoj), int(self.seoj))
        s += ', DEOJ={0}({1:#08x})'.format(str(self.deoj), int(self.deoj))
        s += ', ESV={0}({1:#04x})'.format(self._get_esv_desc(self.esv),
                                          self.esv)
        s += ', OPC={0:#04x}'.format(self.opc)
        for p in self.properties:
            s += ', ' + str(p)
        return s

    def _get_esv_desc(self, esv):
        if esv in ESV_DESC:
            return ESV_DESC[esv]
        return '{0:#04x}'.format(esv)

class Property(object):
    def __init__(self, epc=None, edt=None):
        self._epc = epc
        if edt is None:
            self._pdc = 0
        else:
            self._pdc = len(edt)
        self._edt = edt

    @property
    def epc(self):
        return self._epc

    @property
    def pdc(self):
        return self._pdc

    @property
    def edt(self):
        return self._edt

    def __str__(self):
        s = 'EPC={0:#04x}'.format(self.epc)
        s+= ', PDC={0:#04x}'.format(self.pdc)
        if self.edt is not None:
            s+= ', EDT=['
            for dt in self.edt:
                s+='{0:#04x}, '.format(dt)
            s+= ']'
        return s

COMMON_HDR_LEN = 12 # EHD1, EHD2, TID, SEOJ, DEOJ, ESV, and OPC
def decode(data):
    # decode Echonet Lite header and SEOJ, DEOJ.
    if len(data) < COMMON_HDR_LEN:
        # not an Echonet Lite frame
        print('not an Echonet Lite frame, missing common headers.')
        return None
    (ehd1, ehd1, tid,
     seoj0, seoj1, seoj2,
     deoj0, deoj1, deoj2,
     esv, opc) = struct.unpack('!2BH8B',
                               data[0:COMMON_HDR_LEN])
    seoj = EOJ(seoj0, seoj1, seoj2)
    deoj = EOJ(deoj0, deoj1, deoj2)

    # decode EPCs
    def decode_epc():
        (epc, pdc) = struct.unpack('!2B', data[ptr:ptr+2])
        edt = None
        if pdc != 0:
            edt = struct.unpack('!{0}B'.format(pdc), data[ptr+2:ptr+2+pdc])
        pl = Property(epc, edt)
        return (pl, 2 + pdc)

    msg = Message()
    msg.tid = tid
    msg.seoj = seoj
    msg.deoj = deoj
    msg.esv = esv
    msg.opc = opc
    ptr = COMMON_HDR_LEN
    nproperties = opc
    while len(data[ptr:]) > 1:
        (pl, pl_len) = decode_epc()
        msg.properties.append(pl)
        ptr += pl_len
        nproperties -= 1
    if nproperties != 0:
        print('OPC count ({0}) and # of properties ({1}) doesn\'t match.'.format(
            opc, opc - nproperties))
        return None

    return msg


def encode(message):
    data = bytearray()
    if message.opc == None:
        message.opc = len(message.properties)

    data += struct.pack('!2BH6B',
                        EHD1,
                        EHD2_FMT1,
                        message.tid & 0xffff,
                        message.seoj.clsgrp,
                        message.seoj.cls,
                        message.seoj.instance_id,
                        message.deoj.clsgrp,
                        message.deoj.cls,
                        message.deoj.instance_id)
    data += struct.pack('!B', message.esv)
    data += struct.pack('!B', message.opc)
    for p in message.properties:
        data += struct.pack('!BB', p.epc, p.pdc)
        if p.pdc > 0:
            data += struct.pack('!{0}B'.format(p.pdc), *p.edt)

    return data


if __name__ == '__main__':
    m = Message()
    m.tid = 2
    m.seoj = EOJ(10,10,10)
    m.deoj = EOJ(20,20,20)
    m.esv = 0x60
    m.opc = 2
    req1 = Property()
    req1.epc = 0x80
    req1.pdc = 0x02
    req1.edt = [0x01, 0x02]
    m.properties.append(req1)
    req2 = Property()
    req2.epc = 0x81
    req2.pdc = 0x03
    req2.edt = [0x03, 0x04, 0x05]
    m.properties.append(req2)
    print(m)
    em = encode(m)
    m2 = decode(em)
    print(m2)
