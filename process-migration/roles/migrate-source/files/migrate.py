#!/usr/bin/python3
import subprocess
import yaml
import socket
import pathlib
from contextlib import closing

BASE_PATH = '/home/ubuntu/'

def get_checkpoint_cmd(container):
    dir = "/tmp/dump-{}/".format(container['name'])
    path = pathlib.Path(dir)
    path.mkdir(parents=True, exist_ok=True)


with open("config.yaml", 'r') as ymlfile:
    cfg = yaml.full_load(ymlfile)

commands = []


print('==== CHECKPOINT ======')
downtime_start = time.time()

pool.map(checkpoint, list(zip(containers, postcopy_ports)))

print('>> CALCULATE')
container_sizes = pool.map(calculate_size, containers)
transfer_tasks = list(reversed(sorted(zip(containers, container_sizes, postcopy_ports), key=lambda x: x[1])))

print('>> CHECKPOINT TRANSFER + NOTIFY')
transfer_results = []
for (index, (container, size, postcopy_port)) in enumerate(transfer_tasks):
  target_size = 0
  if index + 1 < len(transfer_tasks):
    target_size = transfer_tasks[index + 1][1]
  print('Starting transfer of ' + container)
  result = pool.apply_async(measured_transfer, (container, size, target_size, postcopy_port))
  print('Waiting for transfer of ' + container)
  ret = queue.get()
  if (ret != 0):
    error(container + ' measured transfer failed.')
  transfer_results.append(result)
[result.wait() for result in transfer_results]
downtime_end = time.time()
print('Total downtime: %.2f second(s)' % (downtime_end - downtime_start))
