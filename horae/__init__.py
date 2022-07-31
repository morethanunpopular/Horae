import os
import sys
import uuid
import shutil
import subprocess
import celery

app = celery.Celery('tasks', broker='pyamqp://guest@localhost//', backend='rpc://')

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

  def execute(self, command):
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    self.add_pid(process.pid)
    line = ''
    output = []
    for c in iter(lambda: process.stdout.read(1), b""):
        line += c.decode()
        if c.decode() == '\n':
          output.append(line)
          print(line)
          line = ''
    print(process.returncode)
    return output
 
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
  def _setup(self):
    pass

  def _teardown(self):
    pass

  def run(self):
    with cgroup(self.cpu, self.memory, self.job_name) as c:
      return c.execute(self.command)

@app.task
def hrun(command, cpu, memory):
    j = Job(command, cpu, memory,hrun.request.id)
    return j.run()



if __name__ == '__main__':
   hrun.delay('/home/gcampbell/Horae/test.sh')