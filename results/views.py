import glob
import itertools
import ntpath

from django.shortcuts import render

import os, json

from django_tables2 import tables, utils, Column, TemplateColumn

from accservermanager.settings import CAR_MODEL_TYPES, DATA_DIR


class LeaderBoard(tables.Table):
    position = Column(empty_values=())
    raceNumber = Column(accessor='car.raceNumber')
    carModel = Column(accessor='car.carModel')
    teamName = Column(accessor='car.teamName')
    drivers = Column(accessor='car.drivers')
    bestLap = Column(accessor='timing.bestLap')
    laps = Column(accessor='timing.lapCount')

    def __init__(self, *args, **kwargs):
        super(LeaderBoard, self).__init__(*args, **kwargs)
        self.counter = itertools.count(start=1)

    def render_position(self):
        return '%d' % next(self.counter)

    def render_carModel(self, value):
        return CAR_MODEL_TYPES[value][1]

    def render_drivers(self, value):
        return '/'.join([d['shortName'] for d in value])

    def render_bestLap(self, value):
        s = value//1000
        m = s//60
        s %=60
        return '%i:%02i.%03i'%(m, s, value%1000)


class Results(tables.Table):
    name = Column()
    type = Column()
    entries = Column()
    wetSession = Column()
    view = TemplateColumn(template_name='results/table/results_view_column.html')
    # delete = TemplateColumn(template_name='results/table/results_delete_column.html')


def results(request, *args, **kwargs):
    """ Read the select results file and display the selected portion of the json object """
    instance = kwargs['instance']
    result = args[0]
    results_path = os.path.join(DATA_DIR, 'instances', instance, 'results')
    results = json.load(open(os.path.join(results_path, result+'.json'), 'rb'))

    # drill down into the json object to the selected part
    obj = results
    path = ['results', result]

    context = {
        'path': [(j, '/'+'/'.join(path[:i+1])) for i,j in enumerate(path)],
        'table': LeaderBoard(obj['leaderBoardLines'])
    }
    return render(request, 'results/results.html', context)


def resultSelect(request, instance):
    """ Show available results """
    results_path = os.path.join(DATA_DIR, 'instances', instance, 'results')
    files = glob.glob('%s/*result*.json'%(results_path))

    results = []
    for f in files:
        r = json.load(open(f, 'rb'))
        results.append(dict(
            name=os.path.splitext(ntpath.basename(f))[0],
            type=r['type'], # TODO: decode session type, seems to be borked atm
            entries=len(r['leaderBoardLines']),
            wetSession=r['isWetSession'],
        ))


    context = {
        'table' : Results(results),
    }
    return render(request, 'results/results.html', context)