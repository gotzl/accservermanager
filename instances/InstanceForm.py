from django import forms

from accservermanager.settings import CAR_GROUPS
from cfgs.confEdit import createLabel
from cfgs.confSelect import getCfgsField

from accservermanager import settings


class InstanceForm(forms.Form):
    """
    Form used to fire up a new server instance
    """
    instanceName = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"onkeyup":"nospaces(this)"}))

    serverName = forms.CharField(max_length=100)

    password = forms.CharField(max_length=100, required=False)
    spectatorPassword = forms.CharField(max_length=100, required=False)
    adminPassword = forms.CharField(max_length=100, required=False)

    maxConnections = forms.IntegerField(max_value=1000, min_value=0, required=False)

    carGroup = forms.ChoiceField(widget=forms.Select, choices=CAR_GROUPS)
    trackMedalsRequirement = forms.IntegerField(max_value=3, min_value=0, required=False)
    safetyRatingRequirement = forms.IntegerField(max_value=99, min_value=-1, required=False)
    racecraftRatingRequirement= forms.IntegerField(max_value=99, min_value=-1, required=False)

    isRaceLocked = forms.BooleanField(required=False)
    dumpLeaderboards = forms.BooleanField(required=False)
    registerToLobby = forms.BooleanField(required=False)
    randomizeTrackWhenEmpty = forms.BooleanField(required=False)

    maxCarSlots = forms.IntegerField(max_value=1000, min_value=0, required=False)

    allowAutoDQ = forms.BooleanField(required=False)
    shortFormationLap = forms.BooleanField(required=False)
    dumpEntryList = forms.BooleanField(required=False)

    udpPort = forms.IntegerField(max_value=None, min_value=1000)
    tcpPort = forms.IntegerField(max_value=None, min_value=1000)
    lanDiscovery = forms.BooleanField(required=False)

    def __init__(self, data):
        super().__init__(data)

        # There is an issue with the 'required' error, so set this field
        # to not-required. This is ok, since it is always pre-filled.
        self.fields['cfg'] = getCfgsField(label='Config', required=False)

        for key in self.fields:
            if key=='cfg': continue
            # generate better label
            self.fields[key].label = createLabel(key)

            # add help text if available
            if key in settings.MESSAGES:
                self.fields[key].help_text = settings.MESSAGES[key]

            # use default values from the 'data' object
            if key in data:
                self.fields[key].initial = data[key]
