from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import loader
from django import forms

from random_word import RandomWords
try: r = RandomWords()
except: r = None

import subprocess, time, datetime, string, glob
from multiprocessing import Value
from threading import Thread
from pathlib import Path

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
    def __init__(self, instanceDir):
        super().__init__()

        # add all configuration values to the object
        for key, val in json.load(open(os.path.join(instanceDir, 'cfg', 'configuration.json'), 'r')).items():
            setattr(self, key, val)
        for key, val in json.load(open(os.path.join(instanceDir, 'cfg', 'settings.json'), 'r')).items():
            setattr(self, key, val)

        # find the name of the config file, just needed to display it in the instances list
        self.config = Path(os.path.join(instanceDir, 'cfg', 'event.json')).resolve().name

        self.p = None
        self.stdout = None
        self.stderr = None
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

    path = request.path
    if path[0] == '/': path = path[1:]
    if path[-1] == '/':path = path[:-1]
    path = path.split('/')

    return HttpResponse(template.render(
        {'path' : [(j, '/'+'/'.join(path[:i+1])) for i,j in enumerate(path)],},
        request))


@login_required
def stdout(request, name):
    if 'lines' not in request.POST:
        return download(executors[name].stdout)
    return log(executors[name].stdout, int(request.POST['lines']))


@login_required
def stderr(request, name):
    if 'lines' not in request.POST:
        return download(executors[name].stderr)
    return log(executors[name].stderr, int(request.POST['lines']))


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


def log(_f, n):
    if _f is not None and os.path.isfile(_f):
        with open(_f, 'r', encoding='latin-1') as fh:
            return HttpResponse(tail(fh, n))
    raise Http404


def download(_f):
    if _f is not None and os.path.isfile(_f):
        with open(_f, 'r', encoding='latin-1') as fh:
            response = HttpResponse(fh.read(), content_type="text/plain")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(_f)
            return response
    raise Http404


@login_required
def delete(request, name):
    if name in executors:
        if not executors[name].is_alive():
            shutil.rmtree(executors[name].instanceDir)
            executors.pop(name)

    return HttpResponse(json.dumps({'success': True}),
                        content_type='application/json')


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

    # return HttpResponseRedirect('/instances')
    return HttpResponse(json.dumps({'success': True, 'retval':executors[name].retval}),
                        content_type='application/json')


@login_required
def start(request, name):
    """ handle (re)start request from client """
    global executors

    # create the Executor for the instance
    # - if it does not exist yet
    # - if the executor thread was alive and exited
    if name not in executors or  \
        (not executors[name].is_alive() and executors[name].retval is not None):
        inst_dir = os.path.join(settings.INSTANCES, name)
        executors[name] = Executor(inst_dir)

    # don't try to start running instances
    if not executors[name].is_alive():
        executors[name].start()
        i = 0
        # wait max 2 seconds for the instance to start
        while (not executors[name].is_alive() or executors[name].p is None) and i<10:
            time.sleep(.2)
            i+=1

    return HttpResponse(json.dumps({'success': True, 'pid':executors[name].p.pid}),
                        content_type='application/json')


@login_required
def create(request):
    """ handle create/start request from client """
    name = request.POST['instanceName']

    # create instance environment
    if name not in executors:
        inst_dir = os.path.join(settings.INSTANCES, name)

        # return if dir already exist or ports are already in use or ports are equal
        if os.path.isdir(inst_dir) or \
                request.POST['udpPort'] == request.POST['tcpPort'] or \
                len(list(filter(lambda x: x.is_alive() and
                                          (request.POST['udpPort'] in [x.udpPort, x.tcpPort] or
                                          request.POST['tcpPort'] in [x.udpPort, x.tcpPort]),
                                executors.values()))) > 0:
            return HttpResponseRedirect('/instances')

        # create the directory for the instance, copy necessary files
        os.makedirs(os.path.join(inst_dir, 'cfg'))
        os.makedirs(os.path.join(inst_dir, 'log'))
        for f in settings.SERVER_FILES:
            shutil.copy(os.path.join(settings.ACCSERVER,f), os.path.join(inst_dir,f))

        # the target config
        cfg = os.path.join(settings.CONFIGS, request.POST['cfg']+'.json')
        # link the requested config into the instance environment
        os.symlink(cfg, os.path.join(inst_dir, 'cfg', 'event.json'))

        def parse_val(key, d, value):
            if key in ['registerToLobby',
                       'dumpLeaderboards',
                       'isRaceLocked',
                       'randomizeTrackWhenEmpty']:
                return 1 if value=='on' else 0

            if isinstance(d[key], list): value = None
            elif isinstance(d[key], int): value = int(value)
            elif isinstance(d[key], float): value = float(value)
            elif not isinstance(d[key], str):
                print('Unknown type',type(d[key]), type(value))
                value = None
            return value

        # update the configuration.json
        cfg = json.load(open(os.path.join(settings.ACCSERVER, 'cfg', 'configuration.json'), 'r'))
        cfg_keys = ['udpPort','tcpPort', 'maxClients', 'registerToLobby']
        for key in cfg_keys:
            value = parse_val(key, cfg, request.POST[key])
            if value is not None: cfg[key] = value
        json.dump(cfg, open(os.path.join(inst_dir, 'cfg', 'configuration.json'), 'w'))

        # update the settings.json
        stings = json.load(open(os.path.join(settings.ACCSERVER, 'cfg', 'settings.json'), 'r'))
        for key in filter(lambda x:x not in cfg_keys+['csrfmiddlewaretoken', 'cfg','instanceName'], request.POST.keys()):
            value = parse_val(key, stings, request.POST[key])
            if value is not None: stings[key] = value
        json.dump(stings, open(os.path.join(inst_dir, 'cfg', 'settings.json'), 'w'))

        # start the instance
        start(request, name)

    return HttpResponseRedirect('/instances')


