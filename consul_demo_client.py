#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from flask import Flask, render_template
from requests.exceptions import ConnectionError
from socket import gethostname
from time import sleep

import consul

PORT = 5002
SERVER = 'localhost'


def register(client):
    """
    Registering on consul is straightfoward but we also want the consul server
    to run a health check of our service at given interval.

    This is a fail fast strategy so the interval is low and timeout is not set.
    """
    # create a health check that consul will use to monitor us
    check_http = consul.Check.http('http://{}:{}'.format(gethostname(), PORT),
                                   interval='2s')

    # register on consul with the health check
    while True:
        try:
            service_id = '{}:{}'.format(gethostname(), PORT)
            client.agent.service.register('ep2016',
                                          service_id=service_id,
                                          address=gethostname(),
                                          port=PORT,
                                          check=check_http)
            break
        except (ConnectionError, consul.ConsulException) as err:
            print(err)
            print('consul host is down, reconnecting...')
            sleep(0.5)


def get_color(client):
    """
    Read the color from the K/V store, this is a basic usage.
    """
    try:
        index, key = client.kv.get('ep2016/color')
        if key is None:
            raise IndexError('the key is not present')
        color = key.get('Value')
    except (IndexError, ConnectionError, consul.ConsulException):
        color = '#000000'
    return color


if __name__ == '__main__':
    # connect to consul
    cons = consul.Consul(host=SERVER, port=8500)

    # register our service in the consul catalog with health check enabled
    register(cons)

    # create our basic Flask application
    app = Flask(__name__)

    @app.route('/')
    def hello():
        color = get_color(cons)
        return render_template('client.html.j2',
                               color=color,
                               discovery_service='Consul',
                               host=gethostname())

    # block until we CTRL+C
    app.run(host='0.0.0.0', port=PORT)

    # deregister from consul
    try:
        cons.agent.service.deregister('ep2016')
    except ConnectionError:
        pass
