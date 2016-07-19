#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from flask import Flask, render_template
from kazoo.exceptions import NodeExistsError, NoNodeError, SessionExpiredError
from socket import gethostname
from time import sleep

import zc.zk

PATH = '/ep2016/providers'
PORT = 5000
SERVER = 'localhost'


def register(client):
    """
    On zookeeper we want to register as an ephemeral node after creating
    the base PATH on the K/V store.
    """
    while True:
        if client.state == 'CONNECTED':
            try:
                client.create(PATH, ephemeral=False, makepath=True)
            except NodeExistsError:
                pass
            try:
                client.register(PATH, (gethostname(), PORT))
                break
            except NodeExistsError:
                print('waiting for registration...')
                sleep(0.5)
        else:
            print('zookeeper host is down, reconnecting...')
            sleep(0.5)


def get_color(client):
    """
    Read the color from the K/V store, this is a basic usage.
    """
    try:
        color = client.properties('/ep2016/color').get('string_value')
    except (NoNodeError, SessionExpiredError):
        color = '#000000'
    return color


if __name__ == '__main__':
    # connect to multiple zookeeper nodes
    # the 'unknown' node will fail but demonstrates that the client is handling
    # failing hosts gracefully
    while True:
        try:
            zk = zc.zk.ZooKeeper('{}:2181,unknown:2181'.format(SERVER),
                                 session_timeout=5)
            break
        except zc.zk.FailedConnect:
            print('zookeeper host is down, reconnecting...')
            sleep(0.5)

    # register on the /ep2016/providers znode
    register(zk)

    # create our basic Flask application
    app = Flask(__name__)

    @app.route('/')
    def hello():
        color = get_color(zk)
        return render_template('client.html.j2',
                               color=color,
                               discovery_service='ZooKeeper',
                               host=gethostname())

    # block until we CTRL+C
    app.run(host='0.0.0.0', port=PORT)
