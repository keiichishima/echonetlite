#!/usr/bin/env python
# -*- coding: utf-8 -*-

from twisted.internet import reactor
from twisted.internet.protocol import Protocol

import echonetlite
from echonetlite import protocol

class ShellServer(Protocol):
    def dataReceived(self, data):
        command = data.decode('utf-8').rstrip()
        if command == 'search':
            reactor.callWhenRunning(self.do_search)
        elif command == 'list_nodes':
            for node_id in echonetlite.interfaces.monitor.nodes:
                self.transport.write(str(echonetlite.interfaces.monitor.nodes[node_id]).encode('utf-8'))
                self.transport.write('\n'.encode('utf-8'))
        if command == 'shutdown':
            reactor.stop()
        elif command == 'quit':
            self.transport.loseConnection()
        else:
            print('unknown command {0}.'.format(command))

    def do_search(self):
        profile = echonetlite.interfaces.monitor.get_self_node().get_profile()
        profile.send(esv=protocol.ESV_CODE['GET'],
                     props=[protocol.Property(epc=0xd6),],
                     to_eoj=protocol.EOJ(protocol.CLSGRP_CODE['PROFILE'],
                                         protocol.CLS_PR_CODE['PROFILE'],
                                         protocol.INS_PR_NORMAL))
