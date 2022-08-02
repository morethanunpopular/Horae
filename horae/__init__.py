import os
import sys
import uuid
import shutil
import subprocess
import celery
import time
import argparse

app = celery.Celery('tasks', broker=os.environ.get("BROKER_ADDR"), backend='rpc://')

class cgroup(object):

  """
  simple implementation of a cgroup. support creating a cgroup with memory 
  and cpu limits, and the running processes inside of that cgroup
  """
  def __init__(self, cpu, memory, name):

    self.cpu = cpu
    self.memory = memory * 1024 * 1024
    self.name = name
    self.cpu_path = "/sys/fs/cgroup/cpu/Horae/{}".format(self.name)
    self.memory_path = "/sys/fs/cgroup/memory/Horae/{}".format(self.name)


  def setup(self):
    # Check if cgroup already exists or not
    if not self.exists:
      # Set up cgroup
      os.makedirs(self.cpu_path)
      with open("{}/cpu.shares".format(self.cpu_path), 'w+')  as fh:
        fh.write(str(self.cpu))

      print("{}/memory.limit_in_bytes".format(self.memory_path))
      os.makedirs(str(self.memory_path))
      with open("{}/memory.limit_in_bytes".format(self.memory_path), 'w')  as fh:
        fh.truncate()
        fh.write(str(self.memory).strip())
 
  @property
  def tasks(self):
    tasks = []
    for path in (self.cpu_path, self.memory_path):
      tasks_file = "{}/tasks".format(path)
      with open(tasks_file, 'r') as fh:
        for line in fh.readlines():
          tasks.append(line.strip())
    return set(tasks)

  @property 
  def exists(self):
    for path in (self.cpu_path, self.memory_path):
      if not os.path.exists(path):
        return False
    return True

  def __enter__(self):
    self.setup()
    return self

  def __exit__(self, type, value, traceback):
    self.teardown()

  def teardown(self):
    print("Performing Teardown...")
    os.rmdir(self.cpu_path)
    os.rmdir(self.memory_path)

  def execute(self, command, join=True):
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    self.add_pid(process.pid)
    return process
 
  def add_pid(self, pid):
    for path in (self.cpu_path, self.memory_path):
      tasks_file = "{}/tasks".format(path)
      with open(tasks_file, 'a') as fh:
        fh.write(str(pid)) 


class Job(object):

  def __init__(self, command, cpu, memory, name=None):

    self.command = command
    self.cpu = cpu
    self.memory = memory
    if name:
      self.job_name = name
    else:
      self.job_name = uuid.uuid4()

    self.job_directory = '/opt/horae/{}'.format(self.job_name) 

  def setup(self):
      os.makedirs(self.job_directory)

  def teardown(self):
    shutil.rmtree(self.job_directory)

  def run(self, join=True):
    with cgroup(self.cpu, self.memory, self.job_name) as c:
      process =  c.execute(self.command)
      if join:
        line = ''
        for c in iter(lambda: process.stdout.read(1), b""):
            line += c.decode()
            if c.decode() == '\n':
              yield line
              line = ''

@app.task
def hrun(command, cpu, memory):
    j = Job(command, cpu, memory,hrun.request.id)
    output = {}
    log_index = 0
    for line in j.run():
      output[log_index] = line
      hrun.update_state(state='OUTPUT', meta={'type': 'log_line', 'content': output, "index": log_index})
      log_index += 1
    return output 

def hrun_cli():
  parser = argparse.ArgumentParser(description='Execute a command on a Horae Queue')
  parser.add_argument('command', help="Command to run")
  parser.add_argument('--cpu', help="cpu cycles to allocate in MHz", default=1000)
  parser.add_argument('--memory', help="memory to allocated in MB", default=2000)
  args = parser.parse_args()
  result = hrun.delay(args.command, args.cpu, int(args.memory))
  log_index = 0
  while True:
    if result.info:
      if result.info.get('index'):
        if result.info.get('index') != log_index:
          for i in range(log_index, int(result.info['index'])):
            sys.stdout.write(result.info['content'][str(i)])
          log_index = result.info['index']
    if result.ready():
      break
  time.sleep(.1)
  output = result.get()
  for i in range(log_index, len(output.keys())):
    print(output[str(i)])
