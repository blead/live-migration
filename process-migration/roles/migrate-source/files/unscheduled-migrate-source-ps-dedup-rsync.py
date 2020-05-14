#!/usr/bin/python
# based on https://www.redhat.com/en/blog/container-migration-around-world
import socket
import sys
import select
import time
import os
import subprocess
import multiprocessing, multiprocessing.queues
import re
import distutils.util

base_path = '/home/ubuntu/'
precopy_dir = 'predump'
precopy_relative_path = '../' + precopy_dir
precopy_enabled = False
postcopy_enabled = False
pageserver_enabled = False
autodedup_enabled = False
postcopy_port_start = 8027
postcopy_pipe_prefix = '/tmp/postcopy-pipe-'
target_port = 8888

if len(sys.argv) < 3:
  print 'Usage: ' + sys.argv[0] + ' <container1>[,<containers2>,...] <target-address> [pre-copy] [pageserver] [post-copy-port-start] [auto-dedup]'
  sys.exit(1)

containers = sys.argv[1].split(',')
target_address = sys.argv[2]
if len(sys.argv) > 3:
  precopy_enabled = distutils.util.strtobool(sys.argv[3])
if len(sys.argv) > 4:
  # postcopy_enabled = distutils.util.strtobool(sys.argv[4])
  pageserver_enabled = distutils.util.strtobool(sys.argv[4])
if len(sys.argv) > 5:
  postcopy_port_start = int(sys.argv[5])
if len(sys.argv) > 6:
  autodedup_enabled = distutils.util.strtobool(sys.argv[6])
postcopy_ports = [postcopy_port_start + i for i in xrange(len(containers))]
queue = multiprocessing.queues.SimpleQueue()

def error(error):
  print 'Error: ' + error
  if error:
    print error
  sys.exit(1)


from collections import defaultdict
log_dict = defaultdict(lambda: 0)
def log():
  import os
  import csv

  # number = os.environ['NUMBER']
  # experiment_name = os.environ['EXPERIMENT_NAME']

  global log_dict
  # log_dict['experiment'] = experiment_name
  log_dict['premigration'] = float(log_dict['predump']) + float(log_dict['precopy'])
  log_dict['totaltime'] = float(log_dict['premigration']) + float(log_dict['downtime'])
  
  # filename = 'experiment_%s.csv' % number
  # dirname = os.path.dirname(filename)
  # if not os.path.exists(dirname):
      # os.makedirs(dirname)

  # with open(filename, mode='w') as csv_file:
  #   fieldnames = ['experiment', 'scenario', 'predump', 'precopy', 'premigration', 'checkpoint', 'diff', 'transfer', 'restore', 'downtime', 'totaltime']
  #   writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

  #   writer.writeheader()
  #   writer.writerow(log_dict)

  print(log_dict)

def predump(container):
  container_path = base_path + container
  old_cwd = os.getcwd()
  os.chdir(container_path)
  cmd = 'runc checkpoint --pre-dump'
  if pageserver_enabled:
    if container == 'wordpress':
      cmd += ' --page-server 10.0.1.5:9095'
    elif container == 'mysql':
      cmd += ' --page-server 10.0.1.5:9096'
    else:
      exit(1)
  if autodedup_enabled:
    cmd += ' --auto-dedup'
  cmd += ' --image-path ' + precopy_dir + ' ' + container
  print 'prudump cmd : %s' % (cmd)
  start = time.time()
  process = subprocess.Popen(cmd, shell=True)
  ret = process.wait()
  end = time.time()
  print '%s: predump finished after %.2f second(s) with exit code %d' % (container, end - start, ret)
  eval_process = subprocess.Popen('du -sh ' + container_path + '/' + precopy_dir, shell=True, stdout=subprocess.PIPE)
  size, stderr = eval_process.communicate()
  print '%s: predump size %s' % (container, size)
  os.chdir(old_cwd)
  if ret != 0 or stderr:
    error(container + ' predump failed.')

def checkpoint((container, postcopy_port)):
  container_path = base_path + container
  postcopy_pipe_path = postcopy_pipe_prefix + container
  old_cwd = os.getcwd()
  os.chdir(container_path)
  cmd = 'runc checkpoint'
  if precopy_enabled:
    cmd += ' --parent-path ' + precopy_relative_path
  if pageserver_enabled:
    if container == 'wordpress':
      cmd += ' --page-server 10.0.1.5:9090'
    elif container == 'mysql':
      cmd += ' --page-server 10.0.1.5:9091'
    else:
      exit(1)
  if autodedup_enabled:
    cmd += ' --auto-dedup'
  if postcopy_enabled:
    cmd += ' --lazy-pages --page-server localhost:' + str(postcopy_port)
    try:
      os.unlink(postcopy_pipe_path)
    except:
      pass
    os.mkfifo(postcopy_pipe_path)
    cmd += ' --status-fd ' + postcopy_pipe_path
  cmd += ' ' + container
  print 'checkpoint cmd: %s' % (cmd)
  start = time.time()
  process = subprocess.Popen(cmd, shell=True)
  if postcopy_enabled:
    pipe = os.open(postcopy_pipe_path, os.O_RDONLY)
    ret = os.read(pipe, 1)
    if ret == '\0':
      print container + ': ready for lazy page transfer'
    ret = 0
  else:
    ret = process.wait()
  end = time.time()
  print '%s: checkpoint finished after %.2f second(s) with exit code %d' % (container, end - start, ret)
  eval_process = subprocess.Popen('du -sh ' + container_path + '/checkpoint', shell=True, stdout=subprocess.PIPE)
  size, stderr = eval_process.communicate()
  print '%s: checkpoint size %s' % (container, size)
  os.chdir(old_cwd)
  if ret != 0 or stderr:
    error(container + ' checkpoint failed.')

