#!/usr/bin/env python
# -*- coding: utf-8 -*-

from twisted.internet import reactor
from twisted.internet import task
from twisted.internet.protocol import Factory

from echonetlite import shellservice
from echonetlite import ipv4adapter
from echonetlite import middleware
from echonetlite import protocol

class MessageListener(object):
    def __init__(self, monitor):
        self._monitor = monitor

    def on_did_receive(self, msg, from_node):
        # find devices registered in this node
        self_node = self._monitor.get_self_node()
        device = None
        # deliver the message to self devices
        # (XXX need to handel instance_id == 0)
        for d in self_node.devices.values():
            if msg.deoj == d.eoj:
                device = d
                break
            if (msg.deoj.is_clsgrp(d.eoj.clsgrp)
                and msg.deoj.is_cls(d.eoj.cls)
                and msg.deoj.is_all_instance):
                device = d
                break
        if device is None:
            print('not ours: ', msg)
            return

        # call device default message receivers
        if msg.esv in protocol.ESV_REQUEST_CODES:
            device.on_did_receive_request(msg, from_node)
        if msg.esv in protocol.ESV_RESPONSE_CODES:
            device.on_did_receive_response(msg, from_node)
        if msg.esv in protocol.ESV_ERROR_CODES:
            device.on_did_receive_error(msg, from_node)

        # call user defined listeners
        for device in self._monitor.nodes[from_node.node_id].devices.values():
            key_grpcls = msg.seoj.clsgrp << 16 | msg.seoj.cls << 8
            for prop in msg.properties:
                key = key_grpcls | prop.epc
                if key in device.listeners:
                    device.listeners[key](from_node.node_id,
                                          msg.seoj,
                                          device,
                                          msg.esv,
                                          prop)


class Monitor(object):
    def __init__(self):
        # _node_id: a layer 3 address string of this node
        self._node_id = None
        # _nodes: a dict with key as _node_id, value as middleware.Node()
        self._nodes = {}
        # _loopingcalls: a list of twisted.internet.task.LoopingCall()
        self._loopingcalls = []
        # _lister: a MessageLister()
        self._listener = MessageListener(self)
        # sender: adapter.Sender()
        self.sender = None
        # _tid: transaction id
        self._tid = 0

    @property
    def nodes(self):
        return self._nodes

    def get_self_node(self):
        assert(self._node_id in self._nodes)
        return self._nodes[self._node_id]

    def get_node(self, node_id):
        if node_id in self._nodes:
            return self._nodes[node_id]
        return None

    def start(self, node_id, devices, adapter=ipv4adapter):
        self._node_id = node_id
        self.sender = adapter.Sender(local_addr=node_id)
        self_node = middleware.Node(node_id, devices)
        self_node.get_profile().update_device_numbers(devices)
        self._nodes[node_id] = self_node
        reactor.listenMulticast(adapter.echonet_lite_port,
                                adapter.Receiver(
                                    local_addr=node_id,
                                    on_did_receive=self.on_did_receive),
                                listenMultiple=True)
        f = Factory()
        f.protocol = shellservice.ShellServer
        reactor.listenTCP(3611, f)
        reactor.run()

    def on_did_receive(self, data, from_node_id):
        msg = protocol.decode(data)
        if msg is None:
            return
        # add a Node instance if from_node_id is not in the _nodes dict.
        if from_node_id not in self._nodes:
            n = middleware.Node(from_node_id, {})
            self._nodes[from_node_id] = n
        # deliver the received message to listeners.
        self._listener.on_did_receive(msg, self._nodes[from_node_id])

    def send(self, msg, to_node_id=None):
        if msg.tid is None:
            msg.tid = self._tid
            self._tid = (self._tid + 1) % 0xffff
        data = protocol.encode(msg)
        if self.sender is not None:
            reactor.callWhenRunning(self.sender.sendDatagram, data, to_node_id)

    def schedule_call(self, timeout, callback, **kwargs):
        if timeout == 0:
            reactor.callWhenRunning(callback, **kwargs)
        else:
            reactor.callLater(timeout, callback, **kwargs)

    def schedule_loopingcall(self, timeout, callback, **kwargs):
        l = task.LoopingCall(callback, **kwargs)
        l.start(timeout)
        self._loopingcalls.append(l)
        return l

    def unschedule_loopingcall(self, l):
        if l in self._loopingcalls:
            l.stop()
            self._loopingcalls.remove(l)

monitor = Monitor()
