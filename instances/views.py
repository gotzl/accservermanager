from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django import forms

import subprocess, time, datetime
from multiprocessing import Value
from threading import Thread

import os, json

from accservermanager import settings
from cfgs.confSelect import getCfgsField


class Executor(Thread):
    """
    Thread for running the server process
    """
    def __init__(self, serverName, config):
        super().__init__()
        self.p = None
        self.serverName = serverName
        self.config = config

    def run(self):
        cfg_dir = os.path.join(settings.ACCSERVER,'cfg')
        # the target config
        cfg = os.path.join(cfg_dir, 'custom', self.config)
        # the config read by the accServer.exe (i.e. 'custom.json' in its dir)
        cfg_sym = os.path.join(cfg_dir, 'custom.json')
        # remove old symlink and create the new one
        if os.path.exists(cfg_sym): os.remove(cfg_sym)
        os.symlink(cfg, cfg_sym)

        # fire up the server, store stderr to the log/ dir
        _tm = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
        self.p = subprocess.Popen('cd "%s" && %s'%(settings.ACCSERVER,settings.ACCEXEC),
                             shell=True,
                             universal_newlines=True,
                             stdout=subprocess.PIPE,
                             # stdout=open('/dev/null', 'w'),
                             # stdout=open('%s/log/stdout-%s.log'%(settings.ACCSERVER,_tm),'w'),
                             stderr=open('%s/log/stderr-%s.log'%(settings.ACCSERVER,_tm),'w'))

        # wait for the stop signal or for the server to die on its own
        retval = None
        while retval is None:
            if stop.value == 1: self.p.kill()
            time.sleep(1)
            retval = self.p.poll()

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
                cfg = json.load(open(PATH,'r'))
                for key in ['serverName','udpPort','tcpPort']:
                    cfg[key] = request.POST[key]
                json.dump(cfg, open(PATH,'w'))

                stop.value = 0
                executor_inst = Executor(cfg['serverName'], request.POST['cfg'])
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
        self.fields['serverName'] = forms.CharField(label='Server name', max_length=100)
        self.fields['udpPort'] = forms.IntegerField(max_value=None, min_value=1000)
        self.fields['tcpPort'] = forms.IntegerField(max_value=None, min_value=1000)
        for key in ['serverName','udpPort','tcpPort']:
            self.fields[key].required = True
            self.fields[key].initial = data[key]
        self.fields['cfg'] = getCfgsField()
        self.fields['cfg'].required = True
        self.fields['cfg'].label = 'Config'


PATH = '%s/cfg/configuration.json'%settings.ACCSERVER


def index(request):
    cfg = json.load(open(PATH,'r'))

    template = loader.get_template('instances/index.html')
    context = {
        'form': InstanceForm(cfg),
        'running': executor_inst is not None and executor_inst.is_alive(),
        'executor': executor_inst,
    }
    return HttpResponse(template.render(context, request))

