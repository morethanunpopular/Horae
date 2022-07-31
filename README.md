
# Horae
Horae is simple HPC-style job queue written in python, built on top of celery. In short, you submit a task to a celery job queue, which then gets executed by an apropriate celery worker, inside of a cgroup for setting CPU and memory limits.

# Usage

## hrun
`hrun` is a simple wrapper function used for submitting jobs to the celery queue:
```
>>> from horae import hrun
>>> result = hrun.delay("echo lol", 1000, 1000)
>>> result.get()
['lol\n']
>>> result = hrun.delay("echo hello world", 1000, 1000)
>>> result.get()
['hello world\n']
```

## Job
the `Job` class represents a Job to be executed in Horae.

```
>>> import horae
>>> j = horae.Job('echo lol', 1000,1000, 'test_job')
>>> j.job_name
'test_job'
>>> j.memory
1000
>>> j.cpu
1000
>>> j.run()
lol
```
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

