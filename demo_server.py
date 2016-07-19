#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from flask import Flask, render_template
from kazoo.client import KazooClient
from kazoo.exceptions import NodeExistsError, NoNodeError, SessionExpiredError
from random import choice
from requests.exceptions import ConnectionError

import consul
import etcd
import zc.zk

COLORS = ['#859900', '#cb4b16', '#dc322f', '#6c71c4', '#268bd2', '#2aa198',
          '#d33682', '#b58900']
SERVER = 'localhost'


def consul_set_color(color):
    """
    Set the color in the K/V store, this is a basic usage.
    """
    try:
        cons.kv.put('ep2016/color', color)
    except (ConnectionError, consul.ConsulException):
        print('consul host is down, reconnecting...')


def consul_get_hosts():
    """
    Returns the list of available hosts providing the 'ep2016' service.
    """
    consul_hosts = []
    try:
        index, services = cons.health.service('ep2016', passing=True)
        for service_info in services:
            service = service_info['Service']
            consul_hosts.append((service.get('Address'), service.get('Port')))
    except (ConnectionError, consul.ConsulException):
        print('consul host is down, reconnecting...')
    return consul_hosts


def etcd_set_color(color):
    """
    Set the color in the K/V store, this is a basic usage.
    """
    try:
        etc.write('/ep2016/color', color)
    except (etcd.EtcdException, etcd.EtcdConnectionFailed):
        print('etcd host is down, reconnecting...')


def etcd_get_hosts():
    """
    Returns the list of available hosts providing the 'ep2016' service.
    """
    etcd_hosts = []
    try:
        children = etc.read('/ep2016/providers', recursive=True).children
        for child in children:
            if child.dir is True:
                continue
            host, port = child.value.split(':')
            etcd_hosts.append((host, port))
    except (etcd.EtcdException, etcd.EtcdConnectionFailed):
        print('etcd host is down, reconnecting...')
    return etcd_hosts


def zookeeper_set_color(color):
    """
    Set the color in the K/V store, this is a basic usage.

    This is not ephemeral so it will survive this script's death.
    """
    if zk.state == 'CONNECTED':
        try:
            zk.create(path='/ep2016/color',
                      value=color,
                      ephemeral=False,
                      makepath=True)
        except NodeExistsError:
            kz.set(path='/ep2016/color', value=color)
        except SessionExpiredError:
            print('zookeeper host is down, reconnecting...')


def zookeeper_get_hosts():
    """
    Returns the list of available hosts providing the 'ep2016' service.
    """
    zookeeper_hosts = []
    if zk.state == 'CONNECTED' or True:
        try:
            addresses = zk.children('/ep2016/providers')
        except NoNodeError:
            print('zookeeper node path is missing')
        except SessionExpiredError:
            print('zookeeper host is down, reconnecting...')
        else:
            for address in sorted(addresses):
                host, port = address.split(':')
                zookeeper_hosts.append((host, port))
    return zookeeper_hosts


if __name__ == '__main__':
    # zookeeper
    # connect to multiple zookeeper nodes with one we know will fail
    # this demonstrates the kazoo fault tolerance
    kz = KazooClient(hosts='{}:2181,unknown:2181'.format(SERVER))
    kz.start()
    zk = zc.zk.ZooKeeper(kz)

    # etcd
    etc = etcd.Client(host=SERVER, port=4001, allow_reconnect=True)

    # consul
    cons = consul.Consul(host=SERVER, port=8500)

    app = Flask(__name__)

    @app.route('/')
    def hello():
        color = choice(COLORS)

        # zookeeper
        # set color and get available hosts providing the 'ep2016' service
        zookeeper_set_color(color)
        zookeeper_hosts = zookeeper_get_hosts()

        # etcd
        # set color and get available hosts providing the 'ep2016' service
        etcd_set_color(color)
        etcd_hosts = etcd_get_hosts()

        # consul
        # set color and get available hosts providing the 'ep2016' service
        consul_set_color(color)
        consul_hosts = consul_get_hosts()

        return render_template('server.html.j2',
                               color=color,
                               consul_hosts=consul_hosts,
                               etcd_hosts=etcd_hosts,
                               zookeeper_hosts=zookeeper_hosts)

    # block until we CTRL+C
    app.run(host='0.0.0.0', port=8000, debug=True)
