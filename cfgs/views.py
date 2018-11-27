from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render

import os, json, shutil

from accservermanager import settings
from cfgs.confEdit import createLabel, createForm
from cfgs.confSelect import CfgsForm, getCfgs, CfgCreate


@login_required
def confCreate(request):
    """ Create a new config based on the backuped origin custom.json """
    _base = os.path.join(settings.ACCSERVER,'cfg','custom.json')
    _f = os.path.join(settings.CONFIGS, request.POST['name']+'.json')
    if not os.path.exists(_f):  shutil.copy(_base, _f)
    return HttpResponseRedirect('/cfgs')


@login_required
def confDelete(request):
    """ Delete a config file """
    _f = os.path.join(settings.CONFIGS, request.POST['cfg']+'.json')
    if os.path.exists(_f):  os.remove(_f)
    return HttpResponseRedirect('/cfgs')


def confSelect(request):
    """ Show available configs and form to create a new config """
    context = {
        'form' : CfgCreate(),
        'cfgs' : getCfgs(),
    }
    return render(request, 'cfgs/confSelect.html', context)


def formForKey(request, config, *args):
    """ Read the select config file and display the selected portion of the json object """
    cfg_path = os.path.join(settings.CONFIGS, config+'.json')
    cfg = json.load(open(cfg_path, 'r'))
    args = args[0]

    # drill down into the json object to the selected part
    obj = cfg
    path = '/cfgs/%s'%config
    if len(args)>0:
        for arg in args.split('/'):
            if isinstance(obj, list):
                # handle add/remove requests for list objects
                if arg in ['add','remove']:
                    # copy the last object and add to the list
                    if arg=='add': obj.append(obj[-1])
                    # remove selected element
                    elif arg=='remove':
                        obj.remove(obj[int(args.split('/')[-1])])

                    json.dump(cfg, open(cfg_path, 'w'))
                    return HttpResponseRedirect(path)

                # select specific element of the list object
                arg = int(arg)
                # if the element is not in the list, redirect to the current path
                # (happens eg when jumping to another config which doesn't have the same
                # number of events)
                if arg>=len(obj): return HttpResponseRedirect(path)

            obj = obj[arg]
            path = '%s/%s'%(path,arg)

    if request.method == 'POST':
        # another config was selected
        if 'cfgs' in request.POST.keys():
            return HttpResponseRedirect('/cfgs/%s/%s'%(request.POST['cfgs'],args))

        # the form was submitted, update the values in the json obj and dump it to file
        if isinstance(obj, list): obj = obj[int(request.POST['_id'])]
        for key, value in request.POST.items():
            if key in ['csrfmiddlewaretoken', '_id']: continue

            if isinstance(obj[key], list): continue
            if isinstance(obj[key], int): value = int(value)
            elif isinstance(obj[key], float): value = float(value)
            elif not isinstance(obj[key], str):
                print('Unknown type',type(obj[key]), type(value))
            obj[key] = value

        json.dump(cfg, open(cfg_path, 'w'))
        return HttpResponseRedirect(request.path)

    _form, _forms = None, None
    # create the form only if an element of the config was selected
    if path != '/cfgs/%s'%config:
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
        'cfgs': CfgsForm(config),
        'cfg': config,
        'forms': _forms,
        'form': _form
    }
    return render(request, 'cfgs/confEdit.html', context)
