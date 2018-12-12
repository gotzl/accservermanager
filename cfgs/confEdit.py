from django import forms
from django.utils.safestring import mark_safe

import re

from accservermanager.settings import TRACKS, SESSION_TYPES


def fieldForKey(key, value):
    # list of fields that get special treatment, other fields are derived from value type
    if key == 'trackName':
        return forms.ChoiceField(
            widget=forms.Select,
            choices=TRACKS,
        )
    if key == 'sessionType':
        return forms.ChoiceField(
            widget=forms.Select,
            choices=SESSION_TYPES,
        )

    if isinstance(value, list): return forms.CharField()
    if isinstance(value, int): return forms.IntegerField()
    if isinstance(value, float): return forms.FloatField()
    if isinstance(value, str): return forms.CharField()
    return None


def createLabel(key):
    """ create label from json key, ie thisIsAKey -> This Is A Key """
    key = key[0].upper()+key[1:]
    return ' '.join(re.findall('[A-Z][^A-Z]*', key))


def createForm(obj, path):
    """ create a form form the objs keys, pre-filled with its values """

    # if the object is a list, create a form for each item
    if isinstance(obj, list):
        return [createForm(obj[i],'%s/%i'%(path,i)) for i in range(len(obj))]

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
                                               label=mark_safe('<a href="%s/%s">%s</a>'%(path,key,key)))

        else:
            form.fields[key] = fieldForKey(key, value)
            form.fields[key].label = createLabel(key)
            form.fields[key].initial = value
            form.fields[key].required = True

    return form