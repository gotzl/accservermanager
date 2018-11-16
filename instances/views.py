from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader

import subprocess, time
from multiprocessing import Value
from threading import Thread

class Executor(Thread):
    def run(self):
        p = subprocess.Popen('cd /server/ && WINEDEBUG=-all wine accServer.exe',
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        retval = None
        while retval is None:
            if stop.value == 1: p.terminate()
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
    }
    return HttpResponse(template.render(context, request))

