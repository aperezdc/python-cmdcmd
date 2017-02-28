# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2017 Adrian Perez <aperez@igalia.com>
# Copyright © 2010 Igalia S.L.
#
# Distributed under terms of the MIT license.

"""
Common utilities used all along Valkyrie.
"""

import errno
import os


class LockError(RuntimeError):
    """Base class for :class:`Lock` exceptions."""


class CannotLockError(LockError):
    """Lock cannot be acquired."""


class AlreadyLockedError(LockError):
    """Tried to lock an already-locked lock."""


class AlreadyUnlockedError(LockError):
    """Tried to unlock an already-unlocked lock."""


class Lock(object):
    """This class contains the implementation of a simple lockfile.

    This can be used to avoid multiple processes running concurrently.

    :param process: Name of the process. A directory will be created with
        the name of the process to hold locks on.
    :param name: Name of the lock to be set.
    """

    BASE_DIR = os.environ.get("LOCKDIR", "/var/lock")
    O_MODE = os.O_CREAT | os.O_EXCL | os.O_RDWR

    def __init__(self, process, name=None):
        self._lockfile = self.file_path(process, name)

        lockdir = os.path.dirname(self._lockfile)

        if not os.path.isdir(lockdir):
            os.mkdir(lockdir, 0o755)
        if not os.access(lockdir, os.W_OK):
            raise ValueError("Directory {!r} not writable".format(lockdir))

        self._lockfile = os.path.join(lockdir, name)
        self._fileno = None

    def file_path(self, process, name=None):
        """Build the path to a lock file.

        :param process: Name of the process.
        :param name: Name of the lock.
        """
        if name is None:
            name = "lock"
        return os.path.abspath(os.path.expanduser(
            os.path.join(self.BASE_DIR, process, name)))

    file_path = classmethod(file_path)

    path = property(lambda self: self._lockfile,
                    doc="Full path to the lock file")

    locked = property(lambda self: self._fileno is not None,
                      doc="Whether the lock is being held")

    def __enter__(self):
        """Obtain the lock for use in a ``with`` statement.
        This method is provided to make :class:`Lock` instances useable as
        context managers.

        :rtype: :class:`Lock`
        """
        self.lock()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Release the lock when exiting a ``with`` statement.
        """
        self.unlock()

    def lock(self, tryonly=False):
        """Obtain the lock.
        If the lock cannot be obtained, then :class:`CannotLockError`
        is raised, unless *trylock* is passed.

        :param tryonly: If ``True``, do not raise an exception.
        :return: Whether the lock was successfully acquired.
        :rtype: bool
        """
        if self.locked:
            raise AlreadyLockedError(self.path)

        try:
            self._fileno = os.open(self.path, self.O_MODE)
        except OSError as e:
            if e.errno == errno.EEXIST:
                if tryonly:
                    return False
                else:
                    raise LockError(self.path)
            else:
                raise

        os.write(self._fileno, str(os.getpid()))
        os.close(self._fileno)
        return True

    def try_lock(self):
        """Try to acquire the lock.

        :return: Whether the lock was successfully acquired.
        :rtype: bool
        """
        return self.lock(tryonly=True)

    def unlock(self):
        """Unlock. If already locked, then :class:`AlreadyLockedError` is
        raised.
        """
        if not self.locked:
            raise AlreadyUnlockedError(self.path)

        os.unlink(self.path)
        self._fileno = None


class Bag(dict):
    """Behaves like a dictionary, but allows attribute reads.
    """
    def __getattr__(self, name):
        return self[name]


__all__ = (
    "Lock",
    "CannotLockError",
    "AlreadyLockedError",
    "AlreadyUnlockedError",
    "Bag",
)
