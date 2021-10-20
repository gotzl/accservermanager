from django import forms

from accservermanager.settings import CAR_GROUPS
from cfgs.confEdit import createLabel
from cfgs.confSelect import getCfgsField

from accservermanager import settings


class BaseForm(forms.Form):
    def __init__(self, data):
        super().__init__(data)

        for key in self.fields:
            if key == 'cfg': continue
            # generate better label
            self.fields[key].label = createLabel(key)

            # add help text if available
            if key in settings.MESSAGES:
                self.fields[key].help_text = settings.MESSAGES[key]

            # use default values from the 'data' object
            if key in data:
                self.fields[key].initial = data[key]


class SettingsForm(BaseForm):
    """
    Form around settings.json
    """
    serverName = forms.CharField(max_length=100)

    password = forms.CharField(max_length=100, required=False)
    spectatorPassword = forms.CharField(max_length=100, required=False)
    adminPassword = forms.CharField(max_length=100, required=False)

    carGroup = forms.ChoiceField(widget=forms.Select, choices=CAR_GROUPS)
    trackMedalsRequirement = forms.IntegerField(max_value=3, min_value=0, required=False)
    safetyRatingRequirement = forms.IntegerField(max_value=99, min_value=-1, required=False)
    racecraftRatingRequirement = forms.IntegerField(max_value=99, min_value=-1, required=False)

    maxCarSlots = forms.IntegerField(max_value=1000, min_value=0, required=False)

    isRaceLocked = forms.BooleanField(required=False)
    allowAutoDQ = forms.BooleanField(required=False)
    shortFormationLap = forms.BooleanField(required=False)
    dumpEntryList = forms.BooleanField(required=False)
    dumpLeaderboards = forms.BooleanField(required=False)
    randomizeTrackWhenEmpty = forms.BooleanField(required=False)
    ignorePrematureDisconnects = forms.BooleanField(required=False)


class ConfigurationForm(BaseForm):
    """
    Form around configuration.json
    """
    udpPort = forms.IntegerField(max_value=None, min_value=1000)
    tcpPort = forms.IntegerField(max_value=None, min_value=1000)
    maxConnections = forms.IntegerField(max_value=1000, min_value=0, required=False)
    registerToLobby = forms.BooleanField(required=False)
    lanDiscovery = forms.BooleanField(required=False)


class AssistRulesForm(BaseForm):
    """
    Form around assistRules.json
    """
    stabilityControlLevelMax = forms.IntegerField(max_value=100, min_value=0, required=False)
    disableIdealLine = forms.BooleanField(required=False)
    disableAutosteer = forms.BooleanField(required=False)
    disableAutoPitLimiter = forms.BooleanField(required=False)
    disableAutoGear = forms.BooleanField(required=False)
    disableAutoClutch = forms.BooleanField(required=False)
    disableAutoEngineStart = forms.BooleanField(required=False)
    disableAutoWiper = forms.BooleanField(required=False)
    disableAutoLights = forms.BooleanField(required=False)


class EventRulesForm(BaseForm):
    """
    Form around eventRules.json
    """
    qualifyStandingType = forms.IntegerField(min_value=0, required=False)
    pitWindowLengthSec = forms.IntegerField(required=False)
    driverStintTimeSec = forms.IntegerField(required=False)
    mandatoryPitstopCount = forms.IntegerField(min_value=0, required=False)
    maxTotalDrivingTime = forms.IntegerField(required=False)
    maxDriversCount = forms.IntegerField(min_value=0, required=False)
    isRefuellingAllowedInRace = forms.BooleanField(required=False)
    isRefuellingTimeFixed = forms.BooleanField(required=False)
    isMandatoryPitstopRefuellingRequired = forms.BooleanField(required=False)
    isMandatoryPitstopTyreChangeRequired = forms.BooleanField(required=False)
    isMandatoryPitstopSwapDriverRequired = forms.BooleanField(required=False)
    tyreSetCount = forms.IntegerField(min_value=0, required=False)


class InstanceForm(forms.Form):
    """
    Form used to fire up a new server instance
    """
    instanceName = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"onkeyup": "nospaces(this)"}))

    def __init__(self, data):
        super().__init__(data)
        self.settings = SettingsForm(data)
        self.configuration = ConfigurationForm(data)
        self.assistRules = AssistRulesForm(data)
        self.eventRules = EventRulesForm(data)

        # There is an issue with the 'required' error, so set this field
        # to not-required. This is ok, since it is always pre-filled.
        # This field has to be instantiated here in order to pick-up new configs.
        self.fields['event'] = getCfgsField(label='Event', required=False)

    def is_valid(self):
        return self.settings.is_valid() and self.configuration.is_valid() and self.assistRules.is_valid() and self.eventRules.is_valid()
