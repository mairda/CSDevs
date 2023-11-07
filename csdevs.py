# This Python file uses the following encoding: utf-8
#
# TBD: Import thread based save with a pending frames to save list (take save
# time out of capture time): NOT NEEDED, each frame capture is it's own thread
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

# FIXME: Things like auto-focus changes and focus absolute changes are not
# persistent

import sys
import time

import errno
from fcntl import ioctl

# import pathlib

from math import sin, cos, atan2, pi, pow, sqrt

import random

import glob

from PySide6.QtCore import (Qt, QCoreApplication, QLoggingCategory, QPoint,
                             qSetMessagePattern, QSettings, QPointF, QSize,
                             QTimer, QVersionNumber, Signal, Slot, qCDebug,
                             qCWarning)
from PySide6.QtGui import (QBrush, QColor, QColorConstants, QFont, QIcon,
                           QImage, QPen, QPixmap)
from PySide6.QtWidgets import (QApplication, QDialog, QDialogButtonBox,
                               QFileDialog, QGraphicsScene, QGraphicsView,
                               QGraphicsPixmapItem, QMessageBox, QWidget)
# from PySide6.QtUiTools import QUiLoader

# import ctypes

from v4l2py.device import Device
from v4l2py.raw import (v4l2_capability, v4l2_format, v4l2_control, v4l2_input,
                        v4l2_fmtdesc, v4l2_frmsizeenum, v4l2_queryctrl,
                        V4L2_INPUT_TYPE_CAMERA, V4L2_BUF_TYPE_VIDEO_CAPTURE,
                        VIDIOC_ENUMINPUT, VIDIOC_ENUM_FRAMESIZES, VIDIOC_G_FMT,
                        VIDIOC_S_FMT, VIDIOC_QUERYCAP, VIDIOC_QUERYCTRL,
                        V4L2_CID_BASE, V4L2_CID_LASTP1,
                        V4L2_CID_CAMERA_CLASS_BASE, V4L2_CID_EXPOSURE_AUTO,
                        V4L2_EXPOSURE_AUTO, V4L2_EXPOSURE_MANUAL,
                        V4L2_EXPOSURE_SHUTTER_PRIORITY,
                        V4L2_EXPOSURE_APERTURE_PRIORITY,
                        V4L2_CID_POWER_LINE_FREQUENCY,
                        V4L2_CID_POWER_LINE_FREQUENCY_DISABLED,
                        V4L2_CID_POWER_LINE_FREQUENCY_50HZ,
                        V4L2_CID_POWER_LINE_FREQUENCY_60HZ, V4L2_CID_PRIVACY,
                        V4L2_CAP_VIDEO_CAPTURE, V4L2_FRMSIZE_TYPE_DISCRETE,
                        V4L2_FRMSIZE_TYPE_STEPWISE,
                        V4L2_FRMSIZE_TYPE_CONTINUOUS, V4L2_CTRL_TYPE_INTEGER,
                        V4L2_CTRL_FLAG_DISABLED, V4L2_CTRL_TYPE_BOOLEAN,
                        V4L2_CTRL_TYPE_MENU, V4L2_CTRL_TYPE_BUTTON,
                        V4L2_CTRL_TYPE_INTEGER64, V4L2_CTRL_TYPE_CTRL_CLASS,
                        V4L2_CTRL_TYPE_STRING, VIDIOC_ENUM_FMT, VIDIOC_G_CTRL)

from dlgCSDevs import Ui_dlgCSDevs
from dlgSettings import dlgSettings
from dlgInfo import dlgInfo
from dlgAbout import dlgAbout

from CSTODMath import CSTODMath
from csdCapture import captureThread
from CSAllFonts import CSAllFonts

# from csdMessages import (disable_warnings, enable_warnings, disable_debug,
#                          enable_debug, warning_message, debug_message)


# 2022/05/03 - Restarting to fix bugs in frame capture and save


# Primes lower than 120... might use these to automatically adjust capture
# period if we get a timer tick during capture. The question is do we reduce it
# if we stop seeing the problem and what minimum to use if we do...
TWO_MIN_PRIMES = [ 2, 3, 5, 7, 11, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61,
                   67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113 ]


