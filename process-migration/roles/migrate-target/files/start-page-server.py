#!/usr/bin/python3
import subprocess
import yaml
import socket
import pathlib
from contextlib import closing

BASE_PATH = '/home/ubuntu'

def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

def get_pageserver_cmd_and_port(container, port=None):
    dir = "{}/{}/checkpoint".format(BASE_PATH, container)
    path = pathlib.Path(dir)
    path.mkdir(parents=True, exist_ok=True)
    if port is None:
        port = find_free_port()
    cmd = "criu page-server --images-dir {} --port {}".format(dir, port)
    print(cmd)
    return cmd, port

with open("config.yaml", 'r') as ymlfile:
    cfg = yaml.full_load(ymlfile)

commands = []
for container in cfg['containers']:
    if container['pageserver']:
        pageserver_port = container['pageserver']['port']
        cmd, port = get_pageserver_cmd_and_port(container['name'], pageserver_port)
    else:
        cmd, port = get_pageserver_cmd_and_port(container['name'])
    print("[{}] running pageserver on port {}".format(container['name'], port))
    commands.append(cmd)

procs = [ subprocess.Popen(cmd, shell=True) for cmd in commands ]
for p in procs:
    print(p)
    p.wait()