# File based lock.
# Taken from https://github.com/sakkada/django-syncdata/blob/master/syncdata/utils.py

import os
import time


class FileLockedException(Exception):
    pass


class FileLock:
    locktime = 60 * 60 * 4
    lockname = ".lock"

    def __init__(self, basedir, locktime=None, lockname=None):
        self.basedir = basedir

        if locktime:
            self.locktime = locktime
        if lockname:
            self.lockname = lockname

    def lock(self, force=False):
        if self.check() and not force:
            return False

        lockname = self.get_name()
        if os.path.exists(lockname):
            os.utime(lockname, None)
        else:
            open(lockname, "a").close()
        return True

    def unlock(self):
        lockname = self.get_name()
        os.path.exists(lockname) and os.unlink(lockname)

    def check(self, astime=False, remained=True):
        lockname = self.get_name()
        elapsed = (
            time.time() - os.path.getmtime(lockname)
            if os.path.exists(lockname)
            else None
        )

        if not (not elapsed is None and elapsed < self.locktime):
            return False

        return (self.locktime - elapsed if remained else elapsed) if astime else True

    def update(self):
        lockname = self.get_name()
        if self.check() and os.path.exists(lockname):
            os.utime(lockname, None)
            return True
        return False

    def get_name(self):
        return os.path.abspath(os.path.join(self.basedir, self.lockname))
