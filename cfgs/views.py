from django.http import HttpResponseRedirect
from django.shortcuts import render

import os, json, shutil

from accservermanager import settings
from cfgs.confEdit import createLabel, createForm
from cfgs.confSelect import CfgsForm, getCfgs, CfgCreate

PATH = os.path.join(settings.ACCSERVER,'cfg','custom')


def confCreate(request):
    """ Create a new config based on the backuped origin custom.json """
    if request.method == 'POST':
        _base = os.path.join(PATH,'../','custom.json.bkup')
        _f = os.path.join(PATH, request.POST['name']+'.json')
        if not os.path.exists(_f):  shutil.copy(_base, _f)
        return HttpResponseRedirect('..')


def confDelete(request):
    """ Delete a config file """
    if request.method == 'POST':
        _f = os.path.join(PATH, request.POST['cfg']+'.json')
        if os.path.exists(_f):  os.remove(_f)
        return HttpResponseRedirect('..')


def confSelect(request):
    """ Show available configs and form to create a new config """
    if request.method == 'POST':
        print(request.path)
        cfg = os.path.splitext(request.POST['cfgs'])[0]
        return HttpResponseRedirect('/cfgs/%s/'%cfg)

    context = {
        'form' : CfgCreate(),
        'cfgs' : [os.path.splitext(i)[0] for i in getCfgs()],
    }
    return render(request, 'cfgs/confSelect.html', context)


def formForKey(request, config, *args):
    """ Read the select config file and display the selected portion of the json object """
    cfg = json.load(open(os.path.join(PATH, config+'.json'),'r'))
    args = args[0]

    # drill down into the json object to the selected part
    obj = cfg
    path = config
    if len(args)>0:
        for arg in args.split('/'):
            if isinstance(obj, list): arg = int(arg)
            obj = obj[arg]
            path = '%s/%s'%(path,arg)

    # the form was submitted, update the values in the json obj and dump it to file
    if request.method == 'POST':
        for key, value in request.POST.items():
            if key in ['csrfmiddlewaretoken', 'selectedCfg']: continue

            if isinstance(obj[key], list): continue
            if isinstance(obj[key], int): value = int(value)
            elif isinstance(obj[key], float): value = float(value)
            elif not isinstance(obj[key], str):
                print('Unknown type',type(obj[key]), type(value))
            obj[key] = value

        json.dump(cfg, open(os.path.join(PATH, config+'.json'),'w'))
        return HttpResponseRedirect(request.path)

    _form, _forms = None, None
    # create the form only if an element of the config was selected
    if path != config:
        _form = createForm(obj, path)

    # ugly switch to handle list-values (like events)
    if isinstance(_form, list):
        _forms = _form
        _form = None

    # extract first level keys of the json object, they are displayed in the navigation sidebar
    # only if they are not emptylists
    emptyList = lambda x: not (isinstance(cfg[x], list) and len(cfg[x])==0)
    keys = sorted(filter(emptyList, cfg.keys()))

    context = {
        'keys': [(k, createLabel(k)) for k in keys],
        'cfgs': CfgsForm(config+'.json'),
        'cfg': config,
        'forms': _forms,
        'form': _form
    }
    return render(request, 'cfgs/index.html', context)
