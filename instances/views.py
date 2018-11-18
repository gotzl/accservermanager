from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django import forms

from random_word import RandomWords
r = RandomWords()

import subprocess, time, datetime
from multiprocessing import Value
from threading import Thread

import os, shutil, json, resource

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
        self.stderr = None
        self.retval = None
        self.instanceDir = instanceDir
        self.config = config
        self.stop = Value('i', 0)



    def run(self):
        # fire up the server, store stderr to the log/ dir
        _tm = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
        self.stderr = '%s/log/stderr-%s.log'%(self.instanceDir, _tm)
        self.p = subprocess.Popen(settings.ACCEXEC,
                                  # set working dir
                                  cwd=self.instanceDir,
                                  # limit ram to 1GB soft, 2GB hard
                                  preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_DATA, (2**30, 2**31)),
                                  shell=True,
                                  universal_newlines=True,
                                  stdout=subprocess.PIPE,
                                  # stdout=open('/dev/null', 'w'),
                                  #  stdout=open('%s/log/stdout-%s.log'%(inst_dir,_tm),'w'),
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
def stderr(request, name):
    text = ''
    if name in executors:
        text = subprocess.check_output(['tail', executors[name].stderr])
    return HttpResponse(text)


@login_required
def stdout(request, name):
    text = ''
    if name in executors:
        serverout = os.path.join(executors[name].instanceDir, 'log', 'server.log')
        text = subprocess.check_output(['tail', serverout])
    return HttpResponse(text)


@login_required
def delete(request, name):
    if name in executors:
        shutil.rmtree(executors[name].instanceDir)
        executors.pop(name)

    return HttpResponseRedirect("../../")


@login_required
def start(request):
    return startstop(request, request.POST['instanceName'])


@login_required
def startstop(request, name, start=True):
    """ handle start/stop request from client """
    if request.method == 'POST':
        global executors
        if start:
            if name not in executors:
                # create instance environment
                inst_dir = os.path.join(settings.INSTANCES, name)

                # return if dir already exist or ports are already in use or ports are equal
                if os.path.isdir(inst_dir) or \
                        request.POST['udpPort'] == request.POST['tcpPort'] or \
                        len(list(filter(lambda x: request.POST['udpPort'] in [x.udpPort, x.tcpPort] or
                                                  request.POST['tcpPort'] in [x.udpPort, x.tcpPort],
                                        executors.values()))) > 0:
                    return HttpResponseRedirect("../")

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

            return HttpResponseRedirect("../")

        else:
            if name in executors and executors[name].stop.value != 1:
                executors[name].stop.value = 1

                i = 0
                # wait max 2 seconds for the instance to stop
                while executors[name].is_alive() and i<10:
                    time.sleep(.2)
                    i+=1

            return HttpResponseRedirect("../../")


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

