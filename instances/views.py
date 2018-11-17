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
    def __init__(self, serverName, config):
        super().__init__()
        self.p = None
        self.serverName = serverName
        self.config = config

    def run(self):
        cfg_dir = os.path.join(settings.ACCSERVER,'cfg')
        cfg = os.path.join(cfg_dir, 'custom', self.config)
        cfg_sym = os.path.join(cfg_dir, 'custom.json')
        if os.path.exists(cfg_sym): os.remove(cfg_sym)
        os.symlink(cfg, cfg_sym)

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
                executor_inst = Executor(cfg['serverName'], request.POST['cfg'])
                executor_inst.start()

        else:
            if executor_inst is not None:
                stop.value = 1
                executor_inst = None

    return HttpResponseRedirect("../")


class InstanceForm(forms.Form):
    def __init__(self, data):
        super().__init__()
        self.fields['serverName'] = forms.CharField(
            label='Server name',
            initial = data['serverName'],
            required=True,
            max_length=100)
        self.fields['cfg'] = getCfgsField()
        self.fields['cfg'].required = True
        self.fields['cfg'].label = 'Config'


PATH = '%s/cfg/configuration.json'%settings.ACCSERVER

def index(request):
    cfg = json.load(open(PATH,'r'))

    template = loader.get_template('instances/index.html')
    context = {
        'form': InstanceForm({'serverName':cfg['serverName']}),
        'running': executor_inst is not None and executor_inst.is_alive(),
        'executor': executor_inst,
    }
    return HttpResponse(template.render(context, request))