class InstanceForm(forms.Form):
    """
    Form used to fire up a new server instance
    """
    def __init__(self, data):
        super().__init__()
        self.fields['instanceName'] = forms.CharField(
            max_length=100,
            widget=forms.TextInput(attrs={"onkeyup":"nospaces(this)"}))

        self.fields['serverName'] = forms.CharField(max_length=100)
        self.fields['password'] = forms.CharField(max_length=100)
        self.fields['spectatorPassword'] = forms.CharField(max_length=100)
        self.fields['adminPassword'] = forms.CharField(max_length=100)

        self.fields['maxClients'] = forms.IntegerField(max_value=100, min_value=0)
        self.fields['spectatorSlots'] = forms.IntegerField(min_value=0)

        self.fields['trackMedalsRequirement'] = forms.IntegerField(max_value=3, min_value=0)
        self.fields['safetyRatingRequirement'] = forms.IntegerField(max_value=99, min_value=-1)
        self.fields['racecraftRatingRequirement'] = forms.IntegerField(max_value=99, min_value=-1)

        self.fields['isRaceLocked'] = forms.BooleanField(initial=False)
        self.fields['dumpLeaderboards'] = forms.BooleanField(initial=True)
        self.fields['registerToLobby'] = forms.BooleanField(initial=True)
        self.fields['randomizeTrackWhenEmpty'] = forms.BooleanField(initial=False)

        self.fields['allowAutoDQ'] = forms.BooleanField(initial=False)
        self.fields['shortFormationLap'] = forms.BooleanField(initial=False)
        self.fields['dumpEntryList'] = forms.BooleanField(initial=False)

        self.fields['udpPort'] = forms.IntegerField(max_value=None, min_value=1000)
        self.fields['tcpPort'] = forms.IntegerField(max_value=None, min_value=1000)

        self.fields['cfg'] = getCfgsField()
        self.fields['cfg'].required = True
        self.fields['cfg'].label = 'Config'

        # generate a label, all fields are required
        for key in self.fields:
            self.fields[key].label = createLabel(key)
            self.fields[key].required = True
            if key in settings.MESSAGES:
                self.fields[key].help_text = settings.MESSAGES[key]

        # use defaults from the 'data' object
        for key in data:
            if key not in self.fields:
                continue
            self.fields[key].initial = data[key]

        if self.fields['trackMedalsRequirement'].initial == -1:
            self.fields['trackMedalsRequirement'].initial = 0



def random_word():
    s = 'somename'
    try:
        while s is None or any(c for c in s if c not in string.ascii_letters):
            s = r.get_random_word(hasDictionaryDef="true",
                              minLength=5,
                              maxLength=10)
    except: pass
    return s


def index(request):
    # read defaults from files
    cfg = json.load(open(os.path.join(
        settings.ACCSERVER, 'cfg', 'configuration.json'), 'r'))
    cfg.update(json.load(open(os.path.join(
        settings.ACCSERVER, 'cfg', 'settings.json'), 'r')))

    # some static defaults
    cfg['instanceName'] = random_word()
    cfg['serverName'] = 'ACC server'
    cfg['dumpLeaderboards'] = 1

    for inst_dir in glob.glob(os.path.join(settings.INSTANCES, '*')):
        inst_name = os.path.split(inst_dir)[-1]
        if inst_name not in executors:
            executors[inst_name] = Executor(inst_dir)

    template = loader.get_template('instances/instances.html')
    context = {
        'form': InstanceForm(cfg),
        'executors': executors,
    }
    return HttpResponse(template.render(context, request))

