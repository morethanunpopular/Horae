
# Horae
Horae is simple HPC-style job queue written in python, built on top of celery. In short, you submit a task to a celery job queue, which then gets executed by an apropriate celery worker, inside of a cgroup for setting CPU and memory limits.


# Isntallation

- clone this repo on each node you wish to be in the cluster
- run `pip install .` from inide this repository 
- launch a rabitmq instance somewhere asscessible to all worked
- On all Nodes you wish to be Horae workers, run:
```
BORKER_ADDR=pyamqp://guest@localhost// sudo  /usr/local/bin/celery -A horae  worker --loglevel=INFO
```

*note* make sure to replace the RabbitMQ connection string in the above command with the apropriate one for your environment

# Usage

## hrun

hrun is a simple CLI utility for running commands on the Horae cluster. You can optionally specify the CPU and memory limits to place on the job:

```
$ hrun "echo hello world" 
hello world
```

or with memory and CPU limits:
```
hrun --cpu 1000 --memory 1000 "vmstat -S M 1 10"
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 2  0    379    357    364  18065    0    0     0    12    1    1  4  1 94  0  0
 3  0    379    353    364  18065    0    0     0   484 17321 73190 13 11 76  0  0
 1  0    379    307    364  18065    0    0     0   164 13892 67608 20 15 64  0  0
 2  0    379    347    364  18065    0    0     0   516 10910 72606 11  9 81  0  0
 2  0    379    346    364  18065    0    0     0     8 11431 79772 11  7 82  0  0
 3  0    379    292    364  18065    0    0     0   180 11347 68279 15 10 75  0  0
 3  0    379    250    364  18065    0    0     0   400 13162 73140 27 10 63  0  0
 3  0    380    238    363  18023    0    0     0   508 12491 64137 34 10 56  0  0
 4  0    380    307    361  17937    0    0     0   780 13143 63499 35 12 53  0  0
 2  0    380    353    361  17936    0    0    12   156 12253 73284 24 10 66  0  0
```


There s also an `hrun` function, which is a simple wrapper function used for submitting jobs to the celery queue:
```
>>> from horae import hrun
>>> result = hrun.delay("vmstat -S M 1 2", 1000, 1000)
>>> for items in result.get().items():
...   print(items)
... 
('0', 'procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----\n')
('1', ' r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st\n')
('2', ' 1  1    400   2419    251  17731    0    0     0    12    1    1  4  1 94  0  0\n')
('3', ' 4  0    400   2489    251  17983    0    0    16 252252 12303 11258 10 16 66  7  0\n')
>>> 
```
Note how in the above, the function returns a dictionary, which each key  being a number. This indicates the order in which the output was generated, and can be used in reconstructing the output.

## Job
the `Job` class represents a Job to be executed in Horae.

```
>>> j = horae.Job('vmstat -S M 1 2', 1000,1000, 'example_job')
>>> j.cpu
1000
>>> j.job_name
'example_job'
>>> for line in j.run():
...   print(line)
... 
/sys/fs/cgroup/memory/Horae/example_job/memory.limit_in_bytes
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 3  1    453   1055    203  20709    0    0     0    13    1    1  4  1 94  0  0
 1  2    453    744    203  21004    0    0   108 263496 14920 168333 11 22 59  8  0
```

Notice in the above how you can iterate over the `Job.run` method. This will return command output live. 

## cgroup
horae implements a simple cgroup class used for creating, updating, and destroying cgroups with CPU share and Memory limits:

```
>>> from horae import cgroup
>>> c = cgroup(1000,1000,'test')
>>> c.setup()
>>> c.execute('sleep 100', join=False)
[]
>>> c.execute('sleep 100', join=False)
[]
>>> c.tasks
{'8177', '8181'}
>>> c.teardown()
```

`with` syntax is also supported for automated setup and teardown:

```
>>> with cgroup(1000,1000,'test') as c:
...   c.execute('echo hello world')
... 
hello world
```

