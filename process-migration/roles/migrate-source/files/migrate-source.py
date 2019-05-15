#!/usr/bin/python
# based on https://www.redhat.com/en/blog/container-migration-around-world
import socket
import sys
import select
import time
import os
import shutil
import subprocess
import distutils.util

base_path = '/home/ubuntu/'
predump_dir = 'predump'
pre = False
lazy = False
lazy_port = '8027'
postcopy_pipe_prefix = '/tmp/postcopy-pipe-'

if len(sys.argv) < 3:
  print 'Usage: ' + sys.argv[0] + ' <container id> <dest> [pre-copy] [post-copy] [post-copy-port]'
  sys.exit(1)

container = sys.argv[1]
dest = sys.argv[2]
if len(sys.argv) > 3:
  pre = distutils.util.strtobool(sys.argv[3])
if len(sys.argv) > 4:
  lazy = distutils.util.strtobool(sys.argv[4])
if len(sys.argv) > 5:
  lazy_port = str(int(sys.argv[5]))

container_path = base_path + container
predump_relative_path = '../' + predump_dir
postcopy_pipe_path = postcopy_pipe_prefix + container

def error():
  print 'Something did not work. Exiting!'
  sys.exit(1)

def pre_dump():
  old_cwd = os.getcwd()
  os.chdir(container_path)
  cmd = 'runc checkpoint --pre-dump --image-path ' + predump_dir + ' ' + container
  print cmd
  start = time.time()
  ret = os.system(cmd)
  end = time.time()
  print "%s: predump finished after %.2f second(s) with %d" % (container, end - start, ret)
  os.chdir(old_cwd)
  if ret != 0:
    error()

def real_dump(precopy, postcopy, postcopy_port = '8027'):
  old_cwd = os.getcwd()
  os.chdir(container_path)
  cmd = 'runc checkpoint'
  if precopy:
    cmd += ' --parent-path ' + predump_relative_path
  if postcopy:
    cmd += ' --lazy-pages --page-server localhost:' + postcopy_port
    try:
      os.unlink(postcopy_pipe_path)
    except:
      pass
    os.mkfifo(postcopy_pipe_path)
    cmd += ' --status-fd ' + postcopy_pipe_path
  cmd += ' ' + container
  print cmd
  start = time.time()
  p = subprocess.Popen(cmd, shell=True)
  if postcopy:
    p_pipe = os.open(postcopy_pipe_path, os.O_RDONLY)
    ret = os.read(p_pipe, 1)
    if ret == '\0':
      print 'Ready for lazy page transfer'
    ret = 0
  else:
    ret = p.wait()
  end = time.time()
  print '%s: checkpoint finished after %.2f second(s) with %d' % (container, end - start, ret)
  os.chdir(old_cwd)
  if ret != 0:
    error()

def xfer_dump(process = 'DUMP'):
  cmd = 'rsync -aqz %s %s::home' % (container_path, dest)
  print 'Transferring %s to %s::%s' % (process, dest, container_path)
  start = time.time()
  ret = os.system(cmd)
  end = time.time()
  print '%s transfer time %s seconds' % (process, end - start)
  if ret != 0:
    error()

def touch(fname):
  open(fname, 'a').close()

if pre:
  pre_dump()
  xfer_dump('PRE-DUMP')
real_dump(pre, lazy, lazy_port)
xfer_dump()

cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cs.connect((dest, 8888))

input = [cs]

cs.send(
  '{ "restore" : { "path" : "' + base_path +
  '", "container" : "' + container +
  '", "lazy" : "' + str(lazy) +
  '", "port" : "' + lazy_port + '" } }'
)

while True:
  inputready, outputready, exceptready = select.select(input,[],[], 5)

  if not inputready:
    break

  for s in inputready:
    answer = s.recv(1024)
    print answer
