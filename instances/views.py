from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django import forms

import subprocess, time, datetime
from multiprocessing import Value
from threading import Thread

import os, shutil, json

from accservermanager import settings
from cfgs.confEdit import createLabel
from cfgs.confSelect import getCfgsField


class Executor(Thread):
    """
    Thread for running the server process
    """
    def __init__(self, instanceDir, serverName, config):
        super().__init__()
        self.p = None
        self.instanceDir = instanceDir
        self.serverName = serverName
        self.config = config

    def run(self):
        # fire up the server, store stderr to the log/ dir
        _tm = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
        self.p = subprocess.Popen('cd "%s" && %s'%(self.instanceDir, settings.ACCEXEC),
                             shell=True,
                             universal_newlines=True,
                             stdout=subprocess.PIPE,
                             # stdout=open('/dev/null', 'w'),
                             # stdout=open('%s/log/stdout-%s.log'%(inst_dir,_tm),'w'),
                             stderr=open('%s/log/stderr-%s.log'%(self.instanceDir, _tm),'w'))

        # wait for the stop signal or for the server to die on its own
        retval = None
        while retval is None:
            if stop.value == 1: self.p.kill()
            time.sleep(1)
            retval = self.p.poll()

        shutil.rmtree(self.instanceDir)
        print("Retval:",retval)


# globals for the server process and communication
# the stop signal
stop = Value('i', 0)
# the server process execution thread
executor_inst = None


def startstop(request, start=True):
    """ handle start/stop request from client """
    if request.method == 'POST':
        global executor_inst
        if start:
            if executor_inst is None or not executor_inst.is_alive():
                # create instance environment
                inst_dir = os.path.join(settings.INSTANCES, request.POST['instanceName'])
                shutil.copytree(settings.ACCSERVER, inst_dir)
                # the target config
                cfg = os.path.join(settings.CONFIGS, request.POST['cfg']+'.json')
                # copy it to the config read by the accServer.exe (i.e. 'custom.json' in its dir)
                shutil.copy(cfg, os.path.join(inst_dir, 'custom.json'))

                # update the configuration.json
                cfg = json.load(open(os.path.join(settings.ACCSERVER,'cfg','configuration.json'), 'r'))
                for key in ['serverName','udpPort','tcpPort']:
                    cfg[key] = request.POST[key]
                json.dump(cfg, open(os.path.join(inst_dir, 'cfg', 'configuration.json'), 'w'))

                stop.value = 0
                executor_inst = Executor(inst_dir, cfg['serverName'], request.POST['cfg'])
                executor_inst.start()

        else:
            if executor_inst is not None:
                stop.value = 1
                executor_inst = None

    return HttpResponseRedirect("../")


class InstanceForm(forms.Form):
    """
    Form used to fire up a new server instance
    """
    def __init__(self, data):
        super().__init__()
        self.fields['instanceName'] = forms.CharField(max_length=100)
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
    cfg['instanceName'] = 'test'

    template = loader.get_template('instances/index.html')
    context = {
        'form': InstanceForm(cfg),
        'running': executor_inst is not None and executor_inst.is_alive(),
        'executor': executor_inst,
    }
    return HttpResponse(template.render(context, request))

