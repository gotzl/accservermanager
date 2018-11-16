from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader

import subprocess, time, datetime
from multiprocessing import Value
from threading import Thread

from accservermanager import settings


class Executor(Thread):
    def run(self):
        _tm = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
        p = subprocess.Popen('cd "%s" && %s'%(settings.ACCSERVER,settings.ACCEXEC),
                             shell=True,
                             universal_newlines=True,
                             stdout=subprocess.PIPE,
                             # stdout=open('/dev/null', 'w'),
                             # stdout=open('%s/log/stdout-%s.log'%(settings.ACCSERVER,_tm),'w'),
                             stderr=open('%s/log/stderr-%s.log'%(settings.ACCSERVER,_tm),'w'))
        retval = None
        while retval is None:
            if stop.value == 1: p.kill()
            time.sleep(1)
            retval = p.poll()

        print("Retval:",retval)


stop = Value('i', 0)
executor_inst = None


def startstop(request, start=True):
    if request.method == 'POST':
        global executor_inst
        if start:
            if executor_inst is None or not executor_inst.is_alive():
                stop.value = 0
                executor_inst = Executor()
                executor_inst.start()

        else:
            if executor_inst is not None:
                stop.value = 1
                executor_inst = None

    return HttpResponseRedirect("../")


def index(request):
    template = loader.get_template('instances/index.html')
    context = {
        'running': executor_inst is not None and executor_inst.is_alive()
    }
    return HttpResponse(template.render(context, request))

