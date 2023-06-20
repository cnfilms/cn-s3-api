import os
import threading
from logging import getLogger


class ProgressPercentage(object):

    def __init__(self, filename, logger=None):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()
        self._logger = getLogger() if not logger else logger

    def __call__(self, bytes_amount):
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            self._logger.info("\r%s  %s / %s  (%.2f%%)" % (
                self._filename, self._seen_so_far, self._size, percentage
            ))


