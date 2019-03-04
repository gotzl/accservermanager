import glob
import ntpath

from django import forms
from django.utils.safestring import mark_safe

from accservermanager.settings import CAR_MODEL_TYPES
from django.shortcuts import render

import os, json, getpass, copy, re
from sys import platform

import django_tables2 as tables

from cfgs.confEdit import createLabel


def fieldForKey(key, value, results):
    from cfgs.confEdit import fieldForKey as fallback
    if key == 'carModelType':
        return forms.ChoiceField(
            widget=forms.Select,
            choices=CAR_MODEL_TYPES,
        )
    if key == 'carIndex':
        return forms.ChoiceField(
            widget=forms.Select,
            choices=enumerate(results['cars']),
        )
    if key == 'driverIndex':
        return forms.ChoiceField(
            widget=forms.Select,
            choices=enumerate(results['drivers']),
        )

    return fallback(key, value)


def createForm(obj, path, results):
    """ create a form form the objs keys, pre-filled with its values """

    # if the object is a list, create a form for each item
    if isinstance(obj, list):
        return [createForm(obj[i], path + [str(i)], results) for i in range(len(obj))]

    # if the object is a integer, create a temporary object and proceed
    if isinstance(obj, int):
        obj = {'value': obj}

    # iterate over the objects elements and add fields to the form
    form = forms.Form()
    for key, value in sorted(obj.items(), key=lambda x:x[0]):
        # if the element is a object itself, let the form display a link to further drilldown into this object
        if isinstance(value, dict) or \
                (isinstance(value, list) and len(value)>0 and isinstance(value[0], dict)):
            form.fields[key] = forms.CharField(widget=forms.TextInput,
                                               disabled=True,
                                               label=mark_safe('<a href="/%s">%s</a>'%('/'.join(path+[key]),key)))

        else:
            form.fields[key] = fieldForKey(key, value, results)
            form.fields[key].label = createLabel(key)
            form.fields[key].initial = value
            form.fields[key].required = True

    return form

class cars(tables.Table):
    raceNumber = tables.Column()
    carGuid = tables.Column()
    teamIndex = tables.Column()
    carModelType = tables.Column()
    cupCategory = tables.Column()
    def render_carModelType(self, value):
        return next(filter(lambda x:x[0]==value, CAR_MODEL_TYPES))[1]

class drivers(tables.Table):
    driverCategory = tables.Column()
    # playerID = tables.Column()
    firstName = tables.Column()
    # secondName = tables.Column()
    lastName = tables.Column()
    # nickName = tables.Column()
    shortName = tables.Column()
    nationality = tables.Column()
    weight = tables.Column()

class teams(tables.Table):
    displayName = tables.Column()
    teamName = tables.Column()
    competitorName = tables.Column()
    competitorNationality = tables.Column()
    nationality = tables.Column()
    teamGuid = tables.Column()

class laps(tables.Table):
    # driverIndex = tables.Column()
    # carIndex = tables.Column()
    driver = tables.Column()
    car = tables.Column()
    lapTime = tables.Column()
    splitTimes = tables.Column()
    totalTime = tables.Column()
    timeStamp = tables.Column()
    lapStates = tables.Column()

class carDrivers(tables.Table):
    c = tables.Column()
    d = tables.Column()

class startingDriverIndex(tables.Table):
    c = tables.Column()
    d = tables.Column()

class carStateResult(tables.Table):
    c = tables.Column()
    lapCount = tables.Column(accessor='s.lapCount')
    avgLapTime = tables.Column(accessor='s.avgLapTime')
    bestLap  = tables.Column(accessor='s.bestLap.lapTime')
    s = tables.Column()

class s(tables.Table):
    pass


def driver(idx, results):
    return results['drivers'][idx]

def team(idx, results):
    return results['teams'][idx]

def car(idx, results):
    data = copy.copy(results['cars'][idx])
    data['team'] = team(data['teamIndex'], results)
    return data


WINEPREFIX = os.environ['WINEPREFIX'] if 'WINEPREFIX' in os.environ else \
    '/home/%s/.wine/dosdevices'%getpass.getuser()
PATH = "c:/users/%s/My Documents/Assetto Corsa Competizione/Results/Server"%getpass.getuser()


def index(request, result, *args):
    """ Read the select results file and display the selected portion of the json object """
    results_path = os.path.join(PATH, result+'.json')
    if platform != "Windows":
        results_path = os.path.join(WINEPREFIX, results_path)

    results = json.load(open(results_path, 'r', encoding='latin-1'))
    args = args[0]

    # drill down into the json object to the selected part
    obj = results
    path = ['results', result]
    arg = None

    if len(args)==0:
        args = 'events'

    for arg in args.split('/'):
        if isinstance(obj, list):
            # select specific element of the list object
            arg = int(arg)

        obj = obj[arg]
        path.append(str(arg))

    _form, _forms, _table = None, None, None
    # create the form only if an element of the config was selected
    if len(path) > 2:
        if isinstance(obj, list):
            if arg is not None and arg in globals():
                if arg=='carDrivers':
                    # resolve cars, drivers
                    data = [{'c': car(i['c'],results), 'd': [driver(j, results) for j in i['d']]} for i in obj]
                elif arg=='startingDriverIndex':
                    # resolve cars, drivers
                    data = [{'c': car(i['c'],results), 'd': driver(i['d'],results)} for i in obj]
                elif arg=='laps':
                    data = copy.copy(obj)
                    for j in data:
                        j['driver'] = driver(j['driverIndex'], results)
                        j['car'] = car(j['carIndex'], results)
                elif arg=='carStateResult':
                    # remove cars that have no valid info?
                    data = list(filter(lambda x:x['s']['totalTimeOfficial']!=0, obj))
                    for i in data:
                        i['c'] = car(i['c'], results)
                else: data = obj
                _table = globals()[arg](data)
            else : _forms = createForm(obj, path, results)

        else:
            _form = createForm(obj, path, results)

    # extract first level keys of the json object, they are displayed in the navigation sidebar
    # only if they are not emptylists
    emptyList = lambda x: not (isinstance(results[x], list) and len(results[x])==0)
    keys = sorted(filter(emptyList, results.keys()))

    context = {
        'path': [(j, '/'+'/'.join(path[:i+1])) for i,j in enumerate(path)],
        'table': _table,
        'form': _form,
        'forms': _forms
    }
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