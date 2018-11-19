from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django import forms

from random_word import RandomWords
r = RandomWords()

import subprocess, time, datetime
from multiprocessing import Value
from threading import Thread

import os, shutil, json
try: import resource
except: resource = None

from accservermanager import settings
from cfgs.confEdit import createLabel
from cfgs.confSelect import getCfgsField


class Executor(Thread):
    """
    Thread for running the server process
    """
    def __init__(self, instanceDir, serverCfg, config):
        super().__init__()
        for key in serverCfg: setattr(self,key,serverCfg[key])
        self.p = None
        self.stdout = None
        self.stderr = None
        self.retval = None
        self.instanceDir = instanceDir
        self.config = config
        self.stop = Value('i', 0)



    def run(self):
        preexec_fn = None
        exec = settings.ACCEXEC
        if resource:
            # in linux, limit ram to 1GB soft, 2GB hard
            preexec_fn = lambda: resource.setrlimit(resource.RLIMIT_DATA, (2**30, 2**31))
        else:
            # if 'resource' is not available, assume windows which needs to full path to the exec
            exec = os.path.join(self.instanceDir, settings.ACCEXEC)

        # fire up the server, store stderr to the log/ dir
        _tm = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        self.stdout = os.path.join(self.instanceDir, 'log', 'stdout-%s.log'%(_tm))
        self.stderr = os.path.join(self.instanceDir, 'log', 'stderr-%s.log'%(_tm))
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


# the server process execution threads
executors = {}


@login_required
def instance(request, name):
    if name not in executors: return HttpResponseRedirect('/instances')
    template = loader.get_template('instances/instance.html')
    return HttpResponse(template.render({}, request))


@login_required
def stdout(request, name):
    return log(name,executors[name].stdout)


@login_required
def stderr(request, name):
    return log(name, executors[name].stderr)


# https://stackoverflow.com/questions/136168/get-last-n-lines-of-a-file-with-python-similar-to-tail
def tail(f, n=10):
    assert n >= 0
    pos, lines = n+1, []
    while len(lines) <= n:
        try:
            f.seek(-pos, 2)
        except IOError:
            f.seek(0)
            break
        finally:
            lines = list(f)
        pos *= 2
    return lines[-n:]


def log(name, _f):
    text = ''
    if name in executors:
        text = tail(open(_f))
    return HttpResponse(text)


@login_required
def delete(request, name):
    if name in executors:
        shutil.rmtree(executors[name].instanceDir)
        executors.pop(name)

    return HttpResponseRedirect('/instances')


@login_required
def stop(request, name):
    """ handle stop request from client """
    global executors
    if name in executors and executors[name].stop.value != 1:
        executors[name].stop.value = 1

        i = 0
        # wait max 2 seconds for the instance to stop
        while executors[name].is_alive() and i<10:
            time.sleep(.2)
            i+=1

    return HttpResponseRedirect('/instances')


@login_required
def start(request):
    """ handle start request from client """
    name = request.POST['instanceName']
    if name not in executors:
        # create instance environment
        inst_dir = os.path.join(settings.INSTANCES, name)

        # return if dir already exist or ports are already in use or ports are equal
        if os.path.isdir(inst_dir) or \
                request.POST['udpPort'] == request.POST['tcpPort'] or \
                len(list(filter(lambda x: request.POST['udpPort'] in [x.udpPort, x.tcpPort] or
                                          request.POST['tcpPort'] in [x.udpPort, x.tcpPort],
                                executors.values()))) > 0:
            return HttpResponseRedirect('/instances')

        shutil.copytree(settings.ACCSERVER, inst_dir)
        # the target config
        cfg = os.path.join(settings.CONFIGS, request.POST['cfg']+'.json')
        # copy it to the config read by the accServer.exe
        shutil.copy(cfg, os.path.join(inst_dir, 'cfg', 'custom.json'))

        # update the configuration.json
        cfg = json.load(open(os.path.join(settings.ACCSERVER, 'cfg', 'configuration.json'), 'r'))
        for key in ['serverName','udpPort','tcpPort']:
            cfg[key] = request.POST[key]
        json.dump(cfg, open(os.path.join(inst_dir, 'cfg', 'configuration.json'), 'w'))

        executors[name] = Executor(inst_dir, cfg, request.POST['cfg'])
        executors[name].start()

    return HttpResponseRedirect('/instances')


class InstanceForm(forms.Form):
    """
    Form used to fire up a new server instance
    """
    def __init__(self, data):
        super().__init__()
        self.fields['instanceName'] = forms.CharField(max_length=100, widget=forms.TextInput(attrs={"onkeyup":"nospaces(this)"}))
        self.fields['serverName'] = forms.CharField(max_length=100)
        self.fields['udpPort'] = forms.IntegerField(max_value=None, min_value=1000)
        self.fields['tcpPort'] = forms.IntegerField(max_value=None, min_value=1000)
        for key in ['serverName','udpPort','tcpPort', 'instanceName']:
            self.fields[key].label = createLabel(key)
            self.fields[key].required = True
            self.fields[key].initial = data[key]
        self.fields['cfg'] = getCfgsField()
        self.fields['cfg'].required = True
        self.fields['cfg'].label = 'Config'


def index(request):
    cfg = json.load(open(os.path.join(settings.ACCSERVER,'cfg','configuration.json'), 'r'))
    cfg['instanceName'] = r.get_random_word(hasDictionaryDef="true",minLength=5, maxLength=10)

    template = loader.get_template('instances/index.html')
    context = {
        'form': InstanceForm(cfg),
        'executors': executors,
    }
    return HttpResponse(template.render(context, request))

