from django.http import HttpResponseRedirect
from django.shortcuts import render
from django import forms

import os, glob, json, ntpath

from accservermanager import settings
from cfgs.confEdit import createLabel, createForm

PATH = os.path.join(settings.ACCSERVER,'cfg','custom')


def getCfgs():
    return glob.glob('%s/*.json'%(os.path.join(settings.ACCSERVER,'cfg','custom')))


class CfgsForm(forms.Form):
    def __init__(self, selected=None):
        super().__init__()
        self.fields['cfgs'] = forms.ChoiceField(
            widget=forms.Select(attrs={"onChange":'this.form.submit()'}),
            choices=[('','')]+[(ntpath.basename(i),ntpath.basename(i)) for i in getCfgs()],
            initial=None if selected is None else selected,
            label='',
        )
        self.fields['cfgs'].empty_label = "Select a config"



def confSelect(request):
    if request.method == 'POST':
        cfg = os.path.splitext(request.POST['cfgs'])[0]
        return HttpResponseRedirect('/cfgs/%s/'%cfg)

    context = {
        'cfgs' : CfgsForm(),
        'cfg' : None,
    }
    return render(request, 'cfgs/index.html', context)


def formForKey(request, config, *args):
    cfg = json.load(open(os.path.join(PATH, config+'.json'),'r'))
    args = args[0]

    obj = cfg
    path = config
    if len(args)>0:
        for arg in args.split('/'):
            if isinstance(obj, list): arg = int(arg)
            obj = obj[arg]
            path = '%s/%s'%(path,arg)

    if request.method == 'POST':
        for key, value in request.POST.items():
            if key in ['csrfmiddlewaretoken', 'selectedCfg']: continue

            if isinstance(obj[key], list): continue
            if isinstance(obj[key], int): value = int(value)
            elif isinstance(obj[key], float): value = float(value)
            elif not isinstance(obj[key], str):
                print('Unknown type',type(obj[key]), type(value))
            obj[key] = value

        json.dump(cfg, open(PATH,'w'))
        return HttpResponseRedirect(request.path)

    _form, _forms = None, None
    if path != config:
        _form = createForm(obj, path)

    if isinstance(_form, list):
        _forms = _form
        _form = None

    emptyList = lambda x: not (isinstance(cfg[x], list) and len(cfg[x])==0)
    context = {
        'keys': [(k, createLabel(k)) for k in sorted(filter(emptyList, cfg.keys()))],
        'cfgs' : CfgsForm(config+'.json'),
        'cfg' : config,
        'forms' : _forms,
        'form' : _form
    }
    return render(request, 'cfgs/index.html', context)
