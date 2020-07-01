import glob
import itertools
import ntpath

from django.shortcuts import render

import os, json

from django.utils.html import format_html
from django_tables2 import tables, Column, TemplateColumn, RequestConfig

from accservermanager.settings import CAR_MODEL_TYPES, DATA_DIR


class LeaderBoard(tables.Table):
    position = Column(empty_values=())
    raceNumber = Column(accessor='car.raceNumber')
    carModel = Column(accessor='car.carModel')
    teamName = Column(accessor='car.teamName')
    drivers = Column(accessor='car.drivers')
    bestLap = Column(accessor='timing')
    laps = Column(accessor='timing.lapCount')
    totaltime = Column(accessor='timing.totalTime')

    def __init__(self, *args, **kwargs):
        super(LeaderBoard, self).__init__(*args, **kwargs)
        self.counter = itertools.count(start=1)

    def render_position(self):
        return '%d' % next(self.counter)

    def render_carModel(self, value):
        for model in CAR_MODEL_TYPES:
            if model[0]==value: return model[1]
        return 'Unknown model %i'%value

    def render_drivers(self, value):
        short = ' / '.join([d['shortName'] for d in value])
        long = ' / '.join(['%s %s'%(d['firstName'],d['lastName']) for d in value])
        return format_html('<p title="{}">{}</p>', long, short)

    def render_time(self, value):
        s = value//1000
        m = s//60
        s %=60
        if m==0: return '%02i.%03i'%(s, value%1000)
        return '%i:%02i.%03i'%(m, s, value%1000)

    def render_bestLap(self, value):
        return format_html('<p title="{}">{}</p>',
                           ' | '.join(list(map(self.render_time, value['bestSplits']))),
                           self.render_time(value['bestLap']))

    def render_totaltime(self, value):
        return self.render_time(value)


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
    results = json.load(open(os.path.join(results_path, result+'.json'), 'rb', encoding='utf-16'))

    path = request.path
    if path[0] == '/': path = path[1:]
    if path[-1] == '/':path = path[:-1]
    path = path.split('/')

    context = {
        'path': [(j, '/'+'/'.join(path[:i+1])) for i,j in enumerate(path)],
        'table': LeaderBoard(results['leaderBoardLines'])
    }
    return render(request, 'results/results.html', context)


def resultSelect(request, instance):
    """ Show available results """
    results_path = os.path.join(DATA_DIR, 'instances', instance, 'results')
    files = sorted(glob.glob('%s/*result*.json'%(results_path)), reverse=True)

    results = []
    for f in files:
        r = json.load(open(f, 'rb', encoding='utf-16'))
        results.append(dict(
            name=os.path.splitext(ntpath.basename(f))[0],
            type=r['type'], # TODO: decode session type, seems to be borked atm
            entries=len(r['leaderBoardLines']),
            wetSession=r['isWetSession'],
        ))

    path = request.path
    if path[0] == '/': path = path[1:]
    if path[-1] == '/':path = path[:-1]
    path = path.split('/')

    table = Results(results)
    RequestConfig(request).configure(table)

    context = {
        'path' : [(j, '/'+'/'.join(path[:i+1])) for i,j in enumerate(path)],
        'table' : table,
    }
    return render(request, 'results/results.html', context)