from django import forms

import os, glob, ntpath

from accservermanager import settings


def getCfgs():
    """ Check the cfg/custom folder for available configs, return list of file names w/o suffix """
    return list(map(lambda x: os.path.splitext(ntpath.basename(x))[0],
                    glob.glob('%s/*.json'%(os.path.join(settings.ACCSERVER,'cfg','custom')))))


class CustomSelect(forms.Select):
    """ Select widget where the option with value None or '' is default or hidden """
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        options = super(CustomSelect, self).create_option(name, value, label, selected, index, subindex=None, attrs=None)
        if value is None or len(value)==0: options['attrs'] = {'selected':True, 'disabled':True, 'hidden':True}
        # print(value)
        return options


def getCfgsField(selected=None, attrs=None):
    """ A select component showing the available configs """
    return forms.ChoiceField(
        widget=CustomSelect(attrs=attrs),
        choices=[('','')] + [(i,i) for i in getCfgs()],
        initial=None if selected is None else selected,
        label='',
    )


class CfgsForm(forms.Form):
    """ A form with a select component showing the available configs """
    def __init__(self, selected=None):
        super().__init__()
        self.fields['cfgs'] = getCfgsField(selected, attrs={"onChange":'this.form.submit()'})


class CfgCreate(forms.Form):
    """ A form creating a new config, only holds a name field """
    name = forms.CharField(max_length=100,
                           required=True,
                           widget=forms.TextInput(attrs={"onkeyup":"nospaces(this)"}))