from django import forms
from django.utils.safestring import mark_safe

import re

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
                                               label=mark_safe('<a href="/cfgs/%s/%s">%s</a>'%(path,key,key)))

        else:
            form.fields[key] = fieldForKey(key)
            form.fields[key].initial = value
            form.fields[key].required = True
            form.fields[key].label = createLabel(key)
    return form