def transfer(container):
  container_path = base_path + container
  eval_process = subprocess.Popen('du -sh ' + container_path, shell=True, stdout=subprocess.PIPE)
  size, stderr = eval_process.communicate()
  print '%s: total size (container + predump) %s' % (container, size)
  if container == 'mysql':
    cmd = 'rsync -aq %s %s::home' % (container_path, target_address)
  else:
    cmd = 'rsync -aq %s/predump %s::home/%s' % (container_path, target_address, container)
  print '%s: transferring predump to %s::%s' % (container, target_address, container)
  start = time.time()
  process = subprocess.Popen(cmd, shell=True)
  ret = process.wait()
  end = time.time()
  print '%s: predump transfer time %.2f seconds' % (container, end - start)
  if ret != 0 or stderr:
    error(container + ' transfer failed.')

def calculate_size(container):
  container_path = base_path + container
  cmd = 'rsync -a --dry-run --stats %s %s::home' % (container_path, target_address)
  print container + ': evaluating checkpoint transfer size'
  start = time.time()
  process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
  ret, stderr = process.communicate()
  match = re.search('Total transferred file size: ([\d,]+) bytes', ret)
  if match == None or stderr:
    error(container + ' size calculation failed.')
  size = int(match.group(1).replace(',', ''))
  end = time.time()
  print '%s: total checkpoint transfer size %d bytes' % (container, size)
  print '%s: checkpoint transfer size calculation time %.2f seconds' % (container, end - start)
  return size

def checkpoint_transfer(container):
  container_path = base_path + container
  eval_process = subprocess.Popen('du -sh ' + container_path, shell=True, stdout=subprocess.PIPE)
  size, stderr = eval_process.communicate()
  print '%s: total size (container + predump + checkpoint) %s' % (container, size)
  if False and container == 'mysql':
    cmd = 'rsync -aq %s %s::home' % (container_path, target_address)
  else:
    cmd = 'rsync -aq %s/checkpoint %s::home/%s' % (container_path, target_address, container)
  print '%s: transferring checkpoint to %s::%s' % (container, target_address, container)
  start = time.time()
  process = subprocess.Popen(cmd, shell=True)
  ret = process.wait()
  end = time.time()
  print '%s: checkpoint transfer time %.2f seconds' % (container, end - start)
  if ret != 0 or stderr:
    error(container + ' transfer failed.')
  # notify(container, postcopy_port)

def notify((container, postcopy_port)):
  start = time.time()
  cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  cs.connect((target_address, target_port))
  input = [cs]
  cs.send(
    '{ "restore" : { "path" : "' + base_path +
    '", "container" : "' + container +
    '", "lazy" : "' + str(postcopy_enabled) +
    '", "port" : "' + str(postcopy_port) + '" } }'
  )
  while True:
    inputready, outputready, exceptready = select.select(input,[],[], 5)
    if not inputready:
      break
    for s in inputready:
      answer = s.recv(1024)
      print container + ': ' + answer
  end = time.time()
  print '%s: target notification time %.2f seconds' % (container, end - start)

pool = multiprocessing.Pool(processes=len(containers))

if precopy_enabled:
  print 'PREDUMP'
  start = time.time()
  pool.map(predump, containers)
  end = time.time()
  log_dict['predump'] = '%.2f' % (end - start)

  print 'PREDUMP TRANSFER'
  tart = time.time()
  pool.map(transfer, containers)
  end = time.time()
  log_dict['precopy'] = '%.2f' % (end - start)

print 'CHECKPOINT'
downtime_start = time.time()
# Start our dummy server here
subprocess.call('echo "enable server back1/redir" | \
  socat unix-connect:/var/run/haproxy/admin.sock stdio', shell=True)
subprocess.call('echo "disable server back1/source" | \
  socat unix-connect:/var/run/haproxy/admin.sock stdio', shell=True)
start = time.time()
pool.map(checkpoint, zip(containers, postcopy_ports))
end = time.time()
log_dict['checkpoint'] = '%.2f' % (end - start)

print 'CALCULATE'
container_sizes = pool.map(calculate_size, containers)

print 'CHECKPOINT TRANSFER'
checkpoint_transfer_start = time.time()
pool.map(checkpoint_transfer, containers)
checkpoint_transfer_end = time.time()
print 'Total checkpoint transfer time: %.2f second(s)' % (checkpoint_transfer_end - checkpoint_transfer_start)
log_dict['transfer'] = '%.2f' % (checkpoint_transfer_end - checkpoint_transfer_start)


print 'NOTIFY'
start = time.time()
pool.map(notify, zip(containers, postcopy_ports))
end = time.time()
downtime_end = time.time()
log_dict['restore'] = '%.2f' % (end - start)
log_dict['downtime'] = '%.2f' % (downtime_end - downtime_start)

print 'Total downtime: %.2f second(s)' % (downtime_end - downtime_start)

log_dict['premigration'] = float(log_dict['predump']) + float(log_dict['precopy'])
log_dict['totaltime'] = float(log_dict['premigration']) + float(log_dict['downtime'])

print(log_dict)
# log()