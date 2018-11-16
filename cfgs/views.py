from django.http import HttpResponseRedirect
from django.shortcuts import render
from django import forms
from django.utils.safestring import mark_safe

import re, json

from accservermanager import settings

TRACKS = (
    ('misano', 'Misano'),
    ('paul_ricard', 'Paul Ricard'),
    ('nurburgring', 'Nuerburgring GP'),
)

FIELDS = {
    'trackName': forms.ChoiceField(
        widget=forms.Select,
        choices=TRACKS,
    ),
    'sessionType': forms.IntegerField(max_value=None, min_value=0)
}


PATH = '%s/cfg/custom.json'%settings.ACCSERVER


def fieldForKey(key):
    if key in FIELDS: return FIELDS[key]
    return forms.FloatField()


def createLabel(key):
    key = key[0].upper()+key[1:]
    return ' '.join(re.findall('[A-Z][^A-Z]*', key))


def createForm(obj, path):
    if isinstance(obj, list):
        return [createForm(obj[i],'%s/%i'%(path,i)) for i in range(len(obj))]

    if isinstance(obj, int):
        obj = {'value': obj}

    form = forms.Form()
    for key, value in sorted(obj.items(),key=lambda x:x[0]):
        if (isinstance(value,dict)):
            form.fields[key] = forms.CharField(widget=forms.TextInput,
                                               disabled=True,
                                               label=mark_safe('<a href="/cfgs%s/%s">%s</a>'%(path,key,key)))

        else:
            form.fields[key] = fieldForKey(key)
            form.fields[key].initial = value
            form.fields[key].required = True
            form.fields[key].label = createLabel(key)
    return form


def formForKey(request, *args):
    cfg = json.load(open(PATH,'r'))

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

    if request.method == 'POST':
        for key, value in request.POST.items():
            if key == 'csrfmiddlewaretoken': continue

            if isinstance(obj[key], list): continue
            if isinstance(obj[key], int): value = int(value)
            elif isinstance(obj[key], float): value = float(value)
            elif not isinstance(obj[key], str):
                print('Unknown type',type(obj[key]), type(value))
            obj[key] = value

        json.dump(cfg, open(PATH,'w'))
        return HttpResponseRedirect(request.path)

    _form, _forms = None, None
    if path != '':
        _form = createForm(obj, path)

    if isinstance(_form, list):
        _forms = _form
        _form = None

    emptyList = lambda x: not (isinstance(cfg[x], list) and len(cfg[x])==0)
    context = {
        'keys': [(k, createLabel(k)) for k in sorted(filter(emptyList, cfg.keys()))],
        'forms' : _forms,
        'form' : _form
    }
    return render(request, 'cfgs/index.html', context)
