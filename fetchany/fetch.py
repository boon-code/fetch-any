import os
import shutil
import logging
import threading
import vcstools

try:
    import queue
except ImportError:
    import Queue as queue


class Fetcher(threading.Thread):

    def __init__(self, qin, workdir):
        threading.Thread.__init__(self)
        self._qin = qin
        self._workdir = workdir
        self.success = None
        self.failed = list()
        self._log = logging.getLogger("Fetcher")

    def run(self):
        try:
            while True:
                spec = self._qin.get(False)
                co_path = os.path.join(self._workdir, spec['path'])
                c = vcstools.get_vcs_client(spec['type'], co_path)
                repo_exists = c.detect_presence()
                if repo_exists and spec.get('force-clean', False):
                    self._log.info("{type}: Force clean path: {0}".format(co_path, **spec))
                    shutil.rmtree(co_path)
                    repo_exists = False
                if repo_exists:
                    op = "Updating"
                    self._log.debug("{type}: Updating {0} (url={fetch})".format(co_path, **spec))
                    ret = c.update(version=spec.get('revision', ''),
                             force_fetch=True)
                else:
                    op = "Fetching"
                    self._log.debug("{type}: Fetching url={fetch} -> {0}".format(co_path, **spec))
                    ret = c.checkout(spec['fetch'],
                                    version=spec.get('revision', ''),
                                    shallow=spec.get('shallow', False))
                self._qin.task_done()
                if ret:
                    spec['co_revision'] = c.get_version()
                    self._log.debug("{type}: {0} path '{path}' to {co_revision} succeeded".format(op, **spec))
                if not ret:
                    self._log.debug("{type}: {0} path '{path}' failed: {1}".format(op, ret, **spec))
                    self.failed.append(spec)
                    self.success = False
        except queue.Empty:
            if self.success is None:
                self.success = True
            self._log.debug("Stopping work: Input queue is empty")
            return None
