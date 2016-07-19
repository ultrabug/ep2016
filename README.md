# EuroPython 2016 talk

## Using Service Discovery to build dynamic python applications

This repository features the **source code** showcased in my talk.

## Prerequisites
A local instance of consul, etcd and zookeeper with no special configuration, just localhost stuff.

If you want to test only one of them, please comment the useless code for the other service discovery servers at the bottom of the `demo_server.py` file.

## Run it !

- First we create a virtualenv, install the python librairies and run the demo server.

```bash

mkvirtualenv ep2016
pip install -r requirements.txt

python demo_server.py
```

- Then point your browser to the local demo server at `http://localhost:8000/`
- You will get the basic interface where you'll see that no service has been discovered yet
- Now run the client of your choosing (or all of them) **on a new console** and see the service appear on the web interface !

```bash
# workon is available via the virtualenvwrapper package
# whatever you use, just make sure that you are in the virtualenv you created earlier
workon ep2016

python consul_demo_client.py
```
