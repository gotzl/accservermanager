from django.shortcuts import render
from django import forms
from django.utils.safestring import mark_safe

import json

TRACKS = (
    ('misano', 'Misano'),
    ('paulricard', 'Paul Ricard'),
    ('nuerburg', 'Nuerburgring GP'),
)

FIELDS = {
    'trackName': forms.ChoiceField(
        required=True,
        widget=forms.Select,
        choices=TRACKS,
    ),
    'sessionType': forms.IntegerField(max_value=None, min_value=0)
}


def fieldForKey(key):
    if key in FIELDS: return FIELDS[key]
    return forms.FloatField()


def createForm(obj, path):
    if isinstance(obj, list):
        return [createForm(obj[i],'%s/%i/'%(path,i)) for i in range(len(obj))]

    if isinstance(obj, int):
        obj = {'value': obj}

    form = forms.Form()
    for key, value in sorted(obj.items(),key=lambda x:x[0]):
        if (isinstance(value,dict)):
            form.fields[key] = forms.CharField(widget=forms.TextInput,
                                               disabled=True,
                                               label=mark_safe('<a href="/cfgs%s%s">%s</a>'%(path,key,key)))

        else:
            form.fields[key] = fieldForKey(key)
            form.fields[key].initial = value

    return form


def formForKey(request, *args):
    path = '/run/media/gotzl/stuff/games/Steam/steamapps/common/Assetto Corsa Competizione/server/cfg/custom.json'
    cfg = json.load(open(path))

    args = args[0]
    if len(args)>0 and args[-1] == '/':
        args = args[:-1]

    obj = cfg
    path = ''
    if len(args)>0:
        for arg in args.split('/'):
            if isinstance(obj, list): arg = int(arg)
            obj = obj[arg]
            path = '%s/%s'%(path,arg)

    _forms = None
    if path != '':
        _forms = createForm(obj, path)

    emptyList = lambda x: not (isinstance(cfg[x], list) and len(cfg[x])==0)
    context = {
        'keys': sorted(filter(emptyList, cfg.keys())),
        'forms' : _forms if _forms is None or isinstance(_forms, list) else [_forms],
    }
    return render(request, 'cfgs/index.html', context)
