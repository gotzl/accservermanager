from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django import forms

import subprocess, time, datetime
from multiprocessing import Value
from threading import Thread

import json

from accservermanager import settings


class Executor(Thread):
    def __init__(self, serverName):
        super().__init__()
        self.p = None
        self.severName = serverName

    def run(self):
        _tm = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
        self.p = subprocess.Popen('cd "%s" && %s'%(settings.ACCSERVER,settings.ACCEXEC),
                             shell=True,
                             universal_newlines=True,
                             stdout=subprocess.PIPE,
                             # stdout=open('/dev/null', 'w'),
                             # stdout=open('%s/log/stdout-%s.log'%(settings.ACCSERVER,_tm),'w'),
                             stderr=open('%s/log/stderr-%s.log'%(settings.ACCSERVER,_tm),'w'))
        retval = None
        while retval is None:
            if stop.value == 1: self.p.kill()
            time.sleep(1)
            retval = self.p.poll()

        print("Retval:",retval)


stop = Value('i', 0)
executor_inst = None


def startstop(request, start=True):
    if request.method == 'POST':
        global executor_inst
        if start:
            if executor_inst is None or not executor_inst.is_alive():
                cfg = json.load(open(PATH,'r'))
                cfg['serverName'] = request.POST['serverName']
                json.dump(cfg, open(PATH,'w'))

                stop.value = 0
                executor_inst = Executor(cfg['serverName'])
                executor_inst.start()

        else:
            if executor_inst is not None:
                stop.value = 1
                executor_inst = None

    return HttpResponseRedirect("../")


class InstanceForm(forms.Form):
    serverName = forms.CharField(label='Server name', required=True, max_length=100)


PATH = '%s/cfg/configuration.json'%settings.ACCSERVER

def index(request):
    cfg = json.load(open(PATH,'r'))

    template = loader.get_template('instances/index.html')
    context = {
        'configName' : 'default',
        'serverName' : executor_inst.severName if executor_inst is not None else None,
        'process': executor_inst.p if executor_inst is not None else None,
        'running': executor_inst is not None and executor_inst.is_alive(),
        'form': InstanceForm({'serverName':cfg['serverName']})
    }
    return HttpResponse(template.render(context, request))