class CSDevs(QDialog):
    '''
    Main window class for CSDevs, derived from QDialog (dialog box main window)
    '''

    version = QVersionNumber(1, 0, 1)
    cfgVersionOK = False

    # Lists for all video devices and cameras among them
    allDevs = []
    cameras = []

    monitoring = False

    # We can't use a normal OK button with an accept role because it will close
    # and destroy the main window and it's objects if there is a thread running
    # to capture a frame and that will end by signaling a non-existing window.
    # We'll fake an OK button by using the reset role and do the accept with a
    # delayed finish if there is a thread running
    okButton = None
    doAccept = False
    doReject = False

    # There isn't an About role for a standard button box, but we'll re-use Yes
    # role for it
    aboutButton = None

    # sbValueNest = 0
    # hsValueNest = 0

    lateClose = Signal()

    capThread = None
    lastCapBroke = False
    lostCamera = False

    # Frame capture timer
    capTimer = QTimer()
    tFrameTick = 0
    wastedCapTicks = 0
    frameCaptureAndSave = True

    tCaptureDurations = []
    tCaptureSum = 0.0
    tMaxCaptures = 10

    # Camera information
    capDev = None
    switchingDev = False
    cameraFormats = None
    width = 0
    height = 0

    openCount = 0
    threadCount = 0

    # Camera control management
    controlIndex = -1
    switchingControl = False
    ctrlCurVal = None
    readCamCtrl = False

    lastTOD = ""
    lastFrameBrightness = -1.0
    lastFrameContrast = -1.0
    lastFrameSaturation = -1.0

    # Frame statistic targets for auto-exposure (< 0.0 means disabled)
    frameDayBrightnessTarget = 120.0
    frameDayContrastTarget = 49.0
    frameDaySaturationTarget = 40.0

    frameDayBrightnessMinTarget = 120.0
    frameDayContrastMinTarget = 49.0
    frameDaySaturationMinTarget = 40.0

    # 100
    frameNightBrightnessTarget = -1.0
    frameNightContrastTarget = -1.0
    frameNightSaturationTarget = -1.0

    frameNightBrightnessMinTarget = -1.0
    frameNightContrastMinTarget = -1.0
    frameNightSaturationMinTarget = -1.0

    # Persistent state key constant elements per-camera for targets
    kDayBrightnessTarget = "Day Brightness Target"
    kDayContrastTarget = "Day Contrast Target"
    kDaySaturationTarget = "Day Saturation Target"
    kNightBrightnessTarget = "Night Brightness Target"
    kNightContrastTarget = "Night Contrast Target"
    kNightSaturationTarget = "Night Saturation Target"

    kDayBrightnessMinTarget = "Day Brightness Minimum Target"
    kDayContrastMinTarget = "Day Contrast Minimum Target"
    kDaySaturationMinTarget = "Day Saturation Minimum Target"
    kNightBrightnessMinTarget = "Night Brightness Minimum Target"
    kNightContrastMinTarget = "Night Contrast Minimum Target"
    kNightSaturationMinTarget = "Night Saturation Minimum Target"

    rCtrlForce = 0
    loLimit = 0
    hiLimit = 16777214
    noClampLoLimit = None
    noClampHiLimit = None
    ctrlNegativeUse = False

    tuneProperties = ["Brightness", "Contrast", "Saturation"]
    tunedControls = []
    tuningControlSettings = None
    imageTuningControls = None
    tuningControlSettingsDay = []
    imageTuningControlsDay = []
    tuningControlSettingsNight = []
    imageTuningControlsNight = []
    tuneLogging = True
    tuneMathLogging = True
    kTuneDay = "Day"
    kTuneNight = "Night"
    kTuneMin = "Minimum"
    kTuneMax = "Maximum"
    kNegativeUse = "Negative Use"
    kEncourageRange = "Encourage Range"

    controls = []

    # Some time constants
    daySeconds = 24.0 * 60.0 * 60.0
    astronomicalTwilight = daySeconds * 18.0 / 360.0

    # Our location (default is zero longitude on the equator)
    latitude = 0.0
    longitude = 0.0
    # tzOffset = 1.0 * -3600.0
    tzOffset = 0.0

    # Persistent state key constants latitude, longitude
    kLatitude = "Latitude"
    kLongitude = "Longitude"

    # Persistent state key constant element per-camera for capture filename
    kCaptureFilename = "Capture Filename"

    # After editing it, how long to leave capture filename before saving it
    saveEditedCaptureFileNameDelay = 10.0

    # For formats that support it keep a persistent image quality for save,
    # we need a class copy because we can't always set the horizontal slider
    # when we load the value, e.g. if file format doesn't have a quality
    # property. Default quality is best. qualFormats is a list of filename
    # extensions for image file types that have a save quality property. ONLY
    # USE LOWERCASE EXTENTIONS HERE
    qualFormats = [ '.jpg', '.jpeg' ]
    kImageFileQuality = "Image File Quality"
    imageFileQuality = 100

    # Persistent per-camera auto-focus keys and values
    kPerCameraAF = "Auto-focus"
    kPerCameraFocus = "Focus"
    camAF = False
    camFocus = None

    # If we don't have an existing scene
    newScene = True

    # Scene objects
    colorSky = None
    colorGround = None
    colorSun = None
    sceneSky = None
    sceneGround = None
    sceneSun = None
    pointSun = None
    sceneMoon = None
    pointMoon = None

    # Limit values for the sun color
    # mostSet = "#fd3516"
    # mostSet = "#fa5f55"
    # mostRise = "#fce13d"
    # mostRise = "#fcffb5"
    colorSunLow = QColor("#fa5f55")
    colorSunNoon = QColor("#fcffb5")
    RSunLow = None
    GSunLow = None
    BSunLow = None
    RSunNoon = None
    GSunNoon = None
    BSunNoon = None
    RdSun = 0
    GdSun = 0
    BdSun = 0
    RSunMin = 0
    GSunMin = 0
    BSunMin = 0
    RSunMax = 0
    GSunMax = 0
    BSunMax = 0

    # Co-ordinates we last drew the sun/moon at in the day view
    lastXObject = -1.0
    lastYObject = -1.0

    # An image of the moon to use rather than a white circle
    # Load the moon image, JPEG doesn't support transparency (surrounding black
    # sky) and computing it is too much trouble, use a TIFF with transparent
    # sky area
    theMoon = QImage("799A0918T.TIFF")
    pmMoon = None

    # Time-of-day management
    todTimer = QTimer()
    todCalc = CSTODMath()
    bounceVal = -1.0
    revBounceVal = -1.0
    forceTime = False
    forceAmount = 0.005

    saveCapFilename = 0.0

    # Information to place caption text on captured images
    captionText = ""
    captionDateStamp = False
    captionTimeStamp = False
    captionTwoFourHour = False
    captionLocation = 11
    captionInsetX = 10
    captionInsetY = 6
    captionTextR = 240
    captionTextG = 240
    captionTextB = 240
    theFonts = None
    captionFontFamily = ""
    captionFontFilename = ""
    captionFontSize = 16

    # Persistent state key element constants for caption text
    kCaptionText = "Caption Text"
    kCaptionDateStamp = "Caption Date Stamp"
    kCaptionTimeStamp = "Caption Time Stamp"
    kCaptionTwoFourHour = "Caption 24 Hour"
    kCaptionLocation = "Caption Frame Location"
    kCaptionInsetX = "Caption Indent X"
    kCaptionInsetY = "Caption Indent Y"
    kCaptionTextR = "Caption Red"
    kCaptionTextG = "Caption Green"
    kCaptionTextB = "Caption Blue"
    kCaptionFontFamily = "Caption Font Family"
    kCaptionFontSize = "Caption Font Size"

    # help and about dialogs we can show or not
    help = None
    about = None

    logCategory = QLoggingCategory("csdevs")

    # FIXME: Add linkage between this window class and the frame capture class
    # that handles failures such as the video device file not existing by
    # showing a message box rather than displaying it in the debug log and
    # continuing, repeating the failure.

    def __init__(self):
        '''
        Constructor
        '''

        super(CSDevs, self).__init__()

        random.seed()

        # self.load_ui()
        self.ui = Ui_dlgCSDevs()
        self.ui.setupUi(self)

        # Setup enough information for a default QSettings to work
        QCoreApplication.setOrganizationName("DaveWasHere")
        QCoreApplication.setOrganizationDomain("mair-family.org")
        # QCoreApplication.setApplicationName("csdevs.py")
        QCoreApplication.setApplicationName("CSDevs")

        # Use a theme icon for a still frame camera as the application icon
        myIcon = QIcon.fromTheme("camera-photo")
        self.setWindowIcon(myIcon)

        self.cfgVersionOK = self.verify_version()

        # Have a help and an about dialog ready. These could be created on
        # the call to the slot that displays them. For now they don't seem like
        # much of an overhead as runtime persistent state
        self.help = dlgInfo()
        self.about = dlgAbout()

        # Set the colot infomration we'll use for drawing a circle in the "day
        # view" representing the sun through daytime
        self.__init_day_view_sun_colors()

        # Set but don't start the frame capture timer
        self.set_capture_interval(False)

        # Load tuner control settings from config
        self.reload_tune_settings()

        # Action button with the text "About". We'll use it to show the About
        # dialog.
        self.aboutButton = self.ui.buttonBox.addButton("About",
                                                       QDialogButtonBox.ActionRole)

        # Reset role button with the text Close. We'll use it's signals to
        # permit the main window to be closed with a delay if the button is
        # pressed and a capture thread is running
        self.okButton = self.ui.buttonBox.addButton("Close",
                                                    QDialogButtonBox.ResetRole)

        pbHelp = self.ui.buttonBox.button(QDialogButtonBox.Help)
        if pbHelp is not None:
            pbHelp.setDefault(True)

        # Second timer to show the time-of-day view
        self.todTimer.setInterval(60000)
        self.todTimer.stop()

        self.__fill_camera_list()

        # Get the list of font family to font filenames
        self.theFonts = CSAllFonts()

        # Load our saved configuration settings
        self.load_persistent_settings()

        # Setup signal to slot direction
        self.connect_controls()

        # Show the time-of-day view once then let the timer handle it
        self.__draw_icon_by_angle()
        self.todTimer.start()

        # Show ourselves and take focus
        self.show()
        self.activateWindow()

        # If we don't support the available configuration version then exit
        if not self.cfgVersionOK:
            QTimer.singleShot(1, self.app_rejected)

    def setVisible(self, visible):
        '''
        Over-ride setVisible to add the enabling of the monitor button on app
        load

        Parameters
        ----------
            visible: Boolean
                True if the window is being made visible, else False
        '''

        # Call our parent
        super(CSDevs, self).setVisible(visible)

        # If we are now visible and there are any cameras and monitor is not
        # enabled
        if visible and (len(self.cameras) != 0) and\
                not self.ui.pbMonitor.isEnabled():
            # Pretend signal to the slot for changing cameras in the UI, it
            # will enable the monitor button for the first camera in the list
            self.use_another_camera(self.ui.cbCameras.currentIndex())

    def __init_day_view_sun_colors(self):
        '''
        This is just to turn the content seen below into a single function call
        in the constructor
        '''

        # Split the run rise/set and noon colors into R, G, B values
        self.RSunLow = self.colorSunLow.red()
        self.GSunLow = self.colorSunLow.green()
        self.BSunLow = self.colorSunLow.blue()
        self.RSunNoon = self.colorSunNoon.red()
        self.GSunNoon = self.colorSunNoon.green()
        self.BSunNoon = self.colorSunNoon.blue()

        # ...and get the range of each
        self.RdSun = self.RSunNoon - self.RSunLow
        self.GdSun = self.GSunNoon - self.GSunLow
        self.BdSun = self.BSunNoon - self.BSunLow

        # ...and the min/max of each color element
        if self.RSunNoon > self.RSunLow:
            self.RSunMax = self.GSunNoon
            self.RSunMin = self.GSunLow
        else:
            self.RSunMax = self.RSunLow
            self.RSunMin = self.RSunNoon
        if self.GSunNoon > self.GSunLow:
            self.GSunMax = self.GSunNoon
            self.GSunMin = self.GSunLow
        else:
            self.GSunMax = self.GSunLow
            self.GSunMin = self.GSunNoon
        if self.BSunNoon > self.BSunLow:
            self.BSunMax = self.BSunNoon
            self.BSunMin = self.BSunLow
        else:
            self.BSunMax = self.BSunLow
            self.BSunMin = self.BSunLow

    def __load_video_device_list(self):
        '''
        Get a list of all video devnodes that can be opened for binary data
        read/update without caring what they are (the update would be required
        to make settings). Add the devnode and file-description for successful
        cases to a class list. We'll find the cameras from them later and
        destroy this list.
        '''

        # Start by opening all /dev/video* devices that we can
        if len(self.allDevs) == 0:
            for device in glob.glob('/dev/video*'):
                try:
                    qCDebug(self.logCategory,
                            "Trying to open {}".format(device))
                    # debug_message("Trying to open {}".format(device))
                    fd = open(device, 'rb+', buffering=0)
                    devnode = (device, fd)
                    self.allDevs.append(devnode)
                except Exception:
                    next
            if len(self.allDevs) == 0:
                qCWarning(self.logCategory, 'No video devices found.')
                # warning_message('No video devices found.')

    def __is_duplicate_camera_name(self, camName):
        '''
        Camera names aren't required to be unique, detect duplicates

        Parameters
        ----------
            camName: String
                Contains the text name of a V4L2 device

        Returns True if the name has been stored in known V4L2 device list, else
        returns False
        '''

        for aCam in self.cameras:
            curName = aCam[1].name.decode('utf-8')
            if curName == camName:
                return True
        return False

    def __unduplicate_camera_name(self, camInput):
        '''
        Force an extra alphabet character on the name of a new camera that has a
        pre-existing name. This just makes it easy to see cameras in the UI and
        doesn't matter for operating the camera

        Parameters
        ----------
            camInput: String
                The name of a V4L2 device

        Returns a modified name if the supplied name is a duplicate.
        '''

        fixer = "a"
        camName = camInput.name.decode('utf-8')
        fixedName = camName
        while self.__is_duplicate_camera_name(fixedName):
            fixedName = camName + fixer
            fixb = fixer.encode('utf-8')
            fixb[0] + 1
            fixer = fixb.decode('utf-8')
        camInput.name = fixedName.encode('utf-8')

        return camInput

    def get_camera_control_by_ID(self, fdCam, ctrlID):
        '''
        Get the control style for a single control by ID for a given camera

        Parameters
        ----------
            fdCam: Integer
                An open file descriptor for a V4L2 device
            ctrlID: Integer
                A V4L2 control supported by the device referenced by fdCam

        Returns the v4l2_queryctrl structure for the supplied control ID for the
        camera fdCam references. If the attempt to obtain the v4l2_queryctrl
        structure fails or the control is disabled, returns None
        '''

        try:
            # Create a query control object for the ID and read it
            queryctrl = v4l2_queryctrl(ctrlID)
            ioctl(fdCam, VIDIOC_QUERYCTRL, queryctrl)

            # debug_message("CONTROL {} HAS NAME {}".format(ctrlID, queryctrl.name))

            # Ignore disabled controls
            if queryctrl.flags & V4L2_CTRL_FLAG_DISABLED:
                queryctrl = None

            # if queryctrl is not None:
            #     if queryctrl.name.decode('utf-8') == "Saturation":
            #         debug_message("Got Saturation by ID {}, range is {} ~ {}".format(ctrlID, queryctrl.minimum, queryctrl.maximum))
        except (TypeError, OSError):
            # Don't parse what error occurred, just assume we can't use the
            # control ID
            queryctrl = None

        return queryctrl

    def get_current_camera_control_by_ID(self, ctrlID):
        '''
        Get the control style for a single control by ID for the currently
        active camera in an instance

        Parameters
        ----------
            ctrlID: Integer
                A V4L2 control supported by the device referenced by fdCam

        Returns the v4l2_queryctrl structure for the supplied control ID for the
        current object's open device. If there is no open device or if the
        attempt to obtain the v4l2_queryctrl structure  fails (usually due to an
        unsupported ctrlID for the open device being used as ctrlID) returns
        None
        '''

        if self.capDev is not None:
            return self.get_camera_control_by_ID(self.capDev.fileno(), ctrlID)

        return None

    def get_camera_control_value_by_ID(self, fdCam, ctrlID):
        '''
        Get the current value for a given control for a given camera.


        Parameters
        ----------
            fdCam: Integer
                An open file descriptor for a V4L2 device
            ctrlID: Integer
                A V4L2 control supported by the device referenced by fdCam

        If the control ID is supported by the device identified by fdCam it
        returns the value in the format supported for that ctrlID. If fdCam is
        invalid (not open), not a V4L2 device or is valid and open but ctrlID
        is not supported by the device returns None.
        '''

        try:
            # Create a query control object for the ID and read it
            ctrlVal = v4l2_control(ctrlID)
            ioctl(fdCam, VIDIOC_G_CTRL, ctrlVal)

            # Keep a copy so we can detect it not changing
            self.ctrlCurVal = ctrlVal
            # debug_message("Camera ctrl {} = {}".format(ctrlID, ctrlVal.value))
        except (TypeError, OSError):
            ctrlVal = None

        return ctrlVal

    def get_current_camera_control_value_by_ID(self, ctrlID):
        '''
        Get the current value for a given control for the open V4L2 device
        in-use by instance.


        Parameters
        ----------
            ctrlID: Integer
                A V4L2 control supported by the device referenced by fdCam

        If the control ID is supported by the instance's open device it returns
        returns the value in the format supported for that ctrlID. If there is
        no open device or is not a V4L2 device or is valid and open but ctrlID
        is not supported by the device, returns None.
        '''

        if self.capDev is not None:
            return self.get_camera_control_value_by_ID(self.capDev.fileno(),
                                                       ctrlID)

        return None

    def __camera_control_list(self, fdCam, minID, maxID):
        '''
        Get a V4L2 device's control list between two control IDs as an array of
        v4l2_queryctrl, in general use for whole V4L2 generic control list, the
        camera specific controls and extends the first result using the second
        as-needed.

        Parameters
        ----------
            fdCam: Integer
                A file-descriptor for an open V4L2 device
            minID: Integer
                A V4L2 control ID. Does not need to be supported by the device
                referenced by fdCam but must be less than or equal to maxID
            maxID: Integer
                A V4L2 control ID. Does not need to be supported by the device
                referenced by fdCam but must be greater than or equal to minID

        Returns an array of all v4l2_queryctrl that can be retrieved using V4L2
        for fdCam for V4L2 controls between minID and maxID inclusive.
        '''

        ctrlList = []
        if fdCam is not None:
            try:
                curID = minID
                while curID <= maxID:
                    queryctrl = self.get_camera_control_by_ID(fdCam, curID)
                    if queryctrl is not None:
                        ctrlList.append(queryctrl)
                        queryctrl = None

                    # Next ID
                    curID += 1
            except:
                # FIXME: By now no exception should be possible, handled in
                # get_camera_control_by_ID(). If not, this should be a message
                # box
                qCWarning(self.logCategory,
                          "Exception gathering camera control list")

        return ctrlList

    def get_camera_controls(self, fdCam):
        '''
        Get an array of control v4l2_queryctrl structures for all controls that
        can be referenced for a supplied V4L2 device.

        Parameters
        ----------
            fdCam: Integer
                A file-descriptor for an open V4L2 device

        Returns an array of all v4l2_queryctrl that can be retrieved using V4L2
        for fdCam. This obtains the standard and camera specific controls in the
        same array.
        '''

        ctrlList = self.__camera_control_list(fdCam,
                                              V4L2_CID_BASE,
                                              V4L2_CID_LASTP1 - 1)
        camCtrls = self.__camera_control_list(fdCam,
                                              V4L2_CID_CAMERA_CLASS_BASE,
                                              V4L2_CID_PRIVACY)

        # debug_message("V4L2 has {} controls".format(len(ctrlList)))
        # debug_message("Camera has {} controls".format(len(camCtrls)))
        ctrlList.extend(camCtrls)

        return ctrlList

    def __load_camera_list(self):
        '''
        From the list we have of all /dev/video* nodes we populated using
        __load_video_device_list() go through them finding those with an input
        and with a type that;s a V4L2 camera input. During operation the loop
        attempts to find plausible auto-focus ON/OFF switch and manual focus
        adjust controls. Once finished the list of self.allDevs that are camera
        inputs are copied to self.cameras and all items in self.allDevs are
        closed and the list is cleared.

        Format of items in self.cameras is a tuple of devnode, the v4l2_input
        struct for the device, the control list for it, the v4l2_capability
        structure for it, the discovered (guessed) manual focus adjust control
        ID for it and the discovered (guessed) auto-focus switch control ID for
        it)

        FIXME: We need a way to update entries on this list when a camera drops
        off-line and re-appears at a different devnode.
        '''

        # Go through what we found with __load_video_device_list()
        for aDev in self.allDevs:
            index = 0
            while True:
                vInput = v4l2_input(index)
                try:
                    # Find out the input tuple and only deal with cameras
                    ioctl(aDev[1], VIDIOC_ENUMINPUT, vInput)
                    if vInput.type == V4L2_INPUT_TYPE_CAMERA:
                        qCDebug(self.logCategory,
                                "Found camera named {}".format(vInput.name))
                        vCap = v4l2_capability()
                        ioctl(aDev[1], VIDIOC_QUERYCAP, vCap)
                        self.__dump_camera_capability(vCap)

                        # Get the control list
                        ctrlList = self.get_camera_controls(aDev[1])

                        # Fix duplicates, the names only matter to us
                        # vInput = self.__unduplicate_camera_name(vInput)
                        # debug_message("Fixed name {}".format(input_.name))

                        # Does the camera have autofocus and a focus control
                        # FIXME: This is very rough...
                        ctrlFocus = 0
                        ctrlAutoFocus = 0
                        for aCtrl in ctrlList:
                            ctrlName = aCtrl.name.decode('utf-8')
                            ctrlName = ctrlName.lower()
                            if ("focus" in ctrlName):
                                if ("auto" in ctrlName) and\
                                        (aCtrl.type == V4L2_CTRL_TYPE_BOOLEAN):
                                    msg = "    Auto-focus control: "
                                    msg += "({}) {}".format(aCtrl.id, ctrlName)
                                    qCDebug(self.logCategory, msg)
                                    # debug_message("Auto-focus control: ({}) {}".format(aCtrl.id, ctrlName))
                                    ctrlAutoFocus = aCtrl.id
                                if not ("auto" in ctrlName) and\
                                        (aCtrl.type == V4L2_CTRL_TYPE_INTEGER):
                                    msg = "    Focus control: "
                                    msg += "({}) {}".format(aCtrl.id, ctrlName)
                                    qCDebug(self.logCategory, msg)
                                    # debug_message("Focus control: ({}) {}".format(aCtrl.id, ctrlName))
                                    ctrlFocus = aCtrl.id

                        # Create a tuple with the devnode, the v4l2_input
                        # struct, the control list for it and it's device
                        # capabilities struct. Add the tuple to a class list
                        aCam = (aDev[0], vInput, ctrlList, vCap, ctrlFocus,
                                ctrlAutoFocus)
                        self.cameras.append(aCam)
                except (IndexError, IOError, OSError, TypeError):
                    qCWarning(self.logCategory,
                              "Error for "
                              "{}, it may not be a camera".format(aDev[0]))
                    break
                # yield input_
                index += 1

            # Don't need the open devnodes from allDevs anymore. We'll only use
            # the camera list from here
            aDev[1].close()
        # No more allDevs
        self.allDevs.clear()

    def __get_camera_display_name(self, aCam):
        '''
        Given an instance of a camera in the type expected in the self.cameras
        member generate a human readable name for the camera based on the
        devnode and device type name

        Parameters
        ----------
            aCam: A tuple of the type used for elements in self.cameras

        Returns a string with content in the format:
            <devnode name> - <device type name>
        e.g.:
            /dev/video0 - SuperCam 100

        If aCam is None returns an empty string
        '''

        if aCam is not None:
            camName = "{} - ".format(aCam[0])
            camName += aCam[3].card.decode('utf-8')
        else:
            camName = ""

        return camName

    def __fill_camera_list(self):
        '''
        Find the local devices via file-system (/dev/video*) that might be V4L2
        devices then use v4l2 API for each to identify camera inputs resulting
        in such cases existing as tuples in the array self.cameras then use that
        list to populate the Cameras drop list in the UI. For information on the
        tuple in self.cameras see __load_camera_list().

        Issues a warning message box either if no video dev nodes are V4L2
        camera inputs or if there are no video dev nodes.
        '''

        # Empty the list
        self.ui.cbCameras.clear()

        # Get all the video devices and walk through them looking for cameras
        self.__load_video_device_list()
        if len(self.allDevs) > 0:
            self.__load_camera_list()
            if len(self.cameras) > 0:
                for aCam in self.cameras:
                    # camName = aCam[1].name.decode('utf-8')
                    # camName = "{} - ".format(aCam[0])
                    # camName += aCam[3].card.decode('utf-8')
                    camName = self.__get_camera_display_name(aCam)
                    self.ui.cbCameras.addItem(camName)
            else:
                QMessageBox.warning(self, "No Cameras",
                                    "No cameras were found on your computer")
        else:
            QMessageBox.warning(self, "No video devices",
                                "No video devices were found on your computer")

    def __find_camera_by_name(self, camName):
        '''
        Given a string camera name, get it's tuple from the camera list for the
        object or return None if the name doesn't exist

        Parameters
        ----------
            camName: String
                Contains the name of a camera in the format used in the cameras
                drop list in the UI.

        Returns a tuple in the format described by __load_camera_list() if the
        supplied name exists in the object's camera list, else returns None
        '''

        for aCam in self.cameras:
            aCamName = self.__get_camera_display_name(aCam)
            if camName == aCamName:
                return aCam
        return None

    def __find_current_camera(self):
        '''
        Use the name of the current item in the UI camera drop list to get it's
        tuple from the object's camera list

        Returns a tuple in the format described by __load_camera_list() if the
        UI name exists in the object's camera list, else returns None
        '''

        camName = self.ui.cbCameras.currentText()
        return self.__find_camera_by_name(camName)

    def __devnode_for_camera_name(self, camName):
        '''
        Get the devnode name for a camera name

        Parameters
        ----------
            camName: String
                Contains the name of a camera in the format used in the cameras
                drop list in the UI.

        Return the devnode for the supplied camName if it is in the object's
        camera list or an empty string if not
        '''

        aCam = self.__find_camera_by_name(camName)
        if aCam is not None:
            theNode = aCam[0]
        else:
            theNode = ""

        return theNode

    def __devnode_for_current_camera(self):
        '''
        Returns the devnode name for the current camera name in the UI camera
        list drop list or returns an empty string if not found
        '''

        aCam = self.__find_current_camera()
        if aCam is not None:
            # Get the camera name and it's devnode
            # camName = aCam[1].name.decode('utf-8')
            # camName = self.__get_camera_display_name(aCam)
            # theNode = self.__devnode_for_camera_name(camName)
            theNode = aCam[0]
        else:
            theNode = ""

        return theNode

    def show_controls_for_camera_by_name(self, camName):
        '''
        Populate the control names combobox based on a given camera name

        Parameters
        ----------
            camName: String
                Contains a camera name in the format used in the UI cameras
                drop list
        '''

        # debug_message("Showing controls for {}".format(camName))
        # Find the camera by name
        aCam = self.__find_camera_by_name(camName)
        if aCam is not None:
            # Found, clear the current controls
            # debug_message("Found camera, clearing controls")
            self.ui.cbControls.clear()

            # we have the whole camera tuple, get the control list
            ctrlList = aCam[2]
            # debug_message("Control list has length {}".format(len(ctrlList)))
            for aCtrl in ctrlList:
                self.ui.cbControls.addItem(aCtrl.name.decode('utf-8'))

            self.ui.cbControls.setEnabled(True)

    def show_controls_for_current_camera(self):
        '''
        Populate the control names combobox based on the currently selected
        camera name in the UI
        '''

        self.show_controls_for_camera_by_name(self.ui.cbCameras.currentText())

    def __close_ready_dialogs(self):
        '''
        One implementation to end the ready about and help dialogs
        '''

        if self.help is not None:
            self.help.accept()
        if self.about is not None:
            self.about.accept()

    def __arrange_late_close(self, useAcceptClose=True):
        '''
        Use one implementation to arrange for a late close whether accepting
        or rejecting the main window
        '''

        if useAcceptClose is True:
            self.doReject = False
            self.doAccept = True
        else:
            self.doAccept = False
            self.doReject = True

        # Show something in the UI to say we noted the close but are
        # waiting for the thread to exit
        msg = "Waiting for active capture to end before closing"
        self.ui.lblStatus.setText(msg)
        self.set_capture_interval(False)

    @Slot()
    def app_accepted(self):
        '''
        Closing (accepting) the app has to delay the close if there is a capture
        thread running or close immediately if there isn't.

        If a capture thread is running this function doesn't accept the app, it
        notes the need to, shows a message as a status in the UI and returns
        without closing the app. The noted need to close is handled later when
        the running capture thread signals it's finished.
        '''

        # FIXME: Does this need to be synchronized with the capture image tick?
        if self.capThread is None:
            self.__close_ready_dialogs()
            qCDebug(self.logCategory, "Accepting main window")
            self.accept()
        else:
            self.__arrange_late_close()

    @Slot()
    def app_rejected(self):
        '''
        As with accept, closing the app via a rejected signal has to delay the
        close if there is a capture thread running or close immediately if there
        isn't.

        If a capture thread is running this function doesn't reject the app, it
        notes the need to, shows a message as a status in the UI and returns
        without closing the app. The noted need to close is handled later when
        the running capture thread signals it's finished.
        '''

        # FIXME: Does this need to be synchronized with the capture image tick?
        if self.capThread is None:
            self.__close_ready_dialogs()
            qCDebug(self.logCategory, "Rejecting main window")
            # debug_message("Rejecting main window")
            self.reject()
        else:
            self.__arrange_late_close(useAcceptClose=False)

    # Slot to handle closing later than requested because there was a capture
    # thread running when the close was requested and we had to wait for it to
    # end. It has when this signal is sent.
    @Slot()
    def do_late_close(self):
        '''
        The close method used if an attempt was made to close the app but was
        noted, though not performed, due to an active capture thread existing.

        Since it would be possible to open a child window like Settings between
        a noted need to close and the signaling of this slot then this slot
        closes all child windows that would mask an accept/reject operation on
        the main window.
        '''

        # FIXME: Does this need to be synchronized with the capture image tick?
        if self.capThread is None:
            self.__close_ready_dialogs()
            if self.doAccept is True:
                self.accept()
                self.doAccept = False
            elif self.doReject is True:
                self.reject()
                self.doReject = False

    def set_capture_interval(self, doStart=True):
        '''
        Set the capture interval for a frame capture timer object and, if
        requested, starts the timer. The UI format for the timer is in seconds
        and the timer object uses milliseconds. This function multiplies the UI
        value by 1000 and sets the capture timer object.

        Parameters
        ----------
            doStart: Boolean
                True if the timer interval should be set and timer should be
                started, False if the timer interval should be set but the timer
                not started.
        '''

        if doStart:
            # Set the timer interval and start it
            capPeriod = self.ui.sbCapPeriod.value() * 1000
            qCDebug(self.logCategory,
                    "Capture period is {}ms".format(capPeriod))
            # debug_message("Capture period is {}ms".format(capPeriod))
            self.capTimer.setInterval(capPeriod)
            self.capTimer.start()

            # Also do a one-shot to update now
            QTimer.singleShot(1, self.frame_tick)
        else:
            self.capTimer.stop()

    def set_image_quality_control_states(self, chooseEnabled=True,
                                         forceEnabled=False):
        '''
        Set the state of the image quality horizontal slider and related
        controls, the Quality: prompt label and the numeric label used to show
        the current quality value. There has to be a capture filename input for
        quality to be enabled.

        Parameters
        ----------
            chooseEnabled: Boolean
                True if the user can choose to set the image quality based on
                file format, else False
            forceEnabled: Boolean
                True if enabling of the controls should be forced rather than
                considered based on file format. This is mostly useful for
                testing when it's not possible to save in a format supporting
                automatic enablement of quality.
        '''

        # Don't enable quality if the filename isn't enabled
        if not self.ui.leCapFile.isEnabled():
            # debug_message("Capture file disabled, forcing quality off")
            chooseEnabled = False
            forceEnabled = False

        # If we can make an automatic choice
        if chooseEnabled:
            theFile = self.ui.leCapFile.text()

            # Get any extension from the filename
            dotPos = theFile.rfind('.')
            if dotPos != -1:
                fileExt = theFile[dotPos:]
            else:
                fileExt = ""

            qualFile= (fileExt.lower() in self.qualFormats)
        else:
            # Not an automatic choice, use the force enabled value
            qualFile = forceEnabled

        # Set the enabled state of the image quality controls
        self.ui.lblImgQual.setEnabled(qualFile)
        self.ui.lblImgQuality.setEnabled(qualFile)
        self.ui.hsImgQuality.setEnabled(qualFile)

        # Use stored quality value for files that support it or 100 (highest
        # quality otherwise. Assumed quality value for all file types is integer
        # percentage
        if qualFile:
            qualVal = self.imageFileQuality
        else:
            qualVal = 95

        # Set the quality value
        self.ui.hsImgQuality.setValue(qualVal)

    def use_another_camera(self, index):
        '''
        Changed camera in the UI camera list.

        Parameters
        ----------
            index: Integer
                Contains the item number of the newly selected camera
        '''

        # Enable the monitor button when a known camera is selected
        haveCam = ((index >= 0) and (index < self.ui.cbCameras.count()))
        if haveCam:
            # Close current camera and open new one
            self.__close_camera()
            self.__open_camera()
            if self.capDev is not None:
                self.reset_camera_control_monitoring()
                self.switchingDev = True

                # Switch back to not monitoring
                self.ui.pbMonitor.setEnabled(haveCam)
                self.__disable_boolean_controls()
                self.__disable_integer_control()
                self.ui.cbControls.setEnabled(False)
                self.ui.cbControls.clear()
                self.ui.leCapFile.setEnabled(False)
                self.ui.pbDlgCapFile.setEnabled(False)
                self.set_image_quality_control_states()
                self.ui.cbFormats.clear()
                self.ui.cbFormats.setEnabled(False)
                self.ui.lwFrameSizes.clear()
                self.ui.lwFrameSizes.setEnabled(False)

                # Load this camera's persistent settings
                self.load_persistent_settings_for_camera()

                # Load the tuning settings for it
                self.reload_tune_settings()

    def get_camera_formats(self, aDev):
        '''
        Get a list of camera formats (CODECs) supported by the specified source
        using v4l2

        Parameters
        ----------
            aDev: a Device object from the v4l2py.device library

        Returns an array of video capture formats, excluding H264 (MPEG-4),
        supported by aDev
        '''

        cameraFormats = []

        fmt = v4l2_fmtdesc()
        fmt.index = 0
        fmt.type = V4L2_CAP_VIDEO_CAPTURE

        while True:
            try:
                qCDebug(self.logCategory,
                        "Checking format {}".format(fmt.index))
                # debug_message("Checking format {}".format(fmt.index))
                if ioctl(aDev.fileno(), VIDIOC_ENUM_FMT, fmt) == 0:
                    pixelformat = {}
                    # save the int type ID and string plus the description
                    pixelformat['pixelformat_int'] = fmt.pixelformat
                    pixelformat['pixelformat'] = "%s%s%s%s" % \
                        (chr(fmt.pixelformat & 0xFF),
                            chr((fmt.pixelformat >> 8) & 0xFF),
                            chr((fmt.pixelformat >> 16) & 0xFF),
                            chr((fmt.pixelformat >> 24) & 0xFF))
                    if pixelformat['pixelformat'] != 'H264':
                        pixelformat['description'] = fmt.description.decode()

                        # Add all except H264 to the list we'll return
                        cameraFormats.append(pixelformat)
                        qCDebug(self.logCategory,
                                "Format: {}".format(pixelformat))
                        # debug_message("Format: {}".format(pixelformat))
            except (IOError, OSError) as e:
                # debug_message("I/O Error getting formats {}".format(e.errno))
                # debug_message("Error: {}".format(errno.errorcode[e.errno]))
                if e.errno == errno.EINVAL:
                    # debug_message("No more formats")
                    break

            fmt.index = fmt.index + 1

        return cameraFormats

    def __calcMCD(self, a, b):
        '''
        Given a value (a) and a step-size (b), return the step-size only if the
        current value is on a step ( a % b == 0). For example, __calcMCD(640, 10)
        returns 10 but the next integer value a in __calcMCD(a, 10) where the
        result is 10 is 650

        Parameters
        ----------
            a: Integer
                A control value
            b: Integer
                A step size for the control
        '''

        if b == 0:
            return a

        return self.__calcMCD(b, a % b)

    def __dump_camera_capability(self, cp):
        '''
        Debug function to dump the capabilities of the object's V4L2 video
        source.
        '''

        txt = cp.driver.decode('utf-8')
        qCDebug(self.logCategory, "      Driver: {}".format(txt))
        # debug_message("      Driver: {}".format(txt))
        txt = cp.card.decode('utf-8')
        qCDebug(self.logCategory, "        Card: {}".format(txt))
        # debug_message("        Card: {}".format(txt))
        txt = cp.bus_info.decode('utf-8')
        qCDebug(self.logCategory, "    Bus Info: {}".format(txt))
        qCDebug(self.logCategory, "     Version: {}".format(cp.version))
        qCDebug(self.logCategory, "Capabilities: {}".format(cp.capabilities))
        qCDebug(self.logCategory, " Device Caps: {}".format(cp.device_caps))
        # debug_message("    Bus Info: {}".format(txt))
        # debug_message("     Version: {}".format(cp.version))
        # debug_message("Capabilities: {}".format(cp.capabilities))
        # debug_message(" Device Caps: {}".format(cp.device_caps))

    # Get frame sizes for a given frame format for a given camera
    def get_camera_format_frame_sizes(self, aDev, cameraFormat):
        '''
        For a give camera and frame format return the supported frame sizes.

        Parameters
        ----------
            aDev: a Device object from the v4l2py.device library
                The device to get the frame sizes for
            cameraFormat: String
                Contains the name of a CODEC format for device frames

        Returns an array of arrays. If any frame sizes are supported then each
        is defined in the element of an array of all supported sizes for the
        camera and codec. The format of each item is a two dimensional array
        containing the X and Y size (in that order) of a given supported frame
        size.
        '''

        allR = []

        framesize = v4l2_frmsizeenum()
        framesize.index = 0
        framesize.pixel_format = cameraFormat['pixelformat_int']
        try:
            # cp = v4l2_capability()
            # ioctl(aDev.fileno(), VIDIOC_QUERYCAP, cp)
            while ioctl(aDev.fileno(), VIDIOC_ENUM_FRAMESIZES,
                        framesize) == 0:
                if framesize.type == V4L2_FRMSIZE_TYPE_DISCRETE:
                    allR.append([framesize.discrete.width,
                                 framesize.discrete.height])

                # for continuous and stepwise, let's just use min and
                # max they use the same structure and only return
                # one result
                elif framesize.type == V4L2_FRMSIZE_TYPE_CONTINUOUS or\
                        framesize.type == V4L2_FRMSIZE_TYPE_STEPWISE:
                    # FIXME: Do something with the unused variables
                    if hasattr(framesize.stepwise, 'max_height'):
                        max_height = framesize.stepwise.max_height
                    else:
                        max_height = 1280
                    if hasattr(framesize.stepwise, 'max_width'):
                        max_width = framesize.stepwise.max_width
                    else:
                        max_width = 1024

                    min_width = framesize.stepwise.min_width
                    min_height = framesize.stepwise.min_height

                    stepWidth = framesize.stepwise.step_width
                    stepHeight = framesize.stepwise.step_height

                    widthCounter = 1
                    heightCounter = 1

                    # ######### Low resolution #########
                    if self.__calcMCD(min_width, stepWidth) == stepWidth and\
                            self.__calcMCD(min_height, stepHeight) == stepHeight:
                        allR.append([min_width, min_height])

                    # ######### High resolution #########
                    if self.__calcMCD(max_width, stepWidth) == stepWidth and\
                            self.__calcMCD(min_height, stepHeight) == stepHeight:
                        allR.append([max_width, min_height])

                    break

                framesize.index = framesize.index + 1

        except (IOError, OSError) as e:
            # EINVAL is the ioctl's way of telling us that there are no
            # more formats, so we ignore it
            if e.errno != errno.EINVAL:
                msg = "Unable to determine supported framesizes (resolutions),"
                msg += " this may be a driver issue)."
                self._logger.error(msg)

        return allR

    # Get all needed format information for all frame sizes supported for a
    # given frame format
    def __get_camera_resolutions_by_format(self, aDev, cameraFormat):
        '''
        For a give camera and frame format return the supported frame sizes but
        cleaned of entries containing a frame rate

        Parameters
        ----------
            aDev: a Device object from the v4l2py.device library
                The device to get the frame sizes for
            cameraFormat: String
                Contains the name of a CODEC format for device frames

        Returns an array of arrays. If any frame sizes are supported then each
        is defined in the element of an array of all supported sizes for the
        camera and codec. The format of each item is a two dimensional array
        containing the X and Y size (in that order) of a given supported frame
        size.
        '''

        try:
            allR = self.get_camera_format_frame_sizes(aDev, cameraFormat)
            # self.getCameraFormatFrameRates(aDev, cameraFormat)
        except:
            qCWarning(self.logCategory,
                      "Failed to get camera frame format sizes")
            # debug_message("Failed to get camera frame format sizes")

        qCDebug(self.logCategory,
                "Preparing resolution list from {}".format(len(allR)))
        # debug_message("Preparing resolution list from {}".format(len(allR)))

        temp = []

        # clean resolutions without FPS: some broken cameras have this
        # configuration
        for resolution in allR:
            if len(resolution) >= 2:
                temp.append(resolution[0])
                temp.append(resolution[1])
            else:
                temp.append(-1)
                temp.append(-1)

        return temp

    # Open the current camera, does nothing if a camera is open so gets called
    # to make sure the camera is open when it is open
    def __open_camera(self):
        # Accessing a capDev instance with no open camera will init the object
        # which will retry an open and if the camera devnode no longer exists
        # we will init capDev for that device
        try:
            capDevIsNone = (self.capDev == None)
        except FileNotFoundError:
            title = "Camera devnode not found"
            msg = "Unable to re-open the camera devnode for the current camera."
            msg += " Capture has to be restarted. You may have to re-connect"
            msg += " the capture camera."
            QMessageBox.critical(self, title, msg)
            self.capDev = None
            self.set_capture_interval(False)

        if capDevIsNone:
            # Get the current camera's devnode
            devnode = self.__devnode_for_current_camera()
            if devnode != "":
                # A raw device for the v4l2 devnode
                # pl = pathlib.Path(devnode)
                devid = devnode[-1:]
                qCDebug(self.logCategory,
                        "Opening camera {} by ID {}".format(devnode, devid))
                # debug_message("Opening camera {} by ID {}".format(devnode, devid))
                self.capDev = Device.from_id(devid)
                # FIXME: The device might be in the closed state at this point
                if self.capDev is not None:
                    # if self.capDev.closed:
                    #     self.capDev.open()
                    qCDebug(self.logCategory, "Devnode is {}".format(devnode))
                    qCDebug(self.logCategory,
                            "Capture device is {}".format(self.capDev))
                    qCDebug(self.logCategory,
                            "Filenumber is {}".format(self.capDev.fileno()))
                    # debug_message("Devnode is {}".format(devnode))
                    # debug_message("Capture device is {}".format(self.capDev))
                    # debug_message("Filenumber is {}".format(self.capDev.fileno()))
                    self.openCount += 1
                    msg = "Opened camera: {} ".format(self.capDev.fileno())
                    msg += "({} opens)".format(self.openCount)
                    qCDebug(self.logCategory, msg)
                    # debug_message(msg)
                else:
                    qCWarning(self.logCategory,
                              "Failed to open camera {}".format(devnode))
                    # debug_message("Failed to open camera {}".format(devnode))

    def __close_camera(self):
        # If we have a v4l2 device open, close it
        if self.capDev is not None:
            if not self.capDev.closed:
                qCDebug(self.logCategory,
                        "Closing camera: {}".format(self.capDev.fileno()))
                # debug_message("Closing camera: {}".format(self.capDev.fileno()))
                self.capDev.close()
            self.capDev = None

    # Only use on failures - close and open a camera device file-handle
    def reopen_camera(self):
        self.__close_camera()
        self.__open_camera()

    @property
    def camera_is_open(self):
        return (self.capDev is not None)

    # Toggle the state of monitoring for a camera. Turning it on populates
    # the frame formats and sizes. Turning it off clears them
    # FIXME: It's possible for monitoring to be False when capturing frames.
    # There are two state changes that get the timer active, monitor and
    # capture. But what happens if monitor is used twice or on different cameras
    # before the capture is enabled? Would we take the wrong path through this
    # amd leave settings() to take the wrong path as well?
    def toggle_monitor(self, checked):
        cDev = (self.capDev is not None)
        cTimer = self.capTimer.isActive()
        qCDebug(self.logCategory,
                "toggle_monitor, have device: "
                "{}, timer running: {}".format(cDev, cTimer))
        # debug_message("toggle_monitor, have device: {}, timer running: {}".format(cDev, cTimer))

        # The frame capture timer is active if we are toggling monitoring off
        if self.capTimer.isActive():
            # Stop the timer, close the camera set the text of the button that
            # signaled us to the text "Monitor"
            self.set_capture_interval(False)
            self.monitoring = False
            self.__close_camera()

            self.ui.pbMonitor.setText("Monitor")
            msg = "Access the camera and get it's features, e.g. controls, "
            msg += "formats, etc."
            self.ui.pbMonitor.setToolTip(msg)
        else:
            # Get a device, gives us a file descriptor that lasts as long
            # as the object. Keeps the existing one if it already exists
            self.__open_camera()
            if self.capDev is not None:
                self.monitoring = True

                # Populate the control list, re-enable handling changes if
                # needed
                self.show_controls_for_current_camera()
                if self.switchingDev:
                    qCDebug(self.logCategory,
                            "Re-enabling control change handling")
                    # debug_message("Re-enabling control change handling")
                    self.switchingDev = False
                    self.changed_control(self.ui.cbControls.currentIndex())

                where = 0
                try:
                    # Get the supported camera formats and store the list in
                    # the class
                    where = 1
                    self.cameraFormats = self.get_camera_formats(self.capDev)

                    # For each supported format, get the supported resolutions
                    where = 2
                    qCDebug(self.logCategory,"Camera formats is "
                            "{}".format(self.cameraFormats))
                    # msg = "Camera formats is {}".format(self.cameraFormats)
                    # debug_message(msg)
                    for aFormat in self.cameraFormats:
                        allR = self.__get_camera_resolutions_by_format(self.capDev,
                                                                       aFormat)
                        if allR is not None:
                            aFormat['resolutions'] = allR

                    qCDebug(self.logCategory, "Formats and resolutions:")
                    qCDebug(self.logCategory, "{}".format(allR))
                    # debug_message("Formats and resolutions:")
                    # debug_message("{}".format(allR))

                    # Clear, populate and enable the format combobox
                    where = 3
                    self.ui.cbFormats.clear()
                    where = 4
                    for aFormat in self.cameraFormats:
                        self.ui.cbFormats.addItem(aFormat['description'])
                    where = 5
                    self.ui.cbFormats.setEnabled(True)

                    where = 6
                    # Enable the capture filename line edit, file dialog and
                    # image quality if needed
                    self.ui.leCapFile.setEnabled(True)
                    self.ui.pbDlgCapFile.setEnabled(True)
                    self.set_image_quality_control_states()

                    where = 9999
                except Exception as f:
                    devnode = self.__devnode_for_current_camera()
                    msg = "Failed to access"
                    msg += " previously found camera"
                    msg += " at {}".format(devnode)
                    msg += " exception {}".format(type(f))
                    msg += " at {}".format(where)
                    QMessageBox.warning(self, "Unable to access camera",
                                        msg)

    # Changed frame format (CODEC) for the current camera
    def changed_format(self, index):
        # Clear, populate and enable the frame sizes list
        self.ui.lwFrameSizes.clear()
        if self.cameraFormats is not None:
            # Find the format in our list for the camera
            curFormat = self.ui.cbFormats.currentText()
            for aFormat in self.cameraFormats:
                if aFormat['description'] == curFormat:
                    # Found, get all the resolutions
                    allR = aFormat['resolutions']
                    qCDebug(self.logCategory, "changed_format, "
                            "res={}".format(allR))
                    # debug_message("changed_format, res={}".format(allR))
                    iRes = 0
                    # Walk them and add each to the UI list control
                    lastRes = len(allR) - 1
                    while iRes < lastRes:
                        # Each entry in allR is two elements (width, height)
                        # Build the user view with an x between them and add it
                        newRes = "{}".format(allR[iRes])
                        newRes += "x{}".format(allR[iRes + 1])
                        self.ui.lwFrameSizes.addItem(newRes)
                        # Move on two elements at a time
                        iRes += 2
        self.ui.lwFrameSizes.setEnabled(True)

    # Given a frame size in the format <width>x<height> save the width and
    # height in the class
    def record_frame_size(self, frameSize):
        xPos = frameSize.find('x')
        if (xPos) > 0 and (xPos < (len(frameSize) - 1)):
            self.width = int(frameSize[:xPos])
            self.height = int(frameSize[xPos + 1:])
        else:
            # Unrecognized, assume 640x480
            self.width = 640
            self.height = 480

    # Get a frame format description from the frame format's data
    def get_format_by_description(self, description):
        for aFormat in self.cameraFormats:
            aDescription = aFormat['description']
            if aDescription == description:
                return aFormat

        return None

    def __set_codec_and_frame_size(self):
        # We have to have an open camera
        if self.capDev is not None:
            # debug_message("Setting codec and frame size")
            # Get the format description, pixel format and integer code
            fmtDescription = self.ui.cbFormats.currentText()
            # debug_message("Frame format is {}".format(fmtDescription))
            curFmt = self.get_format_by_description(fmtDescription)
            if curFmt is not None:
                # Set the codec
                pixFmt = curFmt['pixelformat_int']
                # debug_message("Pixel format is {}".format(pixFmt))

                try:
                    fmt = v4l2_format()
                    fmt.type = V4L2_BUF_TYPE_VIDEO_CAPTURE
                    ioctl(self.capDev.fileno(), VIDIOC_G_FMT, fmt)
                    # msg = "HOWDY: {}".format(type(fmt.fmt.pix))
                    # debug_message(msg)
                    # msg = "HOWDY: {}".format(fmt.fmt.pix)
                    # debug_message(msg)
                    # msg = "HOWDY  width = {}".format(fmt.fmt.pix.width)
                    # debug_message(msg)
                    # msg = "HOWDY height = {}".format(fmt.fmt.pix.height)
                    # debug_message(msg)
                    # msg = "HOWDY  codec = {}".format(fmt.fmt.pix.pixelformat)
                    # debug_message(msg)
                    # Only set it if something is changing
                    if (fmt.fmt.pix.width != self.width) or\
                            (fmt.fmt.pix.height != self.height) or\
                            (fmt.fmt.pix.pixelformat != pixFmt):
                        fmt.fmt.pix.width = self.width
                        fmt.fmt.pix.height = self.height
                        fmt.fmt.pix.pixelformat = pixFmt
                        # msg = "HOWDY  width = {}".format(fmt.fmt.pix.width)
                        # debug_message(msg)
                        # msg = "HOWDY height = {}".format(fmt.fmt.pix.height)
                        # debug_message(msg)
                        # msg = "HOWDY  "
                        # msg += "codec = {}".format(fmt.fmt.pix.pixelformat)
                        # debug_message()
                        ioctl(self.capDev.fileno(), VIDIOC_S_FMT, fmt)
                        # debug_message("Set current codec and frame size")
                except (TypeError, OSError):
                    qCWarning(self.logCategory, "Failed to set codec")
                    # debug_message("Failed to set codec")

    # A frame size has been selected for the selected format for a monitored
    # camera. This starts frame capture
    def frame_size_selected(self, item):
        # If we have a capture file displayed
        theFile = self.ui.leCapFile.text()
        if theFile != "":
            # Stop any timer and close current devices
            self.set_capture_interval(False)
            self.__close_camera()

            try:
                # Get new v4l2 devices
                self.__open_camera()
                qCDebug(self.logCategory, "Camera opened for "
                        "frame size selection")
                # msg = "Camera opened for frame size selection"
                # debug_message(msg)

                # Use the UI to save the frame size in the class
                # Get the new frame size and split into width and height
                self.record_frame_size(item.text())

                # Set the codec and frame size based on the UI and class
                self.__set_codec_and_frame_size()
                # debug_message("CODEC and frame size set")

                # Set and start the timer
                self.set_capture_interval()

                # Use the monitor button to stop capture, change it's
                # text accordingly
                if self.capTimer.isActive():
                    self.ui.pbMonitor.setText("Stop")
                    msg = "Click to stop image capture"
                    self.ui.pbMonitor.setToolTip(msg)
            except Exception as e:
                qCWarning(self.logCategory, "Exception in "
                          "frame size select: {}".format(type(e)))
                # msg = "Exception in frame size select: {}".format(type(e))
                # debug_message(msg)
                self.__close_camera()

    # Create a setting when we have no user input, use the default or the
    # mid-point if there is no default
    def __create_best_fit_control_setting_by_name(self, ctrlName, iLimit=None):
        # Don't change any current setting
        aCtrl = self.__setting_control_by_name(ctrlName)
        if aCtrl is None:
            # If we are not currently setting it, get the control details
            # and use the middle value
            qCtrl = self.__current_camera_control_by_name(ctrlName)
            if qCtrl is not None:
                # FIXME: Only integer for tuning? We probably don't want to tune
                # through multi-state controls (menu of options) but something
                # that can be on/off (two-state boolean) or floating point might
                # be useful
                if qCtrl.type == V4L2_CTRL_TYPE_INTEGER:
                    try:
                        prefCtrl = qCtrl.default_value
                    except:
                        rCtrl = qCtrl.maximum - qCtrl.minimum
                        prefCtrl = int(qCtrl.minimum + (rCtrl / 2.0))

                    if iLimit is not None:
                        if prefCtrl > iLimit:
                            prefCtrl = iLimit
                    self.add_control_setting_by_ID(qCtrl.id, prefCtrl)

    # FIXME: These frame/control value/fraction/range translation functions
    # look wrong when they don't treat range as max - min + 1. IOW, if there are
    # the values 0...255 they have a range of 256 values. That's max - min + 1
    # rather than max - min. But it doesn't appear to matter. The reason is that
    # there are max - min + 1 values in-use regardles of the range and the
    # difference between any consecutive pair is either 1 / (max - min + 1) or
    # 1 / (max - min).
    # But, if you consider the translation from value to fraction of range back
    # to value it's seen that the one using the range of (max - min) has
    # fractions between 0.0 and 1.0 in steps of 1 / (max - min). And the one
    # using the range of (max - min + 1) has fractions between 0.0 and
    # (max - min) / (max - min + 1) in steps of 1 / (max - min + 1). These are
    # equivalent sets for any max/min values except equal ones (zero range).
    # To put it numerically:
    # Using a range of integer values 7...326
    # max = 326
    # min = 7
    # max - min = 319 (Range A)
    # max - min + 1 = 320 (Range B)
    # Step A = 1 / 319
    # Step B = 1 / 320
    # Any value <n> has:
    # Fraction A: (<n> - min) / Step A
    # Fraction B: (<n> - min) / Step B
    # There are 320 values in both ranges
    # There are 319 steps in both ranges
    # Therefore:
    # Range A iterates in 319 steps of 1/319
    # Range B iterates in 319 steps of 1/320
    # Both ranges begin at zero
    # Range A ends at 319/319
    # Range B ends at 319/320
    #
    # Adjust the fraction value for any reason, such as change of brightness
    #
    # Convert back to property value is as follows:
    # For Range A: multiply fraction by 319 and add min
    # For range B: multiple fraction by 320 and add min
    #
    # Property to fraction and back are equivalent for any value in each range.
    #
    # Even though the actual fraction values are slightly different in each
    # range simple algebra is also equivalent in each range, e.g. multiplying
    # fraction in each range for a single property value by a constant to change
    # a property like brightness in each range converts back to the same
    # result property value from both ranges.

    # Take a control or frame minimum and current value then translate the
    # value to zero-based in property range or from zero-base to within property
    # range (reverse) based on the state of toZero (set False to convert from
    # zero minimum based value back to fMin minimum based value)
    def __property_zero_base(self, fValue, fMin, toZero=True):
        # Can't convert a value smaller than minimum to zero-based
        if (toZero is True) and (fValue < fMin):
            raise ValueError

        if toZero is True:
            fValue -= fMin
        else:
            fValue += fMin

        return 1.0 * fValue

    # Given a frame property or control minimum, maximum value return the
    # property's value range
    def __property_range(self, fMin, fMax):
        if fMin > fMax:
            # Negative range
            return 1.0 * (fMin - fMax)

        return 1.0 * (fMax - fMin)

    # Given a frame or control minimum, maximum and current value return the
    # value as a fraction of the property range
    def __property_value_as_fraction(self, fValue, fMin, fMax):
        fRange = self.__property_range(fMin, fMax)

        # Don't allow zero range or value greater than max (min was checked in
        # __property_zero_base(). Result is a value between 0.0 and 1.0 or an
        # exception
        if (fRange == 0.0) or (fValue > fMax):
            raise ValueError

        # Re-align supplied value to zero at suplied minimum
        zValue = self.__property_zero_base(fValue, fMin)

        # Return value as a fraction (decimal) of range
        return zValue / fRange

    # Given a fractional value within a minimum to maximum range return
    # the value representing that fraction of the range. Returns a float, caller
    # should choose to int or round for preferred integer value
    def __property_fraction_as_value(self, fFrac, fMin, fMax):
        # Only works for fractions between 0.0 and 1.0 (would be between
        # fMin..fMax as a value)
        if (fFrac < 0.0) or (fFrac > 1.0):
            raise ValueError

        fRange = self.__property_range(fMin, fMax)
        zValue = fFrac * fRange
        fValue = self.__property_zero_base(zValue, fMin, False)

        return fValue

    # Given a frame or control value and range for it limit the value to the
    # range
    def __limit_property_value_to_range(self, fValue, fMin, fMax):
        if fValue < fMin:
            fValue = fMin
        elif fValue > fMax:
            fValue = fMax

        return fValue

    # Caller is expected to supply values in the range 0.0 through 1.0 that
    # are zero based fractions of the value in the property's range
    # FIXME: Control deltas rarely reach +/-1
    def __compute_applied_deltaE(self, frmFrac, tgtFrac, ctrlFrac,
                                deltaPower=1.5):
        # If the control is not at the limits the frame property it affects will
        # not be zero or one so apply the necessary frame target to the control
        # fraction
        if (ctrlFrac >= 0.0) and (ctrlFrac <= 1.0):
            # Use the ratio between frame target and frame property multiplied
            # by the ctrl property to obtain a proposed control property that
            # obtains the frame target (assuming control has linear effect on
            # frame)
            ctrlTgtFrac = ctrlFrac
            #* tgtFrac / frmFrac

            # If the control is not at the top or bottom of the range
            if (ctrlFrac > 0.0) and (ctrlFrac < 1.0):
                # Is the control closer to the top of the range but not at it
                if ctrlFrac >= 0.5:
                    useLimit = 1.0
                # Is the control closer to the bottom of the range but not at it
                # FIXME: The condition is implied by the if statement above
                # elif ctrlFrac < 0.5:
                else:
                    useLimit = 0.0
                ctrlToLimit = useLimit - ctrlFrac
                remFrame = useLimit - frmFrac
                tgtToLimit = useLimit - tgtFrac
                dFrame = remFrame - tgtToLimit
                if remFrame != 0.0:
                    dfFrame = dFrame / remFrame
                else:
                    # Nothing remaining in the frame range, don't divide by zero
                    dfFrame = 1.0 * dFrame
                dCtrl = dfFrame * ctrlToLimit
                ctrlTgtFrac = ctrlFrac + dCtrl
            else:
                # We can only use the whole range
                if frmFrac != 0.0:
                    ctrlTgtFrac = ctrlFrac * tgtFrac / frmFrac
                else:
                    # Frame fraction is zero, don't divide by it, just use the
                    # control target as a ratio to apply to the control
                    ctrlTgtFrac = ctrlFrac * tgtFrac
                dCtrl = -1.0
            if (ctrlTgtFrac < 0.0) or (ctrlTgtFrac > 1.0):
                qCDebug(self.logCategory,
                        "Messed "
                        "control delta: {}/{}".format(ctrlTgtFrac, dCtrl))
                # debug_message("Messed control delta: {}/{}".format(ctrlTgtFrac, dCtrl))

            # a) Difference to white must be 1.0 - ctrlFrac
            # b) Remaining brightness must be 1.0 - frmFrac
            # a) and b) are equivalent ranges
            # when increasing to target, ctrlFrac to Target is the required
            # fraction of a) to apply to b)
            # if tgtFrac > frmFrac:
            #     ctrlToHigh = 1.0 - ctrlFrac
            #     remFrame = 1.0 - frmFrac
            #     tgtToHigh = 1.0 - tgtFrac
            #     dFrame = remFrame - tgtToHigh
            #     dfFrame = dFrame / remFrame
            #     dCtrl = dfFrame * ctrlToHigh
            #     ctrlTgtFrac = ctrlFrac + dCtrl
            #     debug_message("^: {}, {}, {}, {}, {}, {}, {}".format(ctrlToHigh, remFrame, tgtToHigh, dFrame, dfFrame, dCtrl, ctrlTgtFrac))
            #     if ctrlTgtFrac > 1.0:
            #         debug_message("Messed positive control delta: {}".format(dCtrl))
            # elif tgtFrac < frmFrac:
            #     ctrlToLow = 0.0 - ctrlFrac
            #     remFrame = 0.0 - frmFrac
            #     tgtToLow = 0.0 - tgtFrac
            #     dFrame = remFrame - tgtToLow
            #     dfFrame = dFrame / remFrame
            #     dCtrl = dfFrame * ctrlToLow
            #     ctrlTgtFrac = ctrlFrac + dCtrl
            #     debug_message("v: {}, {}, {}, {}, {}, {}, {}".format(ctrlToLow, remFrame, tgtToLow, dFrame, dfFrame, dCtrl, ctrlTgtFrac))
            #     if ctrlTgtFrac < 0.0:
            #         debug_message("Messed negative control delta: {}".format(dCtrl))

            # If we will exceed 1 then the ctrlTgtFrac is no use, the control is
            # probably over 0.5 and the ratio of target and frame is > 1. just
            # use half the remaining control range to 1!
            # FIXME: The fact that this is required for utility means the
            # ratio equation above is invalid
            if ctrlTgtFrac > 1.0:
                ctrlTgtFrac = ctrlFrac + (1.0 - ctrlFrac) / 2.0
            elif ctrlTgtFrac < 0.0:
                ctrlTgtFrac = ctrlFrac - ctrlFrac / 2.0
        # elif (ctrlFrac == 0.0) or (ctrlFrac == 1.0):
        #     # No resolution in control data so just use frame ratio in the
        #     # control, operation will migrate to using the computing path of
        #     # this conditional as the control adjusts the frame
        #     ctrlTgtFrac = tgtFrac
        else:
            raise ValueError

        # Get the required delta but accuracy is not precise and outdoor light
        # will not be constant between frames so limit the size we return
        # without making the steps linear and don't lose the sign of the
        # required step
        dTgt = ctrlTgtFrac - ctrlFrac
        if dTgt >= 0:
            dSign = 1.0
        else:
            dSign = -1.0

        dCtrl = dSign * pow(abs(dTgt), deltaPower)

        # debug_message("  Frame: {}/{}".format(frameFrac, targetFrac))
        # debug_message("Control: {}({})/{}".format(ctrlFrac, ctrlVal, ctrlTgtFrac))
        # debug_message("Using control delta: {}".format(dCtrl))

        return dCtrl

    def is_frac(self, aValue):
        return (aValue >= 0.0) and (aValue <= 1.0)

    def __compute_applied_delta(self, frmFrac, tgtFrac, ctrlFrac,
                                 deltaPower=1.5):
        '''
        Compute a fractional delta to apply to a control that affects an image
        property if we are given the current fractional value of the property,
        the target fractional value of the property, the current fractional
        value of the control and a power to use for damping the computed delta
        in case the image property doesn't change in a linear reaction to the
        control's changes.

        Parameters
        ----------
            frmFrac: Number between 0.0 and 1.0
                The current fraction of the property range that is present in
                the frame. The identity of the frame property and the control
                don't need to be known. It might be 0.5 and the property might
                be brightness, or something else.
            tgtFrac: Number between 0.0 and 1.0
                The target fraction of the property range desired for the frame.
            ctrlFrac: Number between 0.0 and 1.0
                The target fraction of the value range currently set for a
                control that adjusts whatever property is being considered.
            deltaPower: Floating point number
                A power to raise the computed delta to before returning it. See
                the note at the end of this description.

        Returns a floating point number between -1.0 and 1.0 that is the
        recommeded delta to apply to the control used for ctrlFrac in order to
        adjust the property represented in frmFrac towards the required target.

        deltaPower can be used to "adjust towards" the required value assuming
        it's not possible to establish an exact relationship between control
        values and frame property values. A deltaPower of 1.0 assumes that the
        relationship exists, any other value used should be a number greater
        than but close to 1.0, e.g. 1.1 or 1.2 in daytime, 1.05 or 1.15 in
        nighttime. However, the behavior will be dependent on the video source
        and control being adjusted. For example, the Gamma control should
        probably be used with a higher power to adjust frame brightness than the
        Brightness control should because the Gamma control will also adjust
        contrast and saturation at the same time and the higher power results in
        a less aggressive adjustment. The effective range of deltaPower is very
        small, for controls on most video sources values as high as 1.5 will
        tend to reach the limit of floating point resolution and the function
        will return no control delta before the required frame property value is
        reached.
        '''

        if self.is_frac(frmFrac) and self.is_frac(tgtFrac) and\
                self.is_frac(ctrlFrac):
            # debug_message("-- Adjust frame from {} to {} with control {} ^{}".format(frmFrac, tgtFrac, ctrlFrac, deltaPower))

            frmDeltaFrac = tgtFrac - frmFrac
            # debug_message("-- Frame delta is {}".format(frmDeltaFrac))

            if frmDeltaFrac >= 0:
                dSign = 1.0
            else:
                dSign = -1.0
            dCtrlFrac = dSign * pow(abs(frmDeltaFrac), deltaPower)
            # debug_message("-- Control delta frac is {}".format(dCtrlFrac))
            newCtrlFrac = ctrlFrac + dCtrlFrac
            if not self.is_frac(abs(newCtrlFrac)):
                qCDebug(self.logCategory, "--| Messed "
                        "control delta: {}/{}".format(dCtrlFrac, newCtrlFrac))
                # debug_message("--| Messed control delta: {}/{}".format(dCtrlFrac,
                #                                                        newCtrlFrac))

                # If we will exceed 1 then the ctrlTgtFrac is no use, the
                # control is probably over 0.5 and the ratio of target and frame
                # is > 1. just use a control delta that's half the remaining
                # control range to 1!
                # FIXME: If this is required for utility it means the ratio
                # equation above is invalid
                if newCtrlFrac > 1.0:
                   dCtrlFrac = (1.0 - ctrlFrac) / 2.0
                   # debug_message("--| Forcing control target frac {}".format(dCtrlFrac))
                # If we will exceed 0 (negative) then the ctrlTgtFract is also
                # no use, the control is probably close to zero and the frame
                # needs a larger negative delta. Just use a control delta that's
                # half the remaining control range to zero!
                elif newCtrlFrac < 0.0:
                   dCtrlFrac = ctrlFrac / 2.0
                   # debug_message("--| Forcing control target frac {}".format(dCtrlFrac))
        else:
           raise ValueError

        return dCtrlFrac

    # Pick a power to use when computing a delta for a control.
    #
    # Consider any property of the frame as a fraction between 0 and 1, e.g.
    # brightness is none (black) at the fraction zero and whiteout at the
    # fraction 1. Consider the same applied to any control range. The brightness
    # control might have a range from 1 to 100 but divide any control value
    # by the range (100) and the control has the same style as the frame
    # property, a value between zero (minimum control) and 1 (maximum control).
    # The idea is to take the required change in the frame property in the range
    # 0 to 1 and change the control property by a similar amount. The truth is
    # that there isn't a guaranteed linear relationship between control values
    # and their effect on the frame, but it is better to increase the brightness
    # control by about a quarter (0.25) when the frame brightness needs to be
    # increased by a quarter (0.25). This is the delta, it can be negative one
    # quarter (-0.25) to darken the frame and reduce the brightness control by a
    # quarter. It applies to all controls and properties, not just frame
    # brightness and the brightness control.
    #
    # There's little point in assuming the required frame delta has a linear
    # relationship with control adjustment so it is best not to apply a control
    # "too hard". In order to dampen the effect of the control having a
    # non-linear effect on the frame property the required frame delta is raised
    # to a power, close to but slightly greater than 1. This makes the the frame
    # delta slightly smaller than needed for a "perfect" adjustment. This
    # smaller value is used as the control delta and added to the current
    # control fraction. This new control fraction is converted back into the
    # control range and that is used as the new control value.  Raising the
    # required frame change to a power close to but greater than 1 provides some
    # control when close to the target but allows stronger changes when far from
    # the target. Besides, especially for outside views, the light will not be
    # constant and there will be seconds between frames. So applying the
    # required change from the last frame "perfectly" to the next frame is
    # probably worthless.
    #
    # The following is an example:
    #
    # Assume the frame brightness can be between 0 and 255, is currently 20 and
    # the preferred brightness is about 160. So, the frame brightness range is
    # 256 and the current brightness of 20 is the fraction 0.078125. The target
    # brightness of 160 is the fraction 0.625. We need to increase the
    # brightness fraction by 0.546875. The brightness control value can be any
    # integer between 1 and 100 (a range of 100) and is currently the value 15.
    # The brightness control fraction is 0.15 and we want to increase brightness
    # by 0.546875. If we took this fraction of the control range we'd get
    # 54.6875 and if we added that to the current control value of 15 we'd get
    # 69.6875 and use the integer part to change the control to 69 hoping to
    # get the same increase in the frame brightness as we applied to the
    # control.
    #
    # However, the effect of the control on the frame property isn't that linear
    # so, to avoid overshooting around the required value due to a non-linear
    # relationship between control value and frame property value we raise the
    # required frame delta by a small power greater than but close to 1, e.g.
    # 1.1 and the equation becomes:
    #
    # Frame delta: 160 - 20 = 140
    # Frame delta fraction: 140 / 256 = 0.546875
    # Control delta fraction: 0.546875^1.1 = 0.514845448
    # Control delta is slightly lower than frame delta
    # New control value: 15 + 0.514845448 * 100 = 66
    #
    # Be aware of the behavior of other power values:
    #
    # 1         Control delta follows same line as frame delta (moves directly
    #           to the assumed required value of 69 in one step for the example
    #           above.
    # > 1       Effect on control delta of a given frame delta is reduced
    #           but follows a curve with larger control delta for larger frame
    #           delta. Control delta gets less effective the higher the power
    #           gets above 1. In the example above using the power 1.1 moved the
    #           control value to 66 when the literal target was 69. It would
    #           be expected to take 4 iterations to reach the target frame
    #           property value.
    #           Using the power 2 we would get a first new control value of 44
    #           and probably only be able to reach a target frame property value
    #           of 150 (instead of 160) due to floating point resolution.
    # >0..<1    Larger control delta from smaller frame delta. We'd overshoot
    #           the target on the firt pass.
    # 0         We'd add the entire control range to the current control range
    #           on every pass and limit control would set us at the high limit
    #           on the first pass
    # <0        Very large control delta from smaller frame delta, we'd have
    #           math failures on the second pass.
    #
    # The best option is values greater than but close to 1, e.g. between 1.1
    # and 1.25 because control adjustment is always restrained but more-so when
    # control is close to useful target and control adjustment becomes less
    # restrained when control is far from useful target. The larger the power
    # > 1 causes more restraint for small required changes quickly reaching the
    # limit of floating point resolution but the restraint is more rapidly
    # removed as required change increases.
    #
    # The behavior at night needs to be less aggressive than it can be at day
    # because there is so little of any property available in the view that
    # required frame adjustments are frequently high and it only takes something
    # like a car headlight in the view to break the model.
    #
    # There also needs to be a choice of two powers that can operate based on
    # the property/control combination and as-desired by the caller. For
    # example, the Brightness control adjusts the frame Brightness but doesn't
    # have a lot of effect on the frame's Contrast or Saturation other than at
    # extremes. However, the Gamma control affects Brightness, Contrast and
    # Saturation at the same time so changes to Brightness via the Brightness
    # control can safely use a lower power than changes to Brightness via the
    # Gamma control. The slowPow value is for cases like the Gamma control used
    # to adjust any frame property and the usePreferred argument when true
    # forces the use of fastPow regardless of the property/control combination.
    #
    # FIXME: This can be made configuration based rather than code constants.
    # Perhaps as part of the settings for each control in the property it is to
    # be used to adjust.
    def __get_control_tune_power(self, imgProp, ctrlName, usePreferred=True):
        if self.lastTOD == self.kTuneDay:
            fastPow = 1.05
            slowPow = 1.15
        else:
            # Tune more carefully at night
            # fastPow = 1.25
            # slowPow = 1.5
            fastPow = 1.1
            slowPow = 1.2

        if  (imgProp == "Brightness") and\
                ((ctrlName == imgProp) or (ctrlName == "Gain")) and\
                (usePreferred is True):
            # More effective deltas when control is directly for property
            usePower = fastPow
        elif  (imgProp == "Contrast") and (ctrlName == imgProp) and\
                (usePreferred is True):
            # More effective deltas when control is directly for property
            usePower = fastPow
        elif  (imgProp == "Saturation") and (ctrlName == imgProp) and\
                (usePreferred is True):
            # More effective deltas when control is directly for property
            usePower = fastPow
        else:
            usePower = slowPow

        # debug_message("Tuning Power: {}".format(usePower))
        return usePower

    def __get_whole_control_delta(self, ctrlName):
        ctrlRange = 0
        qCtrl = self.__current_camera_control_by_name(ctrlName)
        if qCtrl is not None:
            # FIXME: Only integer for tuning? We probably don't want to tune
            # through multi-state controls (menu of options) but something
            # that can be on/off (two-state boolean) or floating point might
            # be useful
            if (qCtrl.type == V4L2_CTRL_TYPE_INTEGER) or\
                    (qCtrl.type == V4L2_CTRL_TYPE_INTEGER64):
                ctrlRange = qCtrl.maximum - qCtrl.minimum

        return ctrlRange

    # Given a control ID, frame, target and range of a property, indication the
    # control has negative effect on property, control limits and image
    # property being adjusted...then compute and return a new value for the
    # property or None if no change is required.
    # FIXME: On first pass this doesn't use the current control value which
    # always seems to be assumed somewhere like the mid-point of range
    def __tune_control_value_by_ID(self, ctrlID, vFrame, tFrame, rFrame,
                                   rCtrlForce=-1, dNeg=False,
                                   forceMin=None, forceMax=None, imgProp=None):
        # Get the control information and settings
        aCtrl = self.__setting_control_by_ID(ctrlID)
        qCtrl = self.get_current_camera_control_by_ID(ctrlID)

        # If it is a real camera control and we are setting it
        if (aCtrl is not None) and (qCtrl is not None):
            # FIXME: Only integer for tuning?
            if qCtrl.type == V4L2_CTRL_TYPE_INTEGER:
                ctrlName = qCtrl.name.decode('utf-8')

                # So we have:
                #   Last frame value (vFrame): <n>
                #   Target frame value (tFrame): in range <min>-<max>
                #   Frame range (rFrame): <max> - <min>
                #   control value (vCtrl): in aCtrl
                #   control range (rCtrl): qCtrl
                # Compute estimated new control value as follows:
                #   Frame Value Fraction of range (vFrameFrac) = vFrame / rFrame
                #   Frame Target Fraction of range (tFrameFrac) = tFrame / rframe
                #   Frame Delta Fraction of range (dFameFrac) = tFrameFrac - vFrameFrac
                #   Control Value Fraction of range (ctrlFrac) = vCtrl / rCtrl
                #   Control Delta Fraction of range (dCtrlFrac) = ctrlFrac + dFrameFrac
                #   New control value (vCtrlNew) = dCtrlFrac * rCtrl
                #

                # Frame value and target values as fractions of property range
                # limit them to property range delta from frame value to target
                # (as a fraction of property range)
                try:
                    valFrac = self.__property_value_as_fraction(vFrame, 1.0,
                                                                rFrame)
                except ValueError:
                    if vFrame < 1.0:
                        valFrac = 0.0
                    elif vFrame > rFrame:
                        valFrac = 1.0
                    else:
                        raise
                try:
                    tgtFrac = self.__property_value_as_fraction(tFrame, 1.0,
                                                                rFrame)
                except ValueError:
                    if tFrame < 1.0:
                        tgtFrac = 0.0
                    elif tFrame > rFrame:
                        tgtFrac = 1.0
                    else:
                        raise
                dFrameFrac = tgtFrac - valFrac

                # Get the control value, range and offset of minimum from zero.
                # Set forced min/max if needed
                minCtrl = 1.0 * qCtrl.minimum
                maxCtrl = 1.0 * qCtrl.maximum
                if forceMin is not None:
                    minCtrl = self.__limit_property_value_to_range(forceMin,
                                                                   minCtrl,
                                                                   maxCtrl)
                if forceMax is not None:
                    maxCtrl = self.__limit_property_value_to_range(forceMax,
                                                                   minCtrl,
                                                                   maxCtrl)

                # if rCtrlForce <= 1:
                #     rCtrl = maxCtrl - minCtrl + 1.0
                # else:
                if rCtrlForce >= 0:
                    # FIXME: Remove this and only use forceMin, forceMax
                    msg = "Don't use forced range for {} ".format(ctrlName)
                    msg += "({}, {}-{})".format(rCtrlForce, minCtrl, maxCtrl)
                    qCDebug(self.logCategory, msg)
                    # debug_message(msg)
                    # rCtrl = rCtrlForce * 1.0

                # Get one control step as a fraction of control range
                if minCtrl == maxCtrl:
                    minCtrlDelta = 0.0
                    dCtrlLimit = 0;
                else:
                    if minCtrl < maxCtrl:
                        ctrlRange = maxCtrl- minCtrl
                    else:
                        ctrlRange = minCtrl - maxCtrl
                    minCtrlDelta = 1.0 / ctrlRange

                    # Also get a percentage control delta limit
                    if ctrlRange > 15:
                        # Cheat for ranges > 100
                        if ctrlRange <= 100:
                            # dCtrlLimit = int(ctrlRange * 0.15)
                            dCtrlLimit = int(ctrlRange * random.uniform(0.01, 0.15))
                        else:
                            dCtrlLimit = random.randint(1, 15)
                    else:
                        dCtrlLimit = 1;

                # Use the current control value and get it as a fraction of the
                # control range
                ivCtrl = int(aCtrl.value)
                vCtrl = 1.0 * aCtrl.value
                try:
                    ctrlFrac = self.__property_value_as_fraction(vCtrl, minCtrl,
                                                                 maxCtrl)
                except ValueError:
                    if vCtrl < minCtrl:
                        ctrlFrac = 0.0
                    elif vCtrl > maxCtrl:
                        ctrlFrac = 1.0
                    else:
                        raise

                # Convert the delta needed as a fraction of the frame property
                # into a fraction of the control range on a curve that makes
                # small adjustments when close to the target, large adjustments
                # when far from target.

                # Get the power to raise the required delta to. When the frame
                # property is outside the property range use the preferred
                # power for the property and control via the
                rMin = self.__preferred_target_by_property(imgProp, False)
                rMax = self.__preferred_target_by_property(imgProp, True)
                preferredPower = ((vFrame < rMin) or (vFrame > rMax))
                usePower = self.__get_control_tune_power(imgProp, ctrlName,
                                                         preferredPower)

                # Use it to compute a delta to apply as a fraction of the
                # control range
                expFrac = self.__compute_applied_delta(valFrac, tgtFrac,
                                                       ctrlFrac,
                                                       deltaPower=usePower)

                # We now have frame value, adjustment and control value in the
                # same domain (a fraction between zero and one) via dFrameFrac,
                # expFrac and ctrlFrac respectively

                # Only bother tuning if the required frame delta is more than
                # 10% of a single control delta
                # FIXME: Is it worth testing if dFrameFrac < minCtrlDelta as
                # well as the 10% case and for the other 90% adjust the control
                # by 1 in the correct direction just to have minimal volatility.
                if abs(dFrameFrac) <= (minCtrlDelta / 10.0):
                    msg = "Discarding {}/{} ".format(imgProp, ctrlName)
                    msg += "frame delta {:.6f} < ".format(dFrameFrac)
                    msg += "{:.6f} minimum control delta, ".format(minCtrlDelta)
                    msg += "control fraction is {:.6f}".format(dFrameFrac)
                    qCDebug(self.logCategory, msg)
                    # debug_message(msg)
                    dFrameFrac = 0.0
                    expFrac = 0.0

                # Apply the computed control delta fraction in the correct
                # direction. dNeg is True if positive control adjustment has a
                # negative effect on the frame property. expFrac can be + or -
                # regardless of dNeg
                if dFrameFrac != 0.0:
                    if dNeg:
                        dCtrlFrac = ctrlFrac - expFrac
                    else:
                        dCtrlFrac = ctrlFrac + expFrac

                    # New control value from new fraction
                    try:
                        vCtrlNew = self.__property_fraction_as_value(dCtrlFrac,
                                                                     minCtrl,
                                                                     maxCtrl)
                    except ValueError:
                        if dCtrlFrac < 0.0:
                            vCtrlNew = minCtrl
                        elif dCtrlFrac > 1.0:
                            vCtrlNew = maxCtrl
                        else:
                            raise

                    # Limit the delta to avoid extreme adjustments
                    dCtrlNew = abs(vCtrlNew - aCtrl.value)
                    if dCtrlNew > dCtrlLimit:
                        if vCtrlNew >= aCtrl.value:
                            vCtrlNew = int(aCtrl.value + dCtrlLimit)
                        else:
                            vCtrlNew = int(aCtrl.value - dCtrlLimit)

                    if self.tuneMathLogging is True:
                        msg = "Tune (ratios) {}/{} ".format(imgProp, ctrlName)
                        msg += "{:.6f}: ".format(ctrlFrac)
                        msg += "{:.6f} - {:.6f} = ".format(valFrac, tgtFrac)
                        msg += "{:.6f} ^ {:.3f} ".format(dFrameFrac, usePower)
                        msg += "d {:.6f} == {:.6f}".format(expFrac, dCtrlFrac)
                        qCDebug(self.logCategory, msg)
                        # debug_message(msg)
                else:
                    # No adjustment required
                    dCtrlFrac = ctrlFrac
                    vCtrlNew = vCtrl

                # Tiny values of dCtrlFrac don't let the control move, plus it
                # can be zero when there is a frame delta. Force it by one in
                # those cases. In truth this would oscillate +/-1 around the
                # perfect control setting, but since the scene light is often
                # not going to be constant the effect will have little impact
                # plus the controls will start following actual property changes
                # earlier
                if int(vCtrlNew) == ivCtrl:
                    if dCtrlFrac != ctrlFrac:
                        dFrac = dCtrlFrac
                        aFrac = ctrlFrac
                    elif (dFrameFrac != expFrac):
                        dFrac = dFrameFrac
                        aFrac = expFrac
                    else:
                        dFrac = None
                        aFrac = None

                    if (dFrac != None) and (aFrac != None):
                        if dFrac > aFrac:
                            vCtrlNew += 1.0
                        else:
                            vCtrlNew -= 1.0

                # Limit value within control range
                # FIXME: This only works properly when value is increasing
                # beyond maxCtrl
                vCtrlNew = self.__limit_property_value_to_range(vCtrlNew,
                                                                minCtrl,
                                                                maxCtrl)

                # Make sure we have an integer of the new control value
                # FIXME: Find a way to avoid repeating the int conversion of
                # vCtrlNew. int is a better way to test if old and new value
                # differ for applying +/-1 but that may exceed range so limit
                # to range has to be after and returns a float if supplied a
                # float
                ivCtrlNew = int(vCtrlNew)

                # msg = "             Frame: "
                # msg += "{} of {} gives: {}".format(vFrame,
                #                                    rframe,
                #                                    vFrameFrac)
                # debug_message(msg)
                # msg = "            Target: {} gives {}".format(tFrame,
                #                                                tFrameFrac)
                # debug_message(msg)
                if self.tuneLogging is True:
                    # msg = "Control {} change: {} to {}/({}~{})".format(ctrlName,
                    #                                                    ivCtrl,
                    #                                                    ivCtrlNew,
                    #                                                    minCtrl,
                    #                                                    maxCtrl)
                    # msg += " (Adjust "
                    # if imgProp is not None:
                    #     msg += "{} via ".format(imgProp)
                    # # msg += "{} by {} from {} to {}".format(ctrlName, dFrameFrac,
                    # msg += "{} by {:.6f}/{:.6f} ".format(ctrlName, dFrameFrac,
                    #                                      expFrac)
                    # msg += "from {:.6f} to {:.6f})".format(ctrlFrac, dCtrlFrac)
                    if self.tuneMathLogging is True:
                        msg = " \\_ "
                    else:
                        msg = "Tune (ctrl) {}/{}: ".format(imgProp, ctrlName)
                    msg += " {} -> {} ".format(ivCtrl, ivCtrlNew)
                    msg += "({}~{})".format(minCtrl, maxCtrl)
                    qCDebug(self.logCategory, msg)
                    # debug_message(msg)
                # msg = "           Control: "
                # msg += "{} of {} gives {}".format(zCtrl,
                #                                   rCtrl,
                #                                   ctrlFrac)
                # debug_message(msg)
                # debug_message("    Control {} change: {} to {}".format(ctrlName,
                #                                                       ivCtrl,
                #                                                       ivCtrlNew))

                return ivCtrlNew

        return None

    # Given a control name, store the range limits in class members, min and
    # max allow overrides if not None, loDef and hiDef allow default values if
    # none can be determined automatically, encourageLimits being True causes
    # control values outside of the supplied range to be clamped at the nearest
    # limit. When encourageLimits is False a control value outside it's range is
    # "migrated" towards it's nearest limit.
    def set_named_control_limits(self, ctrlName, min=None, max=None, loDef=0,
                                 hiDef=64, encourageLimits=True):
        # debug_message("set_named_control_limits with encourage {}".format(encourageLimits))
        # Find the named control's query control data for the current camera
        qCtrl = self.__current_camera_control_by_name(ctrlName)
        if qCtrl is not None:
            # If we found it, use the minimum and maximum
            self.loLimit = qCtrl.minimum
            self.hiLimit = qCtrl.maximum
        else:
            # If not found, use the defaults
            self.loLimit = loDef
            self.hiLimit = hiDef

        # If we have encourage limits don't use the noClamp Limits
        if encourageLimits is True:
            self.noClampLoLimit = None
            self.noClampHiLimit = None
        else:
            # Not using encourage limits, keep a note of the control limits
            # even if we use the supplied min/max
            # debug_message("Don't encourage limits, keeping access to {}/{}".format(self.loLimit, self.hiLimit))
            self.noClampLoLimit = self.loLimit
            self.noClampHiLimit = self.hiLimit

        # Over-ride any setting with supplied min and max
        if min is not None:
            self.loLimit = min
        if max is not None:
            self.hiLimit = max

    def __tod_tuning_control_settings(self, todName):
        # Make a local reference to the correct TOD list (default to the day
        # tuning controls
        if todName == self.kTuneNight:
            todTuningControls = self.tuningControlSettingsNight
        else:
            todTuningControls = self.tuningControlSettingsDay

        return todTuningControls

    def __tod_tuning_control_info(self, todName):
        # Make a local reference to the correct TOD list (default to the day
        # tuning control info
        if todName == self.kTuneNight:
            locTuningControlInfo = self.imageTuningControlsNight
        else:
            locTuningControlInfo = self.imageTuningControlsDay

        # debug_message("tod {} tuning control info length is {}".format(todName, len(locTuningControlInfo)))
        return locTuningControlInfo

    def use_named_control_all_properties_hi_limit(self, ctrlName,
                                                  todName="Day"):
        locTuningControls = self.__tod_tuning_control_settings(todName)

        # Walk all the tunable controls looking for the name
        # (tuneProperty, ctrlName, rForce, rMin, rMax, negativeUse,
        # encourageRange)
        for aTuner in locTuningControls:
            # If found, and it has a greater hiLimit than currently used
            if (aTuner[1] == ctrlName) and (aTuner[4] > self.hiLimit):
                # hiLimit from this tuning instead
                self.hiLimit = aTuner[4]

    def use_named_control_all_properties_lo_limit(self, ctrlName,
                                                  todName="Day"):
        locTuningControls = self.__tod_tuning_control_settings(todName)

        # Walk all the tunable controls looking for the name
        # (tuneProperty, ctrlName, rForce, rMin, rMax, negativeUse,
        # encourageRange)
        for aTuner in locTuningControls:
            # If found, and it has a lesser loLimit than currently used
            if (aTuner[1] == ctrlName) and (aTuner[3] < self.loLimit):
                # loLimit from this tuning instead
                self.loLimit = aTuner[3]

    # Instead of clamping a control to a limit guide it towards the limit
    def __guide_control_value_to_current_range(self, iCtrl):
        if (self.noClampLoLimit is not None) and\
                (self.noClampHiLimit is not None):
            # debug_message("Don't clamp limit")
            if (self.noClampLoLimit <= self.loLimit) and\
                    (self.noClampHiLimit >= self.hiLimit):
                # In this case, we have two limits, the preferred and probably a
                # whole control range.

                # If the control value is outside the preferred range use the
                # nearest preferred value as a target to reach
                if iCtrl < self.loLimit:
                    tgtVal = 1.0 * self.loLimit
                elif iCtrl > self.hiLimit:
                    tgtVal = 1.0 * self.hiLimit
                else:
                    # Shouldn't happen but let the clamper handle it anyway
                    raise AttributeError

                # Get the control and target value as a fraction of the no-clamp
                # range.
                ctrlFrac = self.__property_value_as_fraction(1.0 * iCtrl,
                                                             self.noClampLoLimit,
                                                             self.noClampHiLimit)
                tgtFrac =  self.__property_value_as_fraction(tgtVal,
                                                             self.noClampLoLimit,
                                                             self.noClampHiLimit)

                # Compute the delta to apply to the control, it's in the
                # direction of the nearest limit in the preferred range
                # FIXME: Power could be better managed than constant
                expFrac = self.__compute_applied_delta(ctrlFrac, tgtFrac,
                                                       ctrlFrac, 1.5)

                # Apply the delta to the control fraction
                ctrlFrac += expFrac

                # New control value from new fraction, restricted to no-clamp
                # range
                try:
                    vCtrlNew = self.__property_fraction_as_value(ctrlFrac,
                                                                 self.noClampLoLimit,
                                                                 self.noClampHiLimit)
                except ValueError:
                    # Failed to do the guidance, just let the clamp handle it
                    raise AttributeError

                # Result
                iCtrl = int(vCtrlNew)
        else:
            # Control not configured for guidance, should be clamped
            raise AttributeError

        return iCtrl

    def __limit_control_value_to_current_range(self, iCtrl):
        # Limit the offered value if it's a believable control
        if iCtrl is not None:
            try:
                iCtrl = self.__guide_control_value_to_current_range(iCtrl)
            except AttributeError:
                # Clamp the control within the limits
                # debug_message("Clamp limit, {}/{}".format(self.noClampLoLimit,
                #                                          self.noClampHiLimit))
                if iCtrl < self.loLimit:
                    iCtrl = self.loLimit
                if iCtrl > self.hiLimit:
                    iCtrl = self.hiLimit

        return iCtrl

    # FIXME: These should make errors known to the caller, e.g. when the camera
    # has no tuning control config, when the tuning controls aren't supported
    # by the camera and more. Probably by raising an identifying exception
    #
    # Save a tuning control's properties to configuration for a given camera
    # and a given time-of-day. Camera name is required. At least the daytime
    # time of day properties must exist and in the presence of only daytime
    # it's values will be used for all 24 hours of the day
    # tuneVal = (tuneProperty, ctrlName, rForce, rMin, rMax, negativeUse,
    #            encourageRange)
    def __config_save_camera_tuning_control(self, camName, tuneVal,
                                            todName="Day"):
        mySet = QSettings()

        # We have to have a camera to have a tuning control
        if camName is None:
            camName = ""

        if camName != "":
            # Select the tuning control group for the supplied time of day
            mySet.beginGroup(todName)

            # Have a camera name group under the time of day group
            mySet.beginGroup(camName)

            # allProperties = mySet.childGroups()

            # Use the image property in the tuneVal as a group,
            # e.g. brightness, contrast, saturation
            mySet.beginGroup(tuneVal[0])

            # Use the control name to group it's properties
            mySet.beginGroup(tuneVal[1])

            # Save the properties
            self.save_persistent_int(self.kTuneMin, tuneVal[3], None, mySet)
            self.save_persistent_int(self.kTuneMax, tuneVal[4], None, mySet)
            self.save_persistent_bool(self.kNegativeUse, tuneVal[5], None,
                                      mySet)
            self.save_persistent_bool(self.kEncourageRange, tuneVal[6], None,
                                      mySet)

            # End of control name group
            mySet.endGroup()

            # End of imeage property group
            mySet.endGroup()

            # End of camera name
            mySet.endGroup()

            # End of time-of day
            mySet.endGroup()

    # Save a tuning control for the current camera
    def __config_save_current_camera_tuning_control(self, tuneVal, todName):
        camName = self.ui.cbCameras.currentText()
        return self.__config_save_camera_tuning_control(camName, tuneVal,
                                                        todName)

    def __config_remove_camera_tuning_control(self, camName, ctrlName, todName,
                                              property):
        mySet = QSettings()

        # We have to have a camera to have a tuning control
        if camName is None:
            camName = ""

        if camName != "":
            # Select the tuning control group for the supplied time of day
            mySet.beginGroup(todName)

            # Have a camera name group under the time of day group
            mySet.beginGroup(camName)

            allProperties = mySet.childGroups()
            if property in allProperties:
                # Use the image property as a group,
                # e.g. brightness, contrast, saturation
                mySet.beginGroup(property)

                # Use the control name to group it's properties
                mySet.beginGroup(ctrlName)

                # Remove everything here
                mySet.remove("")

                # End of control name group
                mySet.endGroup()

                # End of imeage property group
                mySet.endGroup()

            # End of camera name
            mySet.endGroup()

            # End of time-of day
            mySet.endGroup()

    # Given a settings object nested at the level of the camera and given a
    # list of property names (from runtime settings like settings dialog), get
    # rid of any config properties that don't exist in the property list
    def __config_remove_redundant_tuning_properties(self, mySet, propList):
        # Get the child groups at the current config level
        cfgProps = mySet.childGroups()

        # Get rid of any config properties that don't exist in the supplied
        # properties list
        for aProp in cfgProps:
            if aProp in propList:
                continue

            # Assumed property in config but not in settings
            mySet.beginGroup(aProp)
            mySet.remove("")
            mySet.endGroup()
            # debug_message("Config remove TOD property: {}/{}/{}".format(todName,
            #                                                            camName,
            #                                                            aProp))

    # Given a settings object nested at the level of a camera's image
    # property and given a list of of tuner control names (from runtime
    # settings like the settings dialog), get rid of any config tuners that
    # don't exist in the tuners list
    def __config_remove_redundant_tuning_controls(self, mySet, propTuners):
        # Get the child groups at this level, assumed tuner controls for an
        # unknown property
        cfgTuners = mySet.childGroups()

        # Get rid of any config tuners that don't exist in the supplied
        # settings list
        for aCfgTuner in cfgTuners:
            if aCfgTuner in propTuners:
                continue

            # Tuner in config but not in settings
            mySet.beginGroup(aCfgTuner)
            mySet.remove("")
            mySet.endGroup()
            # debug_message("Config remove property tuner: {}/{}/{}/{}".format(todName,
            #                                                                 camName,
            #                                                                 aProp,
            #                                                                 aCfgTuner))

    def __config_remove_redundant_camera_tuning(self, camName, dlgConfig):
        mySet = QSettings()

        # We have to have a camera to have a tuning control
        if camName is None:
            camName = ""

        if camName != "":
            # Walk the tuning properties for day and night
            todName = "Day"
            while todName is not None:
                # Select the tuning control group for the supplied time of day
                mySet.beginGroup(todName)
                locTuners = self.__tod_tuning_control_settings(todName)
                n = len(locTuners)

                # Have a camera name group under the time of day group
                mySet.beginGroup(camName)
                if n > 0:
                    # Get a list of the unique properties in the tuners
                    # including tuners for each property and a list linking
                    # them
                    tuneProps = list()
                    propTunerIndices = list()
                    tunerLists = []
                    for aTuner in locTuners:
                        if not (aTuner[0] in tuneProps):
                            # Tuner property not known yet, add it to property
                            # list, add a new control list for it and note the
                            # index of the control list
                            tuneProps.append(aTuner[0])
                            i = len(tunerLists)
                            aList = list()
                            tunerLists.append(aList)
                            propTunersMap = (aTuner[0], i)
                            propTunerIndices.append(propTunersMap)
                        else:
                            i = -1

                        # Add the control to the correct property list
                        if i == -1:
                            for aPropTunerMap in propTunerIndices:
                                if aTuner[0] == aPropTunerMap[0]:
                                    i = aPropTunerMap[1]
                        if i != -1:
                            aPropTunersList = tunerLists[i]
                            aPropTunersList.append(aTuner[1])
                        else:
                            qCDebug(self.logCategory, "No new property, "
                                    "no old property "
                                    "for {}/{}".format(aTuner[0], aTuner[1]))
                            # debug_message("No new property, no old property for {}/{}".format(aTuner[0], aTuner[1]))

                    # Get rid of any config properties that don't exist in
                    # settings for this time-of-day/camera
                    self.__config_remove_redundant_tuning_properties(mySet,
                                                                     tuneProps)

                    # Clean config of missing tuners not in settings
                    for aProp in tuneProps:
                        mySet.beginGroup(aProp)

                        # Get a list of the tuners for this property
                        propTuners = list()
                        for aPropTunersMap in propTunerIndices:
                            if aPropTunersMap[0] == aProp:
                                propTuners = tunerLists[aPropTunersMap[1]]

                        # Get rid of any config tuners that don't exist in
                        # settings for this time-of-day/camera/property
                        self.__config_remove_redundant_tuning_controls(mySet,
                                                                       propTuners)

                        # End the tuning property group
                        mySet.endGroup()

                else:
                    # No controls at this time of day, remove the
                    # camera
                    # FIXME: Does this remove other things about the camera that
                    # we can keep? For example, targets might want to stay even
                    # if there are no tuning controls to achieve them with.
                    mySet.remove("")
                    qCDebug(self.logCategory, "Config remove "
                            "camera TOD: {}/{}".format(todName, camName))
                    # debug_message("Config remove camera TOD: {}/{}".format(todName,
                    #                                                       camName))

                # End the camera group
                mySet.endGroup()

                # End the time-of-day group
                mySet.endGroup()
                if todName == "Day":
                    todName = "Night"
                else:
                    todName = None

    def __config_remove_current_camera_tuning_control(self, tuneVal, todName):
        camName = self.ui.cbCameras.currentText()
        return self.__config_remove_camera_tuning_control(camName, tuneVal,
                                                          todName)

    def replace_property_control_tuning_by_TOD(self, todName, tuneVal):
        i = self.tuning_control_index_by_property_TOD(todName, tuneVal[0],
                                                      tuneVal[1])
        locTuningControls = self.__tod_tuning_control_settings(todName)
        if i != -1:
            # Delete any existing version of the tuner
            del locTuningControls[i]

        # Add the replacement
        locTuningControls.append(tuneVal)
        # self.__dump_tuning_controls_by_property_TOD(None, "Day")

    def __tod_image_tuning_control_info(self, property, todName):
        locTuningControlInfo = self.__tod_tuning_control_info(todName)
        for aTuneInfo in locTuningControlInfo:
            if aTuneInfo[0] == property:
                return aTuneInfo

        return None

    def __populate_image_tuning_control_info(self, todName="Day"):
        locTuningControls = self.__tod_tuning_control_settings(todName)
        lucTuningControlInfo = self.__tod_tuning_control_info(todName)

        lucTuningControlInfo.clear()
        for aTuner in locTuningControls:
            # Find any existing tuning control info for this property
            if self.__tod_image_tuning_control_info(aTuner[0], todName) is None:
                # None, we can create one
                nTuningCtrls = 0
                for bTuner in locTuningControls:
                    if bTuner[0] == aTuner[0]:
                        nTuningCtrls += 1

                if nTuningCtrls > 0:
                    tuningCtrlsInfo = (aTuner[0], 0, nTuningCtrls)
                    lucTuningControlInfo.append(tuningCtrlsInfo)

    # Load all tuning controls properties from configuration for a given camera
    # and a given time-of-day. Camera name is required. At least the daytime
    # time of day properties must exist and in the presence of only daytime
    # it's values will be used for all 24 hours of the day
    # tuneVal = (tuneProperty, ctrlName, rForce, rMin, rMax, negativeUse,
    #            encourageRange)
    def __config_load_camera_tuning_controls(self, camName, todName="Day"):
        mySet = QSettings()

        # Start with no tuning controls
        locTuningControls = self.__tod_tuning_control_settings(todName)
        locTuningControls.clear()

        # We have to have a camera to have a tuning control
        if camName is None:
            camName = ""

        if camName != "":
            # Select the tuning control group for the supplied time of day
            mySet.beginGroup(todName)

            # Have a camera name group under the time of day group
            mySet.beginGroup(camName)

            # Get the child groups, which should each be a tunable image
            # property
            allProperties = mySet.childGroups()
            for aProperty in allProperties:
                mySet.beginGroup(aProperty)

                # Get the child groups, which should each be a control name
                tuners = mySet.childGroups()
                for aTuner in tuners:
                    # The control name groups it's properties
                    mySet.beginGroup(aTuner)

                    # Load the properties
                    minVal = self.load_persistent_int(self.kTuneMin, None, None,
                                                      mySet)
                    maxVal = self.load_persistent_int(self.kTuneMax, None, None,
                                                      mySet)
                    negUse = self.load_persistent_bool(self.kNegativeUse, None,
                                                       None, mySet)
                    encRange = self.load_persistent_bool(self.kEncourageRange,
                                                         None, None, mySet)

                    # Create the tuning value
                    tuneVal = (aProperty, aTuner, -1, minVal, maxVal, negUse,
                               encRange)
                    locTuningControls.append(tuneVal)

                    # End of control name group
                    mySet.endGroup()

                # End of image property group
                mySet.endGroup()

            # End of camera name
            mySet.endGroup()

            # End of time-of day
            mySet.endGroup()

            self.__populate_image_tuning_control_info(todName)

    # Load all tuning controls for the current camera
    def __config_load_current_camera_tuning_controls(self, todName="Day"):
        camName = self.ui.cbCameras.currentText()
        self.__config_load_camera_tuning_controls(camName, todName)

    def tuning_control_index_by_property_TOD(self, property, todName, ctrlName):
        locTuningControls = self.__tod_tuning_control_settings(todName)
        i = -1
        for aTuner in locTuningControls:
            i += 1
            if (aTuner[0] == property) and (aTuner[1] == ctrlName):
                return i

        return -1

    # Save tuning control information for an image property (brightness,
    # contrast, saturation). If rMin or rMax is None the control's limit is
    # used. negativeUse means the effect on the property is opposite to the
    # control range, higher control setting is lower image property.
    # encourageRange allows for multiple properties to use the same control
    # with different ranges. By default the largest range wins and if the value
    # is beyond the range for a given property's control tune settings  it
    # can't be adjusted, unless encourageRange is used. It allows the given
    # poperty/control to work in the direction of limit it has exceeded, e.g.
    # Image brightness property is affected by contrast but in a limited range.
    # The whole contrast range can be used for the contrast property. If the
    # Brightness range for contrast has encourageRange True when the control is
    # beyond the minimum Brightness range for contrast then the lowest minimum
    # (or control minimum) is treated as a temporary minimum and the control
    # allowed to rise (reverse for a control above a property's range maximum).
    # However, it is not allowed to further extend the distance past the
    # property/control's real tuning range limit, i.e. the Brightness with
    # contrast below tuning minimum example can't move it further down, only
    # up.
    def store_property_control_tuning(self, tuneProperty, ctrlName, rMin=None,
                                      rMax=None, negativeUse=False,
                                      encourageRange=False, todName="Day"):
        locTuningControls = self.__tod_tuning_control_settings(todName)

        # msg = "Storing property {} control {} tuning".format(tuneProperty,
        #                                                      ctrlName)
        # debug_message(msg)
        # Restrict min/max to control range
        qCtrl = self.__current_camera_control_by_name(ctrlName)
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
            # No need for forced range, let min/max imply it:
            # rForce = rMax - rMin + 1
            rForce = -1
            tuneVal = (tuneProperty, ctrlName, rForce, rMin, rMax, negativeUse,
                       encourageRange)
            # msg = "Appended property {} ".format(tuneProperty)
            # msg += "control {} tuning".format(ctrlName)
            # debug_message(msg)
            locTuningControls.append(tuneVal)
            self.__config_save_current_camera_tuning_control(tuneVal, todName)

    def reload_tune_settings(self):
        self.__config_load_current_camera_tuning_controls("Day")
        self.__config_load_current_camera_tuning_controls("Night")

    def __dump_tuning_controls_by_property_TOD(self, property=None,
                                               todName="Day"):
        qCDebug(self.logCategory, "DUMP OF "
                "TUNING CONTROLS FOR {}".format(property))
        # debug_message("DUMP OF TUNING CONTROLS FOR {}".format(property))

        locTuningControls = self.__tod_tuning_control_settings(todName)

        iTuningControl = -1
        iOfProperty = -1

        # Walk all the tunable controls keeping absolute and per-property index
        for aTuningCtrl in locTuningControls:
            iTuningControl += 1

            if property is not None:
                # If it's not one of our property
                if aTuningCtrl[0] != property:
                    continue

            # Count it
            iOfProperty += 1
            # ctrlName = aTuningCtrl[1]
            msg = " {} @ {} - ".format(iOfProperty, iTuningControl)
            msg += "{}/{}  {}-{}".format(aTuningCtrl[0], aTuningCtrl[1],
                                         aTuningCtrl[3], aTuningCtrl[4])
            qCDebug(self.logCategory, msg)
            # debug_message(msg)

    # Get the index in all tuning controls of the first control for a given
    # image property (e.g. brightness, contrast, saturation) and a given time
    # of day
    def __first_tuning_ctrl_index_by_property_TOD(self, property,
                                                  todName="Day"):
        locTuningControls = self.__tod_tuning_control_settings(todName)

        iTuningControl = -1

        for aTuningCtrl in locTuningControls:
            iTuningControl += 1

            # If it's one of our property
            if aTuningCtrl[0] == property:
                return iTuningControl

        return -1

    # Find the index in controls of all types for the nth control of a given
    # type, e.g. 3rd tuning control for brightness in all tuning controls for
    # brightness, contrast and saturation.
    def __tuning_control_index_for_property_TOD_index(self, property,
                                                      todName="Day", iTarget=0):
        locTuningControls = self.__tod_tuning_control_settings(todName)

        iTuningControl = -1
        iOfProperty = -1

        # Walk all the tunable controls keeping index
        for aTuningCtrl in locTuningControls:
            iTuningControl += 1

            # If it's one of our property
            if aTuningCtrl[0] == property:
                # Count it
                iOfProperty += 1

                # If we reach the supplied target index for this control
                if iOfProperty == iTarget:
                    # Return it's actual index in all tunable controls
                    return iTuningControl

        # Not found
        msg = "__tuning_control_index_for_property_TOD_index "
        msg += "failed to find {}".format(property)
        msg += " index {} from {}/{}".format(iTarget,
                                             iOfProperty,
                                             iTuningControl)
        qCDebug(self.logCategory, msg)
        # debug_message(msg)
        return -1

    # Get the index of the tuning state for the named property. The tuning
    # state for each property contains the index of the next control to try
    # among it's tunable controls.
    def tuning_state_index_by_property(self, property):
        # If it's a tunable property
        if property in self.tuneProperties:
            aTuner = None
            iTuner = -1

            # Walk all tuning data
            locImageTuningControlInfo = self.__tod_tuning_control_info(self.lastTOD)
            for aTuner in locImageTuningControlInfo:
                iTuner += 1

                # If we found the supplied property's tuning data
                if aTuner[0] == property:
                    # Return it's index in the tuning controls list
                    return iTuner

        # Error, property name either isn't in tuneProperties or doesn't have
        # an entry in the tuning data
        return -1

    # Step through the controls of a given property to find the index of one in
    # all controls of that property that can be adjusted
    def __next_tuning_control_index_by_property_TOD(self, property, todName=None):
        self.__switch_TOD_controls()

        iTuningState = self.tuning_state_index_by_property(property)
        if iTuningState == -1:
            # No tuning data for property
            qCDebug(self.logCategory,
                    "No tuning data found for {}".format(property))
            # debug_message("No tuning data found for {}".format(property))
            return -1

        # Use the tuning state to get the index in all tunable controls of the
        # current control of the supplied property to work on. Skip controls we
        # can't use but Keep within the count of known controls of this
        # property. And don't exceed one time round all controls of the
        # supplied property
        tuningState = self.imageTuningControls[iTuningState]
        iCtrl = tuningState[1]
        iCount = tuningState[2]
        iFirst = -1
        ctrlNotFound = False
        skippedCount = 0
        while True:
            # Get the index in all tuning controls of the control at the
            # current tuning control index
            if todName is None:
                todName = self.lastTOD
            iTuner = self.__tuning_control_index_for_property_TOD_index(property,
                                                                        todName,
                                                                        iCtrl)
            if iTuner == -1:
                # If we have already failed to find the required index
                if ctrlNotFound:
                    # Report and stop looking
                    msg = "Unable to find "
                    msg += "tuning control for {}".format(property)
                    qCDebug(self.logCategory, msg)
                    # debug_message(msg)
                    break
                else:
                    # self.__dump_tuning_controls_by_property_TOD(property,
                    #                                             self.lastTOD)
                    # When it's the first failure to find the required index
                    # then restart but look for the initial tuning index for
                    # the property instead of the "current" index
                    iCtrl = self.__first_tuning_ctrl_index_by_property_TOD(property,
                                                                           todName)
                    iFirst = -1
                    ctrlNotFound = True
                    continue

            # We've been through them all for this property
            if iFirst == iTuner:
                break

            # If this is the first we've checked, record the index to catch
            # going round them all
            if iFirst == -1:
                iFirst = iTuner

            # Use the tuning data at the index we obtained, the format is:
            # (tuneProperty, ctrlName, rForce, rMin, rMax, negativeUse,
            #  encourageRange)
            aTuner = self.tuningControlSettings[iTuner]
            ctrlName = aTuner[1]

            # Find the control being set
            aCtrl = self.__setting_control_by_name(ctrlName)

            # If it has no tuning data create a default automatically
            if aCtrl is None:
                qCDebug(self.logCategory,
                        "No tune setting for {}".format(ctrlName))
                # debug_message("No tune setting for {}".format(ctrlName))
                self.__create_best_fit_control_setting_by_name(ctrlName)

                # Get the new saved setting
                aCtrl = self.__setting_control_by_name(ctrlName)
            else:
                # If we have already tuned it then skip it for this property
                if aCtrl.id in self.tunedControls:
                    # Break our knowledge of the first control we found and we
                    # can try again with previously found tuners
                    iFirst = -1
                    ctrlNotFound = False

                    # Prevent a return with the control just found
                    aCtrl = None

            # Update the tuning control index to the next control and range
            # limit it
            iCtrl += 1
            if iCtrl >= iCount:
                iCtrl = 0

                # Count that we've been round the list. If we have done that
                # more times than there are properties it must mean any
                # tuner control we could find for this property is already
                # being tuned by another property
                skippedCount += 1
                if skippedCount > len(self.tuneProperties):
                    break

            # Replace the current property's tuning state
            tuningCtrlsInfo = (property, iCtrl, iCount)
            self.imageTuningControls[iTuningState] = tuningCtrlsInfo

            # Only use a tunable control we found if we are able to adjust it
            if aCtrl is not None:
                # It exists, does it have a range that can vary
                # FIXME: Should this permit < -1 to be a valid range? i.e. use
                # abs(aTuner[4] - aTuner[3]) so that a range in either direction
                # is supported
                rCtrl = aTuner[4] - aTuner[3]
                if rCtrl > 1:
                    # Return it's index in the tuning controls list for all
                    # property types
                    return iTuner

        # No control found that can be adjusted, this state may not persist
        return -1

    def __frame_last_value_by_property(self, property):
        # Get the value the property last had in a frame, if it had a usable
        # value
        if property == "Brightness":
            lastValue = self.lastFrameBrightness
        elif property == "Contrast":
            lastValue = self.lastFrameContrast
        elif property == "Saturation":
            lastValue = self.lastFrameSaturation
        else:
            lastValue = -1.0

        return lastValue

    def __preferred_day_target_by_property(self, property, getTargetMax=True):
        '''
        Get the day minimum or maximum target value for the named property.

        Parameters
        ----------
            property: string
                Contains the name of the property to get the target for
            getTargetMax: boolean
                If True caller wants the daytime maximum target for the
                property. If False caller wants the daytime minimum target for
                the property

            Returns the number value of the requested target for the named
            property.
        '''

        if property == "Brightness":
            if getTargetMax:
                tgtVal = self.frameDayBrightnessTarget
            else:
                tgtVal = self.frameDayBrightnessMinTarget
        elif  property == "Contrast":
            if getTargetMax:
                tgtVal = self.frameDayContrastTarget
            else:
                tgtVal = self.frameDayContrastMinTarget
        elif property == "Saturation":
            if getTargetMax:
                tgtVal = self.frameDaySaturationTarget
            else:
                tgtVal = self.frameDaySaturationMinTarget
        else:
            # Unrecognized property
            # FIXME: Should this be a NameError exception?
            tgtVal = 0.0

        return tgtVal

    def __preferred_night_target_by_property(self, property, getTargetMax=True):
        '''
        Get the night minimum or maximum target value for the named property.

        Parameters
        ----------
            property: string
                Contains the name of the property to get the target for
            getTargetMax: boolean
                If True caller wants the daytime maximum target for the
                property. If False caller wants the daytime minimum target for
                the property

            Returns the number value of the requested target for the named
            property.
        '''

        tgtVal = None
        if property == "Brightness":
            if getTargetMax:
                if self.frameNightBrightnessTarget >= 0:
                    tgtVal = self.frameNightBrightnessTarget
            else:
                if self.frameNightBrightnessMinTarget >= 0:
                    tgtVal = self.frameNightBrightnessMinTarget
        elif  property == "Contrast":
            if getTargetMax:
                if self.frameNightContrastTarget >= 0:
                    tgtVal = self.frameNightContrastTarget
            else:
                if self.frameNightContrastMinTarget >= 0:
                    tgtVal = self.frameNightContrastMinTarget
        elif property == "Saturation":
            if getTargetMax:
                if self.frameNightSaturationTarget >= 0:
                    tgtVal = self.frameNightSaturationTarget
            else:
                if self.frameNightSaturationMinTarget >= 0:
                    tgtVal = self.frameNightSaturationMinTarget
        else:
            # Unrecognized property
            # FIXME: Should this be a NameError exception?
            tgtVal = 0.0

        if tgtVal is None:
            # No night value found for the requested property, use day value all
            # day
            tgtVal = self.__preferred_day_target_by_property(property,
                                                             getTargetMax)

        return tgtVal

    def __preferred_target_by_property(self, property, getTargetMax=True):
        # Get the day target value for the named property or, if it's night
        # and we have a nighttime target use it
        itsDaytime = self.todCalc.its_daytime()
        if itsDaytime:
            tgtVal = self.__preferred_day_target_by_property(property,
                                                             getTargetMax)
        else:
            tgtVal = self.__preferred_night_target_by_property(property,
                                                               getTargetMax)

        return tgtVal

    # Given a control and limits decide it it can be adjusted (tuned)
    # FIXME: The negativeEffect is associated with the
    # if lastValue versus tgtVal test. It would be better to avoid the two
    # return cases for each lastvalue/tgtVal test by combining negativeEffect
    # into the lastvalue/tgtVal  test
    def __can_tune_property(self, ctrlName, lastValue, tgtVal, ctrlVal,
                            negativeEffect=False, encourageLimits=False):
        # Use the delta between current value and target to decide
        # if any tuning is possible for this control.
        if lastValue < tgtVal:
            # If we want to increase from the last value to a new target but
            # the control value has exceeded this tuner's high limit then if we
            # are using encourage limits for this tuning use the highest high
            # limit for the control in all tuners
            if (ctrlVal > self.hiLimit) and encourageLimits:
                self.use_named_control_all_properties_hi_limit(ctrlName,
                                                               self.lastTOD)

            if negativeEffect:
                if ctrlVal > self.loLimit:
                    return True
            else:
                if ctrlVal < self.hiLimit:
                    # Can tune the required positive direction
                    return True
        elif lastValue > tgtVal:
            # If we want to decrease from the last value to a new target but
            # the control value has exceeded this tuner's low limit then if we
            # are using encourage limits for this tuning use the lowest low
            # limit for the control in all tuners
            if (ctrlVal < self.loLimit) and encourageLimits:
                self.use_named_control_all_properties_lo_limit(ctrlName,
                                                               self.lastTOD)

            if negativeEffect:
                if ctrlVal < self.hiLimit:
                    # Can tune the required negative direction
                    return True
            else:
                if ctrlVal > self.loLimit:
                    # Can tune the required negative direction
                    return True

        # Can't tune this control
        return False

    # Switch time-of-day controls if needed
    def __switch_TOD_controls(self):
        if self.todCalc.its_daytime():
            todNow = self.kTuneDay
        else:
            todNow = self.kTuneNight

        if self.lastTOD != todNow:
            # Time-of-day change
            self.lastTOD = todNow

            # Set the working copy of the tuning controls
            self.tuningControlSettings = self.__tod_tuning_control_settings(todNow)
            self.imageTuningControls = self.__tod_tuning_control_info(todNow)

    # There is little point in tuning contrast or saturation if
    # brightness is far-off (black-out and white-out have no
    # contrast to adjust). Also, there is little point in tuning saturation if
    # contrast is far-off (absolute zero contrast would have one color, excess
    # contrast would make saturation adjustment very volatile)
    def __property_masked(self, property):
        if property != "Brightness":
            lBright = self.__frame_last_value_by_property("Brightness")
            minBright = self.__preferred_target_by_property("Brightness", False)
            maxBright = self.__preferred_target_by_property("Brightness", True)
            tBright = minBright + (maxBright - minBright) / 2.0
            dBright = abs(tBright - lBright)
            if ((lBright < minBright) or (lBright > maxBright) ) and\
                    (dBright > (tBright / 2.0)):
                qCDebug(self.logCategory, "Contrast masked by Brightness: "
                        "{}, {}/{}-{}, {}".format(lBright, tBright, minBright,
                                                  maxBright, dBright))
                # debug_message("Contrast masked by Brightness: {}, {}/{}-{}, {}".format(lBright, tBright, minBright, maxBright, dBright))
                return True

            if property == "Saturation":
                lCont = self.__frame_last_value_by_property("Contrast")
                minCont = self.__preferred_target_by_property("Contrast", False)
                maxCont = self.__preferred_target_by_property("Contrast", True)
                tCont = minCont + (maxCont - minCont) / 2.0
                dCont = abs(tCont - lCont)
                if ((lCont < minCont) or (lCont > maxCont) ) and\
                        dCont > (tCont / 2.0):
                    qCDebug(self.logCategory, "Saturation masked by Contrast: "
                            "{}, {}/{}-{}, {}".format(lCont, tCont, minCont,
                                                      maxCont, dCont))
                    # debug_message("Saturation masked by Contrast: {}, {}/{}-{}, {}".format(lCont, tCont, minCont, maxCont, dCont))
                    return True

        return False

    # Get the index of the next property control to tune and tune it if
    # available. This needs to detect controls at the limit of the direction
    # they need to move, it needs the target and current control value after
    # toggling to a new control. Only tune controls where the sign of
    # tgtVal - lastValue is the same as the sign of relevant
    # control limit - aCtrl.value
    # We should find the first control in the list on one pass but not on a
    # subsequent pass in this loop so it should exit if a tunable control is
    # found or we've tried all tunable controls of this property. But there
    # might still be a fractional change in the floating point new control value
    # that's too small to change an integer control value, resulting in a do
    # nothing change to a control. But much less than if we just took each
    # control in turn and made it's adjustment even if it was at the limit in
    # the direction of required movement
    def __tune_property_by_nameA(self, property):
        self.__switch_TOD_controls()

        # Only bother if our last captured frame had a value for the named
        # property
        lastValue = self.__frame_last_value_by_property(property)
        if lastValue >= 0.0:
            # Only try if the supplied property is not masked by a heavy value
            # in another
            if self.__property_masked(property) is False:
                # Get the index of the next property control to tune. This needs
                # to detect controls at the limit of the direction they need to
                # move, it needs the target and current control value after
                # toggling to a new control. Only tune controls where the sign
                # of tgtVal - lastValue is the same as the sign of relevant
                # control limit - aCtrl.value
                # We want to find the first control in the list on first pass
                # but not on subsequent passes in this loop so it should exit if
                # a tunable control is found or we've tried all tunable controls
                # of this property. But there might still be a fractional change
                # in the floating point new control value that's too small to
                # change an integer control value, resulting in a do nothing
                # change to a control. So, this tries to find a control that can
                # be tuned for the image property being worked on.
                iTune = 0
                iFirst = -1
                while iTune >= 0:
                    iTune = self.__next_tuning_control_index_by_property_TOD(property,
                                                                             self.lastTOD)
                    if iFirst == iTune:
                        # If this tuning control matches the first we saw then
                        # we never found one we could tune, finish loop with no
                        # index
                        iTune = -1
                        break

                    if iFirst < 0:
                        # Save the first real control we saw
                        iFirst = iTune

                    # If we have one
                    if iTune >= 0:
                        # Get the tuning data
                        # (tuneProperty, ctrlName, rForce, rMin, rMax,
                        #  negativeUse,encourageRange)
                        aTuner = self.tuningControlSettings[iTune]
                        ctrlName = aTuner[1]
                        # debug_message("TUNING {} VIA {}".format(property, ctrlName))

                        # Get our control state from the name
                        aCtrl = self.__setting_control_by_name(ctrlName)

                        # Set any limits imposed by the tuning
                        self.set_named_control_limits(ctrlName, aTuner[3],
                                                      aTuner[4],
                                                      encourageLimits=aTuner[6])

                        # Use the day target or, at night, if we have a night
                        # target use it instead.
                        tgtMin = self.__preferred_target_by_property(property,
                                                                     False)
                        tgtMax = self.__preferred_target_by_property(property,
                                                                     True)
                        tgtVal = tgtMin + (tgtMax - tgtMin) / 2.0

                        # Use the delta between current value and target to
                        # decide if any tuning is possible for this control
                        if self.__can_tune_property(ctrlName, lastValue, tgtVal,
                                                    aCtrl.value, aTuner[5],
                                                    aTuner[6]):

                            # Tune the control based on the last frame value,
                            # target, property range, forced control range and
                            # manage whether deltas have the same or reverse
                            # direction as control deltas
                            aVal = self.__tune_control_value_by_ID(aCtrl.id,
                                                                   lastValue,
                                                                   tgtVal,
                                                                   256.0,
                                                                   aTuner[2],
                                                                   aTuner[5],
                                                                   imgProp=property)

                            # Limit the offered value
                            # FIXME: If we don't have encourage limits we
                            # shouldn't just hard clamp the limit but adjust
                            # towards it
                            vCtrl = self.__limit_control_value_to_current_range(aVal)
                            if vCtrl != aVal:
                                qCDebug(self.logCategory,
                                        "    Limiting value "
                                        "to {}".format(vCtrl))
                                # msg = "    Limiting value to {}".format(vCtrl)
                                # debug_message(msg)

                            # If we are not going to change from lastValue then
                            # ignore this control and try another
                            if vCtrl == lastValue:
                                continue

                            # If we get here it's a control with a value that
                            # can be adjusted to a different value, exit the
                            # loop
                            break

            else:
                # Masked property
                iTune = -1

            if iTune >= 0:
                # Note the control we are tuning
                self.tunedControls.append(aCtrl.id)

                # vCtrl is already tuned, limited and known to represent an
                # adjustment to the control value on exit from the loop
                # iterating the controls
                self.replace_control_setting_by_ID(aCtrl.id, vCtrl)

                # Update the UI as well, if it's the current control in the list
                # that's being adjusted
                curCtrl = self.ui.cbControls.currentText()
                if curCtrl == ctrlName:
                    # Needs to be done without responding to recursive
                    # ValueChanged signals
                    self.switchingControl = True
                    self.__disable_integer_control()
                    self.setup_integer_control(aCtrl.id)
                    self.switchingControl = False

    def __tune_property_by_name(self, property):
        self.__switch_TOD_controls()

        # Only bother if our last captured frame had a value for the named
        # property
        lastValue = self.__frame_last_value_by_property(property)
        if lastValue >= 0.0:
            # Only try if the supplied property is not masked by a heavy value
            # in another
            if self.__property_masked(property) is False:
                # Get the index of the next property control to tune. This needs
                # to detect controls at the limit of the direction they need to
                # move, it needs the target and current control value after
                # toggling to a new control. Only tune controls where the sign
                # of tgtVal - lastValue is the same as the sign of relevant
                # control limit - aCtrl.value
                # We should find the first control in the list on one pass but
                # not on a subsequent pass in this loop so it should exit if a
                # tunable control is found or we've tried all tunable controls
                # of this property. But there might still be a fractional change
                # in the floating point new control value that's too small to
                # change an integer control value, resulting in a do nothing
                # change to a control. But much less than if we just took each
                # control in turn and made it's adjustment even if it was at the
                # limit in the direction of required movement
                iTune = 0
                iFirst = -1
                while iTune >= 0:
                    iTune = self.__next_tuning_control_index_by_property_TOD(property,
                                                                             self.lastTOD)
                    if iFirst == iTune:
                        # If this tuning control matches the first we saw then we
                        # never found one we could tune, finish loop with no
                        # index
                        iTune = -1
                        break

                    if iFirst < 0:
                        # Save the first real control we saw
                        iFirst = iTune

                    # If we have one
                    if iTune >= 0:
                        # Get the tuning data
                        # (tuneProperty, ctrlName, rForce, rMin, rMax,
                        #  negativeUse,encourageRange)
                        aTuner = self.tuningControlSettings[iTune]
                        ctrlName = aTuner[1]
                        # debug_message("TUNING {} VIA {}".format(property, ctrlName))

                        # Get our control state from the name
                        aCtrl = self.__setting_control_by_name(ctrlName)

                        # Set any limits imposed by the tuning
                        self.set_named_control_limits(ctrlName, aTuner[3],
                                                      aTuner[4],
                                                      encourageLimits=aTuner[6])

                        # Use the day target or, at night, if we have a night
                        # target use it instead.
                        tgtMin = self.__preferred_target_by_property(property,
                                                                     False)
                        tgtMax = self.__preferred_target_by_property(property,
                                                                     True)
                        tgtVal = tgtMin + (tgtMax - tgtMin) / 2.0

                        # Use the delta between current value and target to
                        # decide if any tuning is possible for this control
                        if self.__can_tune_property(ctrlName, lastValue, tgtVal,
                                                    aCtrl.value, aTuner[5],
                                                    aTuner[6]):
                            break
            else:
                # Masked property
                iTune = -1

            if iTune >= 0:
                # Note the control we are tuning
                self.tunedControls.append(aCtrl.id)

                # Tune the control based on the last frame value, target,
                # property range, forced control range and manage whether
                # deltas have the same or reverse direction as control deltas
                iCtrl = self.__tune_control_value_by_ID(aCtrl.id, lastValue,
                                                        tgtVal, 256.0,
                                                        aTuner[2], aTuner[5],
                                                        imgProp=property)

                # Limit the offered value
                # FIXME: If we don't have encourage limits we shouldn't just
                # hard clamp the limit but adjust towards it
                oiCtrl = iCtrl
                iCtrl = self.__limit_control_value_to_current_range(iCtrl)
                if iCtrl != oiCtrl:
                    qCDebug(self.logCategory,
                            "    Limiting value to {}".format(iCtrl))
                    # debug_message("    Limiting value to {}".format(iCtrl))

                # If the value is changing, set the control
                if (iCtrl is not None) and (iCtrl != aCtrl.value):
                    # Update the display as well, if it's the current control
                    # in the list
                    self.replace_control_setting_by_ID(aCtrl.id, iCtrl)
                    curCtrl = self.ui.cbControls.currentText()
                    if curCtrl == ctrlName:
                        # Needs to be done without responding to recursive
                        # ValueChanged signals
                        self.switchingControl = True
                        self.__disable_integer_control()
                        self.setup_integer_control(aCtrl.id)
                        self.switchingControl = False

    def __tune_exposure(self):
        # t0 = time.time()
        # Use this to let deeper code know what tuner controls have already been
        # used to try to avoid having one property move it up by one and another
        # property move it down by one in the same pass.
        self.tunedControls.clear()

        # Tune a control for each property that can be tuned
        for aProperty in self.tuneProperties:
            self.__tune_property_by_nameA(aProperty)
        # t1 = time.time()
        # debug_message("Exposure tuning takes {}".format(t1 - t0))

    def __dump_frame_lighting(self):
        itsNight = self.todCalc.its_nighttime()
        msg = "Brightness: {}/".format(round(self.lastFrameBrightness, 3))
        if itsNight:
            min = self.frameNightBrightnessMinTarget
            max = self.frameNightBrightnessTarget
            msg += "{}~{}, ".format(min, max)
        else:
            min = self.frameDayBrightnessMinTarget
            max = self.frameDayBrightnessTarget
            msg += "{}~{}, ".format(min, max)
        msg += "Contrast: {}/".format(round(self.lastFrameContrast, 3))
        if itsNight:
            min = self.frameNightContrastMinTarget
            max = self.frameNightContrastTarget
            msg += "{}~{}, ".format(min, max)
        else:
            min = self.frameDayContrastMinTarget
            max = self.frameDayContrastTarget
            msg += "{}~{}, ".format(min, max)
        msg += "Saturation: {}/".format(round(self.lastFrameSaturation, 3))
        if itsNight:
            min = self.frameNightSaturationMinTarget
            max = self.frameNightSaturationTarget
            msg += "{}~{}, ".format(min, max)
        else:
            min = self.frameDaySaturationMinTarget
            max = self.frameDaySaturationTarget
            msg += "{}~{}, ".format(min, max)
        qCDebug(self.logCategory, msg)
        # debug_message(msg)

    # Capture finished, handle any pending application close that's waiting on
    # a worker thread to finish
    def capture_finished(self):
        # tExitSignaled = time.time()
        if self.capThread is not None:
            # tSigOverhead = tExitSignaled - self.capThread.exit_time
            # debug_message("Thread exit signal overhead is {}s".format(tSigOverhead))

            # Assume we can save the next frame
            self.frameCaptureAndSave = True

            self.lastCapBroke = self.capThread.receive_broken()
            if not self.lastCapBroke:
                # Save the basic frame statistics
                self.lastFrameBrightness = self.capThread.brightness
                self.lastFrameContrast = self.capThread.contrast
                self.lastFrameSaturation = self.capThread.saturation

                # Show them
                self.__dump_frame_lighting()

                # Auto-exposure adjustments (for next frame capture)
                self.__tune_exposure()

                # If needed, update the current focus from the camera
                # FIXME: This duplicates some of changed_control()
                mfCtrl = self.capThread.manual_focus_control_ID
                if mfCtrl is not None:
                    aCtrl = self.__current_camera_current_control()
                    if aCtrl is not None:
                        if aCtrl.id == mfCtrl:
                            self.switchingControl = True
                            # Turn off all UI for camera controls then handle
                            # the correct type
                            self.__disable_integer_control()
                            self.__disable_boolean_controls()
                            self.__disable_menu_controls()
                            if aCtrl.type == V4L2_CTRL_TYPE_INTEGER:
                                self.setup_integer_control(aCtrl.id, True)
                            elif aCtrl.type == V4L2_CTRL_TYPE_BOOLEAN:
                                self.setup_boolean_control(aCtrl.id, True)
                            elif aCtrl.type == V4L2_CTRL_TYPE_MENU:
                                # Not all menu cases are coded, add missing ones
                                # in the following function
                                self.setup_menu_control(aCtrl.id, True)
                            else:
                                msg = "Control ID {} ".format(aCtrl.id)
                                if aCtrl.type == V4L2_CTRL_TYPE_BUTTON:
                                    msg += "is type BUTTON"
                                    # debug_message(msg)
                                elif aCtrl.type == V4L2_CTRL_TYPE_INTEGER64:
                                    msg += "is type INT64"
                                    # debug_message(msg)
                                elif aCtrl.type == V4L2_CTRL_TYPE_CTRL_CLASS:
                                    msg += "is type CLASS"
                                    # debug_message(msg)
                                elif aCtrl.type == V4L2_CTRL_TYPE_STRING:
                                    msg += "is type STRING"
                                    # debug_message(msg)
                                else:
                                    msg += "is unrecognized type"
                                qCDebug(self.logCategory, msg)
                            self.switchingControl = False
            else:
                self.lastframeBrightness = -1.0
                self.lastFrameContrast = -1.0
                self.lastFrameSaturation = -1.0

            # If we don't have a pending close and the capture timer is running
            doAutoExp = not (self.doAccept or self.doReject) and\
                    self.capTimer.isActive()
            if doAutoExp:
                # Not forcing exit and still capturing, use the capture time to
                # judge if we can do non-save captures beteween save captures to
                # perform more auto-exposure than just the captured frames

                # How long was last saved capture, get it with some overhead
                tCapDuration = 1000.0 * self.capThread.capture_duration

            # Destroy the thread object
            self.capThread.deleteLater()
            self.capThread = None

            # If there's a reason to schedule an auto-exposure tick
            if doAutoExp:
                # If we saved a capture duration
                if tCapDuration > 0.0:
                    nCaptureDurations = len(self.tCaptureDurations)
                    while nCaptureDurations >= self.tMaxCaptures:
                        # remove the oldest element's value from the sum
                        self.tCaptureSum -= self.tCaptureDurations[0]
                        del self.tCaptureDurations[0]
                        nCaptureDurations -= 1

                    # Add the duration of the just captured frame
                    self.tCaptureDurations.append(tCapDuration)
                    nCaptureDurations += 1
                    self.tCaptureSum += tCapDuration

                # Mean of n saved frame capture durations
                nCapDurations = (1.0 * len(self.tCaptureDurations))
                if nCapDurations > 0.0:
                    tCapDuration = self.tCaptureSum
                    tCapDuration /= (1.0 * len(self.tCaptureDurations))
                else:
                    # Shouldn't have got here with no time taken but assume the
                    # frame time tick as a last resort
                    tCapDuration = self.tFrameTick

                # Period between auto-exposure captures and free time to leave
                # at end of tick period
                tN = 2.0
                tAutoExpPeriod = tN * tCapDuration
                tSafetyDuration = 2.0 * tAutoExpPeriod

                # How long has elapsed since last saved capture
                tNow = time.time()
                tSinceLastSave = 1000.0 * (tNow - self.tFrameTick)

                # How long is expected until the next tick
                capPeriod = 1.0 * self.capTimer.interval()
                tCapRemaining = capPeriod - tSinceLastSave

                # Keep the capture durations for more than one tick but less
                # than two
                tKeepForMeans = 1.5 * capPeriod
                nKeepForMeans = int(tKeepForMeans / tCapDuration)
                if nKeepForMeans < 1:
                    nKeepForMeans = 2
                self.tMaxCaptures = nKeepForMeans

                # debug_message("Setting auto-exp capture: {:.3f}/{:.3f}".format(tCapRemaining, tSafetyDuration))
                # debug_message("Capture duration: {:.3f}".format(tCaptureDuration))
                # debug_message("Exposure period: {:.3f}".format(tAutoExpPeriod))
                # debug_message("Since last save: {:.3f}".format(tSinceLastSave))
                # debug_message("Capture period: {:.3f}".format(capPeriod))

                if (tCapRemaining >= tSafetyDuration):
                    # Remaining timer duration is more than enough time for a
                    # wait for another auto-exposure capture before a save is
                    # expected
                    # debug_message("{} timer for auto-exposure only frame".format(tAutoExpDuration))
                    QTimer.singleShot(tAutoExpPeriod, self.frame_tick_no_save)

        # If we have a pending close, end the main window
        if self.doAccept or self.doReject:
            self.__close_camera()
            self.lateClose.emit()

    def adjust_frame_tick_period(self, upwards=True):
        usePeriod = TWO_MIN_PRIMES[-1]

        capPeriod = self.ui.sbCapPeriod.value()
        maxPeriodTune = TWO_MIN_PRIMES[-1]
        if (maxPeriodTune > capPeriod) and (capPeriod <= 120):
            # Allow growth in half steps with a maximum of 120 seconds and
            # minimum of 1 second
            if upwards:
                diffTune = int((120 - capPeriod) / 2)
            else:
                diffTune = 0 - int((1 - capPeriod) / 2)
            approxPeriod = capPeriod + diffTune

            # Find the next larger prime
            for aPrime in TWO_MIN_PRIMES:
                if aPrime > approxPeriod:
                    usePeriod = aPrime

        return usePeriod

    # Frame capture without save timer function (used for auto-exposure
    # adjustment between saving files)
    def frame_tick_no_save(self):
        if self.capThread is None:
            self.frameCaptureAndSave = False
            self.frame_tick()

    # Frame capture and save timer function
    def frame_tick(self):
        # debug_message("Tick")
        # Ignore timeout if a capture thread exists
        if self.capThread is not None:
            qCWarning(self.logCategory, "Tick during capture thread")
            # warning_message("Tick during capture thread")
            self.wastedCapTicks += 1
            # FIXME: Could make it adjust the timer period upwards if this
            # repeats beyond a threshold value of wasted ticks, might be better
            # as a rate, wasted ticks per call to frame_tick is a number between
            # zero and one

            return

        if self.frameCaptureAndSave:
            self.tFrameTick = time.time()

        # Get the current item from the frame sizes list
        # item = self.ui.lwFrameSizes.currentItem()

        # If our last receive broke then close the device, it will be re-opened
        # shortly after
        if self.lastCapBroke:
            qCDebug(self.logCategory,
                    "Last capture was broken, closing device to re-open")
            # debug_message("Last capture was broken, closing device to re-open")
            self.__close_camera()
            self.lastCapBroke = False

        # Make sure the camera is open
        self.__open_camera()

        # We have to have a capture device
        if self.capDev is not None:
            # Get our own copy of the camera so that we know the auto and manual
            # focus controls
            aCam = self.__find_current_camera()

            # debug_message("Capture device is {}".format(self.capDev.fileno()))
            # Set the codec and frame size based on the UI and class
            self.__set_codec_and_frame_size()

            # Get a worker thread and give it the information about capture
            # FIXME: We wouldn't have to preset all the capture thread settings
            # if we gave it a reference to ourselves and let it gather what it
            # wanted to know
            self.threadCount += 1
            # msg = "Starting worker number {}".format(self.threadCount)
            # debug_message(msg)
            self.capThread = captureThread()
            self.capThread.setObjectName("CSDevs Frame Capture")
            self.capThread.set_capture_device(self.capDev)
            self.capThread.set_capture_buffer_count(40)
            nthFrame = self.ui.sbNthFrame.value()
            if nthFrame != self.capThread.n_capture_frame:
                self.capThread.set_capture_frame_number(nthFrame)
            if self.frameCaptureAndSave:
                self.capThread.set_capture_filename(self.ui.leCapFile.text())
            else:
                self.capThread.disable_frame_save()
            if self.ui.hsImgQuality.isEnabled():
                saveQual = self.ui.hsImgQuality.value()
            else:
                saveQual = 0
            self.capThread.set_save_quality(saveQual)

            if len(self.controls) > 0:
                for aCtrl in self.controls:
                    self.capThread.replace_control_setting_by_ID(aCtrl.id,
                                                                 aCtrl.value)
                # debug_message("Setting manual focus ID to {}".format(aCam[4]))
                self.capThread.set_manual_focus_control_ID(aCam[4])
                # debug_message("Setting autofocus ID to {}".format(aCam[5]))
                self.capThread.set_auto_focus_control_ID(aCam[5])

                # FIXME: Auto-focus is horrible, what does it mean if it has no
                # persistent setting, ON or OFF?
                if aCam[5] is not None:
                    aCtrl = self.__setting_control_by_ID(aCam[5])
                    if self.camAF:
                        self.capThread.replace_control_setting_by_ID(aCam[5], 1)
                    else:
                        self.capThread.replace_control_setting_by_ID(aCam[5], 0)

                # Focus setting only matters if there is a control and value. It
                # should get ignored by the camera if auto-focus is enabled
                if (aCam[4] is not None) and (self.camFocus is not None):
                    aCtrl = self.__setting_control_by_ID(aCam[4])
                    self.capThread.replace_control_setting_by_ID(aCam[4], self.camFocus)
            self.capThread.set_caption_text(self.captionText)
            self.capThread.set_caption_datestamp_enabled(self.captionDateStamp)
            self.capThread.set_caption_timestamp_enabled(self.captionTimeStamp)
            self.capThread.set_caption_two_four_hour_enabled(self.captionTwoFourHour)
            self.capThread.set_caption_text_RGB(self.captionTextR,
                                                self.captionTextG,
                                                self.captionTextB)
            self.capThread.set_caption_text_location(self.captionLocation)
            self.capThread.set_caption_inset_X(self.captionInsetX)
            self.capThread.set_caption_inset_Y(self.captionInsetY)

            # Read carefully, we are considering four properties. The family
            # name and the font filename for each of the backup and preferred
            # caption font.
            backupCaptionFontFamily = "Liberation Sans"
            backupCaptionFontFilename = self.theFonts.font_file_for_font_family_filtered(backupCaptionFontFamily, 400, QFont.StyleNormal)
            if backupCaptionFontFilename is not None:
                if backupCaptionFontFilename != "":
                    # debug_message("Setting backup caption font file to {}".format(backupCaptionFontFilename))
                    self.capThread.set_backup_caption_font_filename(backupCaptionFontFilename)
            if (self.captionFontFilename is not None) or (self.captionFontFilename != ""):
                if self.captionFontFamily != "":
                    self.captionFontFilename = self.theFonts.font_file_for_font_family_filtered(self.captionFontFamily, 400, QFont.StyleNormal)
                    if (self.captionFontFilename is None) or (self.captionFontFilename == ""):
                        self.captionFontFilename = backupCaptionFontFilename
                    # debug_message("Setting caption font file to {}".format(self.captionFontFilename))
                    self.capThread.set_caption_font_filename(self.captionFontFilename)
            self.capThread.set_caption_font_size(self.captionFontSize)

            # Connect the thread finished signal back to ourselves
            self.capThread.finished.connect(self.capture_finished)

            # Blank line gap before start of frame capure message to separate
            # iterations
            # debug_message("")
            # debug_message("Starting frame capture thread from UI")
            self.capThread.start()
        else:
            qCWarning(self.logCategory, "Tick with no capture device")
            # debug_message("Tick with no capture device")

    def __setting_control_by_ID(self, ctrlID):
        if len(self.controls) > 0:
            for aCtrl in self.controls:
                if aCtrl.id == ctrlID:
                    return aCtrl

        return None

    # Given a named control, find it in the controls being set for the current
    # camera
    def __setting_control_by_name(self, reqCtrlName):
        ctrlID = self.__current_camera_control_ID_by_name(reqCtrlName)
        if ctrlID is not None:
            # Known control for the camera, is it being set
            return self.__setting_control_by_ID(ctrlID)

        return None

    # This gets us any control setting for the current control in the UI
    def __current_camera_current_control_setting(self):
        ctrlName = self.ui.cbControls.currentText()
        return self.__setting_control_by_name(ctrlName)

    # Given a control name return it's ID if it's in the controls being set
    def __setting_control_ID_by_name(self, ctrlName):
        aCtrl = self.__setting_control_by_name(ctrlName)
        if aCtrl is not None:
            return aCtrl.id

        return None

    def add_control_setting_by_ID(self, ctrlID, value):
        try:
            aCtrl = v4l2_control(ctrlID)
            aCtrl.value = value
            self.controls.append(aCtrl)
        except TypeError:
            msg = "Thread failed to create control {} = {}".format(ctrlID,
                                                                   value)
            qCWarning(self.logCategory, msg)
            # debug_message(msg)

    # Given a control name and value, add it as a by ID control setting for
    # the current camera
    def add_control_setting_by_name(self, ctrlName, value):
        ctrlID = self.__current_camera_control_ID_by_name(ctrlName)
        if ctrlID is not None:
            self.add_control_setting_by_ID(self, ctrlID, value)

    def remove_control_setting_by_ID(self, ctrlID):
        aCtrl = self.__setting_control_by_ID(ctrlID)
        if aCtrl is not None:
            try:
                self.controls.remove(aCtrl)
            except ValueError:
                msg = "Failed to remove stream control "
                msg += "{}".format(aCtrl.id)
                qCWarning(self.logCategory, msg)
                # debug_message(msg)

    # Given a control name remove it by ID control as a setting for
    # the current camera
    def remove_control_setting_by_name(self, ctrlName):
        ctrlID = self.__current_camera_control_ID_by_name(ctrlName)
        if ctrlID is not None:
            self.remove_control_setting_by_ID(ctrlID)

    # Order is not preserved
    def replace_control_setting_by_ID(self, ctrlID, newValue):
        aCtrl = self.__setting_control_by_ID(ctrlID)
        if aCtrl is not None:
            self.remove_control_setting_by_ID(ctrlID)

        self.add_control_setting_by_ID(ctrlID, newValue)

    # Order is not preserved
    def replace_control_setting_by_name(self, ctrlName, newValue):
        ctrlID = self.__current_camera_control_ID_by_name(ctrlName)
        if ctrlID is not None:
            self.replace_control_setting_by_ID(ctrlID, newValue)

    def reset_camera_control_monitoring(self):
        # Reset the camera control monitoring state
        self.controlIndex = -1
        self.switchingControl = False
        self.ctrlCurVal = None
        self.controls.clear()

    # Get the control list entry for a given camera name and given control
    # name
    def __camera_control_by_name(self, aCam, ctrlName):
        if aCam is not None:
            ctrlList = aCam[2]
            aResult = None
            n = 0
            for aCtrl in ctrlList:
                if ctrlName == aCtrl.name.decode('utf-8'):
                    n += 1
                    if aResult is None:
                        aResult = aCtrl
                    else:
                        qCDebug(self.logCategory,
                                "Control "
                                "{} found {} times in list".format(ctrlName, n))
                        # debug_message("Control {} found {} times in list".format(ctrlName, n))
                    # return aCtrl

        # return None
        return aResult

    def __current_camera_control_by_name(self, ctrlName):
        aCam = self.__find_current_camera()
        return self.__camera_control_by_name(aCam, ctrlName)

    # Get the control list entry for the current camera and control
    def __current_camera_current_control(self):
        ctrlName = self.ui.cbControls.currentText()
        return self.__current_camera_control_by_name(ctrlName)

    # Get the control ID for a named control if it's in the control list for
    # a given camera
    def __camera_control_ID_by_name(self, aCam, ctrlName):
        qCtrl = self.__camera_control_by_name(aCam, ctrlName)
        if qCtrl is not None:
            return qCtrl.id

        return None

    # Get the control ID for a named control if it's in the control list for
    # the current camera
    def __current_camera_control_ID_by_name(self, ctrlName):
        aCam = self.__find_current_camera()
        return self.__camera_control_ID_by_name(aCam, ctrlName)

    # Get the control ID for the current camera and control
    def __current_camera_current_control_ID(self):
        ctrlName = self.ui.cbControls.currentText()
        return self.__current_camera_control_ID_by_name(ctrlName)

    def int_control_changed(self, value):
        # Do nothing if we are setting up the UI from the camera
        if self.readCamCtrl:
            qCDebug(self.logCategory, "Integer control changed due to read")
            # debug_message("Integer control changed due to read")
            return

        if self.capDev is not None:
            aCtrl = self.__current_camera_current_control()
            if aCtrl is not None:
                # Only handle int controls here
                if aCtrl.type == V4L2_CTRL_TYPE_INTEGER:
                    self.replace_control_setting_by_ID(aCtrl.id, value)

                    # If we get here we should make focus adjustment persistent.
                    # The member functin called will check if the coontrol being
                    # set is focus for the current camera.
                    self.save_persistent_focus_for_camera(aCtrl.id, value)
                else:
                    qCWarning(self.logCategory,
                              "Attempt to change non-integer control")
                    # debug_message("Attempt to change non-integer control")
            else:
                qCWarning(self.logCategory,
                          "Unable to find current control to change")
                # debug_message("Unable to find current control to change")
        else:
            qCWarning(self.logCategory, "Change control with no capture device")
            # debug_message("Change control with no capture device")

    def boolean_control_changed(self, value):
        # Do nothing if we are setting up the UI from the camera
        if self.readCamCtrl:
            return

        if self.capDev is not None:
            # debug_message("Bool control changing to {}".format(value))
            aCtrl = self.__current_camera_current_control()
            if aCtrl is not None:
                # Only handle bool controls here
                if aCtrl.type == V4L2_CTRL_TYPE_BOOLEAN:
                    if (value == 0) or (value is False):
                        aCtrl.value = 0
                    else:
                        aCtrl.value = 1
                    self.replace_control_setting_by_ID(aCtrl.id, aCtrl.value)

                    # If we get here we should make auto-focus toggling
                    # persistent. The member functin called will check if the
                    # control being set is auto-focus for the current camera.
                    self.save_persistent_AF_for_camera(aCtrl.id, value)

    def __disable_boolean_controls(self):
        # debug_message("Disable boolean control")
        self.ui.cbCtrlVal.setEnabled(False)
        self.ui.cbCtrlVal.setChecked(False)

    def setup_boolean_control(self, ctrlID, reRead=False):
        # debug_message("Setup boolean control")

        # If we have a capture device
        if self.capDev is not None:
            qctrl = self.get_current_camera_control_by_ID(ctrlID)

            # Do we already have a saved setting
            ctrlVal = self.__setting_control_by_ID(ctrlID)
            if (ctrlVal is None) or (reRead is True):
                # No, re-read the control for current state
                self.readCamCtrl = True
                ctrlVal = self.get_current_camera_control_value_by_ID(ctrlID)

            if (qctrl is not None) and (ctrlVal is not None):
                # Populate the UI
                self.ui.cbCtrlVal.setChecked(ctrlVal.value != 0)
                self.ui.cbCtrlVal.setEnabled(True)
            self.readCamCtrl = False

    def __disable_integer_control(self):
        '''
        Disable the UI controls that display an integer camera control. They are
        first set to zero so that no leftover value is seen in the disabled
        UI control. The range based ones have to have zero based ranges set
        first otherwise the setValue will be restricted to the range of the
        previously displayed camera control
        '''

        # debug_message("Disable integer control")
        self.ui.sbCtrlInt.setRange(0, 0)
        self.ui.sbCtrlInt.setValue(0)
        self.ui.sbCtrlInt.setEnabled(False)

        self.ui.lblCtrlIntMin.setText("0")
        self.ui.lblCtrlIntMin.setEnabled(False)

        self.ui.lblCtrlIntMax.setText("0")
        self.ui.lblCtrlIntMax.setEnabled(False)

        self.ui.hsCtrlVal.setRange(0, 0)
        self.ui.hsCtrlVal.setValue(0)
        self.ui.hsCtrlVal.setEnabled(False)

    def int_SB_changed(self, value):
        # Let the original recipient do the camera change
        if self.switchingControl:
            return
        self.switchingControl = True

        # self.sbValueNest += 1
        # msg = "Integer spinbox changed "
        # msg += "({}/{} nested)".format(self.sbValueNest, self.hsValueNest)
        # debug_message(msg)
        # debug_message("Integer spinbox changed")
        # Turn off the slider value changed signal so we don't get looping
        # events
        # self.ui.hsCtrlVal.valueChanged.disconnect()

        # Set the slider to the new value
        self.ui.hsCtrlVal.setValue(value)

        # Set the control
        self.int_control_changed(value)
        # debug_message("Integer spinbox control {}".format(value))

        # Turn on the slider value changed signal again
        # self.ui.hsCtrlVal.valueChanged.connect(self.int_HS_changed)

        # self.sbValueNest -= 1

        # Re-enable value changed for all controls
        self.switchingControl = False

    def int_HS_changed(self, value):
        # Let the original recipient do the camera change
        if self.switchingControl:
            return
        self.switchingControl = True

        # self.hsValueNest += 1
        # msg = "Integer slider changed "
        # msg += "({}/{} nested)".format(self.hsValueNest, self.sbValueNest)
        # debug_message(msg)
        # debug_message("Integer slider changed")
        # Turn off the spinbox value changed signal so we don't get looping
        # events
        # self.ui.sbCtrlInt.valueChanged.disconnect()
        # self.disconnect(None, self.int_SB_changed, None)

        # Set the spinbox to the new value
        self.ui.sbCtrlInt.setValue(value)
        # debug_message("Integer slider control {}".format(value))

        # Set the camera control
        self.int_control_changed(value)

        # Turn on the slider value changed signal again
        # self.ui.sbCtrlInt.valueChanged.connect(self.int_SB_changed)

        # self.hsValueNest -= 1

        # Re-enable value changed for all controls
        self.switchingControl = False

    # Setup the UI for an integer control
    def setup_integer_control(self, ctrlID, reRead=False):
        # debug_message("Setup integer control: {}".format(ctrlID))

        # If we have a capture device
        if self.capDev is not None:
            # if reRead is False:
            #     msg = "Setup control for a valid capture device "
            #     msg += "({})".format(ctrlID)
            #     debug_message(msg)

            # Control configuration, not value
            qctrl = self.get_current_camera_control_by_ID(ctrlID)

            # Do we already have a saved setting
            ctrlVal = self.__setting_control_by_ID(ctrlID)
            if (ctrlVal is None) or (reRead is True):
                # No, re-read the control for current state
                self.readCamCtrl = True
                ctrlVal = self.get_current_camera_control_value_by_ID(ctrlID)
            if (qctrl is not None) and (ctrlVal is not None):
                # debug_message("Read the controls")
                # Populate the UI
                self.ui.sbCtrlInt.setRange(qctrl.minimum, qctrl.maximum)
                self.ui.sbCtrlInt.setSingleStep(qctrl.step)

                self.ui.lblCtrlIntMin.setText("{}".format(qctrl.minimum))
                self.ui.lblCtrlIntMax.setText("{}".format(qctrl.maximum))

                self.ui.hsCtrlVal.setRange(qctrl.minimum, qctrl.maximum)
                self.ui.hsCtrlVal.setSingleStep(qctrl.step)

                # These cause a value changed event, we don't want it to set
                # the camera control if the UI is being setup from reading the
                # camera control. We will already have set switchingControl
                # True if that's so. Although these functions are the value
                # changed slots they ignore setting the camera on the basis of
                # switchingControl
                self.ui.sbCtrlInt.setValue(ctrlVal.value)
                self.ui.hsCtrlVal.setValue(ctrlVal.value)

                # debug_message("Enabling integer controls")
                self.ui.sbCtrlInt.setEnabled(True)
                self.ui.lblCtrlIntMin.setEnabled(True)
                self.ui.lblCtrlIntMax.setEnabled(True)
                self.ui.hsCtrlVal.setEnabled(True)
            else:
                msg = "Failed to read the controls: {} {}".format(qctrl,
                                                                  ctrlVal)
                qCWarning(self.logCategory, msg)
                # debug_message(msg)

            self.readCamCtrl = False

    def __disable_menu_controls(self):
        # debug_message("Disable menu control")
        self.ui.lblCtrlOptions.setEnabled(False)
        self.ui.cbControlOptions.clear()
        self.ui.cbControlOptions.setEnabled(False)

    # Setup the UI for a recognized menu control. There's no data that can be
    # obtained for menu item values for a menu control, they have to be
    # hand-coded, add them here
    def setup_menu_control(self, ctrlID, reRead=False):
        # debug_message("Setup menu control: {}".format(ctrlID))

        # If we have a capture device
        if self.capDev is not None:
            # if reRead is False:
            #     debug_message("Setup control for a valid capture device")

            # Control configuration, not value
            qctrl = self.get_current_camera_control_by_ID(ctrlID)

            # Do we already have a saved setting
            ctrlVal = self.__setting_control_by_ID(ctrlID)
            if (ctrlVal is None) or (reRead is True):
                # No, re-read the control for current state
                self.readCamCtrl = True
                ctrlVal = self.get_current_camera_control_value_by_ID(ctrlID)
            if (qctrl is not None) and (ctrlVal is not None):
                # debug_message("Read the controls")
                # Populate the UI for supported cases

                # ... for POWER LINE FREQUENCY
                if ctrlID == V4L2_CID_POWER_LINE_FREQUENCY:
                    self.ui.cbControlOptions.clear()

                    self.ui.cbControlOptions.addItem("Disabled")
                    self.ui.cbControlOptions.addItem("50Hz")
                    self.ui.cbControlOptions.addItem("60Hz")

                    if ctrlVal.value == V4L2_CID_POWER_LINE_FREQUENCY_DISABLED:
                        iMenu = self.ui.cbControlOptions.findText("Disabled")
                    elif ctrlVal.value == V4L2_CID_POWER_LINE_FREQUENCY_50HZ:
                        iMenu = self.ui.cbControlOptions.findText("50Hz")
                    elif ctrlVal.value == V4L2_CID_POWER_LINE_FREQUENCY_60HZ:
                        iMenu = self.ui.cbControlOptions.findText("60Hz")
                    else:
                        iMenu = -1
                # ...for EXPOSURE AUTO
                elif ctrlID == V4L2_CID_EXPOSURE_AUTO:
                    self.ui.cbControlOptions.clear()

                    self.ui.cbControlOptions.addItem("Auto-exposure")
                    self.ui.cbControlOptions.addItem("Aperture Priority")
                    self.ui.cbControlOptions.addItem("Shutter Priority")
                    self.ui.cbControlOptions.addItem("Manual-exposure")

                    if ctrlVal.value == V4L2_EXPOSURE_AUTO:
                        iMenu = self.ui.cbControlOptions.findText("Auto-exposure")
                    elif ctrlVal.value == V4L2_EXPOSURE_MANUAL:
                        iMenu = self.ui.cbControlOptions.findText("Manual-exposure")
                    elif ctrlVal.value == V4L2_EXPOSURE_SHUTTER_PRIORITY:
                        iMenu = self.ui.cbControlOptions.findText("Shutter Priority")
                    elif ctrlVal.value == V4L2_EXPOSURE_APERTURE_PRIORITY:
                        iMenu = self.ui.cbControlOptions.findText("Aperture Priority")
                    else:
                        iMenu = -1
                else:
                    iMenu = -1

                if iMenu >= 0:
                    self.ui.cbControlOptions.setCurrentIndex(iMenu)

                # These cause a value changed event, we don't want it to set
                # the camera control if the UI is being setup from reading the
                # camera control. We will already have set switchingControl
                # True if that's so. Although these functions are the value
                # changed slots they ignore setting the camera on the basis of
                # switchingControl
                # self.ui.sbCtrlInt.setValue(ctrlVal.value)
                # self.ui.hsCtrlVal.setValue(ctrlVal.value)

                # debug_message("Enabling menu controls")
                self.ui.lblCtrlOptions.setEnabled(True)
                self.ui.cbControlOptions.setEnabled(True)

            else:
                msg = "Failed to read the controls: {} {}".format(qctrl,
                                                                  ctrlVal)
                qCWarning(self.logCategory, msg)
                # debug_message(msg)

            self.readCamCtrl = False

    # FIXME: These could throw a nameError or valueError if it does nothing
    def new_power_line_frequency(self, ctrlID, txtValue):
        if txtValue == "Disabled":
            self.replace_control_setting_by_ID(ctrlID, V4L2_CID_POWER_LINE_FREQUENCY_DISABLED)
        elif txtValue == "50Hz":
            self.replace_control_setting_by_ID(ctrlID, V4L2_CID_POWER_LINE_FREQUENCY_50HZ)
        elif txtValue == "60Hz":
            self.replace_control_setting_by_ID(ctrlID, V4L2_CID_POWER_LINE_FREQUENCY_60HZ)

    def new_auto_exposure_mode(self, ctrlID, txtValue):
        if txtValue == "Auto-exposure":
            self.replace_control_setting_by_ID(ctrlID, V4L2_EXPOSURE_AUTO)
        elif txtValue == "Aperture Priority":
            self.replace_control_setting_by_ID(ctrlID, V4L2_EXPOSURE_APERTURE_PRIORITY)
        elif txtValue == "Shutter Priority":
            self.replace_control_setting_by_ID(ctrlID, V4L2_EXPOSURE_SHUTTER_PRIORITY)
        elif txtValue == "Manual-exposure":
            self.replace_control_setting_by_ID(ctrlID, V4L2_EXPOSURE_MANUAL)

    def menu_control_changed(self, newIndex):
        # Do nothing if we are setting up the UI from the camera
        if self.readCamCtrl:
            return

        if self.capDev is not None:
            aCtrl = self.__current_camera_current_control()
            if aCtrl is not None:
                # Handle menu controls here
                if aCtrl.type == V4L2_CTRL_TYPE_MENU:
                    if (newIndex >= 0) and\
                            (newIndex < self.ui.cbControlOptions.count()):
                        # debug_message("menu control options changing to {}".format(value))
                        # Get the text for the index
                        iText = self.ui.cbControlOptions.itemText(newIndex)

                        # We need to parse all supported cases as text
                        if aCtrl.id == V4L2_CID_POWER_LINE_FREQUENCY:
                            self.new_power_line_frequency(aCtrl.id, iText)
                        if aCtrl.id == V4L2_CID_EXPOSURE_AUTO:
                            self.new_auto_exposure_mode(aCtrl.id, iText)

    # A different control was selected from the control list
    def changed_control(self, newIndex):
        # Do nothing while we are switching camera since it fills the conrol
        # list before the new camera is in a selected state
        if self.switchingDev:
            qCDebug(self.logCategory, "Control change while switching device")
            # debug_message("Control change while switching device")
            return

        # msg = "Selected control changed: {}, {}".format(newIndex,
        #                                                 self.controlIndex)
        # debug_message(msg)

        # The displayed value will be changed to the one for the new control
        # we don't want to set the camera in that case we want to read the
        # camera value.

        # The value isn't applied if the stream is not on so we need to keep
        # them and use them when creating the capture thread.

        # If we are already handling a change in the selected control do
        # nothing
        if self.switchingControl:
            qCDebug(self.logCategory, "Control change while changing control")
            # debug_message("Control change while changing control")
            return

        # The index in the UI has changed and we are not already handling that
        self.switchingControl = (newIndex != self.controlIndex)
        # debug_message("Switching control? {}".format(self.switchingControl))
        if not self.switchingControl:
            # Somehow we switched control to the one already displayed
            return

        # We can only change a control for an active camera
        if self.capDev is not None:
            # Get the current control
            aCtrl = self.__current_camera_current_control()
            if aCtrl is not None:
                # Turn off all UI for camera controls then handle each type
                # independently
                self.__disable_integer_control()
                self.__disable_boolean_controls()
                self.__disable_menu_controls()
                if aCtrl.type == V4L2_CTRL_TYPE_INTEGER:
                    self.setup_integer_control(aCtrl.id)
                elif aCtrl.type == V4L2_CTRL_TYPE_BOOLEAN:
                    self.setup_boolean_control(aCtrl.id)
                elif aCtrl.type == V4L2_CTRL_TYPE_MENU:
                    # Not all menu cases are coded, add missing ones in
                    # the following function
                    self.setup_menu_control(aCtrl.id)
                else:
                    msg = "Control ID {} ".format(aCtrl.id)
                    if aCtrl.type == V4L2_CTRL_TYPE_BUTTON:
                        msg += "is type BUTTON"
                        # debug_message(msg)
                    elif aCtrl.type == V4L2_CTRL_TYPE_INTEGER64:
                        msg += "is type INT64"
                        # debug_message(msg)
                    elif aCtrl.type == V4L2_CTRL_TYPE_CTRL_CLASS:
                        msg += "is type CLASS"
                        # debug_message(msg)
                    elif aCtrl.type == V4L2_CTRL_TYPE_STRING:
                        msg += "is type STRING"
                        # debug_message(msg)
                    else:
                        msg += "is unrecognized type"
                    qCDebug(self.logCategory, msg)

                # Special handling for auto and manual focus. We can show both
                # but only one can be active
                # ctrlName = aCtrl.name.decode('utf-8')
                # if ("focus" in ctrlName.lower()):
                #     # debug_message("Selecting focus control: {}".format(ctrlName))
                #     aCam = self.__find_current_camera()
                #     if aCam is not None:
                #         if (aCam[4] != 0) and (aCam[5] != 0):
                #             # debug_message("This camera has auto and manual focus")
                #             # It has auto-focus and focus. Find out if auto
                #             # is enabled
                #             # debug_message("Getting auto-focus value")
                #             afVal = self.get_current_camera_control_value_by_ID(aCam[5])
                #             # debug_message("Value is {}".format(afVal.value))
                #             if afVal.value == 1:
                #                 # debug_message("Auto-focus is {}".format(afVal.value))
                #                 # If current control is focus then disable it
                #                 if aCtrl.id == aCam[4]:
                #                     # debug_message("Autofocus enabled, displaying focus, disabling adjustment")
                #                     self.ui.sbCtrlInt.setEnabled(False)
                #                     self.ui.hsCtrlVal.setEnabled(False)

        # Finished switching control
        self.switchingControl = False

    # FIXME: All of the following configuration/settings currently down to
    # save_persistent_caption() might be better implemented as a persistent
    # settings class for this application. That would allow for some
    # optimization.

    # Returns the text true or false based on a bool value. Use as the text to
    # store as a persistent application settting (QSettings.setValue).
    def __bool_setting_text(self, aBool):
        if aBool:
            return "true"

        return "false"

    # Decode the text "true" (or "false") into a bool value. Use to decode a
    # persistent application setting that should be bool (QSettings.value)
    # Will return false on unrecognized text. Perhaps it should be ValueError.
    def __decode_bool_setting_text(self, theText):
        if theText == "true":
            return True

        return False

    # This might be inefficient, creates a QSettings for every use, e.g. when
    # used for loading latitude and longitude it creates and destroys two
    # QSettings objects. But, the calling code just looks tidier
    def __config_load_text(self, keyText, default=None, keyGroup=None,\
                           setting=None):
        if setting is None:
            mySet = QSettings()
        else:
            mySet = setting

        if keyGroup is not None:
            mySet.beginGroup(keyGroup)
        # if keyGroup is not None:
        #     keyText = keyGroup + "/" + keyText

        theVal = mySet.value(keyText, default)
        return theVal

    def load_persistent_bool(self, keyText, default=None, keyGroup=None,\
                             setting=None):
        theText = self.__config_load_text(keyText, default, keyGroup, setting)
        return self.__decode_bool_setting_text(theText)

    # May throw ValueError if config value is not numeric
    # default must be text...for now
    def load_persistent_float(self, keyText, default, keyGroup=None,\
                              setting=None):
        return float(self.__config_load_text(keyText, default, keyGroup,
                                             setting))

    # May throw ValueError if config value is not numeric
    # default must be text...for now
    def load_persistent_int(self, keyText, default=None, keyGroup=None,\
                            setting=None):
        return int(self.__config_load_text(keyText, default, keyGroup, setting))

    # This might be inefficient, creates a QSettings for every use, e.g. when
    # used for saving latitude and longitude it creates and destroys two
    # QSettings objects. But, the calling just code looks tidier
    def save_persistent_text(self, keyText, newValue=None, keyGroup=None,\
                             setting=None):
        if setting is None:
            mySet = QSettings()
        else:
            mySet = setting

        if keyGroup is not None:
            mySet.beginGroup(keyGroup)

        if newValue != None:
            mySet.setValue(keyText, newValue)
        else:
            # Delete keys that are to be set to a None value
            mySet.remove(keyText)

        if keyGroup is not None:
            mySet.endGroup()

    def save_persistent_bool(self, keyText, newValue, keyGroup=None,
                             setting=None):
        theText = self.__bool_setting_text(newValue)
        self.save_persistent_text(keyText, theText, keyGroup, setting)

    def save_persistent_float(self, keyText, newValue, keyGroup=None,
                              setting=None):
        # float will be translated automatically to text, keep the function
        # names tidy
        self.save_persistent_text(keyText, newValue, keyGroup, setting)

    def save_persistent_int(self, keyText, newValue, keyGroup=None,
                            setting=None):
        # Int will be translated automatically to text, keep the function names
        # tidy
        self.save_persistent_text(keyText, newValue, keyGroup, setting)

    # This might be inefficient, gets the camera name from the UI for every
    # use, e.g. when used for loading a set of camera settings such as the
    # exposure targets. But, the calling just code looks tidier
    def load_per_camera_text(self, perCamKey, useCam=None, default=None):
        camName = useCam

        # If not given a camera name, get the one in the UI
        if camName is None:
            camName = self.ui.cbCameras.currentText()

        # If we have a camera name, key and return the saved value for the key
        # with the camera as the key group
        if camName != "":
            return self.__config_load_text(perCamKey, default, camName)

        return default

    def load_per_camera_bool(self, perCamKey, useCam=None, default="false"):
        theText = self.load_per_camera_text(perCamKey, useCam, default)
        return self.__decode_bool_setting_text(theText)

    # May throw ValueError if config value is not numeric
    # default must be text...for now
    def load_per_camera_float(self, perCamKey, useCam=None, default="0.0"):
        return float(self.load_per_camera_text(perCamKey, useCam, default))

    # May throw ValueError if config value is not numeric
    # default must be text...for now
    def load_per_camera_int(self, perCamKey, useCam=None, default="0"):
        return int(self.load_per_camera_text(perCamKey, useCam, default))

    # FIXME: This might be inefficient, gets the camera name from the UI for
    # every use, e.g. when used for saving a set of camera settings such as the
    # exposure targets. But, the calling just code looks tidier
    def save_per_camera_text(self, perCamKey, newValue, useCam=None):
        camName = useCam
        if camName is None:
            # No camera specified, use the one in the UI
            camName = self.ui.cbCameras.currentText()

        # If we have a camera name, generate the key and return the saved value
        if camName != "":
            self.save_persistent_text(perCamKey, newValue, camName)

    def save_per_camera_bool(self, perCamKey, newValue=None, useCam=None):
        if newValue is not None:
            theText = self.__bool_setting_text(newValue)
        else:
            # This will cause the mey to be removed
            theText = None
        self.save_per_camera_text(perCamKey, theText, useCam)

    def save_per_camera_float(self, keyText, newValue, useCam=None):
        # Float will be translated automatically to text, keep the function
        # names tidy
        self.save_per_camera_text(keyText, newValue, useCam)

    def save_per_camera_int(self, keyText, newValue, useCam=None):
        # Int will be translated automatically to text, keep the function names
        # tidy
        self.save_per_camera_text(keyText, newValue, useCam)

    def load_persistent_lat_lon(self):
        lat = self.load_persistent_float(self.kLatitude, "181.0")
        lon = self.load_persistent_float(self.kLongitude, "181.0")
        if (lat >= -90.0) and (lat <= 90.0) and (lon >= -180.0) and\
                (lon <= 180.0):
            # Set them locally
            self.latitude = lat
            self.longitude = lon
        else:
            # Invalid persistent value, assume zero longitude on the equator
            self.latitude = 0.0
            self.longitude = 0.0

        # Use them for time-of-day mathematics
        self.todCalc.set_latitude(self.latitude)
        self.todCalc.set_longitude(self.longitude)

        # centHour = int((lon / 15.0))
        # minHour = centHour - 1
        # maxHour = centHour + 1

        # Timezone clock offset
        # self.tzOffset = 3600.0 * centHour
        # self.tzOffset = 1.0 * -3600.0
        self.tzOffset = 0.0

    def save_persistent_lat_lon(self):
        self.save_persistent_float(self.kLatitude, self.latitude)
        self.save_persistent_float(self.kLongitude, self.longitude)

    def load_persistent_capture_file_info_for_camera(self):
        useFilename = self.load_per_camera_text(self.kCaptureFilename)
        self.ui.leCapFile.setText(useFilename)
        try:
            self.imageFileQuality =\
                self.load_per_camera_int(self.kImageFileQuality)
        except (NameError, ValueError):
            # Unrecognized name or invalid value, assume 100 (best quality)
            self.imageFileQuality = 100

        # Set the quality controls, choosing automatically by default
        self.set_image_quality_control_states()

    def save_capture_quality(self):
        # If the quality setting is enabled and changed
        if self.ui.hsImgQuality.isEnabled():
            curQual = self.ui.hsImgQuality.value()
            if curQual != self.imageFileQuality:
                self.imageFileQuality = curQual
                self.save_per_camera_int(self.kImageFileQuality,
                                         self.imageFileQuality)

    # This handles the editing of the capture filename in the UI and saves it
    # if it hasn't changed for a while and looks like a filename. Also makes a
    # quality setting persistent. Force is set true to ignore the wait for
    # changing to finish, e.g. in the case of using the file dialog to select
    # a file which causes a single line edit value change to the final result
    def save_persistent_capture_file_info_for_camera(self, force=False):
        if self.saveCapFilename != 0.0 or force:
            tSinceEdit = time.time() - self.saveCapFilename
            # Allow some seconds
            if (tSinceEdit > self.saveEditedCaptureFileNameDelay) or force:
                # The file must look at least like
                # [<path-to>/]<file>.<ext>
                if self.__reasonable_filename():
                    useFilename = self.ui.leCapFile.text()
                    self.save_per_camera_text(self.kCaptureFilename,
                                              useFilename)

                    # Enable/disable quality based on apparent file type
                    self.set_image_quality_control_states()

                self.save_capture_quality()

                self.saveCapFilename = 0.0

    def load_persistent_AF_for_camera(self):
        return self.load_per_camera_bool(self.kPerCameraAF)

    def save_persistent_AF_for_camera(self, ctrlID, AFval=None):
        # Get the current camera (we need to know an auto-focus control ID for
        # it)
        aCam = self.__find_current_camera()
        # If there is a current camera
        if aCam is not None:
            # If it has an auto-focus control ID matching the supplied conrol ID
            # (probably due to that control being set, but the saved state can
            # be deleted if the AFval argument is None and the camera has a
            # known autofocus control that we got as the ctrlID argument)
            if ctrlID == aCam[5]:
                self.camAF = AFval
                # debug_message("Saving per-camera AF: {}".format(self.camAF))
                self.save_per_camera_bool(self.kPerCameraAF, self.camAF)

    def load_persistent_focus_for_camera(self):
        return self.load_per_camera_int(self.kPerCameraFocus, default="1")

    def save_persistent_focus_for_camera(self, ctrlID, focusVal=None):
        # Only bother if AF is dissabled
        if not self.camAF:
            # Get the current camera (we need to know a focus control ID for it)
            aCam = self.__find_current_camera()
            # If there is a current camera
            if aCam is not None:
                # If it has a focus control ID matching the supplied control ID
                # (probably due to that control being set currently, but the
                # saved state can be deleted if the AFval argument is None and
                # the camera has a known focus control that we got as the ctrlID
                # argument)
                if ctrlID == aCam[4]:
                    # Make the supplied value our preferred focus value
                    self.camFocus = focusVal
                    # Save it, if focudValue is None the key will be deleted
                    # msg = "Saving per-camera focus: {}".format(self.camFocus)
                    # debug_message(msg)
                    self.save_per_camera_int(self.kPerCameraFocus,
                                             self.camFocus)

    def __load_persistent_day_targets(self):
        '''
        Load daytime persistent frame property targets (minimum and maximum).
        These are used as the nighttime targets (i.e. daytime targets are all
        day targets) if there are no persistent nighttime targets.
        '''

        # Maximums
        self.frameDayBrightnessTarget =\
            self.load_per_camera_float(self.kDayBrightnessTarget, None, "120.0")
        self.frameDayContrastTarget =\
            self.load_per_camera_float(self.kDayContrastTarget, None, "50.0")
        self.frameDaySaturationTarget =\
            self.load_per_camera_float(self.kDaySaturationTarget, None, "40.0")

        # Minimums, use maximums as defaults so there would be no min~max range
        # if there are only maximum's in saved state
        self.frameDayBrightnessMinTarget =\
            self.load_per_camera_float(self.kDayBrightnessMinTarget, None,
                                       "{}".format(self.frameDayBrightnessTarget))
        self.frameDayContrastMinTarget =\
            self.load_per_camera_float(self.kDayContrastMinTarget, None,
                                       "{}".format(self.frameDayContrastTarget))
        self.frameDaySaturationMinTarget =\
            self.load_per_camera_float(self.kDaySaturationMinTarget, None,
                                       "{}".format(self.frameDaySaturationTarget))

    def __load_persistent_night_targets(self):
        '''
        Load daytime persistent frame property targets (minimum and maximum).
        If there are any property targets that have no persistent state then the
        value used will be -1 which causes the daytime target for the same
        property to be used as an all-day target instead.
        '''

        # Maximums, use -1 as default and that will cause the daytime target for
        # the same propery to be used all day.
        self.frameNightBrightnessTarget =\
            self.load_per_camera_float(self.kNightBrightnessTarget, None,
                                       "-1.0")
        self.frameNightContrastTarget =\
            self.load_per_camera_float(self.kNightContrastTarget, None, "-1.0")
        self.frameNightSaturationTarget =\
            self.load_per_camera_float(self.kNightSaturationTarget, None,
                                       "-1.0")

        # Minimums, use maximums as default so there woul be no range if there
        # is a saved night maximum target or use the daytime value all day if
        # there is no saved night maximum target.
        self.frameNightBrightnessMinTarget =\
            self.load_per_camera_float(self.kNightBrightnessMinTarget, None,
                                       "{}".format(self.frameNightBrightnessTarget))
        self.frameNightContrastMinTarget =\
            self.load_per_camera_float(self.kNightContrastMinTarget, None,
                                       "{}".format(self.frameNightContrastTarget))
        self.frameNightSaturationMinTarget =\
            self.load_per_camera_float(self.kNightSaturationMinTarget, None,
                                       "{}".format(self.frameNightSaturationTarget))

    def __load_persistent_targets(self):
        '''
        load persistent frame property targets
        '''

        self.__load_persistent_day_targets()
        self.__load_persistent_night_targets()

    def __save_persistent_day_targets(self):
        '''
        Save daytime persistent frame property targets (minimum and maximum).
        '''

        # Maximums
        self.save_per_camera_float(self.kDayBrightnessTarget,
                                   self.frameDayBrightnessTarget)
        self.save_per_camera_float(self.kDayContrastTarget,
                                   self.frameDayContrastTarget)
        self.save_per_camera_float(self.kDaySaturationTarget,
                                   self.frameDaySaturationTarget)

        # Minimums
        self.save_per_camera_float(self.kDayBrightnessMinTarget,
                                   self.frameDayBrightnessMinTarget)
        self.save_per_camera_float(self.kDayContrastMinTarget,
                                   self.frameDayContrastMinTarget)
        self.save_per_camera_float(self.kDaySaturationMinTarget,
                                   self.frameDaySaturationMinTarget)

    def __save_persistent_night_targets(self):
        '''
        Save nighttime persistent frame property targets (minimum and maximum).
        '''

        # Maximums
        self.save_per_camera_float(self.kNightBrightnessTarget,
                                   self.frameNightBrightnessTarget)
        self.save_per_camera_float(self.kNightContrastTarget,
                                   self.frameNightContrastTarget)
        self.save_per_camera_float(self.kNightSaturationTarget,
                                   self.frameNightSaturationTarget)

        # Minimums
        self.save_per_camera_float(self.kNightBrightnessMinTarget,
                                   self.frameNightBrightnessMinTarget)
        self.save_per_camera_float(self.kNightContrastMinTarget,
                                   self.frameNightContrastMinTarget)
        self.save_per_camera_float(self.kNightSaturationMinTarget,
                                   self.frameNightSaturationMinTarget)

    def __save_persistent_targets(self):
        '''
        Make exposure target settings persistent
        '''

        self.__save_persistent_day_targets()
        self.__save_persistent_night_targets()

    # Load caption data from configuration for the current camera
    def load_persistent_caption(self):
        self.captionText = self.load_per_camera_text(self.kCaptionText, None,
                                                     "")
        self.captionDateStamp = self.load_per_camera_bool(self.kCaptionDateStamp,
                                                          None, "false")
        self.captionTimeStamp = self.load_per_camera_bool(self.kCaptionTimeStamp,
                                                          None, "false")
        self.captionTwoFourHour =\
            self.load_per_camera_bool(self.kCaptionTwoFourHour, None, "false")
        try:
            self.captionLocation =\
                self.load_per_camera_int(self.kCaptionLocation, None, "11")
        except ValueError:
            self.captionLocation = 11
        try:
            self.captionInsetX =\
                self.load_per_camera_int(self.kCaptionInsetX, None, "10")
        except:
            self.captionInsetX = 10
        try:
            self.captionInsetY =\
                self.load_per_camera_int(self.kCaptionInsetY, None, "6")
        except:
            self.captionInsetX = 6
        try:
            self.captionTextR = self.load_per_camera_int(self.kCaptionTextR,
                                                         None, "0")
        except ValueError:
            self.captionTextR = 0
        try:
            self.captionTextG = self.load_per_camera_int(self.kCaptionTextG,
                                                         None, "0")
        except ValueError:
            self.captionTextG = 0
        try:
            self.captionTextB = self.load_per_camera_int(self.kCaptionTextB,
                                                         None, "0")
        except ValueError:
            self.captionTextB = 0

        self.captionFontFamily = self.load_per_camera_text(self.kCaptionFontFamily,
                                                           None,
                                                           "Liberation Sans")
        self.captionFontFilename = self.theFonts.font_file_for_font_family_filtered(self.captionFontFamily, 400, QFont.StyleNormal)
        try:
            self.captionFontSize = self.load_per_camera_int(self.kCaptionFontSize,
                                                            None, "16")
        except ValueError:
            self.captionFontSize = 16

    # Make caption settings persistent
    def save_persistent_caption(self):
        self.save_per_camera_text(self.kCaptionText, self.captionText)
        self.save_per_camera_bool(self.kCaptionDateStamp, self.captionDateStamp)
        self.save_per_camera_bool(self.kCaptionTimeStamp, self.captionTimeStamp)
        self.save_per_camera_bool(self.kCaptionTwoFourHour,
                                  self.captionTwoFourHour)
        self.save_per_camera_int(self.kCaptionLocation, self.captionLocation)
        self.save_per_camera_int(self.kCaptionInsetX, self.captionInsetX)
        self.save_per_camera_int(self.kCaptionInsetY, self.captionInsetY)
        self.save_per_camera_int(self.kCaptionTextR, self.captionTextR)
        self.save_per_camera_int(self.kCaptionTextG, self.captionTextG)
        self.save_per_camera_int(self.kCaptionTextB, self.captionTextB)
        self.save_per_camera_text(self.kCaptionFontFamily,
                                  self.captionFontFamily)
        self.save_per_camera_int(self.kCaptionFontSize, self.captionFontSize)

    def load_persistent_settings_for_camera(self):
        self.__load_persistent_targets()
        self.load_persistent_caption()
        self.load_persistent_capture_file_info_for_camera()
        aCam = self.__find_current_camera()
        if aCam is not None:
            if aCam[5] is not None:
                self.camAF = self.load_persistent_AF_for_camera()
                qCDebug(self.logCategory,
                        "Loaded camera AF: {}".format(self.camAF))
                # debug_message("Loaded camera AF: {}".format(self.camAF))
            if aCam[4] is not None:
                self.camFocus = self.load_persistent_focus_for_camera()
                qCDebug(self.logCategory,
                        "Loaded camera focus: {}".format(self.camFocus))
                # debug_message("Loaded camera focus: {}".format(self.camFocus))

    def upgrade_configuration(self, fromVer):
        return True

    def verify_version(self):
        # Load version saved in configuration
        vText = self.__config_load_text("Version", default="0.0.0")
        cfgVersion = QVersionNumber.fromString(vText)
        vChange = QVersionNumber.compare(cfgVersion, self.version)
        if vChange == 0:
            # Config is for our version
            return True
        elif vChange < 0:
            return self.upgrade_configuration(cfgVersion)
        elif vChange > 0:
            # Unsupported, config is for a greater version than our instance
            title = "Error: Saved configuration version is unsupported. "
            title += "{} > {}".format(cfgVersion.toString(),
                                      self.version.toString())
            msg = "The saved CSDevs configuration is for a later version of "
            msg += "CSDevs than the version you are running. You must upgrade "
            msg += "the CSDevs version you run.\n\n"
            msg += "CSDevs can upgrade your saved configuration from one for a "
            msg += "lower version of CSDevs to one for this version but it "
            msg += "cannot downgrade the saved configuration from a higher "
            msg += "version of CSDevs to the one this version of CSDevs "
            msg += "can use."
            QMessageBox.critical(self, title, msg)

        return False

    def load_persistent_settings(self):
        # FIXME: Load only the saved version, compare it with the class member
        # version, create a function to convert persistent settings to higher
        # version models only. If loaded version is less than class member
        # version then convert saved settings to the model in this class (this
        # version) and re-save them before loading any persistent settings.
        self.load_persistent_lat_lon()
        self.load_persistent_settings_for_camera()

    def __get_time_bounce(self, fromTimeFrac=0.0):
        '''
        Given a number that varies between zero and one, modify it to range from
        zero to one to zero, peaking when 0.5 is supplied
        '''

        if fromTimeFrac > 0.5:
            tBounce = 1.0 - fromTimeFrac
        else:
            tBounce = fromTimeFrac

        return 2.0 * tBounce

    # Given a number that varies between zero and one, modify it to range from
    # one to zero to one, reaching zero when 0.5 is supplied
    def __get_time_reverse_bounce(self, fromTimeFrac=0.0):
        if self.bounceVal < 0.0:
            return (1.0 - self.__get_time_bounce(fromTimeFrac))

        return 1.0 - self.bounceVal

    # Compute colors for sky and ground based on the dimmest being as the sky
    # object crosses the horizon and brightest being as the sky object is at the
    # highest position in the view.
    def __get_sky_color(self, timeFrac=0.0, assumeDaytime=False):
        if self.revBounceVal < 0.0:
            tRevBounce = self.__get_time_reverse_bounce(timeFrac)
        else:
            tRevBounce = self.revBounceVal

        skyScale = pow(tRevBounce, 4.0)

        if (assumeDaytime is False) and self.todCalc.its_nighttime():
            defaultSky = QColor(0x2A, 0x2A, 0x35)
            if timeFrac >= 0.0:
                # skyNow = defaultSky.lighter(100.0 + (75.0 * tRevBounce))
                skyNow = defaultSky.lighter(100.0 + (75.0 * skyScale))
                # skyNow = defaultSky.lighter(100.0 + (75.0 * pFrac))
        else:
            # defaultSky = QColor(0x87, 0xCE, 0xFA)
            defaultSky = QColor.fromRgb(0x57, 0x81, 0xf4)
            skyNow = defaultSky
            if timeFrac >= 0.0:
                # skyScale = pow(2.0, tRevBounce) - 1.0
                skyNow = defaultSky.darker(100.0 + (150.0 * skyScale))

        if timeFrac < 0.0:
            skyNow = defaultSky

        return skyNow

    def __get_ground_color(self, timeFrac=0.0):
        defaultGround = QColor(0x7C, 0xFC, 0)

        if self.bounceVal < 0.0:
            tBounce = self.__get_time_bounce(timeFrac)
        else:
            tBounce = self.bounceVal
        if self.revBounceVal < 0.0:
            tRevBounce = self.__get_time_reverse_bounce(timeFrac)
        else:
            tRevBounce = self.revBounceVal

        if timeFrac >= 0.0:
            if self.todCalc.its_daytime():
                groundNow = defaultGround.darker(100.0 + (200.0 * tRevBounce))
            else:
                groundNow = defaultGround.darker(300.0 + (250.0 * tBounce))
        else:
            groundNow = defaultGround

        return groundNow

    def __get_ground_sky_colors(self, timeFrac, assumeDaytime=False):
        # Get the bounce and reverse bounce values as class state
        self.bounceVal = self.__get_time_bounce(timeFrac)
        self.revBounceVal = self.__get_time_reverse_bounce(timeFrac)
        # debug_message("Getting colors from t {}, saving bounce fractions: {}, {}".format(timeFrac, self.bounceVal, self.revBounceVal))

        # Use the existing functions, they won't re-calculate the bounce values
        # in the presence of the class state
        groundNow = self.__get_ground_color(timeFrac)
        skyNow = self.__get_sky_color(timeFrac, assumeDaytime)

        # Drop the saved bounce values
        self.bounceVal = -1.0
        self.revBounceVal = -1.0

        # Return both as a tuple
        return (groundNow, skyNow)

    def iClamp(self, n, minn, maxn):
        if n < minn:
            return minn
        elif n > maxn:
            return maxn
        else:
            return n

    def __offset_point(self, originPos, requiredPos):
        '''
        When the sun ellipse (circle) item is re-positioned it is a relative
        movement to where it was originally drawn, so so if we only have an
        absolute positions to place it at we need to take the offset from origin
        to new absolute position as the required shift.

        * This is not used for the moon because it accepts absolute positioning
        '''

        return requiredPos.__sub__(originPos)

    def __get_sun_color(self, dayFrac):
        '''
        Generate a sun color between rise/set color and nnon color based on
        constant definitions for them and given the fraction the current time is
        of noon.

        Parameters
        ----------
            dayFrac: float
                Current time as a fraction of all daytime today

        Returns
        -------
            A QColor for the sun at the supplied fraction of daytime
        '''

        if (dayFrac >= 0) and (dayFrac <= 1.0):
            # Get the time as a fraction either side of noon (1.0)
            gradient = self.__get_time_bounce(dayFrac)

            # We have to scale the gradient for green and blue to have them stay
            # low at rise/set but red level is fairly constant so we can use the
            # time fraction as-is
            pGradG = pow(gradient, 0.15)
            pGradB = pow(gradient, 0.15)

            '''
            Those are in keeping with what I understand of sunset, noon, sunset
            sun/sky colors. There is most blue scattering at noon and least at
            rise/set. This is why the noon sky is blue and why the sun is yellow
            at most times. It contains a mix that is mostly a constant red power
            with a wide range in green power between low that's 40% of red at
            rise/set and a little higher than red at noon. But blue ranges
            between 33% rise/set and only gets to 70% of red power at noon. But
            rise/set are no more than about 3% each of the day at equinox. So,
            for the green and blue to remain low on the disk over enough time to
            see red for a while at rise/set and for the sun's disk to quickly
            become yellow then green and blue power gradients must be steeper at
            rise/set and flatter the closer we get to noon. The day fraction is
            from 0 (rise) to 1 (noon) to 0 (set) so raising that fraction to a
            power < 1.0 makes it steep at rise/set (left and right edges of
            the curve) and flatter closer to noon (center of curve) and a red
            gradient doesn't really need special handling, it stays about the
            same power all day.
            '''

            # So, calculate R, G and B for the present time of day, clamping
            # each at limits
            nowR = self.iClamp(int(self.RSunLow + gradient * self.RdSun),
                               self.RSunMin, self.RSunMax)
            nowG = self.iClamp(int(self.GSunLow + pGradG * self.GdSun),
                               self.GSunMin, self.GSunMax)
            nowB = self.iClamp(int(self.BSunLow + pGradB * self.BdSun),
                               self.BSunMin, self.BSunMax)

            # Create a sun color from the result
            nowColor = QColor.fromRgb(nowR, nowG, nowB)
            # qCDebug(self.logCategory,
            #         "Making SUN color {}".format(nowColor.name()))
        else:
            # Outside of daytime, it doesn't get used but return the first or
            # last value that would be used in daytime, the rise color
            nowColor = self.colorSunLow

        return nowColor

    # Given ellipse width and height, their product and an angle in radians
    # around the ellipse return the polar length from center to the point on
    # the ellipse at that angle
    def __polar_length(self, elA, elB, elAB, elTheta):
        aElem = (elA * sin(elTheta))**2
        bElem = (elB * cos(elTheta))**2

        return elAB / sqrt(aElem + bElem)

    def __get_day_view_scene(self, view):
        # If it has no scene, add one
        scene = view.scene()
        if scene is None:
            scene = QGraphicsScene()
            view.setScene(scene)
            self.newScene = True

        return scene

    def __get_sky_object_polar_coordinates(self, viewSize, center, t, rObject):
        '''
        Given the size of a view, a center point, a fraction of the day/night
        passed and a radius for an object to draw then use the fraction of day
        or night (each a 180 degree rotation) and compute the polar co-ordinates
        to position something with the radius along an ellispse in something
        with the size
        '''

        # Get another size that's half of that supplied width but the same
        # height, assuming we are calculating a rotation above and around the
        # low center position
        halfSize = QSize(viewSize.width() / 2, viewSize.height())

        # Get the product of the ellipse width and height
        elAB = halfSize.width() * halfSize.height()

        # Sweep between points one pixel below the left and right
        # horizon limits...using radians
        hLimit = halfSize.width() - rObject
        leftStart = atan2(0 - hLimit, -1)
        rightStart = atan2(hLimit, -1)

        # Should be just over pi radians
        sweepAngle = abs(leftStart - rightStart)

        # But, if we just multiply sweepAngle by the fraction of the
        # day/night passed then one end will be at zero radians and all the
        # margin will be at the other end. We need to offset every
        # object's angle by half the margin
        sweepOffset = (sweepAngle - pi) / 2.0

        # Calculate the current angle simply as a fraction of sweep
        angle = t * sweepAngle

        # Get the direction to the Sun (are we in the Southern or Northern
        # hemisphere). True is Northern, False is Southern. True means the
        # sun/moon in a Southerly direction
        skyViewSouth = (self.latitude >= 0.0)

        # Correct it for view direction and the below horizon margins
        if skyViewSouth:
            polAngle = (pi - angle) + sweepOffset
            # debug_message("S: polar angle {}".format(polAngle))
        else:
            polAngle = angle - sweepOffset

        # We have the polar angle, get the polar length
        polLen = self.__polar_length(halfSize.width(), halfSize.height(),
                                     elAB, polAngle)

        # debug_message("Sky object polar: {}, {}".format(polAngle, polLen))

        return (polLen, polAngle)

    def __polar_to_point(self, polLen, polAngle, pCenter, rObject):
        '''
        Given a polar co-ordinate, a center position it is relative to and an
        object radius (hypotenuse) dompute an rectangular QPointF co-ordinate
        for it
        '''

        # x is just the polar length times the cosine of the polar angle...
        # BUT, the draw for the object does it in a rectangle that contains
        # it. So, on the left we can start at the first pixel but on the
        # right we must start object diameter pixels from the right of the
        # view in order to see it. We already made the ellipse width short
        # by the object diameter so if we position it short by object
        # radius it stays in view when above the horizon
        # BUT, the ellipse is currently centered around co-ordinate 0, 0.
        # Also re-position X to the ellipse center's X
        xObject = int(polLen * cos(polAngle) - rObject + pCenter.x())

        # y is just the polar length times the sine of the polar angle...
        # BUT, Because the view has co-ordinates that grow from zero at the
        # top to higher numbers lower down the view we get the lower half
        # of an ellipse. We have to subtract the y value from the sky
        # height
        yObject = int(pCenter.y() - polLen * sin(polAngle))

        # debug_message("Sky object: {}, {}".format(xObject, yObject))
        # qCDebug(self.logCategory,
        #         "Sky object coords: {}, {}".format(xObject, yObject))

        return QPointF(xObject, yObject)

    def __verify_moon_pixmap(self, dObject):
        '''
        Make sure we have a scaled pixmap of the moon in the object
        '''

        # Create the moon, day or night, it will just be underground
        # during day. Use the image of the moon but don't re-scale and
        # change format of the image for every draw, store a copy of
        # the pixmap in the object the first time we scale and convert
        # it and use that after (it's only a few tens of pixels x and y)
        if self.pmMoon is None:
            # For nighttime, use our image of the moon and scale it
            # to the required radius (moon Y is 2684 of image 2809)
            yMoonScale = 2809.0 * dObject / 2684.0
            scaledMoon = self.theMoon.scaledToHeight(yMoonScale)

            # Use a pixmap in the scene
            self.pmMoon = QPixmap.fromImage(scaledMoon)

    def __draw_new_day_scene(self):
        '''
        If no scene exists, or create a new one has been enabled then initialize
        the scene by clearing it, creating the sky, sun, moon and ground objects
        placing the sun and moon behind the ground as a starting/rest point. We
        Won't use target colors here, just basic ones. Updating will set them
        correctly.

        This is also used to get the scene object for an update when it doesn't
        have to be re-created.

        FIXME: This is probably not safe from exceptions and could leave some
               elements not drawn but assumed present
        '''

        # Find the widgit to draw on
        view = self.findChild(QGraphicsView, "dayIcon")
        if view is not None:
            scene = self.__get_day_view_scene(view)
            if self.newScene is True:
                scene.clear()
                qCDebug(self.logCategory, "New day scene, objects cleared")

                # No objects drawn with no colors used...yet
                self.colorSky = QColor("black")
                self.colorGround = QColor("black")
                self.sceneSky = None
                self.sceneGround = None
                self.colorSun = QColor("black")
                self.sceneSun = None
                self.pointSun = None
                self.sceneMoon = None
                self.pointMoon = None

                # Get the size of the view
                vSize = view.size()

                # Set the scene rectangle to match the view
                scene.setSceneRect(0.0, 0.0, vSize.width() * 1.0,
                                   vSize.height() * 1.0)

                # Work out some sizes for objects in the sky
                objectRad = 12.0 * vSize.height() / 128.0
                objectDiam = 2.0 * objectRad

                # Get the size for the sky
                skySize = QSize(vSize.width(), int(85.0 *
                                                   vSize.height() / 128.0))

                # Pen and brush in temporary color for the sky
                tmpPen = QPen(QColorConstants.Svg.lightblue,
                              1,
                              Qt.SolidLine,
                              Qt.SquareCap,
                              Qt.BevelJoin)
                tmpBrush = QBrush(QColorConstants.Svg.lightblue)

                # Add the sky
                self.sceneSky = scene.addRect(0.0, 0.0, skySize.width(),
                                              skySize.height(),
                                              tmpPen, tmpBrush)
                self.colorSky = QColorConstants.Svg.lightblue

                # Make sure we have a moon image pixmap
                self.__verify_moon_pixmap(objectDiam)

                # Rest sun and moon positions
                self.pointSun = QPointF(0.0,
                                        skySize.height() + 2.0 * objectDiam)
                self.pointMoon = QPointF(0.0,
                                         skySize.height() +\
                                            2.0 * self.pmMoon.height())

                # Pen and brush in temporary color for the sun
                tmpPen = QPen(QColorConstants.Svg.yellow,
                              1,
                              Qt.SolidLine,
                              Qt.SquareCap,
                              Qt.BevelJoin)
                tmpBrush = QBrush(QColorConstants.Svg.yellow)

                # Just draw the sun as a colored circle and keep a reference in
                # the object
                self.sceneSun = scene.addEllipse(self.pointSun.x(),
                                              self.pointSun.y(),
                                              objectDiam,
                                              objectDiam,
                                              tmpPen,
                                              tmpBrush)
                self.colorSun = QColorConstants.Svg.yellow

                # Put the moon image pixmap and on the scene as an item and keep
                # a reference in the object
                self.__verify_moon_pixmap(objectDiam)
                itemMoon = QGraphicsPixmapItem(self.pmMoon)
                itemMoon.setOffset(self.pointMoon)
                scene.addItem(itemMoon)
                self.sceneMoon = itemMoon
                # qCDebug(self.logCategory, "Added moon to clear scene at {}".format(self.pointMoon))
                # qCDebug(self.logCategory, " Offset is {}".format(self.sceneMoon.offset()))

                # Pen and brush in temporary color for the ground
                tmpPen = QPen(QColorConstants.Svg.green,
                              1,
                              Qt.SolidLine,
                              Qt.SquareCap,
                              Qt.BevelJoin)
                tmpBrush = QBrush(QColorConstants.Svg.green)

                # Draw the ground, it will ultimately cover one of the movable
                # objects, moon during the day, sun during the night. For now it
                # covers both and the update function moves the correct one into
                # view and corrects all colors
                groundHeight = vSize.height() - skySize.height()
                self.sceneGround = scene.addRect(0.0,
                                                 skySize.height(),
                                                 vSize.width(),
                                                 groundHeight,
                                                 tmpPen,
                                                 tmpBrush)
                self.colorGround = QColorConstants.Svg.green

                # If we get here all the scene objects should exist with basic
                # coloring and both moon and sun out-of-view
                self.newScene = False

            # We return the scene whether or not we cleared and did a new setup
            # of it
            return scene

        # Didn't get the scene to render on, shouldn't happen
        return None

    def __recolor_scene_item(self, sItem, curColor, newColor):
        '''
        Take a scene item, it's current color and a new color and if they differ
        replace the pen and brush for the item with ones having the new color
        '''

        # Create a pen and brush for sky only if the sky color changed
        if curColor.name() != newColor.name():
            newPen = QPen(newColor,
                          1,
                          Qt.SolidLine,
                          Qt.SquareCap,
                          Qt.BevelJoin)
            newBrush = QBrush(newColor)
            sItem.setPen(newPen)
            sItem.setBrush(newBrush)

            return True

        return False

    def __draw_icon_by_angle(self):
        '''
        Draw a pretend time-of-day view as a clock that can be used to infer
        something about outside brightness at the current time. This is updated
        even if the camera is not being used. The information used to draw it
        will be used to assist automatic camera "exposure" adjustment via camera
        controls in due course.
        '''

        view = self.findChild(QGraphicsView, "dayIcon")
        if view is not None:
            # Note if we'll have a new scene
            redraw_scene = self.newScene

            # Get what should be a populated scene. It only gets drawn if needed
            scene = self.__draw_new_day_scene()
        else:
            scene = None

        if scene is not None:
            # Get the size of the scene (should match the view)
            vRect = scene.sceneRect()
            vSize = vRect.size()

            # Get the size for the sky
            skySize = QSize(vSize.width(), int(85.0 *
                                               vSize.height() / 128.0))

            # Work out some sizes for objects in the sky
            objectRad = 12.0 * vSize.height() / 128.0
            objectDiam = 2.0 * objectRad

            # Get the size for the space containing the ellipse that the sky
            # object travels in. It's full ellipse width but half ellipse
            # height. Also allow for a top, left and right one pixel margin.
            # And compensate for the draw function taking a left co-ordinate
            # and width by subtracting the objectDiameter. This allows the
            # object to stay in view when being drawn at the ellipse's right
            # extreme
            elSize = QSize(skySize.width() - 2 - objectDiam,
                           skySize.height() - 1)

            # Get the center of rotation for the sky object
            elCtr = QPoint(vSize.width() / 2, skySize.height())

            # Get the time of day as a fraction of day/night. It ranges from 0.0
            # to 1.0 through the day or night, used to compute an angle for the
            # sky object.
            self.todCalc.test_function(self.todCalc.get_time_now())
            if self.forceTime is False:
                t = self.todCalc.get_time_now_fraction_of_light_period()
            else:
                t = self.savedT + self.forceAmount
                self.savedT = t

            # Get the polar co-ordinates for the sun/moon object currently in
            # view
            polLen, polAngle = self.__get_sky_object_polar_coordinates(elSize,
                                                                       elCtr,
                                                                       t,
                                                                       objectRad)

            # With polar co-ordinates we can compute x, y
            pCenter = QPointF(elCtr.x(), skySize.height())
            xyObject = self.__polar_to_point(polLen, polAngle, pCenter,
                                             objectRad)

            # If we are re-building the scene or have changed the object
            # position then choose colors and draw/re-draw the objects
            # (sky, sun, moon, ground)
            if (redraw_scene is True) or (xyObject.x() != self.lastXObject) or\
                    (xyObject.y() != self.lastYObject):
                # Compute colors based on fraction of day/night time and get
                # pen and brush for each
                groundNow, skyNow = self.__get_ground_sky_colors(t, False)

                # Create a pen and brush for sky only if the sky color changed
                if self.__recolor_scene_item(self.sceneSky, self.colorSky,
                                             skyNow):
                    self.colorSky = skyNow

                # Create a pen and brush for ground only if the ground color
                # changed
                if self.__recolor_scene_item(self.sceneGround, self.colorGround,
                                             groundNow):
                    self.colorGround = groundNow

                if self.todCalc.its_daytime():
                    # For daytime get a suitably colored pen and brush for the
                    # sun
                    # debug_message("Daytime draw")
                    # Sun color
                    # FIXME: Is it worth making this red at sunset/sunrise?
                    sunColor = self.__get_sun_color(t)
                    if self.__recolor_scene_item(self.sceneSun, self.colorSun,
                                                 sunColor):
                        self.colorSun = sunColor

                    # Sun is already there, just move it, the circle's position
                    # is relative to the original placement so we have to use
                    # an offset position
                    skyObjPos = self.__offset_point(self.pointSun, xyObject)
                    self.sceneSun.setPos(skyObjPos)
                else:
                    # Moon is already there, but the scene item from a pixmap
                    # has a position that is absolute not relative like the sun
                    # ellipse (circle), so place the moon directly at xyOffset
                    # qCDebug(self.logCategory, "Moon from {}".format(self.sceneMoon.offset()))
                    self.sceneMoon.setOffset(xyObject)
                    # qCDebug(self.logCategory, "Moon to   {}".format(self.sceneMoon.offset()))

            # Save the position we drew the sky object at so we don't
            # re-draw in the same place
            self.lastXObject = xyObject.x()
            self.lastYObject = xyObject.y()

            # Okay, we've drawn it. Show what we've drawn
            view.show()

    # Setup latitude longitude in the dialog
    def load_settings_lat_lon(self, dlgConfig):
        dlgConfig.setLatitude(self.latitude)
        dlgConfig.setLongitude(self.longitude)

    def __load_settings_targets_day_max(self, dlgConfig):
        '''
        Load a settings dialog's targets tab's day property maximums

        Parameters
        ----------
            dlgConfig: a project dlgSettings class instance
                The settings dialog to set the property day maximums in
        '''

        dlgConfig.setDayBrightnessTarget(self.frameDayBrightnessTarget, 0,
                                         255, 1)
        dlgConfig.setDayContrastTarget(self.frameDayContrastTarget, 0,
                                       255, 1)
        dlgConfig.setDaySaturationTarget(self.frameDaySaturationTarget, 0,
                                         255, 1)

    def __load_settings_targets_day_min(self, dlgConfig):
        '''
        Load a settings dialog's targets tab's day minimum targets

        Parameters
        ----------
            dlgConfig: a project dlgSettings class instance
                The settings dialog to set the property day minimums in
        '''

        dlgConfig.setDayBrightnessMinTarget(self.frameDayBrightnessMinTarget, 0,
                                            255, 1)
        dlgConfig.setDayContrastMinTarget(self.frameDayContrastMinTarget, 0,
                                          255, 1)
        dlgConfig.setDaySaturationMinTarget(self.frameDaySaturationMinTarget, 0,
                                            255, 1)

    def __load_settings_targets_night_max(self, dlgConfig, nightOn=True):
        '''
        Load a settings dialog's targets tab's night maximum targets

        Parameters
        ----------
            dlgConfig: a project dlgSettings class instance
                The settings dialog to set the property night maximums in
            nightOn: boolean
                A rolling state of whether all property night maximums are
                usable

        Returns the value "so far" of nightOn
        '''

        if self.frameNightBrightnessTarget >= 0.0:
            tgtVal = self.frameNightBrightnessTarget
        else:
            tgtVal = self.frameDayBrightnessTarget
            nightOn = nightOn and False
        dlgConfig.setNightBrightnessTarget(tgtVal, 0, 255, 1)

        if self.frameNightContrastTarget >= 0.0:
            tgtVal = self.frameNightContrastTarget
        else:
            tgtVal = self.frameDayContrastTarget
            nightOn = nightOn and False
        dlgConfig.setNightContrastTarget(tgtVal, 0, 255, 1)

        if self.frameNightSaturationTarget >= 0.0:
            tgtVal = self.frameNightSaturationTarget
        else:
            tgtVal = self.frameDaySaturationTarget
            nightOn = nightOn and False
        dlgConfig.setNightSaturationTarget(tgtVal, 0, 255, 1)

        return nightOn

    def __load_settings_targets_night_min(self, dlgConfig, nightOn=True):
        '''
        Load a settings dialog's targets tab's night minimum targets

        Parameters
        ----------
            dlgConfig: a project dlgSettings class instance
                The settings dialog to set the property night minimums in
            nightOn: boolean
                A rolling state of whether all property night minimums are
                usable

        Returns the value "so far" of nightOn
        '''

        if self.frameNightBrightnessMinTarget >= 0.0:
            tgtVal = self.frameNightBrightnessMinTarget
        else:
            tgtVal = self.frameDayBrightnessMinTarget
            nightOn = nightOn and False
        dlgConfig.setNightBrightnessMinTarget(tgtVal, 0, 255, 1)

        if self.frameNightContrastMinTarget >= 0.0:
            tgtVal = self.frameNightContrastMinTarget
        else:
            tgtVal = self.frameDayContrastMinTarget
            nightOn = nightOn and False
        dlgConfig.setNightContrastMinTarget(tgtVal, 0, 255, 1)

        if self.frameNightSaturationMinTarget >= 0.0:
            tgtVal = self.frameNightSaturationMinTarget
        else:
            tgtVal = self.frameDaySaturationMinTarget
            nightOn = nightOn and False
        dlgConfig.setNightSaturationMinTarget(tgtVal, 0, 255, 1)

        return nightOn

    def __load_settings_targets(self, dlgConfig):
        '''
        Load the control values for a settings dialog's targets tab

        Parameters
        ----------
            dlgConfig: a project dlgSettings class instance
                The settings dialog to setup the targets tab for

        Returns the value "so far" of nightOn
        '''

        self.__load_settings_targets_day_max(dlgConfig)
        self.__load_settings_targets_day_min(dlgConfig)

        # Assume we can use all night targets. This is passed through each of
        # the night targets setup functions where it keeps a rolling state of
        # the usability of all properties and returned
        nightOn = True

        # We have to start with night targets on or we'll get -1 values for min
        # when setting max and max when setting min. That would break setting
        # min because setting it uses the valueChanged signal to keep the
        # minimum lower than the maximum. With night targets not enabled setting
        # min would compare the new value with an assumed maximum of -1 and
        # force the new minimum to be -1, which will display within the range
        # limits of the control and be seen as zero.
        dlgConfig.setNightTargetsEnabled(nightOn)

        nightOn = self.__load_settings_targets_night_max(dlgConfig, nightOn)
        nightOn = self.__load_settings_targets_night_min(dlgConfig, nightOn)

        # Disable night targets if not all of them were usable
        if nightOn is False:
            dlgConfig.setNightTargetsEnabled(nightOn)

    # Populate the settings dialog's caption tab from class state
    def load_settings_caption(self, dlgConfig):
        # Text caption on image
        dlgConfig.setCaptionText(self.captionText)
        dlgConfig.setCaptionDateStampChecked(self.captionDateStamp)
        dlgConfig.setCaptionTimeStampChecked(self.captionTimeStamp)
        dlgConfig.setCaptionTwoFourHourTimeChecked(self.captionTwoFourHour)
        dlgConfig.setCaptionLocation(self.captionLocation)
        dlgConfig.setCaptionInsetX(self.captionInsetX)
        dlgConfig.setCaptionInsetY(self.captionInsetY)
        dlgConfig.setCaptionTextR(self.captionTextR)
        dlgConfig.setCaptionTextG(self.captionTextG)
        dlgConfig.setCaptionTextB(self.captionTextB)
        dlgConfig.setCaptionFontFamily(self.captionFontFamily)
        dlgConfig.setCaptionFontSize(self.captionFontSize)

    def save_settings_lat_lon(self, dlgConfig):
        lat = dlgConfig.getLatitudeFloat()
        lon = dlgConfig.getLongitudeFloat()

        # Save them if there was a change
        if (self.latitude != lat) or (self.longitude != lon):
            self.latitude = lat
            self.longitude = lon

            # Save the lat/lon persistently
            self.save_persistent_lat_lon()

            # Use them for time-of-day mathematics
            self.todCalc.set_latitude(self.latitude)
            self.todCalc.set_longitude(self.longitude)

    def __save_settings_targets_day(self, dlgConfig):
        return

    # Store any frame targets from the dialog
    def save_settings_targets(self, dlgConfig):
        # Save the targets
        self.frameDayBrightnessTarget = dlgConfig.dayTgtBrightnessMax
        self.frameDayContrastTarget = dlgConfig.dayTgtContrastMax
        self.frameDaySaturationTarget = dlgConfig.dayTgtSaturationMax

        self.frameDayBrightnessMinTarget = dlgConfig.dayTgtBrightnessMin
        self.frameDayContrastMinTarget = dlgConfig.dayTgtContrastMin
        self.frameDaySaturationMinTarget = dlgConfig.dayTgtSaturationMin

        if dlgConfig.isNightTargetsEnabled():
            self.frameNightBrightnessTarget = dlgConfig.nightTgtBrightnessMax
            self.frameNightContrastTarget = dlgConfig.nightTgtContrastMax
            self.frameNightSaturationTarget = dlgConfig.nightTgtSaturationMax

            self.frameNightBrightnessMinTarget = dlgConfig.nightTgtBrightnessMin
            self.frameNightContrastMinTarget = dlgConfig.nightTgtContrastMin
            self.frameNightSaturationMinTarget = dlgConfig.nightTgtSaturationMin
        else:
            self.frameNightBrightnessTarget = -1.0
            self.frameNightContrastTarget = -1.0
            self.frameNightSaturationTarget = -1.0

            self.frameNightBrightnessMinTarget = -1.0
            self.frameNightContrastMinTarget = -1.0
            self.frameNightSaturationMinTarget = -1.0

        # Make them persistent
        self.__save_persistent_targets()

    def font_not_found(self, family, triedAlready):
        msg = "No known file for font family {}. ".format(self.captionFontFamily)
        if not triedAlready:
            msg += "It may have been installed since CSDevs was launched. "
            msg += "Do you want to re-scan the available fonts? "
            msg += "It might take a while!"

            btn = QMessageBox.question(self, "Unrecognized caption font",
                                       msg)
        else:
            msg += "A default font will be used "
            msg += "unless you change the caption font in settings."
            btn = QMessageBox.warning(self, "Unrecognized caption font family",
                                      msg)
        return (btn == QMessageBox.StandardButton.Yes)

    def save_settings_caption(self, dlgConfig):
        self.captionText = dlgConfig.caption_text
        self.captionDateStamp = dlgConfig.isCaptionDateStampChecked()
        self.captionTimeStamp = dlgConfig.isCaptionTimeStampChecked()
        self.captionTwoFourHour = dlgConfig.isCaptionTwoFourHourTimeChecked()
        self.captionLocation = dlgConfig.getCaptionLocation()
        self.captionInsetX = dlgConfig.getCaptionInsetX()
        self.captionInsetY = dlgConfig.getCaptionInsetY()
        self.captionTextR = dlgConfig.caption_color_red
        self.captionTextG = dlgConfig.caption_color_green
        self.captionTextB = dlgConfig.caption_color_blue
        oldFamily = self.captionFontFamily
        self.captionFontFamily = dlgConfig.captionFontFamily()
        self.captionFontSize = dlgConfig.captionFontSize()

        # Make them persistent for current camera
        self.save_persistent_caption()

        # Get the font character data file
        if self.captionFontFamily != oldFamily:
            # If no family is known assume a fair default
            if self.captionFontFamily == "":
                # Use a default if none supplied
                self.captionFontFamily = "Liberation Sans"
            # oldFont = self.captionFontFilename
            fontFound = False
            reloadFonts = False
            reloadAsked = False
            while not fontFound:
                self.captionFontFilename = self.theFonts.font_file_for_font_family_filtered(self.captionFontFamily, 400, QFont.StyleNormal)
                fontFound = (self.captionFontFilename is not None)
                if not fontFound:
                    # Perhaps the font list has changed, ask user for permission
                    # to re-load the list or say we didn't find it after a
                    # previous re-load
                    reloadFonts = self.font_not_found(self.captionFontFamily,
                                                      reloadAsked)
                    reloadAsked = True
                    if reloadFonts:
                        self.theFonts.load_font_lists()
                    else:
                        # Strictly untrue but make the loop exit at while
                        fontFound = True
            # debug_message("CHANGING CAPTION FONT FILE...")
            # debug_message("FROM: {}".format(oldFont))
            # debug_message("      {}".format(oldFamily))
            # debug_message("  TO: {}".format(self.captionFontFilename))
            # debug_message("      {}".format(self.captionFontFamily))

    # FIXME: Does this need to take care that there was a camera open when the
    # settings dialog was used in order to avoid seeing empty tuning control
    # lists
    def save_tuning_controls(self, dlgConfig):
        # Walk the tuning properties for day and night
        todName = "Day"
        while todName is not None:
            # debug_message("STARTING {} SETTINGS TUNERS".format(todName))
            # Clear the tuning control lists
            locTuningControls = self.__tod_tuning_control_settings(todName)
            locTuningControls.clear()
            # locTuningControlInfo = self.__tod_tuning_control_info(todName)
            # locTuningControlInfo.clear()

            i = -1
            while True:
                i = dlgConfig.iNextTunerForTODName(todName, i)
                if i == -1:
                    # debug_message("FINISHED {} SETTINGS TUNERS".format(todName))
                    break

                # Don't re-check if the TOD matches, just get the tuner at the
                # index we found
                aTuner = dlgConfig.tunerAtIndex(i)
                if aTuner is not None:
                    # if aTuner[1] == "Contrast":
                    #     debug_message("SAVE SETTINGS TUNER: {} {} {} is {}/{}/{}".format(todName, aTuner[0], i, aTuner[1], aTuner[5], aTuner[6]))
                    self.replace_property_control_tuning_by_TOD(todName,
                                                                aTuner)
                    camName = self.ui.cbCameras.currentText()
                    self.__config_save_camera_tuning_control(camName, aTuner,
                                                             todName)

            self.__populate_image_tuning_control_info(todName)
            if todName == "Day":
                todName = "Night"
            else:
                todName = None

    # Save state from the settings dialog and make necessary elements
    # persistent
    def save_settings(self, dlgConfig):
        self.save_settings_lat_lon(dlgConfig)
        self.save_settings_targets(dlgConfig)
        self.save_settings_caption(dlgConfig)
        self.save_tuning_controls(dlgConfig)

        # Clean up any unused config tuning control material
        # debug_message("REMOVING REDUNDANT CAMERA TUNING CONTROL CONFIG")
        camName = self.ui.cbCameras.currentText()
        self.__config_remove_redundant_camera_tuning(camName, dlgConfig)

    def settings(self):
        # Get a settings dialog
        dlgConfig = dlgSettings()

        # Populate the latitude, longitude
        self.load_settings_lat_lon(dlgConfig)

        if self.camera_is_open:
            # Set the camera name to be used to load persistent settings
            camName = self.ui.cbCameras.currentText()
            dlgConfig.set_camera_name(camName)

            # You can only set exposure with a camera being monitored
            if self.monitoring:
                aCam = self.__find_current_camera()
                # debug_message("Monitoring: {}, Pre-load settings controls for {}".format(self.monitoring, aCam))
                if aCam is not None:
                    # Try to load the controls from the camera itself
                    dlgConfig.preloadCameraControlsFromFD(self.capDev.fileno())

                    # Give the dialog the tuning and limit controls for day
                    # and night
                    # debug_message("Reset settings dialog tuning controls {}, {}".format(len(self.tuningControlSettingsDay), len(self.tuningControlSettingsNight)))
                    dlgConfig.resetTuningControls()
                    dlgConfig.reset_limit_controls()
                    iTuners = 0
                    for aTuner in self.tuningControlSettingsDay:
                        # debug_message("Add settings dialog Day tuning control {}".format(aTuner[1]))
                        dlgConfig.supplyTuningControl(aTuner, "Day")
                        iTuners += 1
                    # debug_message("Settings, Day tuners: {}".format(iTuners))
                    iTuners = 0
                    for aTuner in self.tuningControlSettingsNight:
                        # debug_message("Add settings dialog Night tuning control {}".format(aTuner[1]))
                        dlgConfig.supplyTuningControl(aTuner, "Night")
                        iTuners += 1
                    # debug_message("Settings, Night tuners: {}".format(iTuners))
                else:
                    qCDebug(self.logCategory,
                            "No tuning controls, no current camera")
                    # debug_message("No tuning controls, no current camera")
            else:
                qCDebug(self.logCategory,
                        "No tuning controls, not monitoring a camera")
                # debug_message("No tuning controls, not monitoring a camera")

            # The persistent targets and caption should be okay when the camera
            # is not being monitored
            self.__load_settings_targets(dlgConfig)
            self.load_settings_caption(dlgConfig)

        # debug_message("POPULATED SETTINGS READY TO SHOW")
        # self.__dump_tuning_controls_by_property_TOD(None, "Day")
        # dlgConfig.dumpTuners()
        result = dlgConfig.exec()
        if result == QDialog.Accepted:
            # debug_message("ACCEPTED SETTINGS, CAPTION FONT: {}".format(dlgConfig.captionFontFamily()))
            # debug_message("ACCEPTED SETTINGS READY TO SAVE")
            # self.__dump_tuning_controls_by_property_TOD(None, "Day")
            # dlgConfig.dumpTuners()
            # QCoreApplication.setApplicationName("CSDevs")
            self.save_settings(dlgConfig)
            # QCoreApplication.setApplicationName("csdevs.py")
            # debug_message("ACCEPTED SETTINGS SAVED")
            # self.__dump_tuning_controls_by_property_TOD(None, "Day")
            # dlgConfig.dumpTuners()

    def show_info(self):
        # Hide it if visible
        if self.help.isVisible():
            self.help.accept()
        # Show it if not visible
        else:
            # Try to place the info view right of the main window and
            # vertically centered with the main window. On SUSE Linux
            # Tumbleweed the size of the window and it's frame are the same
            # (2022/05/12) and computing the horizontal position is short by a
            # pixel or two and computing the vertical position puts the bottom
            # of both windows at about the same position.

            # Get my screen
            myScreen = self.screen()
            screenRect = myScreen.availableVirtualGeometry()
            screenGSize = screenRect.size()
            screenVSize = myScreen.availableVirtualSize()
            # Use the wider (it should be the sum of combined monitors)
            if screenGSize.width() > screenVSize.width():
                screenVSize = screenGSize
            # debug_message("VScreen rect: {}".format(screenRect))
            qCDebug(self.logCategory, "VScreen size: {}".format(screenVSize))
            # debug_message("VScreen size: {}".format(screenVSize))

            # Get my geometry and frame rectangles on the desktop
            myGeom = self.geometry()
            myFrame = self.frameGeometry()
            qCDebug(self.logCategory, "My geom: {}".format(myGeom))
            qCDebug(self.logCategory, "My frame: {}".format(myFrame))
            # debug_message("My geom: {}".format(myGeom))
            # debug_message("My frame: {}".format(myFrame))

            # Get the help geometry and frame rectangles relative to me
            helpGeom = self.help.geometry()
            helpFrame = self.help.frameGeometry()
            qCDebug(self.logCategory, "Help geom: {}".format(helpGeom))
            qCDebug(self.logCategory, "Help frame: {}".format(helpFrame))
            # debug_message("Help geom: {}".format(helpGeom))
            # debug_message("Help frame: {}".format(helpFrame))

            # Get half the vertical difference between the frames
            # vSpace = int((myGeom.height() - helpGeom.height()) / 2)
            vSpace = int((myFrame.height() - helpFrame.height()) / 2)
            qCDebug(self.logCategory, "Vertical space: {}".format(vSpace))
            # debug_message("Vertical space: {}".format(vSpace))

            # Which side is there room on (prefer right)
            spaceAvail = screenVSize.width() - myFrame.right()
            qCDebug(self.logCategory, "Avail right: {}".format(spaceAvail))
            # debug_message("Avail right: {}".format(spaceAvail))
            if spaceAvail > helpFrame.width():
                # Enough room on the right
                msg = "Help right: {}, {}".format(myGeom.right(),
                                                  myGeom.top() + vSpace)
                qCDebug(self.logCategory, msg)
                # debug_message(msg)

                # Move the information view to the right and vertically
                # centered
                # self.help.move(myGeom.right(), myGeom.top() + vSpace)
                self.help.move(myFrame.right(), myFrame.top() + vSpace)
            else:
                spaceLeft = myGeom.left() - helpGeom.width()
                msg = "Help left: {}, ".format(spaceLeft)
                msg += "{}".format(myGeom.top() + vSpace)
                spaceAvail = screenVSize.width() - myGeom.left()
                if spaceAvail > helpGeom.width():
                    self.help.move(myGeom.left() - helpGeom.width(),
                                   myGeom.top() + vSpace)

            self.help.show()

    def show_about(self):
        # Hide it if visible
        if self.about.isVisible():
            self.about.accept()
        # Show it if not visible
        else:
            self.about.show()
            self.about.activateWindow()

    def __reasonable_filename(self):
        # Check if the name in the UI capture file looks like it has the format
        # of an image file, this is not a good implementation (we could use an
        # image file type list but would have to maintain it. If PILlow has a
        # list of supported file types that would be best since we'll save with
        # it)
        filename = self.ui.leCapFile.text()
        qCDebug(self.logCategory, "Is {} reasonable".format(filename))
        # debug_message("Is {} reasonable".format(filename))

        # Find the last /
        lastSlash = filename.rfind("/")

        # Find a dot before the end
        dotInName = filename.rfind(".")
        # debug_message("Last / {}, Last . {}".format(lastSlash, dotInName))
        if dotInName != -1:
            # To be a reasonable filename the dot would have to be after the
            # last slash plus one and probably no more than five characters
            # before the end and not the last character
            lastChar = len(filename) - 1
            if (dotInName > (lastSlash + 1)) and (dotInName > (lastChar - 5))\
                    and (dotInName < lastChar):
                return True

        return False

    def __choose_capture_file(self):
        # If we already have a file, start browsing from it's directory
        aFile = self.ui.leCapFile.text()
        lastSlash = aFile.rfind("/")
        if lastSlash != -1:
            aDir = aFile[:lastSlash]
        else:
            aDir = ""

        # Setup a file dialog
        fDialog = QFileDialog(self, caption="Set capture image file")
        fDialog.setFileMode(QFileDialog.AnyFile)
        fDialog.setAcceptMode(QFileDialog.AcceptSave)
        if aDir != "":
            fDialog.setDirectory(aDir)
        fDialog.setNameFilter("Images (*.jpg *.jpeg *.png *bmp *.xpm)")

        # Select or create a file
        fileNames = []
        if fDialog.exec():
            # Select a file to save, this should do it's own question about
            # replacing an existing file
            fileNames = fDialog.selectedFiles()

            # We can only save to one file
            fCount = len(fileNames)
            if fCount == 1:
                self.ui.leCapFile.setText(fileNames[0])
                self.save_persistent_capture_file_info_for_camera(True)
            else:
                # Number of files is not one, show a warning
                if fCount == 0:
                    wTitle = "Unnamed file"
                    wMessage = "Unable to capture to an unidentified file"
                else:
                    # This shouldn't happen for AcceptSave
                    wTitle = "Too many files"
                    wMessage = "You can only specify one file to capture to"
                QMessageBox.warning(self, wTitle, wMessage)

    def editing_capture_filename(self, newText):
        # Note that we are editing it, don't save every character change
        self.saveCapFilename = time.time()

    def image_quality_changed(self, newQual):
        qualText = "{}".format(newQual)
        self.ui.lblImgQuality.setText(qualText)
        self.save_capture_quality()

    def connect_controls(self):
        if self.okButton.clicked is not None:
            self.lateClose.connect(self.do_late_close)
            self.okButton.clicked.connect(self.app_accepted)

        if self.aboutButton.clicked is not None:
            self.aboutButton.clicked.connect(self.show_about)

        self.ui.buttonBox.helpRequested.connect(self.show_info)

        self.ui.cbCameras.activated.connect(self.use_another_camera)
        self.ui.pbMonitor.clicked.connect(self.toggle_monitor)
        self.ui.cbFormats.activated.connect(self.changed_format)
        self.ui.lwFrameSizes.itemClicked.connect(self.frame_size_selected)
        self.capTimer.timeout.connect(self.frame_tick)

        self.ui.cbControls.currentIndexChanged.connect(self.changed_control)

        self.ui.hsCtrlVal.valueChanged.connect(self.int_HS_changed)
        self.ui.sbCtrlInt.valueChanged.connect(self.int_SB_changed)

        self.ui.cbCtrlVal.stateChanged.connect(self.boolean_control_changed)

        self.ui.cbControlOptions.currentIndexChanged.connect(self.menu_control_changed)

        self.ui.pbSettings.clicked.connect(self.settings)

        self.ui.leCapFile.textEdited.connect(self.editing_capture_filename)

        self.ui.pbDlgCapFile.clicked.connect(self.__choose_capture_file)

        self.ui.hsImgQuality.valueChanged.connect(self.image_quality_changed)

        self.todTimer.timeout.connect(self.__draw_icon_by_angle)


