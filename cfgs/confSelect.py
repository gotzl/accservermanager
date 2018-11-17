from django import forms

import os, glob, ntpath

from accservermanager import settings


def getCfgsField(selected=None, attrs=None):
    cfgs = glob.glob('%s/*.json'%(os.path.join(settings.ACCSERVER,'cfg','custom')))
    return forms.ChoiceField(
        widget=forms.Select(attrs=attrs),
        choices=[('','')]+[(ntpath.basename(i),ntpath.basename(i)) for i in cfgs],
        initial=None if selected is None else selected,
        label='',
    )


class CfgsForm(forms.Form):
    def __init__(self, selected=None):
        super().__init__()
        self.fields['cfgs'] = getCfgsField(selected, attrs={"onChange":'this.form.submit()'})
