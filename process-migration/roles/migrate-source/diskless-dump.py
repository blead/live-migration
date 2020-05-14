import subprocess
import yaml

import socket
from contextlib import closing


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def get_pageserver_cmd(container, port=None):
    if port is None:
        port = find_free_port()
    # subprocess.run("criu page-server --images-dir {} --port {}".format(container, port))
    return "criu page-server --images-dir {} --port {}".format(container, port)


with open("config.yaml", 'r') as ymlfile:
    cfg = yaml.full_load(ymlfile)
    print(cfg)

for container in cfg['containers']:
    print(container)
    print(get_pageserver_cmd(container))