'''
Program entry point
'''
if __name__ == "__main__":
    # Use Qt Logging
    QLoggingCategory.setFilterRules("csdevs.*.debug=true\n"
                                    "csdev.*.warning=true\n"
                                    "csdevs.*.info=true")
    # qSetMessagePattern("%{category} %{message}")
    # qSetMessagePattern("%{file}(%{line}): %{message}")
    qSetMessagePattern("%{message}")

    # enable_debug()
    # disable_debug()
    # enable_warnings()

    app = QApplication([])

    app.setStyle('Fusion')

    # Create a search path list for icons in the theme. The first is scalable
    # icons that include list-add and list-remove for the settings dialog. The
    # second has a scalable camera-photo icon for the application. The third
    # isn't used because evolution can't be guaranteed installed where this is
    # used but it includes nicer colored list-add and list-remove than the
    # HighContrast defaults
    iconSearchPaths = []
    iconSearchPaths.append("/usr/share/icons/HighContrast/scalable/actions")
    iconSearchPaths.append("/usr/share/icons/HighContrast/scalable/devices")
    # iconSearchPaths.append("/usr/share/evolution/icons/hicolor/48x48/status")
    QIcon.setFallbackSearchPaths(iconSearchPaths)

    widget = CSDevs()
    widget.show()
    # sys.exit(app.exec_())
    sys.exit(app.exec())
