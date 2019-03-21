from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render

import os, json, shutil, glob
from pathlib import Path

from accservermanager import settings
from accservermanager.settings import SESSION_TEMPLATE
from cfgs.confEdit import createLabel, createForm
from cfgs.confSelect import CfgsForm, getCfgs, CfgCreate


@login_required
def confCreate(request):
    """ Create a new config based on the backuped origin custom.json """
    _base = os.path.join(settings.ACCSERVER,'cfg','event.json')
    _f = os.path.join(settings.CONFIGS, request.POST['name']+'.json')
    if not os.path.exists(_f):  shutil.copy(_base, _f)
    return HttpResponseRedirect('/cfgs')


@login_required
def confClone(request):
    """ Clone a config file """
    _f = os.path.join(settings.CONFIGS, request.POST['cfg']+'.json')
    _n = os.path.join(settings.CONFIGS, request.POST['cfg']+'_clone.json')
    if not os.path.exists(_n):  shutil.copy(_f, _n)
    return HttpResponseRedirect('/cfgs')


@login_required
def confRename(request):
    """ Rename a config file """
    _o = request.POST['cfg']
    _n = request.POST['cfgname']
    _old = os.path.join(settings.CONFIGS, _o+'.json')
    _new = os.path.join(settings.CONFIGS, _n+'.json')
    if _o != _n and os.path.exists(_old) and not os.path.exists(_new):
        # create a copy of the config with the new name
        shutil.copy(_old, _new)
        # change the link of instances using the old config
        from instances.views import executors
        for inst_dir in glob.glob(os.path.join(settings.INSTANCES, '*')):
            inst_name = os.path.split(inst_dir)[-1]
            if inst_name in executors:
                executors[inst_name].config = _n+'.json'

            cfg = os.path.join(inst_dir, 'cfg', 'event.json')
            if Path(cfg).resolve().name == _o+'.json':
                os.remove(cfg)
                os.symlink(_new, cfg)

        # finally, remove the original config
        os.remove(_old)

    return HttpResponseRedirect('/cfgs')


@login_required
def confDelete(request):
    """ Delete a config file """
    _f = os.path.join(settings.CONFIGS, request.POST['cfg']+'.json')
    if os.path.exists(_f):
        # check that no executor references the cfg
        # TODO: give some feedback to the UI!
        for inst_dir in glob.glob(os.path.join(settings.INSTANCES, '*')):
            cfg = os.path.join(inst_dir, 'cfg', 'event.json')
            if Path(cfg).resolve().name == request.POST['cfg']+'.json':
                return HttpResponseRedirect('/cfgs')
        os.remove(_f)
    return HttpResponseRedirect('/cfgs')


@login_required
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
    if len(cfg['sessions']) == 0:
        cfg['sessions'] = [SESSION_TEMPLATE]
    args = args[0]

    # drill down into the json object to the selected part
    obj = cfg
    path = ['cfgs',config]
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
                    return HttpResponseRedirect('/'+'/'.join(path))

                # select specific element of the list object
                arg = int(arg)
                # if the element is not in the list, redirect to the current path
                # (happens eg when jumping to another config which doesn't have the same
                # number of events)
                if arg>=len(obj): return HttpResponseRedirect('/'+'/'.join(path))

            obj = obj[arg]
            path.append(str(arg))

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
        # 'keys': [(k, createLabel(k)) for k in keys],
        'cfgs': CfgsForm(config),
        'cfg': config,
        'path': [(j, '/'+'/'.join(path[:i+1])) for i,j in enumerate(path)],
        'forms': _forms,
        'form': _form
    }
    return render(request, 'cfgs/confEdit.html', context)
