import os
import time
import errno


class DirLock():
    def __init__(self, lock_file, poll_interval=1,
                 create_dir=False, timeout=None):
        """
        Context manager to lock a directory using a lockfile.

        Note: Do neither use an existing file nor a file that may get copied
        into the directory while locked as a name for the lock file.
        In the first case, the lock will never be acquired, in the second one,
        the copied file gets deleted after the lock is released.

        Parameters
        ----------
        lock_file : str
            Lockfile name. The directory name of the file is getting locked.
        poll_interval : int or float, optional (default: 1)
            Intervall in seconds to wait if the lock could not be acquired until
            a new attempt is made.
        create_dir : bool, optional (default: False)
            If `True` create the to be locked directory if it is not exisitng.
        timeout : None, int or float, optional (default: None)
            If not `None`, raises a `TimeoutError` if the lock could not be
            acquired after `timeout` seconds.

        Example
        -------
        ```
        from dir_lock import DirLock

        with DirLock("./work_dir/_lock", create_dir=True) as dir_lock:
            print("Created lockfile '{}'".format(dir_lock.lock_file))
            time.sleep(5)
        print("Done, left lock")
        ```
        """
        self._lock_file = lock_file
        self._lock_dir = os.path.dirname(self._lock_file)
        self._LOCKED = False  # Holds the 'True-like' file descriptor if locked

        if not poll_interval > 0.:
            raise ValueError("Poll intervall must be int or float >0.")
        self._sleep = poll_interval

        if not (timeout is None or timeout > 0):
            raise ValueError("Timeout must be None or int or float >0.")
        self._timeout = timeout

        if create_dir:
            os.makedirs(self._lock_dir, exist_ok=True)

    @property
    def lock_file(self):
        return self._lock_file

    def _lock(self):
        # Polling loop to check lock status
        _time = time.time()
        _tries = 1
        while True:
            if not self._LOCKED:
                # This is all the magic: If the lock file is already there, it
                # was created by another process, then we poll and wait.
                # Else we create it and we're good, even if called recursively
                # in an already locked state.
                try:
                    # 'x' -> Error on exist, the whole lock 'magic'
                    lock = open(self._lock_file, "x")
                except OSError as err:
                    if err.errno == errno.EEXIST:
                        pass  # File is present, need to wait for unlock
                    elif err.errno == errno.ENOENT:
                        raise FileNotFoundError(
                            "Directory '{}' does not exist. "
                            "Use 'create_dir=True' or create it manually."
                            "".format(self._lock_dir)) from err
                    else:
                        raise  # Everything else is not our business
                else:
                    self._LOCKED = lock

            # Did we get the lock aka could we create the file?
            if self._LOCKED:
                break  # If so  we're good, get out of the polling loop
            else:
                time.sleep(self._sleep)  # Let's chill a bit and retry

            if self._timeout and ((time.time() - _time) > self._timeout):
                raise TimeoutError(
                    "Could not lock '{}' before timeout. "
                    "Tried {} times within {}s".format(
                        self._lock_dir, _tries, self._timeout))
            _tries += 1

        return self

    def _release(self):
        # If we're locked, close the file and remove it
        if self._LOCKED:
            self._LOCKED.close()
            try:
                os.remove(self._lock_file)
            except OSError:
                pass  # Already removed? OK then, why bother...
            finally:
                self._LOCKED = False

        return None

    def __enter__(self):
        self._lock()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._release()

    def __del__(self):
        self._release()
