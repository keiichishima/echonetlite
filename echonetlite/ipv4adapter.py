#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket

from twisted.internet.protocol import DatagramProtocol

echonet_lite_group = '224.0.23.0'
# echonet_lite_group_IPv6 = 'ff02::1'
echonet_lite_port = 3610

class Receiver(DatagramProtocol):
    def __init__(self, **kwargs):
        super(Receiver, self).__init__()
        self._local_addr = kwargs['local_addr']
        self._on_did_receive = kwargs['on_did_receive']

    def startProtocol(self):
        self.transport.setTTL(1)
        self.transport.joinGroup(echonet_lite_group,
                                 interface=self._local_addr)

    def datagramReceived(self, datagram, address):
        node_id = address[0]
        self._on_did_receive(datagram, node_id)

class Sender(object):
    def __init__(self, local_addr):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.IPPROTO_IP,
                               socket.IP_MULTICAST_IF,
                               socket.inet_aton(local_addr))

    def sendDatagram(self, datagram, node_id=None):
        if node_id is None:
            address = (echonet_lite_group, echonet_lite_port)
        else:
            address = (node_id, echonet_lite_port)
        self.socket.sendto(datagram, address)

if __name__ == '__main__':
    from twisted.internet import reactor

    def on_did_receive(data):
        print(data)

    reactor.listenMulticast(echonet_lite_port,
                            Receiver(
                                local_addr='',
                                on_did_receive=on_did_receive),
                            listenMultiple=True)
    reactor.run()
