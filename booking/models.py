from django.db import models

from accservermanager import settings


class Driver(models.Model):
    firstName=models.CharField(max_length=100, blank=True)
    lastName=models.CharField(max_length=100, blank=True)
    shortName=models.CharField(max_length=20, blank=True)
    driverCategory=models.IntegerField(default=-1, blank=True, null=True,
                                       choices=settings.DRIVER_CATEGORY)
    playerID=models.CharField(max_length=100, primary_key=True)


class Entry(models.Model):
    drivers=models.ManyToManyField(Driver,
                                   verbose_name='list of drivers',
                                   # on_delete=models.DO_NOTHING
                                   )
    raceNumber=models.IntegerField(default=-1)
    forcedCarModel=models.IntegerField(default=-1, blank=True, null=True,
                                       choices=settings.CAR_MODEL_TYPES)
    overrideDriverInfo=models.IntegerField(default=0)
    isServerAdmin=models.IntegerField(default=0)


class EntryList(models.Model):
    name = models.CharField(max_length=100)
    entries = models.ManyToManyField(Entry,
                                   verbose_name='list of entries',
                                   # on_delete=models.DO_NOTHING
                                   )

