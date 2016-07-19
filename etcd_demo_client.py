#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from flask import Flask, render_template
from socket import gethostname
from time import sleep

import etcd
import threading

PATH = '/ep2016/providers'
PORT = 5001
SERVER = 'localhost'
TTL = 5


class HealthPinger(threading.Thread):
    """
    """
    stop = False

    def __init__(self):
        """
        """
        threading.Thread.__init__(self)
        self.client = etcd.Client(host=SERVER, port=4001, allow_reconnect=True)

    def run(self):
        """
        Infinite loop registration to avoid being deleted from the K/V store
        by the TTL.

        We give ourselves 1s delay to register, this is a fail fast strategy.
        """
        while HealthPinger.stop is False:
            self.register()
            sleep(TTL - 1)
        self.deregister()

    def register(self):
        """
        On etcd we want to register as an ephemeral node after creating
        the base PATH on the K/V store.
        """
        my_host = '{}:{}'.format(gethostname(), PORT)
        try:
            self.client.read(PATH)
        except (etcd.EtcdKeyNotFound, KeyError):
            self.client.write(PATH, None, dir=True)
        except etcd.EtcdException:
            print('etcd host is down, reconnecting...')
            return

        try:
            self.client.write(PATH + '/' + my_host,
                              my_host,
                              dir=False,
                              ttl=TTL)
        except etcd.EtcdAlreadyExist:
            pass
        except etcd.EtcdException:
            print('etcd host is down, reconnecting...')
            return

    def deregister(self):
        """
        We also can deregister nicely by deleting our node from the K/V store.
        """
        my_host = '{}:{}'.format(gethostname(), PORT)
        try:
            self.client.delete(PATH + '/' + my_host)
        except (etcd.EtcdKeyNotFound, etcd.EtcdException, KeyError):
            pass


def get_color(client):
    """
    Read the color from the K/V store, this is a basic usage.
    """
    try:
        color = client.read('/ep2016/color').value
    except (etcd.EtcdKeyNotFound, etcd.EtcdException):
        color = '#000000'
    return color


if __name__ == '__main__':
    # connect to etcd with automated reconnection
    while True:
        try:
            etc = etcd.Client(host=SERVER, port=4001, allow_reconnect=True)
            break
        except etcd.EtcdException:
            print('etcd host is down, reconnecting...')
        sleep(0.5)

    # register ourself on the /ep2016/providers node
    register_thread = HealthPinger().start()

    # create our basic Flask application
    app = Flask(__name__)

    @app.route('/')
    def hello():
        color = get_color(etc)
        return render_template('client.html.j2',
                               color=color,
                               discovery_service='etcd',
                               host=gethostname())

    # block until we CTRL+C
    app.run(host='0.0.0.0', port=PORT)

    # ask our health thread to deregister and stop
    HealthPinger.stop = True
