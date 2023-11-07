# This Python file uses the following encoding: utf-8
#
# CSDevs can be used to periodically capture a frame from a video for linux
# video device and, for some devices, save the frame as an image file.
# Copyright (C) 2022 David Mair
#
# This file is part of
# CSDevs
# Version: 1.0
#
# CSDevs is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# CSDevs is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# CSDevs. If not, see <https://www.gnu.org/licenses/>.
#

import os

from copy import deepcopy

from PySide6.QtCore import (Qt, QLoggingCategory, QSettings, QStandardPaths,
                            Slot, qCDebug, qCWarning)
from PySide6.QtGui import (QBrush, QColor, QFont, QFontDatabase, QFontInfo,
                           QRawFont)
from PySide6.QtWidgets import (QDialog, QFontComboBox, QGraphicsScene,
                               QGraphicsView)

from dlgCSDSettings import Ui_SettingsDlg

from v4l2py.device import Device
from v4l2py.raw import (v4l2_queryctrl, V4L2_CTRL_TYPE_INTEGER, V4L2_CID_BASE,
                        V4L2_CID_LASTP1)

from CSTODMath import CSTODMath

from v4l2CameraControlList import v4l2CameraControlList

# from csdMessages import (disable_warnings, enable_warnings, disable_debug,
#                          enable_debug, warning_message, debug_message)


