from django.contrib.auth.decorators import login_required
from django.forms import ModelForm
from django.shortcuts import render
from django_tables2 import tables, RequestConfig

from accservermanager import settings
from booking.models import EntryList, Entry, Driver


class MetaBaseTable:
    row_attrs = {
        'url': lambda record: '%s'%record.pk
    }

class MetaBaseForm:
    fields = '__all__'


class EntryListTable(tables.Table):
    class Meta(MetaBaseTable):
        model = EntryList

class EntryTable(tables.Table):
    class Meta(MetaBaseTable):
        model = Entry

class DriverTable(tables.Table):
    class Meta(MetaBaseTable):
        model = Driver


class DriverForm(ModelForm):
    class Meta(MetaBaseForm):
        model = Driver

class EntryForm(ModelForm):
    class Meta(MetaBaseForm):
        model = Entry

class EntryListForm(ModelForm):
    class Meta(MetaBaseForm):
        model = EntryList


def createForm(request, Form, instance=None):
    if request.method == 'POST':
        form = Form(request.POST, instance=instance)
        if form.is_valid(): form.save()
    else:
        form = Form(instance=instance)

    for key in form.fields:
        if key in settings.MESSAGES:
            form.fields[key].help_text = settings.MESSAGES[key]

    return form


@login_required
def edit(request, Form, instance=None):
    form = createForm(request, Form, instance)

    # path = [request.build_absolute_uri('/').strip("/")]
    path = request.path.strip("/").split('/')
    return render(request,
                  'booking/createEntry.html',
                  {'form': form,
                   'path': [(j, '/'+'/'.join(path[:i+1])) for i,j in enumerate(path)],
                   })


@login_required
def create(request, Form):
    return edit(request, Form, create=True)


def selectEdit(request, Form, Model, pk):
    return edit(request, Form, Model.objects.get(pk=pk))


models = {'drivers':[Driver,DriverTable,DriverForm],
         'entries':[Entry,EntryTable,EntryForm],
         'entrylists':[EntryList,EntryListTable,EntryListForm]}


@login_required
def showObject(request, object, pk=None):
    model = models[object]
    if pk is not None:
        return selectEdit(request, model[2], model[0], pk)

    path = request.path.strip("/").split('/')
    form = createForm(request, model[2], None)
    table = model[1](model[0].objects.all())
    RequestConfig(request).configure(table)
    return render(request,
                  'booking/entries.html',
                  {'table': table,
                   'form': form,
                   'path': [(j, '/'+'/'.join(path[:i+1])) for i,j in enumerate(path)],
                   })


def index(request):
    # create a table for each model
    context = {o:m[1](m[0].objects.all()) for o, m in models.items()}
    return render(request,
                  'booking/index.html',
                  context)