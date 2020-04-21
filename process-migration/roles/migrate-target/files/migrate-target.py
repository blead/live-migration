#!/usr/bin/python
# based on https://www.redhat.com/en/blog/container-migration-around-world
import socket
import sys
from thread import *
import json
import os
import distutils.util
import subprocess

HOST = ''   # Symbolic name meaning all available interfaces
PORT = 8888 # Arbitrary non-privileged port

if len(sys.argv) < 2:
  print 'Usage: ' + sys.argv[0] + ' <source>' + ' [page_server]'
  sys.exit(1)

source_addr = sys.argv[1]

pageserver_enabled = False
if len(sys.argv) > 2:
  pageserver_enabled = distutils.util.strtobool(sys.argv[2])

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print 'Socket created'

#Bind socket to local host and port
try:
  s.bind((HOST, PORT))
except socket.error as msg:
  print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
  sys.exit()

print 'Socket bind complete'

#Start listening on socket
s.listen(10)
print 'Socket now listening'

#Function for handling connections. This will be used to create threads
def clientthread(conn, addr):
  #Sending message to connected client

  #infinite loop so that function do not terminate and thread do not end.
  while True:

    reply = ""
    #Receiving from client
    data = conn.recv(1024)
    if not data:
      break
    if data == 'exit':
      break

    try:
      msg = json.loads(data)
      if 'restore' in msg:
        try:
          lazy = bool(distutils.util.strtobool(msg['restore']['lazy']))
        except:
          lazy = False
        old_cwd = os.getcwd()
        container_path = msg['restore']['path'] + msg['restore']['container']
        image_path = container_path + '/checkpoint'
        postcopy_pipe_path = '/tmp/postcopy-pipe-' + msg['restore']['container']
        os.chdir(container_path)
        if lazy:
          try:
            os.unlink(postcopy_pipe_path)
          except:
            pass
          os.mkfifo(postcopy_pipe_path)
          page_server_cmd = "criu lazy-pages --page-server --address " + source_addr
          page_server_cmd += " --port " + msg['restore']['port']
          page_server_cmd += " --images-dir " + image_path
          page_server_cmd += " --work-dir " + image_path
          page_server_cmd += " -vvv --log-file " + image_path + "/page-server-log"
          page_server_cmd += " --status-fd " + postcopy_pipe_path
          print "Running lazy-pages server: " + page_server_cmd
          p_pipe = os.open(postcopy_pipe_path, os.O_RDONLY)
          lp = subprocess.Popen(page_server_cmd, shell=True)
          ret = os.read(p_pipe, 1)
        cmd = 'runc restore -d --image-path ' + image_path + ' --work-path ' + image_path
        if lazy:
          cmd += ' --lazy-pages'
        cmd += ' ' + msg['restore']['container'] + ' > ../' + msg['restore']['container'] + '_log.txt 2>&1'
        print "Running " +  cmd
        p = subprocess.Popen(cmd, shell=True)
        ret = p.wait()
        if ret == 0:
          reply = "runc restored %s successfully" % msg['restore']['container']
        else:
          reply = "runc failed(%d)" % ret
        os.chdir(old_cwd)
      else:
        print "Unknown request : " + msg
    except:
      continue

    print reply
    conn.sendall(reply)

  #came out of loop
  conn.close()

#now keep talking with the client
while 1:
  #wait to accept a connection - blocking call
  conn, addr = s.accept()
  print 'Connected with ' + addr[0] + ':' + str(addr[1])

  #start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function.
  start_new_thread(clientthread, (conn, str(addr[0]),))

s.close()