class dlgSettings(QDialog):
    todCalc = CSTODMath()

    ignoreDayValueChanged = False
    ignoreNightValueChanged = False
    ignoreLatLonChanged = False
    ignoreTuneValueChanged = False

    ignoreTargetValueChanged = False

    # We need to know the current camera so that we can look-up per-camera
    # persistent settings (e.g. when changing the camera controls that affect
    # an image property such as brightness. Such settings are not saved until
    # the dialog is accepted and are saved by the owner of the dialog
    camName = ""

    # List of control information for camera
    # camControlNames = []

    # List of camera v4l2_queryctrl structures for the camera, includes id,
    # name, type, minimum, maximum, step, default, flags
    # camControls = v4l2CameraControlList()
    dayControls = v4l2CameraControlList()
    nightControls = v4l2CameraControlList()
    controlDayLimits = v4l2CameraControlList()
    controlNightLimits = v4l2CameraControlList()

    # Constant strings for persistent control properties in settings/config
    # FIXME: Could add a persistent user chosen default (preferred) value?
    kIsControl = "Control"
    kCtrlMax = "Maximum"
    kUseMax = "Use Maximum"
    kCtrlMin = "Minimum"
    kUseMin = "Use Minimum"
    kNegativeEffect = "Negative Effect"
    kTargetLimits = "Target Limit"

    kCtrlDay = "Day"
    kCtrlNight = "Night"

    # Keep a local copy of the tuning control list while active
    tuningControlSettings = []
    tuningControlDaySettings = []
    tuningControlNightSettings = []
    tuningTODs = []
    tuningPropertiesByTODName = []

    # Keep a local copy of the limit control list while active
    limitControlSettings = []
    limitControlDaySettings = []
    limitControlNightSettings = []

    logCategory = QLoggingCategory("csdevs.dialog.settings")

    def __init__(self):
        super(dlgSettings, self).__init__()

        # self.load_ui()
        self.ui = Ui_SettingsDlg()
        self.ui.setupUi(self)
        self.captionTextColorChange(0)
        self.ui.rbDMS.toggle()
        self.enableLatLonInput()
        self.ui.dsbLatFloat.setSingleStep(0.00027778)
        # self.changeAutoExpProperty(0)

        self.clean_icon_buttons()

        # Limit caption fonts
        # fFilter = QFontComboBox.ScalableFonts | QFontComboBox.ProportionalFonts
        # self.ui.cbCaptionFont.setFontFilters(fFilter)

        self.connect_controls()

        # Pre-set the control list time-of day properties. They will be used to
        # load presets from configuration
        self.dayControls.set_TOD_period(self.kCtrlDay)
        self.nightControls.set_TOD_period(self.kCtrlNight)
        self.controlDayLimits.set_TOD_period(self.kCtrlDay)
        self.controlNightLimits.set_TOD_period(self.kCtrlNight)

    def clean_icon_buttons(self):
        '''
        Some settings buttons can use theme icons, but they don't always get
        loaded and the button text is sometimes required but the QPushButton
        can't manage it for itself.
        '''

        icon = self.ui.pbAddTuneCtrl.icon()
        if icon.name() == "list-add":
            self.ui.pbAddTuneCtrl.setText("")
        icon = self.ui.pbRemoveTuneCtrl.icon()
        if icon.name() == "list-remove":
            self.ui.pbRemoveTuneCtrl.setText("")
        icon = self.ui.pbAddLimitCtrl.icon()
        if icon.name() == "list-add":
            self.ui.pbAddLimitCtrl.setText("")
        icon = self.ui.pbRemoveLimitCtrl.icon()
        if icon.name() == "list-remove":
            self.ui.pbRemoveLimitCtrl.setText("")

    def set_camera_name(self, newCam=""):
        '''
        Store the camera name in class members

        Parameters
        ----------
            newCam: string
                The new camera name to store
        '''

        self.camName = newCam

        # The control lists will need the camera name to load presets from
        # configuration
        self.dayControls.set_camera_name(newCam)
        self.nightControls.set_camera_name(newCam)
        self.controlDayLimits.set_camera_name(newCam)
        self.controlNightLimits.set_camera_name(newCam)

        # self.playSavedControls()

    @property
    def caption_text(self):
        '''
        The caption text in the settigs dialog as a property member
        '''
        return self.ui.leCaptionText.text()

    def setCaptionText(self, newText):
        self.ui.leCaptionText.setText(newText)

    def isCaptionDateStampChecked(self):
        return self.ui.cbDateStamp.isChecked()

    def setCaptionDateStampChecked(self, check):
        self.ui.cbDateStamp.setChecked(check)

    def isCaptionTimeStampChecked(self):
        return self.ui.cbTimeStamp.isChecked()

    def setCaptionTimeStampChecked(self, check):
        self.ui.cbTimeStamp.setChecked(check)

    def isCaptionTwoFourHourTimeChecked(self):
        return self.ui.cbTwoFourHour.isChecked()

    def setCaptionTwoFourHourTimeChecked(self, check):
        self.ui.cbTwoFourHour.setChecked(check)

    def getCaptionHorizontalLocation(self):
        if self.ui.rbCaptionHCenter.isChecked():
            return 2
        elif self.ui.rbCaptionHRight.isChecked():
            return 3

        # Assume anything else is left
        return 1

    def setCaptionHorizontalLocation(self, newLoc):
        if newLoc == 2:
            self.ui.rbCaptionHCenter.setChecked(True)
        elif newLoc == 3:
            self.ui.rbCaptionHRight.setChecked(True)
        # Anything else, assume left
        else:
            self.ui.rbCaptionHLeft.setChecked(True)

    def getCaptionVerticalLocation(self):
        if self.ui.rbCaptionVCenter.isChecked():
            return 2
        elif self.ui.rbCaptionVTop.isChecked():
            return 3

        # Assume anything else is bottom
        return 1

    def setCaptionVerticalLocation(self, newLoc):
        if newLoc == 2:
            self.ui.rbCaptionVCenter.setChecked(True)
        elif newLoc == 3:
            self.ui.rbCaptionVTop.setChecked(True)
        # Anything else, assume bottom
        else:
            self.ui.rbCaptionVBottom.setChecked(True)

    # Position to place caption on frame. Horizontal is units, vertical is
    # tens. Left = 1, Center = 2, Right = 3; Bottom = 10, Center = 20, Top = 30
    def getCaptionLocation(self):
        hPos = self.getCaptionHorizontalLocation()
        vPos = 10 * self.getCaptionVerticalLocation()

        return hPos + vPos

    # Horizontal is units, vertical is tens. Assumptions are made for invalid
    # values
    def setCaptionLocation(self, newLocation):
        hPos = newLocation % 10
        vPos = int(newLocation / 10)
        # debug_message("Settings: set caption location {}, {}".format(hPos,
        #                                                             vPos))
        self.setCaptionHorizontalLocation(hPos)
        self.setCaptionVerticalLocation(vPos)

    def setCaptionInsetX(self, value):
        if (value >= self.ui.sbCaptionInsetX.minimum()) and\
                (value <= self.ui.sbCaptionInsetX.maximum()):
            self.ui.sbCaptionInsetX.setValue(value)

    def getCaptionInsetX(self):
        return self.ui.sbCaptionInsetX.value()

    def setCaptionInsetY(self, value):
        if (value >= self.ui.sbCaptionInsetY.minimum()) and\
                (value <= self.ui.sbCaptionInsetY.maximum()):
            self.ui.sbCaptionInsetY.setValue(value)

    def getCaptionInsetY(self):
        return self.ui.sbCaptionInsetY.value()

    @property
    def caption_color_red(self):
        '''
        The Red element value of the caption color as a property member
        '''
        return self.ui.sbCaptionTextR.value()

    @property
    def caption_color_green(self):
        '''
        The Green element value of the caption color as a property member
        '''
        return self.ui.sbCaptionTextG.value()

    @property
    def caption_color_blue(self):
        '''
        The Blue element value of the caption color as a property member
        '''
        return self.ui.sbCaptionTextB.value()

    def setCaptionTextR(self, redVal):
        checkVal = int(redVal % 256)
        self.ui.sbCaptionTextR.setValue(checkVal)

    def setCaptionTextG(self, greenVal):
        checkVal = int(greenVal % 256)
        self.ui.sbCaptionTextG.setValue(checkVal)

    def setCaptionTextB(self, blueVal):
        checkVal = int(blueVal % 256)
        self.ui.sbCaptionTextB.setValue(checkVal)

    def setLatitude(self, newLat):
        # Ignore None
        if newLat is not None:
            # Get North or South and only use a positive value
            isNorth = (newLat >= 0.0)
            newLat = abs(newLat)
            if isNorth:
                self.ui.rbLatNorth.setChecked(True)
            else:
                self.ui.rbLatSouth.setChecked(True)

            self.ui.dsbLatFloat.setValue(newLat)

    def setLongitude(self, newLon):
        # Ignore None
        if newLon is not None:
            # Get East or West and only use a positive value
            isEast = (newLon >= 0.0)
            newLon = abs(newLon)
            if isEast:
                self.ui.rbLonEast.setChecked(True)
            else:
                self.ui.rbLonWest.setChecked(True)

            self.ui.dsbLonFloat.setValue(newLon)

    def getLatitudeFloat(self):
        lat = self.ui.dsbLatFloat.value()
        if self.ui.rbLatSouth.isChecked():
            lat = 0.0 - lat

        return lat

    def getLongitudeFloat(self):
        lon = self.ui.dsbLonFloat.value()
        if self.ui.rbLonWest.isChecked():
            lon = 0.0 - lon

        return lon

    def setupEnabledLatLonControls(self, isDMS):
        self.ui.sbLatDegrees.setEnabled(isDMS)
        self.ui.lblLatDegrees.setEnabled(isDMS)
        self.ui.sbLatMinutes.setEnabled(isDMS)
        self.ui.lblLatMinutes.setEnabled(isDMS)
        self.ui.sbLatSeconds.setEnabled(isDMS)
        self.ui.lblLatSeconds.setEnabled(isDMS)

        self.ui.dsbLatFloat.setEnabled(not isDMS)
        self.ui.lblLatFloat.setEnabled(not isDMS)

        self.ui.sbLonDegrees.setEnabled(isDMS)
        self.ui.lblLonDegrees.setEnabled(isDMS)
        self.ui.sbLonMinutes.setEnabled(isDMS)
        self.ui.lblLonMinutes.setEnabled(isDMS)
        self.ui.sbLonSeconds.setEnabled(isDMS)
        self.ui.lblLonSeconds.setEnabled(isDMS)

        self.ui.dsbLonFloat.setEnabled(not isDMS)
        self.ui.lblLonFloat.setEnabled(not isDMS)

    def enableLatLonInput(self):
        self.setupEnabledLatLonControls(self.ui.rbDMS.isChecked())

    # Return the day or night control list depending on auto-exposure radio
    # button selection
    def todControlList(self):
        if self.ui.rbNightCtrls.isChecked():
            ctrlList = self.nightControls
            tod = "Night"
        else:
            # Assume day if not night
            ctrlList = self.dayControls
            tod = "Day"

        for aCtrl in ctrlList:
            qCDebug(self.logCategory,
                    "TOD {} Control list: {}".format(tod, ctrlList))
            # debug_message("TOD {} Control list: {}".format(tod, ctrlList))

        return ctrlList

    def tod_limit_control_list(self):
        '''
        Return the day or night control limit list depending on limit tab radio
        # button selection
        '''

        if self.ui.rbLimitsNight.isChecked():
            return self.controlNightLimits


        # Assume day if not night
        return self.controlDayLimits

    def copy_day_controls(self):
        '''
        Assuming self.dayControls was loaded in a way relevant to the current
        camera then copy the list to the other cases we'll need.
        '''

        # Copy them for night
        self.nightControls = deepcopy(self.dayControls)

        # ...and copy them for day/night limits
        self.controlDayLimits = deepcopy(self.dayControls)
        self.controlNightLimits = deepcopy(self.dayControls)

    def preloadCameraControls(self, camFilename):
        # self.camControls.load_controls_from_camera(camFilename)
        self.dayControls.load_controls_from_camera(camFilename)
        self.copy_day_controls()

    def preloadCameraControlsFromFD(self, camFD):
        # self.camControls.load_controls_from_FD(camFD)
        self.dayControls.load_controls_from_FD(camFD)
        self.copy_day_controls()

    def addCameraControl(self, qCtrl, rtMin=None, rtMax=None, rtDefault=None,
                         rtMinUse=False, rtMaxUse=False, rtEncourageRage=False):
        # if self.ui.rbNightCtrls.isChecked():
        #     todName = "Day"
        # else:
        #     todName = "Night"

        # Get control list based on auto-exposure TOD selection
        ctrlList = self.todControlList()

        try:
            # tuneVal = (tuneProperty, ctrlName, rForce, rMin, rMax, negativeUse, rtEncourageRange)
            ctrlList.add_camera_control(qCtrl, rtMin, rtMax, rtDefault,
                                        rtMinUse, rtMaxUse, rtEncourageRange)
        except (NameError, ValueError):
            msg = "Settings unable to list control {}/{}".format(qCtrl.id,
                                                                 qCtrl.name)
            qCDebug(self.logCategory, msg)
            # debug_message(msg)
            raise NameError

    def setTargetControl(self, control, value, minimum, maximum, step):
        dayRange = maximum - minimum
        if (dayRange > 0) and (step < dayRange) and (value >= minimum) and\
                (value <= maximum):
            if control.maximum() < minimum:
                control.setMaximum(maximum)
                control.setMinimum(minimum)
            else:
                control.setMinimum(minimum)
                control.setMaximum(maximum)

            control.setSingleStep(step)
            control.setValue(value)
            result = True
        else:
            result = False

        return result

    @property
    def dayTgtBrightnessMax(self):
        return self.ui.sbDayTgtBrightness.value()

    @property
    def dayTgtBrightnessMin(self):
        return self.ui.sbDayTgtBrightnessMin.value()

    @property
    def dayTgtContrastMax(self):
        return self.ui.sbDayTgtContrast.value()

    @property
    def dayTgtContrastMin(self):
        return self.ui.sbDayTgtContrastMin.value()

    @property
    def dayTgtSaturationMax(self):
        return self.ui.sbDayTgtSaturation.value()

    @property
    def dayTgtSaturationMin(self):
        return self.ui.sbDayTgtSaturationMin.value()

    def getDayBrightnessTarget(self):
        return self.ui.sbDayTgtBrightness.value()

    def getDayTargetBrightnessMinimum(self):
        return self.ui.sbDayTgtBrightnessMin.value()

    def getDayContrastTarget(self):
        return self.ui.sbDayTgtContrast.value()

    def getDayTargetContrastMinimum(self):
        return self.ui.sbDayTgtContrastMin.value()

    def getDaySaturationTarget(self):
        return self.ui.sbDayTgtSaturation.value()

    def getDayTargetSaturationMinimum(self):
        return self.ui.sbDayTgtSaturationMin.value()

    def setDayBrightnessTarget(self, brightness, minimum, maximum, step):
        if not self.setTargetControl(self.ui.sbDayTgtBrightness, brightness,
                                     minimum, maximum, step):
            qCWarning(self.logCategory, "Day brightness target is invalid:")
            qCWarning(self.logCategory, "{}-{}-{}/{}".format(minimum,
                                                             brightness,
                                                             maximum,
                                                             step))
            # debug_message("Day brightness target is invalid:")
            # debug_message("{}-{}-{}/{}".format(minimum, brightness, maximum,
            #                                    step))

    def setDayContrastTarget(self, contrast, minimum, maximum, step):
        if not self.setTargetControl(self.ui.sbDayTgtContrast, contrast,
                                     minimum, maximum, step):
            qCWarning(self.logCategory, "Day contrast target is invalid:")
            qCWarning(self.logCategory, "{}-{}-{}/{}".format(minimum, contrast,
                                                             maximum, step))
            # debug_message("Day contrast target is invalid:")
            # debug_message("{}-{}-{}/{}".format(minimum, contrast, maximum,
            #                                    step))

    def setDaySaturationTarget(self, saturation, minimum, maximum, step):
        if not self.setTargetControl(self.ui.sbDayTgtSaturation, saturation,
                                     minimum, maximum, step):
            qCWarning(self.logCategory, "Day saturation target is invalid:")
            qCDebug(self.logCategory, "{}-{}-{}/{}".format(minimum, saturation,
                                                           maximum, step))
            # debug_message("Day saturation target is invalid:")
            # debug_message("{}-{}-{}/{}".format(minimum, saturation, maximum,
            #                                    step))

    def setDayBrightnessMinTarget(self, brightness, minimum, maximum, step):
        if not self.setTargetControl(self.ui.sbDayTgtBrightnessMin, brightness,
                                     minimum, maximum, step):
            qCWarning(self.logCategory,
                      "Day brightness minimum target is invalid:")
            qCWarning(self.logCategory,
                      "{}-{}-{}/{}".format(minimum, brightness, maximum, step))
            # debug_message("Day brightness minimum target is invalid:")
            # debug_message("{}-{}-{}/{}".format(minimum, brightness, maximum,
            #                                    step))

    def setDayContrastMinTarget(self, contrast, minimum, maximum, step):
        if not self.setTargetControl(self.ui.sbDayTgtContrastMin, contrast,
                                     minimum, maximum, step):
            qCWarning(self.logCategory,
                      "Day contrast minimum target is invalid:")
            qCWarning(self.logCategory, "{}-{}-{}/{}".format(minimum, contrast,
                                                             maximum, step))
            # debug_message("Day contrast minimum target is invalid:")
            # debug_message("{}-{}-{}/{}".format(minimum, contrast, maximum,
            #                                    step))

    def setDaySaturationMinTarget(self, saturation, minimum, maximum, step):
        if not self.setTargetControl(self.ui.sbDayTgtSaturationMin, saturation,
                                     minimum, maximum, step):
            qCWarning(self.logCategory,
                      "Day saturation minimum target is invalid:")
            qCWarning(self.logCategory, "{}-{}-{}/{}".format(minimum,
                                                             saturation,
                                                             maximum, step))
            # debug_message("Day saturation minimum target is invalid:")
            # debug_message("{}-{}-{}/{}".format(minimum, saturation, maximum,
            #                                    step))

    @property
    def nightTgtBrightnessMax(self):
        if self.ui.gbNightTargets.isChecked():
            return self.ui.sbNightTgtBrightness.value()

        return -1.0

    @property
    def nightTgtBrightnessMin(self):
        if self.ui.gbNightTargets.isChecked():
            return self.ui.sbNightTgtBrightnessMin.value()

        return -1.0

    @property
    def nightTgtContrastMax(self):
        if self.ui.gbNightTargets.isChecked():
            return self.ui.sbNightTgtContrast.value()

        return -1.0

    @property
    def nightTgtContrastMin(self):
        if self.ui.gbNightTargets.isChecked():
            return self.ui.sbNightTgtContrastMin.value()

        return -1.0

    @property
    def nightTgtSaturationMax(self):
        if self.ui.gbNightTargets.isChecked():
            return self.ui.sbNightTgtSaturation.value()

        return -1.0

    @property
    def nightTgtSaturationMin(self):
        if self.ui.gbNightTargets.isChecked():
            return self.ui.sbNightTgtSaturationMin.value()

        return -1.0

    def getNightBrightnessTarget(self):
        if self.ui.gbNightTargets.isChecked():
            return self.ui.sbNightTgtBrightness.value()

        return -1.0

    def getNightContrastTarget(self):
        if self.ui.gbNightTargets.isChecked():
            return self.ui.sbNightTgtContrast.value()

        return -1.0

    def getNightSaturationTarget(self):
        if self.ui.gbNightTargets.isChecked():
            return self.ui.sbNightTgtSaturation.value()

        return -1.0

    def setNightBrightnessTarget(self, brightness, minimum, maximum, step):
        qCDebug(self.logCategory,
                "setNightBrightnessTarget {}".format(brightness))
        # debug_message("setNightBrightnessTarget {}".format(brightness))
        if not self.setTargetControl(self.ui.sbNightTgtBrightness, brightness,
                                     minimum, maximum, step):
            qCWarning(self.logCategory, "Night brightness target is invalid:")
            qCWarning(self.logCategory, "{}-{}-{}/{}".format(minimum,
                                                             brightness,
                                                             maximum, step))
            # debug_message("Night brightness target is invalid:")
            # debug_message("{}-{}-{}/{}".format(minimum, brightness, maximum,
            #                                    step))

    def setNightContrastTarget(self, contrast, minimum, maximum, step):
        if not self.setTargetControl(self.ui.sbNightTgtContrast, contrast,
                                     minimum, maximum, step):
            qCWarning(self.logCategory, "Night contrast target is invalid:")
            qCWarning(self.logCategory, "{}-{}-{}/{}".format(minimum, contrast,
                                                             maximum, step))
            # debug_message("Night contrast target is invalid:")
            # debug_message("{}-{}-{}/{}".format(minimum, contrast, maximum,
            #                                    step))

    def setNightSaturationTarget(self, saturation, minimum, maximum, step):
        if not self.setTargetControl(self.ui.sbNightTgtSaturation, saturation,
                                     minimum, maximum, step):
            qCWarning(self.logCategory, "Night saturation target is invalid:")
            qCWarning(self.logCategory, "{}-{}-{}/{}".format(minimum,
                                                             saturation,
                                                             maximum, step))
            # debug_message("Night saturation target is invalid:")
            # debug_message("{}-{}-{}/{}".format(minimum, saturation, maximum,
            #                                    step))

    def setNightBrightnessMinTarget(self, brightness, minimum, maximum, step):
        if not self.setTargetControl(self.ui.sbNightTgtBrightnessMin,
                                     brightness, minimum, maximum, step):
            qCWarning(self.logCategory,
                      "Night brightness target minimum is invalid:")
            qCWarning(self.logCategory, "{}-{}-{}/{}".format(minimum,
                                                             brightness,
                                                             maximum, step))
            # debug_message("Night brightness target minimum is invalid:")
            # debug_message("{}-{}-{}/{}".format(minimum, brightness, maximum,
            #                                    step))

    def setNightContrastMinTarget(self, contrast, minimum, maximum, step):
        if not self.setTargetControl(self.ui.sbNightTgtContrastMin, contrast,
                                     minimum, maximum, step):
            qCWarning(self.logCategory,
                      "Night contrast target minimum is invalid:")
            qCWarning(self.logCategory, "{}-{}-{}/{}".format(minimum, contrast,
                                                             maximum, step))
            # debug_message("Night contrast target minimum is invalid:")
            # debug_message("{}-{}-{}/{}".format(minimum, contrast, maximum,
            #                                    step))

    def setNightSaturationMinTarget(self, saturation, minimum, maximum, step):
        if not self.setTargetControl(self.ui.sbNightTgtSaturationMin,
                                     saturation, minimum, maximum, step):
            qCWarning(self.logCategory,
                      "Night saturation target minimum is invalid:")
            qCWarning(self.logCategory, "{}-{}-{}/{}".format(minimum,
                                                             saturation,
                                                             maximum, step))
            # debug_message("Night saturation target minimum is invalid:")
            # debug_message("{}-{}-{}/{}".format(minimum, saturation, maximum,
            #                                    step))

    def newDayBrightnessMax(self, newMax):
        # Don't double handle any change
        if not self.ignoreTargetValueChanged:
            self.ignoreTargetValueChanged = True
            min = self.getDayTargetBrightnessMinimum()
            if newMax < min:
                self.ui.sbDayTgtBrightness.setValue(min)
            self.ignoreTargetValueChanged = False

    def newDayBrightnessMin(self, newMin):
        # Don't double handle any change
        if not self.ignoreTargetValueChanged:
            self.ignoreTargetValueChanged = True
            max = self.getDayBrightnessTarget()
            if newMin > max:
                self.ui.sbDayTgtBrightnessMin.setValue(max)
            self.ignoreTargetValueChanged = False

    def newDayContrastMax(self, newMax):
        # Don't double handle any change
        if not self.ignoreTargetValueChanged:
            self.ignoreTargetValueChanged = True
            min = self.getDayTargetContrastMinimum()
            if newMax < min:
                self.ui.sbDayTgtContrast.setValue(min)
            self.ignoreTargetValueChanged = False

    def newDayContrastMin(self, newMin):
        # Don't double handle any change
        if not self.ignoreTargetValueChanged:
            self.ignoreTargetValueChanged = True
            max = self.getDayContrastTarget()
            if newMin > max:
                self.ui.sbDayTgtContrastMin.setValue(max)
            self.ignoreTargetValueChanged = False

    def newDaySaturationMax(self, newMax):
        # Don't double handle any change
        if not self.ignoreTargetValueChanged:
            self.ignoreTargetValueChanged = True
            min = self.getDayTargetSaturationMinimum()
            if newMax < min:
                self.ui.sbDayTgtSaturation.setValue(min)
            self.ignoreTargetValueChanged = False

    def newDaySaturationMin(self, newMin):
        # Don't double handle any change
        if not self.ignoreTargetValueChanged:
            self.ignoreTargetValueChanged = True
            max = self.getDaySaturationTarget()
            if newMin > max:
                self.ui.sbDayTgtSaturationMin.setValue(max)
            self.ignoreTargetValueChanged = False

    def newNightBrightnessMax(self, newMax):
        # Don't double handle any change
        if not self.ignoreTargetValueChanged:
            self.ignoreTargetValueChanged = True
            min = self.nightTgtBrightnessMin
            if newMax < min:
                self.ui.sbNightTgtBrightness.setValue(min)
            self.ignoreTargetValueChanged = False

    def newNightBrightnessMin(self, newMin):
        # Don't double handle any change
        if not self.ignoreTargetValueChanged:
            self.ignoreTargetValueChanged = True
            max = self.nightTgtBrightnessMax
            if newMin > max:
                self.ui.sbNightTgtBrightnessMin.setValue(max)
            self.ignoreTargetValueChanged = False

    def newNightContrastMax(self, newMax):
        # Don't double handle any change
        if not self.ignoreTargetValueChanged:
            self.ignoreTargetValueChanged = True
            min = self.nightTgtContrastMax
            if newMax < min:
                self.ui.sbNightTgtContrast.setValue(min)
            self.ignoreTargetValueChanged = False

    def newNightContrastMin(self, newMin):
        # Don't double handle any change
        if not self.ignoreTargetValueChanged:
            self.ignoreTargetValueChanged = True
            max = self.nightTgtContrastMin
            if newMin > max:
                self.ui.sbNightTgtContrastMin.setValue(max)
            self.ignoreTargetValueChanged = False

    def newNightSaturationMax(self, newMax):
        # Don't double handle any change
        if not self.ignoreTargetValueChanged:
            self.ignoreTargetValueChanged = True
            min = self.nightTgtSaturationMax
            if newMax < min:
                self.ui.sbNightTgtSaturation.setValue(min)
            self.ignoreTargetValueChanged = False

    def newNightSaturationMin(self, newMin):
        # Don't double handle any change
        if not self.ignoreTargetValueChanged:
            self.ignoreTargetValueChanged = True
            max = self.nightTgtSaturationMin
            if newMin > max:
                self.ui.sbNightTgtSaturationMin.setValue(max)
            self.ignoreTargetValueChanged = False

    def isNightTargetsEnabled(self):
        return self.ui.gbNightTargets.isChecked()

    def setNightTargetsEnabled(self, enable=False):
        self.ui.gbNightTargets.setChecked(enable)

    def captionTextColorChange(self, value):
        # Ignore value argument, we are using the slot for all colors, just
        # get them from the controls at once
        rVal = self.ui.sbCaptionTextR.value()
        gVal = self.ui.sbCaptionTextG.value()
        bVal = self.ui.sbCaptionTextB.value()

        # Create a volor and set the sample widget background color to it
        colorVal = QColor(rVal, gVal, bVal, 255)
        # Find the widgit to draw on
        view = self.findChild(QGraphicsView, "wColorView")
        if view is not None:
            # If it has no scene, add one
            scene = view.scene()
            if scene is None:
                scene = QGraphicsScene()
                view.setScene(scene)

            aBrush = QBrush(colorVal)
            scene.setBackgroundBrush(aBrush)

    def newLatFloat(self, newValue):
        # If we are being adjusted by DMS changes do nothing
        if self.ignoreLatLonChanged:
            return

        # Use it to set the DMS without looping back valueChanged
        self.ignoreLatLonChanged = True

        # debug_message("lat value changed type {}".format(type(newValue)))
        deg = abs(self.todCalc.get_angle_degrees(newValue))
        min = abs(self.todCalc.get_angle_minutes(newValue))
        sec = abs(self.todCalc.get_angle_seconds(newValue))
        # debug_message("\\_ {} == {} {} {}".format(newValue, deg, min, sec))
        self.ui.sbLatDegrees.setValue(deg)
        self.ui.sbLatMinutes.setValue(min)
        self.ui.sbLatSeconds.setValue(sec)

        self.ignoreLatLonChanged = False

    def newLatDMS(self, value):
        # If we are being adjusted by float degrees changes do nothing
        if self.ignoreLatLonChanged:
            return

        # Use them to set the float without looping back valueChanged
        self.ignoreLatLonChanged = True

        # Just get the three of them
        deg = self.ui.sbLatDegrees.value()
        min = self.ui.sbLatMinutes.value()
        sec = self.ui.sbLatSeconds.value()

        # Compute and set the float value
        fDegs = self.todCalc.get_DMS_angle_float(deg, min, sec)
        # fDegs = self.todCalc.getDMSFloat(deg, min, sec)
        self.ui.dsbLatFloat.setValue(fDegs)

        self.ignoreLatLonChanged = False

    def newLonFloat(self, newValue):
        # If we are being adjusted by DMS changes do nothing
        if self.ignoreLatLonChanged:
            return

        # Use it to set the DMS without looping back valueChanged
        self.ignoreLatLonChanged = True

        # debug_message("lat value changed type {}".format(type(newValue)))
        deg = abs(self.todCalc.get_angle_degrees(newValue))
        min = abs(self.todCalc.get_angle_minutes(newValue))
        sec = abs(self.todCalc.get_angle_seconds(newValue))
        # debug_message("\\_ {} == {} {} {}".format(newValue, deg, min, sec))
        self.ui.sbLonDegrees.setValue(deg)
        self.ui.sbLonMinutes.setValue(min)
        self.ui.sbLonSeconds.setValue(sec)

        self.ignoreLatLonChanged = False

    def newLonDMS(self, value):
        # If we are being adjusted by float degrees changes do nothing
        if self.ignoreLatLonChanged:
            return

        # Use them to set the float without looping back valueChanged
        self.ignoreLatLonChanged = True

        # Just get the three of them
        deg = self.ui.sbLonDegrees.value()
        min = self.ui.sbLonMinutes.value()
        sec = self.ui.sbLonSeconds.value()

        # Compute and set the float value
        fDegs = self.todCalc.get_DMS_angle_float(deg, min, sec)
        # fDegs = self.todCalc.getDMSFloat(deg, min, sec)
        self.ui.dsbLonFloat.setValue(fDegs)

        self.ignoreLatLonChanged = False

    def isAutoExposureDaytime(self):
        return self.ui.rbDayCtrls.isEnabled() and\
            self.ui.rbDayCtrls.isChecked()

    def isAutoExposureNighttime(self):
        return self.ui.rbNightCtrls.isEnabled() and\
            self.ui.rbNightCtrls.isChecked()

    def getAutoExposureControlsTODKey(self):
        if self.isAutoExposureNighttime():
            return self.kCtrlNight

        return self.kCtrlDay

    def __add_control_to_in_use(self, availControls, availIndex,
                                   inUseControls, pbRemove):
        '''
        Add a control name's text from the available controls UI list at index
        availIndex to the in-use Controls UI list then remove it from the
        available controls UI list. A button that can be used to remove items
        from in-use controls will be enabled if the list is not empty, disabled
        otherwise.

        Parameters
        ----------
            availControls: a QComboBox UI object
                List of available controls that are not currently "in-use"
            availIndex: integer
                The index of an item in availControls
            inUseControls: a Qt UI list object
                List of in-use controls to add the name to
            pbRemove: a QPushButton
                A UI object that can be used to remove items from inUseControls
        '''

        if (availIndex >= 0) and (availIndex < availControls.count()):
            availText = availControls.itemText(availIndex)
            inUseControls.addItem(availText)
            availControls.removeItem(availIndex)

        # debug_message("Fixing remove button")
        self.__set_remove_in_use_button(inUseControls, pbRemove)

    def __add_control_to_available(self, inUseControls, inUseRow,
                                   availControls, pbRemove):
        '''
        Add a control name's text from the inUseControls UI list at row inUseRow
        to the availControls UI list removing inUseRow from the inUseControls
        UI list. A button that can be used to remove items from in-use controls
        will be enabled if the list is not empty, disabled otherwise.

        Parameters
        ----------
            inUseControls: a Qt UI list object
                List of in-use controls to remove the item from
            inUseRow: integer
                The row in inUseControls to remove the item from
            availControls: a QComboBox UI object
                List of available controls to add the name to
            pbRemove: a QPushButton
                A UI object that can be used to remove items from inUseControls
        '''

        # Get the item to be moved, removing it from the in-use controls
        item = inUseControls.takeItem(inUseRow)

        # Add it to the available controls if not already present
        if item is not None:
            ctrlName = item.text()
            # debug_message("Took control name {} from in-use".format(ctrlName))
            if availControls.findText(ctrlName) == -1:
                # msg = "{} not found in available, adding it".format(ctrlName)
                # debug_message(msg)
                availControls.addItem(ctrlName)
        '''
        Tuning controls have a property

            property = self.ui.cbImageProperty.currentText()
            if self.ui.rbDayCtrls.isChecked():
                todName = "Day"
            else:
                todName = "Night"

            # Remove it from the tuning list
            i = self.iTunerForTODNamePropertyAndCtrlName(todName, property,
                                                         ctrlName)
            if i != -1:
                del self.tuningControlSettings[i]
        '''

        # debug_message("Fixing remove button")
        self.__set_remove_in_use_button(inUseControls, pbRemove)

    def indexOfTuningTODName(self, todName):
        i = 0
        for aTODName in self.tuningTODs:
            if aTODName == todName:
                return i
            i += 1

        # Not found
        return -1

    def addTuningTODName(self, todName):
        # Does the name already exist
        if self.indexOfTuningTODName(todName) == -1:
            # Not found, add it
            self.tuningTODs.append(todName)

    def indexOfTuningPropertyByTODName(self, todName, property):
        i = 0
        for aPropByTOD in self.tuningPropertiesByTODName:
            if (aPropByTOD[0] == todName) and (aPropByTOD[1] == todName):
                return i
            i += 1

        # Not found
        return -1

    def addTuningPropertyForTODName(self, todName, property):
        # Does the name already exist
        if self.indexOfTuningPropertyByTODName(todName, property) == -1:
            # Not found, add it
            propByTOD = (todName, property)
            self.tuningPropertiesByTODName.append(propByTOD)

    def iNextPropertyForTODName(self, todName, iPrev=-1):
        lastPropByTOD = len(self.tuningPropertiesByTODName) - 1
        if (iPrev >= 0) and (iPrev < lastPropByTOD):
            for i in range(iPrev + 1, lastPropByTOD):
                aPropByTOD = self.tuningPropertiesByTODName[i]
                if aPropByTOD[0] == todName:
                    return i

        # Not found
        return -1

    def todPropertyAtIndex(self, todName, iProperty):
        if (iProperty >= 0) and (iProperty < len(self.tuningPropertiesByTODName)):
            aProperty = self.tuningPropertiesByTODName[iProperty]
            if aProperty[0] == todName:
                return aProperty[1]

        # Index doesn't exist or has wrong tod name
        return None

    def dumpTuners(self):
        nTuners = len(self.tuningControlSettings)
        qCDebug(self.logCategory, "DUMPING {} TUNERS".format(nTuners))
        # debug_message("DUMPING {} TUNERS".format(nTuners))
        for aTuner in self.tuningControlSettings:
            qCDebug(self.logCategory, "\\_ {} {} {}".format(aTuner[0],
                                                            aTuner[1],
                                                            aTuner[2]))
            # debug_message("\\_ {} {} {}".format(aTuner[0], aTuner[1], aTuner[2]))

    def iNextTunerForTODName(self, todName, iPrev=-1):
        # self.dumpTuners()
        nTuners = len(self.tuningControlSettings)
        # debug_message("Next tuner from {} to {}".format(iPrev + 1, nTuners - 1))
        if (iPrev >= -1) and (iPrev < nTuners):
            for i in range(iPrev + 1, nTuners):
                aTuner = self.tuningControlSettings[i]
                # debug_message("\\_ Checking tuner {} - {}/{}/{}".format(i, aTuner[0], aTuner[1], aTuner[2]))
                if aTuner[0] == todName:
                    return i

        # Not found
        return -1

    def iNextTunerForTODNameAndProperty(self, todName, property, iPrev=-1):
        lastTuner = len(self.tuningControlSettings) - 1
        if (iPrev >= -1) and (iPrev <= lastTuner):
            # debug_message("Prev {} is in search range range 0-{} for {}/{}".format(iPrev + 1, lastTuner, todName, property))
            for i in range(iPrev + 1, lastTuner + 1):
                aTuner = self.tuningControlSettings[i]
                if (aTuner[0] == todName) and (aTuner[1] == property):
                    return i

        # Not found
        return -1

    def iTunerForTODNamePropertyAndCtrlName(self, todName, property, ctrlName):
        i = -1
        while True:
            i = self.iNextTunerForTODNameAndProperty(todName, property,
                                                     i)
            if i == -1:
                break

            # Look for a matching control name
            aTuner = self.__tunerAtIndex(i)
            if aTuner[2] == ctrlName:
                # Success, i is the required index
                break

        return i

    # Class internal way to get a class style tuning control tuple
    def __tunerAtIndex(self, i):
        if (i >= 0) and (i < len(self.tuningControlSettings)):
            return self.tuningControlSettings[i]

        # Not found
        return None

    # Given an index, uses the settings tuple at that index to return a tuple
    # of the type used by main window, doesn't have an initial time-of-day
    # member
    def __nonTODTupleFromIndex(self, i):
        aTuner = self.__tunerAtIndex(i)
        if aTuner is not None:
            tuneVal = (aTuner[1], aTuner[2], aTuner[3], aTuner[4],
                       aTuner[5], aTuner[6], aTuner[7])
            return tuneVal

        return None

    # Class external ways of getting the tuning control at an index (and with
    # other conditions) that return a tuple without the time-pf-day member
    def tunerAtIndex(self, i):
        return self.__nonTODTupleFromIndex(i)

    def todTunerAtIndex(self, todName, i):
        aTuner = self.__tunerAtIndex(i)
        if aTuner is not None:
            # Verify TOD
            if (aTuner[0] == todName):
                return self.__nonTODTupleFromIndex(i)

        # Not found
        return None

    def todPropertyTunerAtIndex(self, todName, property, i):
        aTuner = self.__tunerAtIndex(i)
        if aTuner is not None:
            # Verify TOD and property
            if (aTuner[0] == todName) and (aTuner[1] == property):
                return self.__nonTODTupleFromIndex(i)

        # Not found
        return None

    def resetTuningControls(self, todName=None):
        # Start with no tuning controls
        if todName == None:
            self.tuningControlSettings.clear()
        elif todName == "Day":
            self.tuningControlDaySettings.clear()
        elif todName == "Night":
            self.tuningControlNightSettings.clear()

    def reset_limit_controls(self, todName="Day"):
        '''
        Clear the contents of a list of limit controls

        Parameters
        ----------
            todName: string
                The text name of the list to clear or None. Named lists are
                "Day" and "Night", None is unnamed
        '''

        # Start with no limit controls
        if todName == None:
            self.limitControlSettings.clear()
        elif todName == "Day":
            self.limitControlDaySettings.clear()
        elif todName == "Night":
            self.limitControlNightSettings.clear()

    def supplyTuningControl(self, aTuner, todName="Day", ignoreUI=False):
        # We have to have a camera to have a tuning control
        if self.camName is None:
            self.camName = ""

        if self.camName != "":
            self.ignoreTuneValueChanged = ignoreUI
            # debug_message("Supplied tuning control {} for {}".format(aTuner[1], todName))
            # Copy the supplued tuner for our own use by adding the time of day
            # name for our own use. We can then support multiple time of day
            # concepts in the same dialog
            tuneVal = (todName, aTuner[0], aTuner[1], aTuner[2], aTuner[3],
                       aTuner[4], aTuner[5], aTuner[6])
            # debug_message("Adding saved tuner {}".format(tuneVal))
            self.tuningControlSettings.append(tuneVal)
            self.addTuningTODName(todName)
            self.addTuningPropertyForTODName(todName, aTuner[0])

            self.ignoreTuneValueChanged = False

    def __set_remove_in_use_button(self, inUseList, pbRemove):
        '''
        If a list of in-use controls has non-zero length enable a remove-item
        button. Otherwise disable the button.

        Parameters
        ----------
            inUseList: A Qt UI list
                The remove item button is enabled if this list is not empty,
                otherwise the button is disabled
            pbRemove: A QPushButton
                Button assumed to be for removing items from inUseList
        '''

        # If there is a button and the list is populated
        if pbRemove is not None:
            # Is the list populated
            rmEnabled = (inUseList.count() > 0)
            pbRemove.setEnabled(rmEnabled)

    # Enable remove button if the tuning control list is not empty
    def __enableRemoveTuningCtrl(self):
        rmEnabled = (self.ui.lwTuneCtrls.count() > 0)
        self.ui.pbRemoveTuneCtrl.setEnabled(rmEnabled)

    def removeTuneCtrl(self):
        # Get control list based on auto-exposure TOD selection
        ctrlList = self.todControlList()

        # Get any selected control in the tuning control list
        item = self.ui.lwTuneCtrls.currentItem()
        if item.isSelected():
            ctrlName = item.text()
            # take the item from the tune controls
            row = self.ui.lwTuneCtrls.currentRow()
            self.__add_control_to_available(self.ui.lwTuneCtrls, row,
                                            self.ui.cbAvailableControls,
                                            self.ui.pbRemoveTuneCtrl)
            if self.__is_tune_control_available(ctrlName):
                property = self.ui.cbImageProperty.currentText()
                if self.ui.rbDayCtrls.isChecked():
                    todName = "Day"
                else:
                    todName = "Night"

                # Remove it from the tuning list
                i = self.iTunerForTODNamePropertyAndCtrlName(todName, property,
                                                             ctrlName)
                if i != -1:
                    del self.tuningControlSettings[i]

            self.__set_remove_in_use_button(self.ui.lwTuneCtrls,
                                            self.ui.pbRemoveTuneCtrl)
        else:
            qCWarning(self.logCategory,
                      "Unable to remove {}".format(item.text()))
            # debug_message("Unable to remove {}".format(item.text()))

    def removeTuneCtrlB(self):
        # Get control list based on auto-exposure TOD selection
        ctrlList = self.todControlList()

        # Get any selected control in the tuning control list
        item = self.ui.lwTuneCtrls.currentItem()
        if item.isSelected():
            ctrlName = item.text()
            # take the item from the tune controls
            row = self.ui.lwTuneCtrls.currentRow()
            rItem = self.ui.lwTuneCtrls.takeItem(row)
            if (rItem is not None) and (rItem.text() == ctrlName):
                # If it doesn't already exist in the available controls
                if self.ui.cbAvailableControls.findText(ctrlName) == -1:
                    # Add it to the available controls
                    self.ui.cbAvailableControls.addItem(rItem.text())

                property = self.ui.cbImageProperty.currentText()
                if self.ui.rbDayCtrls.isChecked():
                    todName = "Day"
                else:
                    todName = "Night"

                # Remove it from the tuning list
                i = self.iTunerForTODNamePropertyAndCtrlName(todName, property,
                                                             ctrlName)
                if i != -1:
                    del self.tuningControlSettings[i]

            self.__set_remove_in_use_button(self.ui.lwTuneCtrls,
                                            self.ui.pbRemoveTuneCtrl)
        else:
            qCWarning(self.logCategory,
                      "Unable to remove {}".format(item.text()))
            # debug_message("Unable to remove {}".format(item.text()))

    def changeAutoExpProperty(self, index):
        self.ui.lwTuneCtrls.clear()

        if self.isAutoExposureDaytime():
            todName = "Day"
        else:
            todName = "Night"

        property = self.ui.cbImageProperty.currentText()

        # debug_message("Changing listed tuners for {} {}".format(todName, property))

        # Walk the properties for the current TOD and the selected property
        i = -2
        while (i != -1):
            if i == -2:
                i = -1
            i = self.iNextTunerForTODNameAndProperty(todName, property, i)
            # debug_message("Found control at index {}".format(i))
            if i >= 0:
                aTuner = self.tuningControlSettings[i]
                self.ui.lwTuneCtrls.addItem(aTuner[2])

        self.__set_remove_in_use_button(self.ui.lwTuneCtrls,
                                        self.ui.pbRemoveTuneCtrl)

        # Get day or night control list based on auto-exposure selection
        ctrlList = self.todControlList()

        # Remaining controls for the camera must be in the list we can add from
        self.loadNonPersistentControls(self.ui.cbAvailableControls, ctrlList,
                                       self.ui.lwTuneCtrls)

        # Finally, either clear the control settings with no in-use control
        # selection or make a selection to cause the control settings to be
        # shown
        self.__clear_control_tuning()

    def __add_limit_control(self):
        '''
        Add the selected control in the available limit controls to the in-use
        limit controls (add button clicked in limits tab)
        '''

        # Get control list based on limts TOD selection
        ctrlList = self.tod_limit_control_list()

        # Get the selected item in the available controls
        if self.ui.cbAvailableLimitControls.count() > 0:
            availIndex = self.ui.cbAvailableLimitControls.currentIndex()
            availText = self.ui.cbAvailableLimitControls.currentText()
            if (availIndex >= 0) and\
                    not self.__listed_control_exists(self.limitControlSettings,
                                                     "", availText):
                '''
                # Add it to the correct tuner list
                if self.ui.cbPropCtrlMin.isChecked():
                    rtMin = self.ui.sbPropCtrlMinVal.value()
                else:
                    rtMin = ctrlList.minimum_by_name(availText)
                if self.ui.cbPropCtrlMax.isChecked():
                    rtMax = self.ui.sbPropCtrlMaxVal.value()
                else:
                    rtMax = ctrlList.maximum_by_name(availText)
                rtNeg = self.ui.cbNegativeEffect.isChecked()
                rtTgtRange = self.ui.cbEncourageLimits.isChecked()
                '''
                # The limit value tuple
                # FIXME: Finish it
                limitVal = (availText, None, None, False, None)
                if self.ui.rbLimitsDay.isChecked():
                    todName = "Day"
                else:
                    todName = "Night"
                # self.__supply_limit_control(limitVal, todName)

                # Move it from available to in-use
                self.__add_control_to_in_use(self.ui.cbAvailableLimitControls,
                                             availIndex, self.ui.lwLimitCtrls,
                                             self.ui.pbRemoveLimitCtrl)

    def __remove_limit_control(self):
        '''
        Remove the selected control in the in-use limit controls and add it to
        the available limit controls (remove button clicked in limits tab)
        '''

        # Get control list based on auto-exposure TOD selection
        ctrlList = self.todControlList()

        # We can only remove a selected item
        item = self.ui.lwLimitCtrls.currentItem()
        ctrlName = item.text()
        if item.isSelected():
            # debug_message("Moving {} from in-use to available".format(ctrlName))
            row = self.ui.lwLimitCtrls.currentRow()
            self.__add_control_to_available(self.ui.lwLimitCtrls, row,
                                            self.ui.cbAvailableLimitControls,
                                            self.ui.pbRemoveLimitCtrl)

            '''
            # take the item from the tune controls
            row = self.ui.lwTuneCtrls.currentRow()
            rItem = self.ui.lwTuneCtrls.takeItem(row)
            if (rItem is not None) and (rItem.text() == ctrlName):
                # If it doesn't already exist in the available controls
                if self.ui.cbAvailableControls.findText(ctrlName) == -1:
                    # Add it to the available controls
                    self.ui.cbAvailableControls.addItem(rItem.text())

                property = self.ui.cbImageProperty.currentText()
                if self.ui.rbDayCtrls.isChecked():
                    todName = "Day"
                else:
                    todName = "Night"

                # Remove it from the tuning list
                i = self.iTunerForTODNamePropertyAndCtrlName(todName, property,
                                                             ctrlName)
                if i != -1:
                    del self.tuningControlSettings[i]
            '''
        else:
            qCWarning(self.logCategory,
                      "Unable to remove limit control {}".format(ctrlName))
            # debug_message("Unable to remove limit control {}".format(ctrlName))

    def changeLimitProperty(self, index):
        self.ui.lwTuneCtrls.clear()

        '''
        if self.isAutoExposureDaytime():
            todName = "Day"
        else:
            todName = "Night"

        property = self.ui.cbImageProperty.currentText()

        # debug_message("Changing listed tuners for {} {}".format(todName, property))

        # Walk the properties for the current TOD and the selected property
        i = -2
        while (i != -1):
            if i == -2:
                i = -1
            i = self.iNextTunerForTODNameAndProperty(todName, property, i)
            # debug_message("Found control at index {}".format(i))
            if i >= 0:
                aTuner = self.tuningControlSettings[i]
                self.ui.lwTuneCtrls.addItem(aTuner[2])

        self.__enableRemoveTuningCtrl()
        '''

        # Get day or night control list based on auto-exposure selection
        ctrlList = self.tod_limit_control_list()

        # Remaining controls for the camera must be in the list we can add from
        self.loadNonPersistentControls(self.ui.cbAvailableLimitControls,
                                       ctrlList, self.ui.lwLimitCtrls)

    def set_available_limit_controls(self):
        # Get day or night limit control list based on auto-exposure selection
        ctrlList = self.tod_limit_control_list()

        self.loadNonPersistentControls(self.ui.cbAvailableLimitControls,
                                       ctrlList,
                                       None)

    def playSavedControlsDay(self):
        # Play case
        mySet = QSettings()

        # GROUP START: CAMERA
        mySet.beginGroup(self.camName)

        # #### GROUP START: IMAGE PROPERTY BRIGHTNESS
        mySet.beginGroup("Brightness")

        # ######## GROUP START: TOD CONTROLS FOR DAY
        mySet.beginGroup(self.kCtrlDay)

        # ############ GROUPS FOR INDIVIDUAL CONTROL SETTINGS
        mySet.beginGroup("Brightness")
        # It must have a key just to exist as a group
        mySet.setValue(self.kIsControl, "true")
        mySet.endGroup()

        mySet.beginGroup("Gamma")
        # It must have a key just to exist as a group, but this also has values
        mySet.setValue(self.kIsControl, "true")
        mySet.setValue(self.kCtrlMax, "137")
        mySet.setValue(self.kUseMax, "true")
        mySet.endGroup()

        mySet.beginGroup("Contrast")
        # It must have a key just to exist as a group, but this also has values
        mySet.setValue(self.kIsControl, "true")
        # mySet.setValue(self.kCtrlMin, "16")
        # mySet.setValue(self.kUseMin, "true")
        # mySet.setValue(self.kCtrlMax, "64")
        # mySet.setValue(self.kUseMax, "true")
        # mySet.setValue(self.kTargetLimits, "true")
        mySet.remove(self.kCtrlMin)
        mySet.remove(self.kUseMin)
        mySet.remove(self.kCtrlMax)
        mySet.remove(self.kUseMax)
        mySet.remove(self.kTargetLimits)
        mySet.setValue(self.kNegativeEffect, "true")
        mySet.endGroup()
        # ############ END OF GROUPS FOR INDIVIDUAL CONTROL SETTINGS

        # ######## GROUP END: TOD CONTROLS FOR DAY
        mySet.endGroup()

        # #### GROUP END: IMAGE PROPERTY BRIGHTNESS
        mySet.endGroup()

        # #### GROUP START: IMAGE PROPERTY CONTRAST
        mySet.beginGroup("Contrast")

        # ######## GROUP START: TOD CONTROLS FOR DAY
        mySet.beginGroup(self.kCtrlDay)

        # ############ GROUPS FOR INDIVIDUAL CONTROL SETTINGS
        mySet.beginGroup("Contrast")
        mySet.setValue(self.kIsControl, "true")
        mySet.endGroup()

        mySet.beginGroup("Gamma")
        # It must have a key just to exist as a group, but this also has values
        mySet.setValue(self.kIsControl, "true")
        mySet.setValue(self.kCtrlMax, "137")
        mySet.setValue(self.kUseMax, "true")
        mySet.setValue(self.kNegativeEffect, "true")
        mySet.endGroup()
        # ############ END OF GROUPS FOR INDIVIDUAL CONTROL SETTINGS

        # ######## GROUP END: TOD CONTROLS FOR DAY
        mySet.endGroup()

        # #### GROUP END: IMAGE PROPERTY CONTRAST
        mySet.endGroup()

        # #### GROUP START: IMAGE PROPERTY SATURATION
        mySet.beginGroup("Saturation")

        # ######## GROUP START: TOD CONTROLS FOR DAY
        mySet.beginGroup(self.kCtrlDay)

        # ############ GROUPS FOR INDIVIDUAL CONTROL SETTINGS
        mySet.beginGroup("Saturation")
        mySet.setValue(self.kIsControl, "true")
        mySet.endGroup()

        mySet.beginGroup("Gamma")
        # It must have a key just to exist as a group, but this also has values
        mySet.setValue(self.kIsControl, "true")
        mySet.setValue(self.kCtrlMax, "137")
        mySet.setValue(self.kUseMax, "true")
        mySet.endGroup()
        # ############ END OF GROUPS FOR INDIVIDUAL CONTROL SETTINGS

        # ######## GROUP END: TOD CONTROLS FOR DAY
        mySet.endGroup()

        # #### GROUP END: IMAGE PROPERTY SATURATION
        mySet.endGroup()

        # GROUP END: CAMERA
        mySet.endGroup()

    def playSavedControlsNight(self):
        # Play case
        mySet = QSettings()

        # GROUP START: CAMERA
        mySet.beginGroup(self.camName)

        # #### GROUP START: IMAGE PROPERTY BRIGHTNESS
        mySet.beginGroup("Brightness")

        # ######## GROUP START: TOD CONTROLS FOR NIGHT
        mySet.beginGroup(self.kCtrlNight)

        # ############ GROUPS FOR INDIVIDUAL CONTROL SETTINGS
        mySet.beginGroup("Brightness")
        # It must have a key just to exist as a group
        mySet.setValue(self.kIsControl, "true")
        mySet.endGroup()

        mySet.beginGroup("Gamma")
        # It must have a key just to exist as a group, but this also has values
        mySet.setValue(self.kIsControl, "true")
        mySet.setValue(self.kCtrlMax, "137")
        mySet.setValue(self.kUseMax, "true")
        mySet.endGroup()

        mySet.beginGroup("Contrast")
        # It must have a key just to exist as a group, but this also has values
        mySet.setValue(self.kIsControl, "true")
        # mySet.setValue(self.kCtrlMin, "22")
        # mySet.setValue(self.kUseMin, "true")
        # mySet.setValue(self.kCtrlMax, "64")
        # mySet.setValue(self.kUseMax, "true")
        # mySet.setValue(self.kTargetLimits, "true")
        # mySet.setValue(self.kIsControl, "true")
        mySet.remove(self.kCtrlMin)
        mySet.remove(self.kUseMin)
        mySet.remove(self.kCtrlMax)
        mySet.remove(self.kUseMax)
        mySet.remove(self.kTargetLimits)
        mySet.setValue(self.kNegativeEffect, "true")
        mySet.endGroup()
        # ########### END OF GROUPS FOR INDIVIDUAL CONTROL SETTINGS

        # ######## GROUP END: TOD CONTROLS FOR NIGHT
        mySet.endGroup()

        # #### GROUP END: IMAGE PROPERTY BRIGHTNESS
        mySet.endGroup()

        # #### GROUP START: IMAGE PROPERTY CONTRAST
        mySet.beginGroup("Contrast")

        # ######## GROUP START: TOD CONTROLS FOR NIGHT
        mySet.beginGroup(self.kCtrlNight)

        # ############ GROUPS FOR INDIVIDUAL CONTROL SETTINGS
        mySet.beginGroup("Contrast")
        mySet.setValue(self.kIsControl, "true")
        mySet.endGroup()

        mySet.beginGroup("Gamma")
        # It must have a key just to exist as a group, but this also has values
        mySet.setValue(self.kIsControl, "true")
        mySet.setValue(self.kCtrlMax, "137")
        mySet.setValue(self.kUseMax, "true")
        mySet.setValue(self.kNegativeEffect, "true")
        mySet.endGroup()
        # ############ END OFGROUPS FOR INDIVIDUAL CONTROL SETTINGS

        # ######## GROUP END: TOD CONTROLS FOR NIGHT
        mySet.endGroup()

        # #### GROUP END: IMAGE PROPERTY CONTRAST
        mySet.endGroup()

        # #### GROUP START: IMAGE PROPERTY SATURATION
        mySet.beginGroup("Saturation")

        # ######## GROUP START: TOD CONTROLS FOR DAY
        mySet.beginGroup(self.kCtrlDay)

        # ############ GROUPS FOR INDIVIDUAL CONTROL SETTINGS
        mySet.beginGroup("Saturation")
        mySet.setValue(self.kIsControl, "true")
        mySet.endGroup()

        mySet.beginGroup("Gamma")
        # It must have a key just to exist as a group, but this also has values
        mySet.setValue(self.kIsControl, "true")
        mySet.setValue(self.kCtrlMax, "137")
        mySet.setValue(self.kUseMax, "true")
        mySet.endGroup()
        # ############ END OF GROUPS FOR INDIVIDUAL CONTROL SETTINGS

        # ######## GROUP END: TOD CONTROLS FOR DAY
        mySet.endGroup()

        # #### GROUP END: IMAGE PROPERTY SATURATION
        mySet.endGroup()

        # End camera group
        mySet.endGroup()

    def playSavedControls(self):
        self.playSavedControlsDay()
        self.playSavedControlsNight()

    def loadNonPersistentControls(self, uiList, ctrlList, uiPreListed=None):
        '''
        Load a UI list from a name list and exclude an name that can be found
        in another UI list

        Parameters
        ----------
            uiList: a Qt UI list object
                The list to load
            ctrlList: a list of strings
                The list of names to load the UI list from
            uiPreListed: a Qt UI list object
                The list to check for names in before loading into the first UI
                list. If the name is present in this UI list it is not loaded
                into the first list
        '''

        curName = uiList.currentText()
        uiList.clear()
        if uiPreListed is not None:
            # No pre-listed place for items means all checks in the pre-list are
            # an empty list result
            items = list()
        for ctrlID in ctrlList:
            ctrlName = ctrlList.name_by_ID(ctrlID)
            if uiPreListed is not None:
                items = uiPreListed.findItems(ctrlName, Qt.MatchExactly)
            if items:
                if len(items) >= 1:
                    found = False
                    for anItem in items:
                        if anItem.text() == ctrlName:
                            found = True
                            break

                    # Ignore controls already present in the tuning controls
                    if found:
                        continue

            # We can add this control to the available controls list
            uiList.addItem(ctrlName)

        # If still present, re-select the name that was present when we started
        index = uiList.findText(curName)

        # No longer present, use the top (if there are any left)
        if index < 0:
            if uiList.count() > 0:
                index = 0

        if index >= 0:
            uiList.setCurrentIndex(index)

    # After loading all persistent controls use this to set the list of
    # controls that can be added for auto-exposure operation for the current
    # image properties
    def loadNonPersistentControlsB(self):
        # Get day or night control list based on auto-exposure selection
        ctrlList = self.todControlList()

        curName = self.ui.cbAvailableControls.currentText()
        self.ui.cbAvailableControls.clear()
        for ctrlID in ctrlList:
            ctrlName = ctrlList.name_by_ID(ctrlID)
            items = self.ui.lwTuneCtrls.findItems(ctrlName, Qt.MatchExactly)
            if items:
                if len(items) >= 1:
                    found = False
                    for anItem in items:
                        if anItem.text() == ctrlName:
                            found = True
                            break

                    # Ignore controls already present in the tuning controls
                    if found:
                        continue

            # We can add this control to the available controls list
            self.ui.cbAvailableControls.addItem(ctrlName)

        # If still present, re-select the name that was present when we started
        index = self.ui.cbAvailableControls.findText(curName)

        # No longer present, use the top (if there are any left)
        if index < 0:
            if self.ui.cbAvailableControls.count() > 0:
                index = 0

        if index >= 0:
            self.ui.cbAvailableControls.setCurrentIndex(index)

    # Load a persistent control setting from the tuner list
    def loadPersistentControl(self, item):
        if item == None:
            return

        # Get the control name at the supplied item
        ctrlName = item.text()

        # TOD and property
        if self.ui.rbNightCtrls.isChecked():
            todName = "Night"
        else:
            todName = "Day"
        ctrlList = self.todControlList()
        property = self.ui.cbImageProperty.currentText()
        # if (ctrlName == "Contrast") and (todName == "Day") and\
        #         (property == "Brightness"):
        #     self.dumpTuners()

        # Get the camera control data
        qCtrl = ctrlList.query_control_by_name(ctrlName)

        # Find a tuner for the time-of-day and image property
        i = self.iTunerForTODNamePropertyAndCtrlName(todName, property,
                                                     ctrlName)
        if i != -1:
            aTuner = self.tunerAtIndex(i)
        else:
            # Doesn't exist in tuner list, so work something out from camera
            # data
            aTuner = (property, ctrlName, -1, qCtrl.minimum, qCtrl.maximum,
                      False, False)

        # Populate the UI but ignore signals about changes while doing it
        self.ignoreTuneValueChanged = True
        self.ui.sbPropCtrlMinVal.setValue(aTuner[3])
        self.ui.sbPropCtrlMaxVal.setValue(aTuner[4])

        useMin = (aTuner[3] != qCtrl.minimum)
        useMax = (aTuner[4] != qCtrl.maximum)
        self.ui.cbPropCtrlMin.setChecked(useMin)
        self.ui.cbPropCtrlMax.setChecked(useMax)

        # Because we have ignoreTuneValueChanged setting the check state for
        # the min/max checkboxes won't automatically enable the value controls
        self.ui.sbPropCtrlMinVal.setEnabled(useMin)
        self.ui.sbPropCtrlMaxVal.setEnabled(useMax)

        self.ui.cbNegativeEffect.setChecked(aTuner[5])
        self.ui.cbEncourageLimits.setChecked(aTuner[6])
        self.ignoreTuneValueChanged = False

    def makeAutoExpDayOnly(self, newState):
        self.ui.rbDayCtrls.setChecked(newState)
        self.ui.rbNightCtrls.setEnabled(not newState)
        if newState:
            self.ui.cbNightOnly.setChecked(False)
        self.ui.cbNightOnly.setEnabled(not newState)

    def makeAutoExpNightOnly(self, newState):
        self.ui.rbNightCtrls.setChecked(newState)
        self.ui.rbDayCtrls.setEnabled(not newState)
        if newState:
            self.ui.cbDayOnly.setChecked(False)
        self.ui.cbDayOnly.setEnabled(not newState)

    def changeAutoExpTOD(self, newState):
        # Just load the correct controls
        self.changeAutoExpProperty(0)

    def __listed_control_exists(self, ctrlList, property, ctrlName):
        '''
        Given a control list (list of tuples) check if it contains one with
        property and name.

        Parameters
        ----------
            ctrlList: list of camera control tuples
            property: string
                A property the control should be associated with, e.g.
                "Brightness". Can be "" if the control is not to be associated
                with any property but it must have been added to the list with
                property "", use of "" isn't a wildcard for any instance of name
            ctrlName: string
                The name of the control being searched for with the given
                property in ctrlList

        '''

        for aCtrl in ctrlList:
            if (aCtrl[0] == property) and (aCtrl[1] == ctrlName):
                return True

        return False

    def __is_tune_control_available(self, ctrlName):
        '''
        Return True if the name is present in the available tuning controls
        UI object.
        '''
        # FIXME: This has the problem that whether it is present depends on
        # the selected auto-exposure property, e.g. "Bridghtness", "Contrast",
        # "Saturation". Fix it to use the internal class data
        return (self.ui.cbAvailableControls.findText(ctrlName) != -1)

    def __is_limit_control_available(self, ctrlName):
        '''
        Return True if the name is present in the available limit controls, else
        returns False
        '''
        return (self.ui.cbAvailableLimitControls.findText(ctrlName) != -1)

    def __clear_control_tuning(self):
        '''
        Set the control tuning to all empty if nothing is selected in the in-use
        tuning controls list
        '''

        self.ui.sbPropCtrlMinVal.setValue(0)
        self.ui.cbPropCtrlMin.setChecked(False)

        self.ui.sbPropCtrlMaxVal.setValue(0)
        self.ui.cbPropCtrlMax.setChecked(False)

        self.ui.cbEncourageLimits.setChecked(False)

        self.ui.cbNegativeEffect.setChecked(False)

    def addTuneControl(self):
        # Get control list based on auto-exposure TOD selection
        ctrlList = self.todControlList()

        # Get the selected item in the available controls
        if self.ui.cbAvailableControls.count() > 0:
            availIndex = self.ui.cbAvailableControls.currentIndex()
            availText = self.ui.cbAvailableControls.currentText()
            property = self.ui.cbImageProperty.currentText()
            if (availIndex >= 0) and\
                    not self.__listed_control_exists(self.tuningControlSettings,
                                                     property, availText):
                # Add it to the correct tuner list
                if self.ui.cbPropCtrlMin.isChecked():
                    rtMin = self.ui.sbPropCtrlMinVal.value()
                else:
                    rtMin = ctrlList.minimum_by_name(availText)
                if self.ui.cbPropCtrlMax.isChecked():
                    rtMax = self.ui.sbPropCtrlMaxVal.value()
                else:
                    rtMax = ctrlList.maximum_by_name(availText)
                rtNeg = self.ui.cbNegativeEffect.isChecked()
                rtTgtRange = self.ui.cbEncourageLimits.isChecked()
                tuneVal = (property, availText, -1, rtMin, rtMax, rtNeg,
                           rtTgtRange)
                if self.ui.rbDayCtrls.isChecked():
                    todName = "Day"
                else:
                    todName = "Night"
                self.supplyTuningControl(tuneVal, todName)

                # Move it from available to in-use
                self.__add_control_to_in_use(self.ui.cbAvailableControls,
                                             availIndex, self.ui.lwTuneCtrls,
                                             self.ui.pbRemoveTuneCtrl)

    def addTuneControlB(self):
        # Get control list based on auto-exposure TOD selection
        ctrlList = self.todControlList()

        # Get the selected item in the available controls
        if self.ui.cbAvailableControls.count() > 0:
            availIndex = self.ui.cbAvailableControls.currentIndex()
            availText = self.ui.cbAvailableControls.currentText()
            property = self.ui.cbImageProperty.currentText()
            if (availIndex >= 0) and\
                    not self.__listed_control_exists(self.tuningControlSettings,
                                                     property, availText):
                # Add it to the correct tuner list
                if self.ui.cbPropCtrlMin.isChecked():
                    rtMin = self.ui.sbPropCtrlMinVal.value()
                else:
                    rtMin = ctrlList.minimum_by_name(availText)
                if self.ui.cbPropCtrlMax.isChecked():
                    rtMax = self.ui.sbPropCtrlMaxVal.value()
                else:
                    rtMax = ctrlList.maximum_by_name(availText)
                rtNeg = self.ui.cbNegativeEffect.isChecked()
                rtTgtRange = self.ui.cbEncourageLimits.isChecked()
                tuneVal = (property, availText, -1, rtMin, rtMax, rtNeg,
                           rtTgtRange)
                if self.ui.rbDayCtrls.isChecked():
                    todName = "Day"
                else:
                    todName = "Night"
                self.supplyTuningControl(tuneVal, todName)

                # Move it from available to in-use
                self.ui.cbAvailableControls.removeItem(availIndex)
                self.ui.lwTuneCtrls.addItem(availText)
                self.__set_remove_in_use_button(self.ui.lwTuneCtrls,
                                                self.ui.pbRemoveTuneCtrl)

    def tuneLimitStateChange(self, y):
        if self.ignoreTuneValueChanged:
            return

        # Shorten self.ui
        sUI = self.ui

        # Let anything be saved in one place for checkboxes and spinboxes
        # debug_message("Checking tuning limits for checkbox toggle")
        if self.newTuneLimit():
            # Use the checkboxes to set enabled state for spinboxes
            # debug_message("Applying control setting checkbox toggle")
            minCheck = sUI.cbPropCtrlMin.isChecked()
            sUI.sbPropCtrlMinVal.setEnabled(minCheck)
            maxCheck = sUI.cbPropCtrlMax.isChecked()
            sUI.sbPropCtrlMaxVal.setEnabled(maxCheck)

    def tuneLimitValueChanged(self, newValue):
        if self.ignoreTuneValueChanged:
            return

        # Value doesn't matter, let anything be saved in one place for
        # checkboxes and spinboxes
        self.newTuneLimit()

    # One implementation for min and max, enabled and values
    def newTuneLimit(self):
        # Shorten self.ui and self.camControls lines
        sUI = self.ui
        # ctrls = self.todControlList()

        # Only works for a single selected item
        selItems = sUI.lwTuneCtrls.selectedItems()
        if len(selItems) != 1:
            return False
        i = 0
        for anItem in selItems:
            i += 1
            item = anItem
            if i > 1:
                qCWarning(self.logCategory,
                          "Too many controls selected: {}".format(i))
                # debug_message("Too many controls selected: {}".format(i))
                return False

            ctrlName = item.text()

            # Get the use state for the min and max and switches
            minCheck = sUI.cbPropCtrlMin.isChecked()
            maxCheck = sUI.cbPropCtrlMax.isChecked()
            negEffect = sUI.cbNegativeEffect.isChecked()
            encourageLimits = sUI.cbEncourageLimits.isChecked()

            if minCheck:
                rMin = sUI.sbPropCtrlMinVal.value()
            else:
                rMin = None
            if maxCheck:
                rMax = sUI.sbPropCtrlMaxVal.value()
            else:
                rMax = None

            # FIXME: This is broken if both are enabled
            # if not minCheck or not maxCheck:
            #     ctrlList = self.todControlList()
            #     qCtrl = ctrlList.query_control_by_name(ctrlName)
            # Trying:
            ctrlList = self.todControlList()
            qCtrl = ctrlList.query_control_by_name(ctrlName)
            if qCtrl is not None:
                if rMin is not None:
                    if rMin < qCtrl.minimum:
                        rMin = qCtrl.minimum
                else:
                    rMin = qCtrl.minimum
                if rMax is not None:
                    if rMax > qCtrl.maximum:
                        rMax = qCtrl.maximum
                else:
                    rMax = qCtrl.maximum

            # Get the image property and time-of-day
            property = self.ui.cbImageProperty.currentText()
            if sUI.rbNightCtrls.isChecked():
                todName = "Night"
            else:
                todName = "Day"

            # Set everything in the saved control from the UI
            # First, remove it from the tuning list
            i = self.iTunerForTODNamePropertyAndCtrlName(todName, property,
                                                         ctrlName)
            if i != -1:
                del self.tuningControlSettings[i]

            # Add the modified tuning control to the tuning list
            tuneVal = (property, ctrlName, -1, rMin, rMax, negEffect,
                       encourageLimits)
            # debug_message("MODIFIED TUNER")
            self.supplyTuningControl(tuneVal, todName, True)

        return True

    # Overload setVisible so that we can populate auto-exposure controls on
    # the dialog being displayed
    def setVisible(self, visible):
        super(dlgSettings, self).setVisible(visible)

        # Make sure the tab is Auto-exposure
        self.tab_changed(0)

    def dumpCaptionFont(self, f):
        qCDebug(self.logCategory,
                "CAPTION FONT DUMP:")
        qCDebug(self.logCategory,
                "             Family: {}".format(f.family()))
        qCDebug(self.logCategory,
                "                Key: {}".format(f.key()))
        qCDebug(self.logCategory,
                "     Default Family: {}".format(f.defaultFamily()))
        qCDebug(self.logCategory,
                "             Weight: {}".format(f.weight()))
        qCDebug(self.logCategory,
                "             Italic: {}".format(f.italic()))
        qCDebug(self.logCategory,
                "          Underline: {}".format(f.underline()))
        qCDebug(self.logCategory,
                "           Overline: {}".format(f.overline()))
        qCDebug(self.logCategory,
                "          Strikeout: {}".format(f.strikeOut()))
        qCDebug(self.logCategory,
                "              Style: {}".format(f.style()))
        qCDebug(self.logCategory,
                "         Style Hint: {}".format(f.styleHint()))
        qCDebug(self.logCategory,
                "         Style Name: {}".format(f.styleName()))
        qCDebug(self.logCategory,
                "     Style Strategy: {}".format(f.styleStrategy()))
        qCDebug(self.logCategory,
                "            Kerning: {}".format(f.kerning()))
        qCDebug(self.logCategory,
                "     Letter Spacing: {}".format(f.letterSpacing()))
        qCDebug(self.logCategory,
                "Letter Spacing Type: {}".format(f.letterSpacingType()))
        qCDebug(self.logCategory,
                "       Word Spacing: {}".format(f.wordSpacing()))
        qCDebug(self.logCategory,
                "     Capitalization: {}".format(f.capitalization()))
        qCDebug(self.logCategory,
                "        Fixed Pitch: {}".format(f.fixedPitch()))
        qCDebug(self.logCategory,
                " Hinting Preference: {}".format(f.hintingPreference()))
        qCDebug(self.logCategory,
                "         Pixel Size: {}".format(f.pixelSize()))
        qCDebug(self.logCategory,
                "         Point Size: {}".format(f.pointSize()))
        qCDebug(self.logCategory,
                "   Float Point Size: {}".format(f.pointSizeF()))
        qCDebug(self.logCategory,
                "             String: {}".format(f.toString()))
        # debug_message("CAPTION FONT DUMP:")
        # debug_message("             Family: {}".format(f.family()))
        # debug_message("                Key: {}".format(f.key()))
        # debug_message("     Default Family: {}".format(f.defaultFamily()))
        # debug_message("             Weight: {}".format(f.weight()))
        # debug_message("             Italic: {}".format(f.italic()))
        # debug_message("          Underline: {}".format(f.underline()))
        # debug_message("           Overline: {}".format(f.overline()))
        # debug_message("          Strikeout: {}".format(f.strikeOut()))
        # debug_message("              Style: {}".format(f.style()))
        # debug_message("         Style Hint: {}".format(f.styleHint()))
        # debug_message("         Style Name: {}".format(f.styleName()))
        # debug_message("     Style Strategy: {}".format(f.styleStrategy()))
        # debug_message("            Kerning: {}".format(f.kerning()))
        # debug_message("     Letter Spacing: {}".format(f.letterSpacing()))
        # debug_message("Letter Spacing Type: {}".format(f.letterSpacingType()))
        # debug_message("       Word Spacing: {}".format(f.wordSpacing()))
        # debug_message("     Capitalization: {}".format(f.capitalization()))
        # debug_message("        Fixed Pitch: {}".format(f.fixedPitch()))
        # debug_message(" Hinting Preference: {}".format(f.hintingPreference()))
        # debug_message("         Pixel Size: {}".format(f.pixelSize()))
        # debug_message("         Point Size: {}".format(f.pointSize()))
        # debug_message("   Float Point Size: {}".format(f.pointSizeF()))
        # debug_message("             String: {}".format(f.toString()))

        # info = QFontInfo(f)
        # realFont = QFont(info.family())
        # rawName = realFont.rawName()
        # rawFont = QRawFont.fromFont(f)
        # rawName = rawFont.rawName()
        rawName = self.fontPath(f)
        qCDebug(self.logCategory, "           Raw Name: {}".format(rawName))
        # debug_message("           Raw Name: {}".format(rawName))

    # @Slot()
    # def changeCaptionFont(self, f):
    #     self.fontFile = self.fontPath(f)
    #     # self.dumpCaptionFont(f)

    # Return the font file for the selected caption font. The filename is used
    # in the actual caption generating via PILlow
    # def captionFontFilename(self):
    #     return self.fontFile

    # Supply the font filename that is being used for caption generation
    # def setCaptionFontByFilename(self, newFilename):
    #     sUI = self.UI

    #     # Find the matching font family and select it in the caption font list
    #     aFont = QRawFont(newFilename, 16, QFont.PreferDefaultHinting)
    #     selFont = sUI.cbCaptionFont.findText(aFont.family(), Qt.MatchExactly)
    #     if selFont >= 0:
    #         sui.cbCaptionFont.setCurrentText(aFont.family())

    #     self.fontFile = newFilename

    def captionFontFamily(self):
        return self.ui.cbCaptionFont.currentText()

    def setCaptionFontFamily(self, newFamily):
        self.ui.cbCaptionFont.setCurrentText(newFamily)

    def captionFontSize(self):
        return self.ui.sbCaptionFontSize.value()

    def setCaptionFontSize(self, newSize):
        if newSize >= self.ui.sbCaptionFontSize.minimum() and\
                newSize <= self.ui.sbCaptionFontSize.maximum():
            self.ui.sbCaptionFontSize.setValue(newSize)

    def tab_changed(self, index):
        '''
        The tab was changed in the tab control

        Parameters
        ----------
            index: integer
                The index of the the newly selected tab (zero based)
        '''

        if index == 0:
            # Auto-exposure selected, make sure we show the exposure controls
            qCDebug(self.logCategory, "Init auto-exposure via tab")
            # debug_message("Init auto-exposure via tab")
            self.changeAutoExpProperty(0)
        elif index == 2:
            # Limit selected, make sure we show the limit controls
            qCDebug(self.logCategory, "Init limits via tab")
            # debug_message("Init limits via tab")
            self.changeLimitProperty(0)

    def connect_controls(self):
        '''
        Link Qt signals and slots
        '''

        # Shorten the length of the references to the ui object to reduce some
        # line lengths
        sUI = self.ui

        sUI.twSettingsTabs.currentChanged.connect(self.tab_changed)

        sUI.sbCaptionTextR.valueChanged.connect(self.captionTextColorChange)
        sUI.sbCaptionTextG.valueChanged.connect(self.captionTextColorChange)
        sUI.sbCaptionTextB.valueChanged.connect(self.captionTextColorChange)

        sUI.rbDMS.toggled.connect(self.enableLatLonInput)

        sUI.dsbLatFloat.valueChanged.connect(self.newLatFloat)
        sUI.sbLatDegrees.valueChanged.connect(self.newLatDMS)
        sUI.sbLatMinutes.valueChanged.connect(self.newLatDMS)
        sUI.sbLatSeconds.valueChanged.connect(self.newLatDMS)

        sUI.dsbLonFloat.valueChanged.connect(self.newLonFloat)
        sUI.sbLonDegrees.valueChanged.connect(self.newLonDMS)
        sUI.sbLonMinutes.valueChanged.connect(self.newLonDMS)
        sUI.sbLonSeconds.valueChanged.connect(self.newLonDMS)

        sUI.cbImageProperty.activated.connect(self.changeAutoExpProperty)
        sUI.lwTuneCtrls.itemClicked.connect(self.loadPersistentControl)
        sUI.cbDayOnly.stateChanged.connect(self.makeAutoExpDayOnly)
        sUI.cbNightOnly.stateChanged.connect(self.makeAutoExpNightOnly)
        sUI.rbDayCtrls.toggled.connect(self.changeAutoExpTOD)
        sUI.rbNightCtrls.toggled.connect(self.changeAutoExpTOD)
        # FIXME: sUI.lwTuneCtrls.currentItemChanged.connect(self.changedTuneCtrl)
        sUI.lwTuneCtrls.currentItemChanged.connect(self.loadPersistentControl)
        sUI.pbAddTuneCtrl.clicked.connect(self.addTuneControl)
        sUI.pbRemoveTuneCtrl.clicked.connect(self.removeTuneCtrl)
        sUI.sbPropCtrlMinVal.valueChanged.connect(self.tuneLimitValueChanged)
        sUI.cbPropCtrlMin.toggled.connect(self.tuneLimitStateChange)
        sUI.sbPropCtrlMaxVal.valueChanged.connect(self.tuneLimitValueChanged)
        sUI.cbPropCtrlMax.toggled.connect(self.tuneLimitStateChange)
        sUI.cbNegativeEffect.toggled.connect(self.tuneLimitStateChange)
        sUI.cbEncourageLimits.toggled.connect(self.tuneLimitStateChange)

        sUI.sbDayTgtBrightness.valueChanged.connect(self.newDayBrightnessMax)
        sUI.sbDayTgtBrightnessMin.valueChanged.connect(self.newDayBrightnessMin)
        sUI.sbDayTgtContrast.valueChanged.connect(self.newDayContrastMax)
        sUI.sbDayTgtContrastMin.valueChanged.connect(self.newDayContrastMin)
        sUI.sbDayTgtSaturation.valueChanged.connect(self.newDaySaturationMax)
        sUI.sbDayTgtSaturationMin.valueChanged.connect(self.newDaySaturationMin)

        sUI.sbNightTgtBrightness.valueChanged.connect(self.newNightBrightnessMax)
        sUI.sbNightTgtBrightnessMin.valueChanged.connect(self.newNightBrightnessMin)
        sUI.sbNightTgtContrast.valueChanged.connect(self.newNightContrastMax)
        sUI.sbNightTgtContrastMin.valueChanged.connect(self.newNightContrastMin)
        sUI.sbNightTgtSaturation.valueChanged.connect(self.newNightSaturationMax)
        sUI.sbNightTgtSaturationMin.valueChanged.connect(self.newNightSaturationMin)

        sUI.pbAddLimitCtrl.clicked.connect(self.__add_limit_control)
        sUI.pbRemoveLimitCtrl.clicked.connect(self.__remove_limit_control)
