"""
You can use this example script to test the lock using two terminals.
On one, start `python example.py 1`, then quickly on the other one
`python example.py 2`.
If you monitor the console and the file viewer, you can the locks getting
acquired one after another.

You can play with the sleep and the timeout settings.
"""


import os
import time
import argparse

from dir_lock import DirLock


# Just for pretty CLI arg handling
parser = argparse.ArgumentParser()
parser.add_argument("id")
args = parser.parse_args()

# The directory we want to lock is the parent of the given lock filename
lock_file = "./work_dir/_lock"
print("ID {} : I want to lock '{}'".format(args.id, os.path.dirname(lock_file)))

# Play with these to see a TimeoutError raised
sleepy_time = 5.
timeout = 10.

with DirLock(lock_file, create_dir=True, timeout=timeout) as dir_lock:
    print("ID {} : My turn, created lockfile '{}'".format(
        args.id, dir_lock.lock_file))
    print("ID {} : Sleeping for {}s".format(args.id, sleepy_time))
    time.sleep(sleepy_time)
    print("ID {} : I'm done".format(args.id))

assert not os.path.isfile(lock_file)
print("ID {} : Done, left lock, lockfile is gone".format(args.id))
