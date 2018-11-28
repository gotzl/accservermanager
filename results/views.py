import glob
import ntpath

from cfgs.confEdit import createForm, createLabel
from django.shortcuts import render

import os, json, getpass
from sys import platform

import django_tables2 as tables


class SimpleTable(tables.Table):
    lapTime = tables.Column()
    splitTimes = tables.Column()


WINEPREFIX = os.environ['WINEPREFIX'] if 'WINEPREFIX' in os.environ else \
    '/home/%s/.wine/dosdevices'%getpass.getuser()
PATH = "c:/users/%s/My Documents/Assetto Corsa Competizione/Results/Server"%getpass.getuser()


def driver_laps(obj, driver_idx):
    return filter(lambda x:x['driverIndex'] == driver_idx, obj['events'][0]['sessions'][0]['laps'])


def index(request, result, *args):
    """ Read the select results file and display the selected portion of the json object """
    results_path = os.path.join(PATH, result+'.json')
    if platform != "Windows":
        results_path = os.path.join(WINEPREFIX, results_path)

    results = json.load(open(results_path, 'r'))
    args = args[0]

    # drill down into the json object to the selected part
    obj = results
    path = '/results/%s'%result
    if len(args)>0:
        for arg in args.split('/'):
            if isinstance(obj, list):
                # select specific element of the list object
                arg = int(arg)

            obj = obj[arg]
            path = '%s/%s'%(path,arg)

    _form, _forms = None, None
    # create the form only if an element of the config was selected
    if path != '/results/%s'%result:
        _form = createForm(obj, path)

    # ugly switch to handle list-values (like events)
    if isinstance(_form, list):
        _forms = _form
        _form = None

    # extract first level keys of the json object, they are displayed in the navigation sidebar
    # only if they are not emptylists
    emptyList = lambda x: not (isinstance(results[x], list) and len(results[x])==0)
    keys = sorted(filter(emptyList, results.keys()))

    context = {
        'keys': [(k, createLabel(k)) for k in keys],
        'cfg': result,
        'forms': _forms,
        'form': _form
    }

    if path == '/results/2.000000/drivers/0':
        table = SimpleTable(driver_laps(results,0))
        context['table'] = table

    return render(request, 'results/results.html', context)


def resultSelect(request):
    """ Show available results """
    results_path = PATH
    if platform != "Windows":
        results_path = os.path.join(WINEPREFIX, results_path)
    results = list(map(lambda x: os.path.splitext(ntpath.basename(x))[0],
                    glob.glob('%s/*.json'%(results_path))))
    context = {
        'results' : results,
    }
    return render(request, 'results/resultSelect.html', context)