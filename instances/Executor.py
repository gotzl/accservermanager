import os, subprocess, time, datetime, json
from multiprocessing import Value
from threading import Thread
from pathlib import Path

from accservermanager import settings

try: import resource
except: resource = None


class Executor(Thread):
    """
    Thread for running the server process
    """
    def __init__(self, instanceDir):
        super().__init__()

        # add all configuration values to the object
        for key, val in json.load(open(os.path.join(instanceDir, 'cfg', 'configuration.json'), 'r', encoding='utf-16')).items():
            setattr(self, key, val)
        for key, val in json.load(open(os.path.join(instanceDir, 'cfg', 'settings.json'), 'r', encoding='utf-16')).items():
            setattr(self, key, val)

        # find the name of the config file, just needed to display it in the instances list
        self.config = Path(os.path.join(instanceDir, 'cfg', 'event.json')).resolve().name

        self.p = None
        self.stdout = None
        self.stderr = None
        self.serverlog = None
        self.retval = None
        self.instanceDir = instanceDir

        self.stop = Value('i', 0)

    def run(self):
        preexec_fn = None
        exec = settings.ACCEXEC
        if resource:
            # in linux, limit ram to 1GB soft, 2GB hard
            preexec_fn = lambda: resource.setrlimit(resource.RLIMIT_DATA, (2**30, 2**31))
        else:
            # if 'resource' is not available, assume windows which needs to full path to the exec
            exec = os.path.join(self.instanceDir, *settings.ACCEXEC)

        # fire up the server, store stderr to the log/ dir
        _tm = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        self.stdout = os.path.join(self.instanceDir, 'log', 'stdout-%s.log'%(_tm))
        self.stderr = os.path.join(self.instanceDir, 'log', 'stderr-%s.log'%(_tm))
        self.serverlog = os.path.join(self.instanceDir, 'log', 'server.log')
        self.p = subprocess.Popen(exec,
                                  # set working dir
                                  cwd=self.instanceDir,
                                  # limit ram to 1GB soft, 2GB hard
                                  preexec_fn=preexec_fn,
                                  # shell=True,
                                  universal_newlines=True,
                                  stdout=open(self.stdout,'w'),
                                  stderr=open(self.stderr,'w'))

        # wait for the stop signal or for the server to die on its own
        self.retval = None
        while self.retval is None:
            if self.stop.value == 1: self.p.kill()
            time.sleep(1)
            self.retval = self.p.poll()

        print("Retval:",self.retval)
