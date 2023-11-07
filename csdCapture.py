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

import time
from fcntl import ioctl
from io import BytesIO
import select
import mmap

from v4l2py.device import Device
from v4l2py.raw import (v4l2_buf_type, v4l2_buffer, v4l2_control,
                        v4l2_queryctrl, v4l2_requestbuffers,
                        V4L2_BUF_TYPE_VIDEO_CAPTURE, V4L2_MEMORY_MMAP,
                        VIDIOC_DQBUF, VIDIOC_G_CTRL, VIDIOC_QBUF,
                        VIDIOC_QUERYBUF, VIDIOC_QUERYCTRL, VIDIOC_REQBUFS,
                        VIDIOC_S_CTRL, VIDIOC_STREAMOFF, VIDIOC_STREAMON)

from PySide6.QtCore import (QLoggingCategory, QRunnable, QThread, QThreadPool,
                            qCCritical, qCDebug, qCInfo, qCWarning)
                            # qCFatal doesn't import?

from PIL import (Image, ImageDraw, ImageFont, ImageStat,
                 UnidentifiedImageError)

# from csdMessages import (disable_warnings, enable_warnings, disable_debug,
#                      enable_debug, warning_message, debug_message)


# Worker thread to handle stream off and buffer release
# It needs to own the buffers for as long as it takes to turn the stream off
# so it needs to own the stream file descriptor as well
# FIXME: This probably can't work because the file-descriptor for the camera is
#        owned by the main window not either of the thread classes in this file
#        so when they overlap operations (capture thread allocating buffers and
#        StreamOffTask freeing buffers it breaks).
class StreamOffTask(QRunnable):
    capDev = None
    buffers = []
    req = None

    logCategory = QLoggingCategory("csdevs.audio.thread.stream_off")

    def run(self):
        taskStart = time.time()
        activeThreads = QThreadPool.globalInstance().activeThreadCount()
        maxThreads = QThreadPool.globalInstance().maxThreadCount()
        msg = "STARTING STREAM OFF POOL with "
        msg += "{} active threads and {} max".format(activeThreads, maxThreads)
        qCDebug(self.logCategory, msg)
        # debug_message(msg)
        try:
            self.__stream_off()
            qCDebug(self.logCategory, "Stream is OFF")
            # debug_message("Stream is OFF")
            self.__close_capture_buffers()
            qCDebug(self.logCategory, "Closed capture buffers")
            # debug_message("Closed capture buffers")
            self.__release_capture_buffers()
            qCDebug(self.logCategory, "Released capture buffers")
            # debug_message("Released capture buffers")

            # Finished with the device, this should close the file descriptor
            self.capDev = None
            qCDebug(self.logCategory, "Reset capture device to None")
            # debug_message("Reset capture device to None")

        except (ValueError) as e:
            qCWarning(self.logCategory,
                      "Failed attempt to turn stream off with incomplete data")
            # debug_message("Failed attempt to turn stream off with incomplete data")

        taskTime = time.time() - taskStart
        qCDebug(self.logCategory,
                "Closer task run duration {}".format(taskTime))
        # debug_message("Closer task run duration {}".format(taskTime))

    @property
    def __captureBufferList(self):
        return self.buffers

    def setCaptureBufferList(self, newBufferList):
        if len(self.buffers) != 0:
            msg = "Attempt to set capture buffers in a stream off task already "
            msg += "owning capture buffers"
            qCDebug(self.logCategory, msg)
            # debug_message(msg)
            raise ValueError

        if len(newBufferList) > 0:
            for aBuf in newBufferList:
                self.buffers.append(aBuf)

    def __close_capture_buffers(self):
        '''
        Close each capture buffer in the capture buffer list member in an object
        of this class. Then clear the buffer list.
        '''

        for aBuf in self.buffers:
            aBuf.close()

        self.buffers.clear()

    def __request_capture_buffers(self, newCount):
        '''
        Request capture memory buffers to be used when streaming from the
        current object's in-use V4L2 device.

        Parameters
        ----------
            newCount: Integer
                The number of capture buffers to request from V4L2
        '''

        self.req = None
        # debug_message("Requesting {} capture buffers".format(newCount))
        try:
            if not self.capDev.closed:
                self.req = v4l2_requestbuffers()
                if self.req is not None:
                    # debug_message("Request object created")
                    self.req.type = V4L2_BUF_TYPE_VIDEO_CAPTURE
                    self.req.memory = V4L2_MEMORY_MMAP
                    self.req.count = newCount
                    for iRsv in range(len(self.req.reserved)):
                        self.req.reserved[iRsv] = 0
                    # debug_message("Request object populated")
                    ioctl(self.capDev, VIDIOC_REQBUFS, self.req)
                    # debug_message("Request capture buffers success")
                else:
                    qCWarning(self.logCategory,
                              "Allocate capture buffers request failed")
                    # debug_message("Allocate request failed")
            else:
                raise OSError
        except OSError as e:
            msg = "Failed to request {} capture buffers".format(newCount)
            qCDebug(self.logCategory, msg)
            qCDebug(self.logCategory, "Error code is {}".format(e.errno))
            # debug_message(msg)
            # debug_message("Error code is {}".format(e.errno))
            self.req = None

    def __release_capture_buffers(self):
        '''
        Free any previously requested capture buffers to be used when streaming
        from the current object's in-use V4L2 device, see
        __request_capture_buffers()
        '''

        self.__request_capture_buffers(0)
        if self.req is not None:
            if self.req.count == 0:
                self.req = None
            else:
                msg = "Release capture buffers "
                msg += "result with {} buffers ".format(self.req.count)
                qCDebug(self.logCategory, msg)
                # debug_message(msg)
        else:
            qCDebug(self.logCategory, "Release capture buffers with no result")
            # debug_message("Release capture buffers with no result")

    @property
    def __captureDevice(self):
        return self.capDev

    def setCaptureDevice(self, newCapDev):
        if self.capDev is not None:
            msg = "Attempt to set capture device in a stream off task already "
            msg += "owning a capture device"
            qCWarning(self.logCategory, msg)
            # debug_message(msg)
            raise ValueError

        self.capDev = newCapDev

    def __stream_off(self):
        '''
        Stop streaming from the in-use V4L2 device
        FIXME: This is really slow, commonly takes 75% of the time to capture
               a frame. Testing suggests it's almost all spent in the ioctl. It
               may benefit from background execution (this pool thread)
        '''

        if self.capDev is not None:
            try:
                if not self.capDev.closed:
                    buf_type = v4l2_buf_type(V4L2_BUF_TYPE_VIDEO_CAPTURE)
                    iRes = ioctl(self.capDev.fileno(), VIDIOC_STREAMOFF, buf_type)
                    if iRes != 0:
                        qCWarning(self.logCategory,
                                  "Failed to turn stream off: {}".format(iRes))
                        # debug_message("Failed to turn stream off: {}".format(iRes))
                else:
                    raise OSError
            except (TypeError, OSError) as e:
                qCWarning(self.logCategory, "Stream OFF failed")
                # debug_message("Stream OFF failed")
                if type(e) == OSError:
                    qCWarning(self.logCategory,
                              "\\_ OS error: {}".format(e.errno))
                    # debug_message("\\_ OS error: {}".format(e.errno))
        else:
            qCWarning(self.logCategory,
                      "Stream OFF task with no capture device")
            # debug_message("Stream OFF task with no capture device")
            raise ValueError


class captureThread(QThread):
    '''
    Class implementing a worker thread intended to capture an identified video
    frame from a supplied V4L2 device to a supplied filename. The "identified
    frame" is a frame number after the device is opened and allows for the
    video content to stabilize. Class emits a signal when capture is complete
    and stores captured frame's brightness, contrast and saturation.
    '''

    tThreadExit = 0
    capDev = None
    capFrame = -1
    saveFile = ""
    saveQuality = 0

    lastCaptureElapsed = 0

    buffers = []
    defaultBufCount = 16
    bufCount = 16
    limBufCount = 512
    req = None

    bufToSave = None
    theFrame = None

    # Frame statistics
    frameBrightness = 0.0
    frameContrast = 0.0
    frameSaturation = 0.0

    # Yielding: time in seconds between yields when in tight loops (none at
    # present)
    yieldLimit = 0.4

    # We start with no capture device
    brokenRx = True

    # We can only set controls during stream-on so we need a list of them here
    # that the thread creater can set
    controls = []

    # Keep a local cache of control names to save doing V4L2 ioctls
    ctrlNameCache = {}

    # We need special knowledge of auto and manual focus control IDs to manage
    # decision to adjust focus only based on auto-focus being disabled
    focusAutoID = None
    focusManualID = None

    # Caption text on the image
    captionFontOptions = []
    backupCaptionFontFilename = ""
    captionFontSize = 16
    captionText = ""
    captionDateStamp = False
    captionTimeStamp = False
    captionTwoFourHour = False
    captionLocation = 11
    captionTextR = 240
    captionTextG = 240
    captionTextB = 240

    # Number of pixels to inset text box into the image frame
    captionInsetY = 6
    captionInsetX = 10

    logCategory = QLoggingCategory("csdevs.audio.thread.worker")

    @property
    def exit_time(self):
        '''
        Returns time.time() of thread exit
        '''

        return self.tThreadExit

    def set_capture_device(self, aDev):
        '''
        Interface to pprovide a QDevice object for the video device to be
        captured from. the QDevice will be used for direct v4l2 access and
        stream I/O.

        Parameters
        ----------
            aDev: QDevice obect instance
                The V4L2 device to capture frame(s) from
        '''

        # FIXME: If we are going to use v4l2py.device we should probably use the
        # sub-modules for everything that they can do and we do with v4l2py.raw

        self.capDev = aDev
        self.__clear_control_name_cache()
        self.brokenRx = (self.capDev is not None)

    @property
    def n_capture_buffers(self):
        '''
        Return the number of capture buffers being used during frame capture
        '''

        return self.bufCount

    # Get the number of capture buffers to use during frame capture
    # FIXME: This should be removed and all attempts to get the value be via the
    # n_capture_buffers property
    def getCaptureBufferCount(self):
        return self.bufCount

    def set_capture_buffer_count(self, newCount):
        '''
        Set a number of capture buffers to use during frame capture

        Paramters
        ---------
            newCount: Integer
                The number of capture buffers to be used. If the supplied value
                is less than or equal to zero or greater than a limit in a class
                member then a default value (also a class member) is used.
        '''

        if (newCount > 0) and (newCount <= self.limBufCount):
            self.bufCount = newCount
        else:
            # Unsupported value supplied in newCount, use the default
            self.bufCount = self.defaultBufCount

    @property
    def n_capture_frame(self):
        '''
        Returns the sequential received frame number being used as the captured
        image frame.
        '''

        return self.capFrame

    # Return the frame number that will be captured after the device is opened
    # FIXME: This should be removed and all attempts to get the value be via the
    # n_capture_frame property
    def getCapFrameNumber(self):
        return self.capFrame

    def set_capture_frame_number(self, frameNum=-1):
        '''
        Set the frame number that will be captured after starting streaming from
        the device.

        Paramters
        ---------
            frameNum: Integer
                The received frame number to keep as the captured frame when the
                device is streaming.
        '''

        self.capFrame = frameNum

    @property
    def capture_duration(self):
        '''
        Returns the elapsed time from starting the thread that handles streamed
        frames to the actual capture of a frame.
        '''

        return self.lastCaptureElapsed

    # FIXME: This should be removed and any remaining uses replaced with use of
    # capture_duration
    def getLastCaptureDuration(self):
        return self.lastCaptureElapsed

    @property
    def save_capture_frame(self):
        '''
        True if a save file for the capture frame is set, else returns False
        '''

        return self.saveFile != ""

    # FIXME: This should be removed and any remaining uses replaced with use of
    # save_capture_frame()
    def isFrameSaveEnabled(self):
        return self.saveFile != ""

    def disable_frame_save(self):
        '''
        Disable saving of the captured frame to a file
        '''

        self.saveFile = ""

    @property
    def capture_filename(self):
        '''
        Returns the name of a file to save the captured frame in
        '''

        return self.saveFile

    # Return the destination file for frame capture
    # FIXME: This should be removed and any remaining uses replaced with use of
    # captureFile()
    def getSaveFile(self):
        return self.saveFile

    def set_capture_filename(self, newFile):
        '''
        Set the destination file to save a captured frame in

        Parameters
        ----------
            newFile: String
                Contains the filename to save the captured frame in
        '''

        self.saveFile = newFile

    @property
    def capture_file_save_quality(self):
        '''
        Returns any image format quality value being used if saving captured
        frames. For example, if the capture file is jpeg format it should have
        a quality in the range 0-100.
        '''

        return self.saveQuality

    # Return the destination file save quality (percent)
    # FIXME: This should be removed and any remaining uses replaced with use of
    # capture_file_save_quality()
    def getSaveQuality(self):
        return self.saveQuality

    def set_save_quality(self, newQual):
        '''
        Set the image format quality value to be used whaen saving a captured
        frame. For example, if the capture file is jpeg format it should have
        a quality in the range 0-100.

        Parameters
        ----------
            newQual: integer
                Range based on captured image format which is defined by the
                filename extension, e.g. .jpg, .jpeg files would be expected to
                by JPEG files with a quality in the range 0-100.
        '''

        self.saveQuality = newQual

    @property
    def brightness(self):
        '''
        Returns the brightness of the captured frame. The assumed brightness
        range is from 0 (blackout) to 255 (whiteout).
        '''

        return self.frameBrightness

    # Get the captured frame's brightness
    # FIXME: This should be removed and any remaining uses replaced with use of
    # the brightness() property
    def getBrightness(self):
        return self.frameBrightness

    @property
    def contrast(self):
        '''
        Returns the contrast of the captured frame. The assumed contrast
        range is from 0 (none) to 255 (severe/extreme).
        '''

        return self.frameContrast

    # Get the captured frame's contrast
    # FIXME: This should be removed and any remaining uses replaced with use of
    # the contrast() property
    def getContrast(self):
        return self.frameContrast

    @property
    def saturation(self):
        '''
        Returns the saturation of the captured frame. The assumed saturation
        range is from 0 (monochrome) to 255 (severe/extreme)
        '''

        return self.frameSaturation

    # Get the captured frame's saturation
    # FIXME: This should be removed and any remaining uses replaced with use of
    # the saturation() property
    def getSaturation(self):
        return self.frameSaturation

    def receive_broken(self):
        '''
        Indicate to a caller that capturing from the open device is failing and
        can't be recovered. Giving a reason to close and open the capture device
        in the thread owner
        '''

        return self.brokenRx

    def set_caption_text(self, newText=None):
        '''
        Specify text to be used as a caption this thread will place on the
        captured frame. We can set the caption text settings but not get them.
        FIXME: This should really verify the correct type is supplied

        newText: String
            If not None is a string containing the text to be used in the
            caption. If is None then disables writing of a caption on the
            captured frame.
        '''

        if newText is not None:
            self.captionText = newText
        else:
            self.captionText = ""

    def set_caption_datestamp_enabled(self, enable):
        '''
        Enable/disable the inclusion of a datestamp in any caption applied to
        captured frame

        Parameters
        ----------
            enable: Boolean
                True to enable datestamping caption, False to disable
                datestamping caption.
        '''

        self.captionDateStamp = enable

    def set_caption_timestamp_enabled(self, enable):
        '''
        Enable/disable the inclusion of a timestamp in any caption applied to
        captured frame

        Parameters
        ----------
            enable: Boolean
                True to enable timestamping caption, False to disable
                timestamping caption.
        '''

        self.captionTimeStamp = enable

    def set_caption_two_four_hour_enabled(self, enable):
        '''
        Enable/disable the use of 24 hour time for any enabled timestamp in any
        caption applied to captured frame
        '''

        self.captionTwoFourHour = enable

    def set_caption_text_location(self, newLoc):
        '''
        Specify the location to apply any caption being applied to captured
        frame. An integer encoded identity of locations is used.

        Parameters
        ----------
            newLoc: Integer (encoded scheme for location identity)
                Two digits are used. The least significant digit (units) is the
                horizontal position to place the caption (2 indicates horizontal
                frame center; 3 indicates horizontal frame right; any other
                least-significant digit is accepted as frame left). The most
                significant digit (tens) is the vertical position to place the
                caption (2 indicates vertical center; 3 indicates vertical top;
                any other value tens digit is accepted as vertical bottom). This
                permits 9 locations to place the caption in any captured frame.
        '''

        self.captionLocation = newLoc

    def set_caption_text_RGB(self, rVal, gVal, bVal):
        '''
        Set the RGB color to be used for the text drawn in any caption being
        placed on the captured frame.

        Parameters
        ----------
            rVal: Integer
                The Red component of the caption color value
            gVal: Integer
                The Green component of the caption color value
            bVal: Integer
                The Blue component of the caption color value

            Each of these color components should have a value in the range
            0-255.
        '''

        self.captionTextR = rVal
        self.captionTextG = gVal
        self.captionTextB = bVal

    def set_caption_font_filename(self, fontFile):
        '''
        Specify the filename of a font file containing the font to be used to
        draw any caption text.

        Parameters
        ----------
            fontFile: String
                Contains the filename of a font file that can be used by Qt to
                draw text on an image.
        '''

        self.captionFontOptions.clear()

        self.captionFontOptions.append(fontFile)

        # Add a backup if available, requires backup be set before this
        if self.backupCaptionFontFilename != "":
            self.captionFontOptions.append(self.backupCaptionFontFilename)

    def set_backup_caption_font_filename(self, fontFile):
        '''
        Specify the filename of a backup font file containing the font to be
        used to draw any caption text if it is not possible to used the primary
        font, the one set via set_caption_font_filename()

        Parameters
        ----------
            fontFile: String
                Contains the filename of a font file that can be used by Qt to
                draw text on an image.
        '''

        self.backupCaptionFontFilename = fontFile

    @property
    def caption_font_size(self):
        '''
        Return the font size to be used to draw any caption on a captured frame.
        '''

        return self.captionFontSize

    # FIXME: This should be removed and any remaining uses replaced with use of
    # the caption_font_size() property
    def getCaptionFontSize(self):
        return self.captionFontSize

    def set_caption_font_size(self, newSize):
        '''
        Set the font size (in standard font size units used by Qt) to be used to
        draw any caption on a captured frame.

        Paraeters
        ---------
            newSize: number
                The fontsize to be used to draw any caption
        '''

        self.captionFontSize = newSize

    def __find_camera_control_setting_by_ID(self, ctrlID):
        '''
        Given a control ID supported by the V4L2 device being used for frame
        capture, return the tuple containing the control information.

        Parameters
        ----------
            ctrlID: Integer
                A V4L2 control ID supported by the device being used for frame
                capture.
        '''

        if len(self.controls) > 0:
            for aCtrl in self.controls:
                if aCtrl.id == ctrlID:
                    return aCtrl

        return None

    def add_control_setting_by_ID(self, ctrlID, value):
        '''
        Store a value to be used to set a specified control ID supported by the
        V4L2 device being used for frame capture. The value is retained in a
        list with all other added control settings and they are used to
        adjust the chosen controls when streaming is started for the V4L2
        device.

        Parameters
        ----------
            ctrlID: Integer
                A V4L2 control ID supported by the device being used for frame
                capture.
            value: varies
                The value to be used when setting the specified control ID. The
                value type can be of those valid for V4L2 controls.
        '''

        try:
            aCtrl = v4l2_control(ctrlID)
            aCtrl.value = value
            self.controls.append(aCtrl)
        except TypeError:
            msg = "Capture thread failed to create control {}".format(ctrlID)
            msg += "= {}".format(value)
            qCWarning(self.logCategory, msg)
            # debug_message(msg)

    def remove_control_setting_by_ID(self, ctrlID):
        '''
        Remove a previously stored value that was to be used for a given control
        ID on the V4L2 device being used for frame capture. It removes any
        setting of the specified control ID when capturing.

        Parameters
        ----------
            ctrlID: Integer
                A V4L2 control ID supported by the device being used for frame
                capture. It should also be a control ID with a value previosuly
                listed to be set using add_control_setting_by_ID() but will only
                show a message without failing if the ID is not already listed.
        '''

        aCtrl = self.__find_camera_control_setting_by_ID(ctrlID)
        if aCtrl is not None:
            try:
                self.controls.remove(aCtrl)
            except ValueError:
                msg = "Failed to remove stream control "
                msg += "{}".format(aCtrl.id)
                qCWarning(self.logCategory, msg)
                # debug_message(msg)

    def replace_control_setting_by_ID(self, ctrlID, newValue):
        '''
        Replace a previously saved value to be used to set a specified control
        ID supported by the V4L2 device being used for frame capture. The value
        is retained in a list with all other added control settings and they are
        used to adjust the chosen controls when streaming is started for the
        V4L2 device. The value replaces any previously listed value to be used
        to set the control, if it was not already present this function achieves
        the same result as add_control_setting_by_ID(). Order of setting of
        controls is not preserved using this function.

        Parameters
        ----------
            ctrlID: Integer
                A V4L2 control ID supported by the device being used for frame
                capture.
            newValue: varies
                The new value to be used when setting the specified control ID.
                The value type can be of those valid for V4L2 controls.
        '''
        self.remove_control_setting_by_ID(ctrlID)
        self.add_control_setting_by_ID(ctrlID, newValue)

    @property
    def auto_focus_control_ID(self):
        '''
        Return any saved control ID that can be used to enable/disable
        auto-focus for the V4L2 device being accessed by the class instance.
        It's usually also possible to read the same control value and identify
        if auto-focus is ON/OFF.

        If an auto-focus control is identified and enabled then manual focus
        adjustments are ignored.
        '''

        return self.focusAutoID

    def set_auto_focus_control_ID(self, ctrlID):
        '''
        Set the control ID that can be used to enable/disable auto-focus for the
        V4L2 device being accessed by the class instance. It's usually also
        possible to read the same control value and identify if auto-focus is
        ON/OFF.

        Paramters
        ---------
            ctrlID: Integer
                The ID of a V4L2 control on the capture device that can be used
                to enable/disable auto-focus
        '''

        self.focusAutoID = ctrlID

    @property
    def manual_focus_control_ID(self):
        '''
        Return any saved control ID that can be used to perform manual focus
        adjustments for the V4L2 device being accessed by the class instance.
        It's usually also possible to read the same control value and get the
        current focus position (as a simple number in-range rather than a number
        with any meaning like feet/meters to point of focus).

        If manual and auto-focus control IDs are identified then if auto is
        enabled then manual focus adjustments are ignored when setting the
        camera.
        '''

        return self.focusManualID

    def set_manual_focus_control_ID(self, ctrlID):
        '''
        Set the control ID that can be used to manually adjust focus point for
        the V4L2 device being accessed by the class instance. It's usually also
        possible to read the current focus point via the same control but the
        value usually is just a number in control range with no intrinsic
        meaning such as distance in any common units to point of focus.

        Parameters
        ----------
            vtrlID: Integer
                The ID of a V4L2 control on the capture device that can be used
                to adjust point of focus.
        '''

        self.focusManualID = ctrlID

    def __get_control_style_by_ID(self, ctrlID):
        '''
        Get the control style for a single V4L2 control by ID for the device
        being accessed by an instance of this class.

        See the V4L2 documentation for VIDIOC_QUERYCTRL to get details

        Parameters
        ----------
            ctrlID: Integer
                The V4L2 control ID to get the control style for
        '''

        try:
            # Create a query control object for the ID and read it
            if self.capDev.closed:
                raise OSError
            queryctrl = v4l2_queryctrl(ctrlID)
            ioctl(self.capDev, VIDIOC_QUERYCTRL, queryctrl)
        except (TypeError, OSError):
            queryctrl = None

        return queryctrl

    def __get_control_name_by_ID(self, ctrlID):
        '''
        Given a control ID supported by the V4L2 device being accessed by an
        instance of this class return the name used for the control, e.g.
        Brightness, Contrast, etc.

        Parameters
        ----------
            ctrlID: Integer
                A V4L2 control ID number for the device being accessed by an
                object of this class

        Returns a String containing the name used in V4L2 for the control ID.
        '''

        ctrlName = ""
        queryctrl = self.__get_control_style_by_ID(ctrlID)
        if queryctrl is not None:
            ctrlName = queryctrl.name.decode('utf-8')

        return ctrlName

    # FIXME: __clear_control_name_cache() and __get_cached_control_name_by_ID()
    # have no real purpose. A cache of control ID to name mappings is only
    # useful if we look up the control name more than once, at present we do it
    # once to set the controls, which we only do once per-instance of this class
    def __clear_control_name_cache(self):
        '''
        Reset any cache of control ID to name mappings.
        '''
        self.ctrlNameCache.clear()

    # Get a control name from it's control ID via a local cache, populate the
    # entry when not present. This is only useful if we look up the control
    # name more than once, at present we do it once to set the controls, which
    # we only do once per-instance of this class
    def __get_cached_control_name_by_ID(self, ctrlID):
        '''
        Given a control ID supported by the current object's V4L2 device get the
        name of the control first from a local cache and only use the V4L2 API
        if that fails

        Parameters
        ----------
            ctrlID: Integer
                The V4L2 control ID for a control supported by the V4L2 device
                accessed by the current instance of the class

        Returns a String containing the name used for the control ID, if
        supported

        If the control ID is not supported should raise a ValueError for the
        invalid ID.
        '''

        try:
            ctrlName = self.ctrlNameCache[ctrlID]
        except KeyError:
            ctrlName = self.__get_control_name_by_ID(ctrlID)
            self.ctrlNameCache[ctrlID] = ctrlName

        return ctrlName

    def __get_control_value_by_ID(self, ctrlID):
        '''
        Read the current value for a control supported by the V4L2 device being
        accessed by the object

        Parameters
        ----------
            ctrlID: Integer
                The V4L2 ID for a control supported by the V4L2 device being
                used by the object

        Returns the value for the control in the format used for that control,
        type can vary.
        '''

        try:
            if self.capDev.closed:
                raise OSError
            aCtrl = v4l2_control(ctrlID)
            ioctl(self.capDev, VIDIOC_G_CTRL, aCtrl)
            # debug_message("Ctrl {} = {}".format(aCtrl.id, aCtrl.value))
            value = aCtrl.value
        except (TypeError, OSError):
            value = None
            qCWarning(self.logCategory,
                      "Failed to read control {}".format(ctrlID))
            # debug_message("Failed to read control {}".format(ctrlID))

        return value

    def __set_controls(self):
        '''
        Set the values of any control we have saved values for, see
        add_control_setting_by_ID() and replace_control_setting_by_ID(). The
        values set using those are applied to the current object's in-use V4L2
        device by this function.
        '''
        if not self.capDev.closed and (len(self.controls) > 0):
            # debug_message("Setting controls in stream")

            # Before going through the controls get any auto/manual focus state
            # we want to set. We need three states for the wanted state. We can
            # tell if we want it on/off, if it is on/off but only if there is an
            # auto-focus control. There might only be a manual focus control so
            # we need a third state to not care about auto-focus. Assume we
            # don't care about auto-focus. Then handle any state we can care
            # about
            afWantOn = None
            if self.focusAutoID is not None:
                # It only makes sense for auto-focus to be on or off
                afIsOn = (self.__get_control_value_by_ID(self.focusAutoID) != 0)
                # debug_message("AF is ON: {}".format(afIsOn))

                # We'll need the control name later and if we want it is in the
                # control setting list for this instance
                afCtrlName = self.__get_control_name_by_ID(self.focusAutoID)
                # debug_message("AF Ctrl is: ({}) {}".format(self.focusAutoID, afCtrlName))
                afCtrl = self.__find_camera_control_setting_by_ID(self.focusAutoID)
                if (afCtrl is not None):
                    # debug_message("AF Ctrl Setting: {}".format(afCtrl.value))
                    # Auto-focus has a listed setting in this instance, if it's
                    # on then listed manual focus requests don't work and if
                    # it's off they do so we don't need to check for a listed
                    # manual focus
                    afWantOn = (afCtrl.value != 0)
                else:
                    # If we have no request to set auto-focus but there is a
                    # manual focus that we have a request to set, then we
                    # implicitly want any auto-focus control OFF. Otherwise we
                    # don't care what auto-focus is (want for it doesn't matter)
                    mfID = self.focusManualID
                    if mfID is not None:
                        # debug_message("MF Ctrl ID: {}".format(mfID))
                        mfCtrl = self.__find_camera_control_setting_by_ID(mfID)
                        if mfCtrl is not None:
                            # debug_message("MF Ctrl Value: {}".format(mfCtrl.value))
                            # Found a manual focus setting listed
                            afWantOn = False
                        # else:
                        #     debug_message("MF Ctrl with None Value".format(mfCtrl.value))

                # FIXME: We might need a special case here. We somehow detect AF
                # OFF on a camera reset and if we have a MF setting it's no use.
                # It may be useful to set AF ON then OFF if we have manual focus
                # but that may require leaving it ON for a short time.

            # Text showing the controls we've set
            ctrlVals = ""

            # Go through the settings
            for aCtrl in self.controls:
                # We only set the controls once before exiting, so a cache
                # of the names doesn't help if we populate it here
                ctrlName = self.__get_control_name_by_ID(aCtrl.id)
                # ctrlName = self.__get_cached_control_name_by_ID(aCtrl.id)

                # Prevent setting of focus if auto-focus is to be enabled
                if afWantOn is not None:
                    if afWantOn and (aCtrl.id == self.focusManualID):
                        continue

                # If we want a specific auto-focus state
                if afWantOn is not None:
                    # ...and it's off we want then it must be done before
                    # setting any manual focus value but only disable auto-focus
                    # if it's already on and we are trying to set manual focus
                    if (not afWantOn) and afIsOn and\
                            (aCtrl.id == self.focusManualID):
                        try:
                            # Assumed bool, 0 is off
                            newCtrl = v4l2_control(self.focusAutoID)
                            newCtrl.value = 0
                            ioctl(self.capDev.fileno(), VIDIOC_S_CTRL, newCtrl)
                            ctrlVals += " \\_ ({} {} = {})".format(newCtrl.id,
                                                                 afCtrlName,
                                                                 newCtrl.value)
                            newCtrl = None
                        except:
                            msg = " Set {} off failed ".format(afCtrlName)
                            msg += "before set {}".format(ctrlName)
                            qCWarning(self.logCategory, msg)
                            # debug_message(msg)
                            # Can't set focus below
                            continue
                    # else:
                    #     if (not afWantOn):
                    #         if (not afIsOn):
                    #             if (aCtrl.id == self.focusManualID):
                    #                 debug_message("AF Wanted off, IS off and we want to set MF, no-op with AF")

                try:
                    ctrlVals += " \\_ {} {} = {}".format(aCtrl.id, ctrlName,
                                                         aCtrl.value)
                    newCtrl = v4l2_control(aCtrl.id)
                    newCtrl.value = aCtrl.value
                    ioctl(self.capDev.fileno(), VIDIOC_S_CTRL, newCtrl)
                    newCtrl = None
                # except (TypeError, OSError):
                except:
                    qCWarning(self.logCategory,
                              " Set {} failed".format(ctrlName))
                    # debug_message(" Set {} failed".format(ctrlName))
            if ctrlVals != "":
                qCDebug(self.logCategory, ctrlVals)
                # debug_message(ctrlVals)
            qCDebug(self.logCategory, "__")
            # debug_message("__")

    def __request_capture_buffers(self, newCount):
        '''
        Request capture memory buffers to be used when streaming from the
        current object's in-use V4L2 device.

        Parameters
        ----------
            newCount: Integer
                The number of capture buffers to request from V4L2
        '''

        self.req = None
        # debug_message("Requesting {} capture buffers".format(newCount))
        try:
            if not self.capDev.closed:
                self.req = v4l2_requestbuffers()
                if self.req is not None:
                    # debug_message("Request object created")
                    self.req.type = V4L2_BUF_TYPE_VIDEO_CAPTURE
                    self.req.memory = V4L2_MEMORY_MMAP
                    self.req.count = newCount
                    for iRsv in range(len(self.req.reserved)):
                        self.req.reserved[iRsv] = 0
                    # debug_message("Request object populated")
                    ioctl(self.capDev, VIDIOC_REQBUFS, self.req)
                    # debug_message("Request capture buffers success")
                else:
                    qCWarning(self.logCategory,
                              "Allocate ca[ture buffers request failed")
                    # debug_message("Allocate request failed")
            else:
                raise OSError
        except OSError as e:
            msg = "Failed to request {} capture buffers".format(newCount)
            qCWarning(self.logCategory, msg)
            qCWarning(self.logCategory, "Error code is {}".format(e.errno))
            # debug_message(msg)
            # debug_message("Error code is {}".format(e.errno))
            self.req = None

    def __release_capture_buffers(self):
        '''
        Free any previously requested capture buffers to be used when streaming
        from the current object's in-use V4L2 device, see
        __request_capture_buffers()
        '''

        self.__request_capture_buffers(0)
        if self.req is not None:
            if self.req.count == 0:
                self.req = None
            else:
                msg = "Release capture buffers "
                msg += "result with {} buffers ".format(self.req.count)
                qCDebug(self.logCategory, msg)
                # debug_message(msg)
        else:
            qCDebug(self.logCategory, "Release capture buffers with no result")
            # debug_message("Release capture buffers with no result")

    def __close_capture_buffers(self):
        '''
        Close each capture buffer in the capture buffer list member in an object
        of this class. Then clear the buffer list.
        '''

        for aBuf in self.buffers:
            aBuf.close()

        self.buffers.clear()

    def __setup_capture_buffers(self):
        '''
        Setup capture buffers for use during streaming by the in-use V4L2 device
        by an object of this class. Will release any existing buffers before
        creating new ones.
        '''

        # Free any buffers and allocate new ones
        # t0 = time.time()
        self.__release_capture_buffers()
        self.__request_capture_buffers(self.bufCount)
        # t1 = time.time()
        if self.req is not None:
            try:
                if not self.capDev.closed:
                    # debug_message("mapping {} buffers".format(self.req.count))
                    for ind in range(self.req.count):
                        # setup a buffer
                        buf = v4l2_buffer()
                        buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE
                        buf.memory = V4L2_MEMORY_MMAP
                        buf.index = ind
                        # iRes = ioctl(self.capDev, VIDIOC_QUERYBUF, buf)
                        ioctl(self.capDev, VIDIOC_QUERYBUF, buf)
                        # if iRes == 0:
                        #     debug_message("Setup a query buffer")
                        # else:
                        #     msg = "Failed to setup a query "
                        #     msg ++ "buffer: {}".format(iRes)
                        #     debug_message(msg)

                        mm = mmap.mmap(self.capDev.fileno(), buf.length,
                                       mmap.MAP_SHARED,
                                       mmap.PROT_READ | mmap.PROT_WRITE,
                                       offset=buf.m.offset)
                        self.buffers.append(mm)
                        # debug_message("Appended buffer")

                        # Queue the buffer for capture
                        # iRes = ioctl(self.capDev, VIDIOC_QBUF, buf)
                        ioctl(self.capDev, VIDIOC_QBUF, buf)
                        # if iRes == 0:
                        #     debug_message("Queued a query buffer")
                        # else:
                        #     msg = "Failed to queue a query"
                        #     msg += "buffer: {}".format(iRes)
                        #     debug_message()
                else:
                    raise OSError
            except (TypeError, ValueError):
                qCWarning(self.logCategory, "Failed to setup capture buffers")
                # debug_message("Failed to setup capture buffers")
                self.__close_capture_buffers()
                self.brokenRx = True
        # t2 = time.time()

        # msg = "Setup buffers {}, "format((t3 - t0))
        # msg += "get {}, "format((t1 - t0)
        # msg += "map {}".format((t2 - t0))
        # debug_message(msg)

    def __stream_on(self):
        '''
        Start streaming from the in-use V4L2 device by an object of this class
        '''

        try:
            if not self.capDev.closed:
                buf_type = v4l2_buf_type(V4L2_BUF_TYPE_VIDEO_CAPTURE)
                iRes = ioctl(self.capDev.fileno(), VIDIOC_STREAMON, buf_type)
                if iRes != 0:
                    qCWarning(self.logCategory,
                              "Failed to turn stream on: {}".format(iRes))
                    # debug_message("Failed to turn stream on: {}".format(iRes))
            else:
                raise OSError
        except (TypeError, OSError) as e:
            qCWarning(self.logCategory, "Stream ON failed")
            # debug_message("Stream ON failed")
            if type(e) == OSError:
                qCWarning(self.logCategory, "\\_ OS error: {}".format(e.errno))
                # debug_message("\\_ OS error: {}".format(e.errno))
            self.brokenRx = True

    def __stream_off(self):
        '''
        Stop streaming from the in-use V4L2 device by an object of this class
        FIXME: This is really slow, commonly takes 75% of the time to capture
               a frame. Testing suggests it's almost all spent in the ioctl. It
               can't benefit from background execution because it can't overlap
               a new frame capture because the camera file descriptor is owned
               by the main window.
        '''

        # Check what's available to do this in the background
        # activeThreads = QThreadPool.globalInstance().activeThreadCount()
        # maxThreads = QThreadPool.globalInstance().maxThreadCount()
        # msg = "IN STREAM OFF POOL is {} threads with {} max".format(activeThreads, maxThreads)
        # debug_message(msg)

        try:
            if not self.capDev.closed:
                buf_type = v4l2_buf_type(V4L2_BUF_TYPE_VIDEO_CAPTURE)
                iRes = ioctl(self.capDev.fileno(), VIDIOC_STREAMOFF, buf_type)
                if iRes != 0:
                    qCWarning(self.logCategory,
                              "Failed to turn stream off: {}".format(iRes))
                    # debug_message("Failed to turn stream off: {}".format(iRes))
            else:
                raise OSError
        except (TypeError, OSError) as e:
            qCWarning(self.logCategory, "Stream OFF failed")
            # debug_message("Stream OFF failed")
            if type(e) == OSError:
                qCWarning(self.logCategory, "\\_ OS error: {}".format(e.errno))
                # debug_message("\\_ OS error: {}".format(e.errno))

            # FIXME: Hmm?
            # self.brokenRx = True

    def __dequeue_capture_frame(self):
        '''
        De-queue the next un-accessed, filled capture buffer from the V4L2
        device stream. Provide access as a capture frame memory map.

        Returns the result of a VIDIOC_DQBUF request to the device.
        '''

        try:
            if not self.capDev.closed:
                buf = v4l2_buffer()
                buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE
                buf.memory = V4L2_MEMORY_MMAP
                # iRes = ioctl(self.capDev.fileno(), VIDIOC_DQBUF, buf)
                ioctl(self.capDev.fileno(), VIDIOC_DQBUF, buf)
            else:
                qCDebug(self.logCategory, "Parse frame, no capture device")
                # debug_message("Parse frame, no capture device")
                raise OSError
        except OSError as e:
            qCDebug(self.logCategory, "Failed to parse a frame")
            qCDebug(self.logCategory, "Error {}".format(e.errno))
            # debug_message("Failed to parse a frame")
            # debug_message("Error {}".format(e.errno))
            self.brokenRx = True
            buf = None

        return buf

    def __requeue_frame(self, buf):
        '''
        Re-queue for streaming into by the V4L2 device for the current object a
        previously de-queued capture buffer.

        Buffers are fewer than the total number of frames expected to be
        handled. We setup a reasonable number of buffers to be streamed into
        after turning the stream on, meanwhile we de-queue, process and re-queue
        buffers to parse incoming frames.

        Parameters
        ----------
            buf: The result of a previous use of __dequeue_capture_frame()
        '''

        try:
            if self.capDev.closed:
                raise OSError
            # debug_message("Re-queueing Rx buffer {}".format(buf.index))
            mm = self.buffers[buf.index]
            mm.seek(0)
            # iRes = ioctl(self.capDev, VIDIOC_QBUF, buf)
            ioctl(self.capDev, VIDIOC_QBUF, buf)
        except (IndexError, OSError) as e:
            qCWarning(self.logCategory,
                      "Failed to re-queue frame {}".format(buf.index))
            # debug_message("Failed to re-queue frame {}".format(buf.index))
            if type(e) == OSError:
                qCWarning(self.logCategory, "\\_ OS error: {}".format(e.errno))
                # debug_message("\\_ OS error: {}".format(e.errno))
            self.brokenRx = True

    def __mean_stat(self, imgStat):
        '''
        Given a list of statistics, compute the mean of all in the list. It's
        faster to count while iterating the entries because using something
        like count = len(imgStat) means we iterate imgStat twice, one time for
        count and one time for getting the sum of imgStat

        Parameters
        ----------
            imgStat: A PILlow ImageStat object

        Returns the mean of the values in imgStat
        '''

        result = 0.0
        count = 0
        for aVal in imgStat:
            result += aVal
            count += 1

        if count > 0:
            result /= 1.0 * count

        return result

    def __compute_frame_statistics(self):
        '''
        For a mmap buffer for a frame, compute the brightness, contrast and
        saturation

        The frame used will be in the current object's theFrame member. The
        results are stored in object members and can be accessed via properties
        like brightness(), contrast(), saturation().

        Returns the time spent computing statistics or -1.
        '''

        if self.theFrame is not None:
            try:
                # How long does it take, it's going to be expensive but at least
                # it's only one frame of many frames received
                tp1 = time.time()

                # Image is RGB, get it's stats
                rgbStat = ImageStat.Stat(self.theFrame)

                # Make a HSV pillow image from the RGB one. HSV gives us
                # saturation from the S-band mean and brightness from the V-band
                # mean but contrast is easiest as mean of standard deviation for
                # all bands. Shame we have to convert from RGB to get HSV.
                hsvImage = self.theFrame.convert("HSV")

                # Get the statistics of the HSV image
                hsvStat = ImageStat.Stat(hsvImage)

                # Brightness (Third band of HSV mean, value)
                self.frameBrightness = hsvStat.mean[2]

                # Contrast (mean of all RGB standard deviation bands)
                self.frameContrast = self.__mean_stat(rgbStat.stddev)

                # Saturation (Second band of mean, saturation)
                self.frameSaturation = hsvStat.mean[1]

                # Duration (overhead for statistics)
                tp2 = time.time()
                tImgStats = tp2 - tp1
            except (FileNotFoundError, IndexError, TypeError,
                    UnidentifiedImageError, ValueError):
                # msg = "Failed to compute statistics from frame: "
                # msg += "{}".format(type(e))
                msg = "Failed to compute statistics from frame"
                qCWarning(self.logCategory, msg)
                # debug_message(msg)
                tImgStats = 0
        else:
            qCDebug(self.logCategory,
                    "Attempt to gather statistics with no frame loaded")
            # debug_message("Attempt to gather statistics with no frame loaded")
            tImgStats = -1

        # Return the execution time for the statistics
        return tImgStats

    def __save_frame_as_is(self, buf):
        '''
        Given a de-queued stream buffer save it as a file. The filename is a
        class member set with set_capture_filename()

        Parameters
        ----------
            buf: A V4L2 stream buffer
                The properties indicating which of a previously created set of
                stream buffers to save. It includes the index in the buffer
                array that contains the image frame data to use.

        Returns zero
        '''

        # No capture file, probably capturing for auto-exposure
        if not self.save_capture_frame:
            return

        try:
            # debug_message("Saving frame to {}".format(self.saveFile))
            mm = self.buffers[buf.index]
            # debug_message("mmap buffer")
            vid = open(self.saveFile, "wb+")
            # debug_message("write buffer")
            vid.write(mm.read())
            # debug_message("close save file")
            vid.close()
            # debug_message("Save finished")

            # tImgStats = self.__compute_frame_statistics(mm)
            tImgStats = 0
        except (IndexError, OSError, TypeError, ValueError) as e:
            qCWarning(self.logCategory, "Save FAILED")
            # debug_message("Save FAILED")
            if type(e) == OSError:
                qCWarning(self.logCategory, "\\_ OS error: {}".format(e.errno))
                # debug_message("\\_ OS error: {}".format(e.errno))
            tImgStats = 0

        # Return the execution time for computing the statistics
        return tImgStats

    def __generate_caption_text(self):
        '''
        Return the text of a caption to be used at this time on a frame to be
        saved. An empty String is no-cpation.
        '''

        captionRecord = ""

        # If there is anything to log on the captured image as a caption
        padFields = (self.captionText != "")
        if (padFields) or self.captionDateStamp or\
                self.captionTimeStamp:
            # Generate the caption string
            captionRecord = self.captionText
            if self.captionDateStamp:
                if padFields:
                    captionRecord += " "
                else:
                    padFields = True
                captionRecord += time.strftime("%d %B %Y")
            if self.captionTimeStamp:
                if padFields:
                    captionRecord += " "
                if self.captionTwoFourHour:
                    captionRecord += time.strftime("%H:%M")
                else:
                    captionRecord += time.strftime("%I:%M")

        return captionRecord

    def __get_caption_X(self, wText, wImage):
        '''
        Given the current caption location, calculate an image horizontal X
        co-ordinate to place the caption at based on a previously set
        (or default) caption location code

        Parameters
        ----------
            wText: Integer
                The width of the caption text
            wImage: Integer
                Frame image width
        '''

        hPos = self.captionLocation % 10

        # Center
        if hPos == 2:
            hDraw = int((wImage - wText) / 2) - 1
        # Right
        elif hPos == 3:
            hDraw = wImage - wText - self.captionInsetX
        # Assume left if unrecognized hPos
        else:
            hDraw = self.captionInsetX

        # X position is outside of image, force it 4 pixels in from left
        if (hDraw < 0) or (hDraw > wImage):
            hDraw = 4

        return hDraw

    def __get_caption_Y(self, hText, hImage):
        '''
        Given the current caption location, calculate an image vertical Y
        co-ordinate to place the caption at based on a previously set
        (or default) caption location code

        Parameters
        ----------
            hText: Integer
                The height of the caption text
            hImage: Integer
                Frame image height
        '''

        vPos = int(self.captionLocation / 10)

        # Center
        if vPos == 2:
            vDraw = int((hImage - hText) / 2) - 1
        # Top
        elif vPos == 3:
            vDraw = self.captionInsetY
        # Assume bottom if unrecognized vPos
        else:
            vDraw = hImage - hText - self.captionInsetY

        # Y position is outside of image, force it 4 pixels in from top
        if (vDraw < 0) or (vDraw > hImage):
            vDraw = 4

        return vDraw

    # FIXME: Should the set cases be range limited or is it enough that we
    # got them from a settings dialog which is range limited
    def set_caption_inset_X(self, value):
        '''
        Set a horizontal inset to apply to the position the caption text, e.g.
        so that the text doesn't begin on the first pixel column.

        Parameters
        ----------
            value: Integer
                The horizontal inset to use for the caption position
        '''

        self.captionInsetX = value

    @property
    def caption_inset_X(self):
        '''
        Return a horizontal inset to be applied to the position the caption
        text, e.g. so that the text doesn't begin on the first pixel column.
        '''
        return self.captionInsetX

    # FIXME: Replace any use of this with the caption_inset_X() property and
    # remove this
    def getCaptionInsetX(self):
        return self.captionInsetX

    def set_caption_inset_Y(self, value):
        '''
        Set a vertical inset to apply to the position the caption text, e.g.
        so that the text doesn't begin on the first pixel row.

        Parameters
        ----------
            value: Integer
                The vertical inset to use for the caption position
        '''

        self.captionInsetY = value

    @property
    def caption_inset_Y(self):
        '''
        Return a vertical inset to be applied to the position the caption
        text, e.g. so that the text doesn't begin on the first pixel row.
        '''
        return self.captionInsetY

    # FIXME: Replace any use of this with the caption_inset_Y() property and
    # remove this
    def getCaptionInsetY(self):
        return self.captionInsetY

    def __load_image_from_buffer(self, buf):
        '''
        Given a capture buffer, load the image data from it into a PILlow Image
        object stored in the member of the object named theFrame
        '''

        try:
            mm = self.buffers[buf.index]
            self.theFrame = Image.open(BytesIO(mm.read()))
        except (IndexError, OSError, TypeError,
                UnidentifiedImageError, ValueError) as e:
            qCWarning(self.logCategory, "Load frame FAILED")
            # debug_message("Load frame FAILED")
            if type(e) == OSError:
                qCWarning(self.logCategory, "\\_ OS error: {}".format(e.errno))
                # debug_message("\\_ OS error: {}".format(e.errno))

            self.theFrame = None

    def __save_frame(self):
        '''
        Save the vcaptured frame data as an image file. This version doesn't
        just save the frame buffer, it uses pillow so that we can add a text
        caption.

        Returns the time statistics for processing the frame
        '''

        # tSaveStart = time.time()
        # tSaveHalf = tSaveStart
        tImgStats = 0
        if self.theFrame is not None:
            # Get the frame statistics before considering a caption so that the
            # caption content doesn't pollute the statistics
            tImgStats = self.__compute_frame_statistics()

            # Only caption (and save) if we have a file to save to
            if self.save_capture_frame:
                try:
                    captionRecord = self.__generate_caption_text()
                    if captionRecord != "":
                        drawer = ImageDraw.Draw(self.theFrame)

                        # Get the first available font in the font theme list
                        recordFont = None
                        for fFont in self.captionFontOptions:
                            if fFont is not None:
                                try:
                                    recordFont = ImageFont.truetype(fFont, self.captionFontSize)
                                    # debug_message("ImageFont from: {}".format(fFont))
                                    # fontName = recordFont.getname()
                                    # debug_message("Default ImageFont is {} {}".format(fontName[0], fontName[1]))

                                    # Success, use it
                                    break
                                except OSError:
                                    # Not found, couldn't be loaded, try next in list
                                    # debug_message("Can't make ImageFont from {}".format(fFont))
                                    continue

                        if recordFont is None:
                            # Oh well, use the default bitmap font in PILlow
                            recordFont = ImageFont.load_default()

                        # debug_message("Computing date and time of day")
                        # tday = time.strftime("%d %B %Y %H:%M")
                        # debug_message("Generataing location string")
                        # locTxt = "Santaquin (David's doorstep) {}".format(tday)
                        # fntSize = recordFont.getsize(captionRecord)
                        txtBox = recordFont.getbbox(captionRecord)
                        imgSize = self.theFrame.size
                        # yPos = imgSize[1] - fntSize[1] - 3
                        xPos = self.__get_caption_X(txtBox[2] - txtBox[0],
                                                    imgSize[0])
                        yPos = self.__get_caption_Y(txtBox[3] - txtBox[1],\
                                                    imgSize[1])
                        drawer.text((xPos, yPos), captionRecord,
                                    (self.captionTextR, self.captionTextG,
                                     self.captionTextB),
                                    font=recordFont)

                    # tSaveHalf = time.time()

                    # Save the file, format is automatic based on filename
                    # extension, if quality is positive use it (should be
                    # limited only to files that support it and greater than
                    # zero less than one hundred (i.e. percent)
                    # debug_message("Saving Image of grabbed frame")
                    if self.capture_file_save_quality > 0:
                        self.theFrame.save(self.saveFile,
                                           quality=self.capture_file_save_quality)
                    else:
                        self.theFrame.save(self.saveFile)
                except (FileNotFoundError, IndexError, OSError, TypeError,
                        UnidentifiedImageError, ValueError) as e:
                    qCWarning(self.logCategory, "Save frame FAILED")
                    # debug_message("Save frame FAILED")
                    if type(e) == OSError:
                        qCWarning(self.logCategory,
                                  "\\_ OS error: {}".format(e.errno))
                        # debug_message("\\_ OS error: {}".format(e.errno))

            # Finished with the PILlow image
            self.theFrame = None

        # tSaveEnd = time.time()
        # tSaveDuration = tSaveEnd - tSaveStart
        # tSaveTop = 100.0 * (tSaveHalf - tSaveStart) / tSaveDuration
        # tSaveBottom = 100.0 * (tSaveEnd - tSaveHalf) / tSaveDuration
        # debug_message("Save takes {}, top takes {}, bottom takes {}".format(tSaveDuration, tSaveTop, tSaveBottom))
        # Return the time to compute the image statistics

        return tImgStats

    def __reach_target_frame(self):
        '''
        Set any saved control values for the stream. De-queue and re-queue
        frames preceding the one to be captured, effectively ignoring them. If
        it succeeds the stoppng point is with the required capture frame number
        buffer in the objects bufToSave member.
        '''

        # if (self.saveFile != "") and (self.capFrame > 0):
        if self.capFrame > 0:
            # Choose a frame to use to apply the control settings
            if self.capFrame > 2:
                ctrlFrame = int(self.capFrame / 3)
            else:
                ctrlFrame = 0

            # if len(self.controls) > 0:
            #     msg = "Will set controls on frame {}".format(ctrlFrame)
            #     debug_message(msg)

            # The following loop could run for more than a second but it uses
            # select with a max_t seconds timeout so there is little reason to
            # program it to yield
            curFrame = 0
            max_t = 10.0

            # Read frames until we reach the required one or fail
            while not self.capDev.closed and (curFrame <= self.capFrame):
                # Set camera controls at the chosen frame
                if curFrame == ctrlFrame:
                    # qCDebug(self.logCategory,
                    #         "APPLYING CONTROLS at frame {}".format(curFrame))
                    # debug_message("APPLYING CONTROLS at frame {}".format(curFrame))
                    self.__set_controls()

                # FIXME: We ought to use in_error to decide if we can exit error
                # We already handle ready_to_read and loop if we aren't, i.e.
                # nothing to do and select just timed-out
                ready_to_read, ready_to_write, in_error = ([], [], [])
                selFiles = [self.capDev.fileno()]
                ready_to_read,\
                    ready_to_write,\
                    in_error = select.select(selFiles, [], [], max_t)

                if len(ready_to_read) > 0:
                    if len(ready_to_read) > 1:
                        qCDebug(self.logCategory, "MULTIPLE FRAMES RECEIVED")
                        # debug_message("MULTIPLE FRAMES RECEIVED")
                    buf = self.__dequeue_capture_frame()
                    if buf is None:
                        qCWarning(self.logCategory,
                                  "Frame {} Rx failed".format(curFrame))
                        # debug_message("Frame {} Rx failed".format(curFrame))
                        return -1

                    # debug_message("Frame Rx in buffer {}".format(buf.index))
                    if curFrame != self.capFrame:
                        self.__requeue_frame(buf)
                        curFrame += 1
                    else:
                        self.bufToSave = buf
                        return 0
                else:
                    # See what is the state when select finishes with no
                    # ready to read (usually a timeout)
                    if (len(ready_to_read) == 0) and\
                            (len(ready_to_write) == 0) and\
                            (len(in_error) == 0):
                        qCWarning(self.logCategory, "Camera frame read timeout")
                        # debug_message("Camera frame read timeout")
                        return -2
                    else:
                        qCWarning(self.logCategory,
                                  "select(): read "
                                  "{}, write {}, error {}".format(ready_to_read,
                                                                  ready_to_write,
                                                                  in_error))
                        # debug_message("select(): read {}, write {}, error {}".format(ready_to_read, ready_to_write, in_error))

        return -3

    def runA(self):
        '''
        Capture thread entry point. This could be called directly but the class
        is designed to run this as it's own thread via a the class inheritance
        from QThread.
        '''

        qCDebug(self.logCategory, "")
        # debug_message("")
        msg = "Capturing frame {}".format(self.capFrame)
        if self.save_capture_frame:
            msg += " to {}".format(self.saveFile)
        qCDebug(self.logCategory, msg)
        # debug_message(msg)

        # We must have a capture device and frame number to capture (but it
        # doesn't matter if we have a save frame name, we can capture without
        # saving, e.g. for use in auto-exposure)
        if (self.capDev is not None) and (self.capFrame > 0):
            qCDebug(self.logCategory, "Capture thread device is usable")
            # debug_message("Capture thread device is usable")
            try:
                tStart = time.time()
                tStrmOn = tStart
                tWaitFrame = tStart
                tImgLoad = tStart
                tImgSave = tStart
                tReQ = tStart
                tBufClose = tStart
                tStrmOff = tStart
                tBufFree = tStart
                tBufEnd = tStart
                tImgStats = 0

                qCDebug(self.logCategory, "Capture thread setting up buffers")
                # debug_message("Capture thread setting up buffers")
                self.__setup_capture_buffers()
                if self.req is not None:
                    if len(self.buffers) > 0:
                        tStrmOn = time.time()
                        qCDebug(self.logCategory,
                                "Capture thread turning stream on with "
                                "{} buffers".format(len(self.buffers)))
                        # debug_message("Capture thread turning stream on with {} buffers".format(len(self.buffers)))
                        self.__stream_on()

                        tWaitFrame = time.time()
                        qCDebug(self.logCategory,
                                "Capture thread parsing to target frame")
                        # debug_message("Capture thread parsing to target frame")
                        if self.__reach_target_frame() == 0:
                            tImgLoad = time.time()
                            if self.bufToSave is not None:
                                # we reached the target frame with a buffer to
                                # save. Load it as a PILlow image and save that.
                                qCDebug(self.logCategory,
                                        "Capture thread loading image from current buffer")
                                # debug_message("Capture thread loading image from current buffer")
                                self.__load_image_from_buffer(self.bufToSave)

                                tImgSave = time.time()
                                qCDebug(self.logCategory,
                                        "Capture thread saving frame")
                                # debug_message("Capture thread saving frame")
                                tImgStats = self.__save_frame()

                                # Re-queue the frame buffer for cleanup
                                tReQ = time.time()
                                qCDebug(self.logCategory,
                                        "Capture thread re-queuing frame")
                                # debug_message("Capture thread re-queuing frame")
                                self.__requeue_frame(self.bufToSave)

                                self.bufToSave = None
                                self.brokenRx = False
                            else:
                                tImgSave = tImgLoad
                                tReQ = tImgLoad
                        else:
                            tImgLoad = time.time()
                            tImgSave = tImgLoad
                            tReQ = tImgLoad
                            qCWarning(self.logCategory,
                                      "Buffer failure, must stop stream")
                            # debug_message("Buffer failure, must stop stream")

                        # End the stream, close and free any buffers
                        # Do this in a pool thread because the _stream_off
                        # itself takes 75% of the whole capture runtime. Using a
                        # pool thread means everything from this to closing the
                        # device needs to be in the pool thread
                        tStrmOff = time.time()
                        qCDebug(self.logCategory, "Create closer thread")
                        # debug_message("Create closer thread")
                        closerThread = StreamOffTask()
                        qCDebug(self.logCategory,
                                "Give closer thread the capture device")
                        # debug_message("Give closer thread the capture device")
                        closerThread.setCaptureDevice(self.capDev)
                        qCDebug(self.logCategory,
                                "Give closer thread the capture buffers")
                        # debug_message("Give closer thread the capture buffers")
                        closerThread.setCaptureBufferList(self.buffers)
                        qCDebug(self.logCategory, "Start closer thread")
                        # debug_message("Start closer thread")
                        QThreadPool.globalInstance().start(closerThread)
                        qCDebug(self.logCategory, "Started closer thread")
                        # debug_message("Started closer thread")
                        tOffEnd = time.time()
                    else:
                        qCDebug(self.logCategory, "No capture buffers")
                        # debug_message("No capture buffers")
                tEnd = time.time()

                # Calculate the elapsed time of it all and the elements
                elapsed = tEnd - tStart
                sElapsed = tStrmOn - tStart
                onElapsed = tWaitFrame - tStrmOn
                wElapsed = tImgLoad - tWaitFrame
                ldElapsed = tImgSave - tImgLoad
                svElapsed = tReQ - tImgSave - tImgStats
                cElapsed = tStrmOff - tReQ
                offElapsed = tOffEnd - tStrmOff

                # Save the capture duration only for saved frames
                if self.save_capture_frame:
                    self.lastCaptureElapsed = elapsed

                # Show the elapsed times
                msg = "CAPTURE TIMING: elapsed {:.6f}s".format(elapsed)
                qCDebug(self.logCategory, msg)
                # debug_message(msg)
                msg = " \\ t: frames {:.6f}, ".format(wElapsed)
                msg += "setup {:.6f}, ".format(sElapsed)
                msg += "stream ON {:.6f}, ".format(onElapsed)
                msg += "OFF {:.6f}, ".format(offElapsed)
                msg += "from buf {:.6f}, ".format(ldElapsed)
                msg += "save {:.6f}, ".format(svElapsed)
                msg += "cleanup {:.6f}, ".format(cElapsed)
                msg += "stats gen. {:.6f}, ".format(tImgStats)
                qCDebug(self.logCategory, msg)
                # debug_message(msg)

                # Show each element as a percentage of total time
                percFrac = 100.0 / elapsed
                msg = " \\ %: frames {:.3f}, ".format(wElapsed * percFrac)
                msg += "setup {:.3f}, ".format(sElapsed * percFrac)
                msg += "stream ON {:.3f}, ".format(onElapsed * percFrac)
                msg += "OFF {:.3f}, ".format(offElapsed * percFrac)
                msg += "from buf {:.3f}, ".format(ldElapsed * percFrac)
                msg += "save {:.3f}, ".format(svElapsed * percFrac)
                msg += "cleanup {:.3f}, ".format(cElapsed * percFrac)
                msg += "stats gen. {:.3f}".format(tImgStats * percFrac)
                qCDebug(self.logCategory, msg)
                # debug_message(msg)
                # warning_message(msg)
            except Exception as e:
                qCWarning(self.logCategory,
                          "Capture run failed: {}".format(type(e)))
                # debug_message("Capture run failed: {}".format(type(e)))
                msg = "Time list: {}, {} ".format(tStart, tStrmOn)
                msg += "{}, {} {}, ".format(tWaitFrame, tImgLoad, tImgSave)
                msg += "{}, {}, {}, ".format(tReQ, tBufClose, tStrmOff)
                msg += "{}, {}, {}".format(tBufFree, tBufEnd, tImgStats)
                qCWarning(self.logCategory, msg)
                # debug_message(msg)

                # Try to make sure we end on failure with no capture buffers
                self.__close_capture_buffers()
                self.__release_capture_buffers()

        # Thread will end, abandon state and log exit time
        self.capDev = None
        qCDebug(self.logCategory, "-- Result ready...")
        # debug_message("-- Result ready...")
        self.tThreadExit = time.time()

    # Version that takes the time to turn stream off inline, which is slow
    def run(self):
        '''
        Capture thread entry point. This could be called directly but the class
        is designed to run this as it's own thread via a the class inheritance
        from QThread.
        '''

        qCDebug(self.logCategory, "")
        # debug_message("")
        msg = "Capturing frame {}".format(self.capFrame)
        if self.save_capture_frame:
            msg += " to {}".format(self.saveFile)
        qCDebug(self.logCategory, msg)
        # debug_message(msg)

        # We must have a capture device and frame number to capture (but it
        # doesn't matter if we have a save frame name, we can capture without
        # saving, e.g. for use in auto-exposure)
        if (self.capDev is not None) and (self.capFrame > 0):
            try:
                tStart = time.time()
                tStrmOn = tStart
                tWaitFrame = tStart
                tImgLoad = tStart
                tImgSave = tStart
                tReQ = tStart
                tBufClose = tStart
                tStrmOff = tStart
                tBufFree = tStart
                tBufEnd = tStart
                tImgStats = 0

                self.__setup_capture_buffers()
                if self.req is not None:
                    if len(self.buffers) > 0:
                        tStrmOn = time.time()
                        self.__stream_on()

                        tWaitFrame = time.time()
                        if self.__reach_target_frame() == 0:
                            tImgLoad = time.time()
                            if self.bufToSave is not None:
                                # we reached the target frame with a buffer to
                                # save. Load it as a PILlow image and save that.
                                self.__load_image_from_buffer(self.bufToSave)

                                tImgSave = time.time()
                                tImgStats = self.__save_frame()

                                # Re-queue the frame buffer for cleanup
                                tReQ = time.time()
                                self.__requeue_frame(self.bufToSave)

                                self.bufToSave = None
                                self.brokenRx = False
                            else:
                                tImgSave = tImgLoad
                                tReQ = tImgLoad
                        else:
                            tImgLoad = time.time()
                            tImgSave = tImgLoad
                            tReQ = tImgLoad
                            qCWarning(self.logCategory,
                                      "Buffer failure, must stop stream")
                            # debug_message("Buffer failure, must stop stream")

                        # End the stream, close and free any buffers the
                        # _stream_off itself takes 75% of the whole capture
                        # runtime. Threads can't be used because the camea file
                        # descriptor is owned by the main window and if a new
                        # instance of this thread starts setting up for capture
                        # overlapping another releasing resources it will fail
                        # if stream ON/OFF order reverses or buffer clearup
                        # ovelaps another thread's buffer setup. It might help
                        # if the buffers are owned by the main window and not
                        # created/released on every frame capture.
                        tStrmOff = time.time()
                        self.__stream_off()

                        tBufClose = time.time()
                        self.__close_capture_buffers()

                        tBufFree = time.time()
                        self.__release_capture_buffers()
                        tBufEnd = time.time()
                    else:
                        qCDebug(self.logCategory, "No capture buffers")
                        # debug_message("No capture buffers")
                tEnd = time.time()

                # Calculate the elapsed time of it all and the elements
                elapsed = tEnd - tStart
                sElapsed = tStrmOn - tStart
                onElapsed = tWaitFrame - tStrmOn
                wElapsed = tImgLoad - tWaitFrame
                ldElapsed = tImgSave - tImgLoad
                svElapsed = tReQ - tImgSave - tImgStats
                cElapsed = tStrmOff - tReQ
                offElapsed = tBufClose - tStrmOff
                cClose = tBufFree - tBufClose
                cRelease = tBufEnd - tBufFree

                # Save the capture duration only for saved frames
                if self.save_capture_frame:
                    self.lastCaptureElapsed = elapsed

                # Show the elapsed times
                msg = "CAPTURE TIMING: elapsed {:.6f}s".format(elapsed)
                qCDebug(self.logCategory, msg)
                # debug_message(msg)
                msg = " \\ t: frames {:.6f}, ".format(wElapsed)
                msg += "setup {:.6f}, ".format(sElapsed)
                msg += "stream ON {:.6f}, ".format(onElapsed)
                msg += "OFF {:.6f}, ".format(offElapsed)
                msg += "from buf {:.6f}, ".format(ldElapsed)
                msg += "save {:.6f}, ".format(svElapsed)
                msg += "cleanup {:.6f}, ".format(cElapsed)
                msg += "buffers CLOSE {:.6f}, ".format(cClose)
                msg += "RELEASE {:.6f}, ".format(cRelease)
                msg += "stats gen. {:.6f}, ".format(tImgStats)
                qCDebug(self.logCategory, msg)
                # debug_message(msg)

                # Show each element as a percentage of total time
                percFrac = 100.0 / elapsed
                msg = " \\ %: frames {:.3f}, ".format(wElapsed * percFrac)
                msg += "setup {:.3f}, ".format(sElapsed * percFrac)
                msg += "stream ON {:.3f}, ".format(onElapsed * percFrac)
                msg += "OFF {:.3f}, ".format(offElapsed * percFrac)
                msg += "from buf {:.3f}, ".format(ldElapsed * percFrac)
                msg += "save {:.3f}, ".format(svElapsed * percFrac)
                msg += "cleanup {:.3f}, ".format(cElapsed * percFrac)
                msg += "buffers CLOSE {:.3f}, ".format(cClose * percFrac)
                msg += "RELEASE {:.3f}, ".format(cRelease * percFrac)
                msg += "stats gen. {:.3f}".format(tImgStats * percFrac)
                qCDebug(self.logCategory, msg)
                # debug_message(msg)
                # warning_message(msg)
            except Exception as e:
                qCWarning(self.logCategory,
                          "Capture run failed: {}".format(type(e)))
                # debug_message("Capture run failed: {}".format(type(e)))
                msg = "Time list: {}, {} ".format(tStart, tStrmOn)
                msg += "{}, {} {}, ".format(tWaitFrame, tImgLoad, tImgSave)
                msg += "{}, {}, {}, ".format(tReQ, tBufClose, tStrmOff)
                msg += "{}, {}, {}".format(tBufFree, tBufEnd, tImgStats)
                qCWarning(self.logCategory, msg)
                # debug_message(msg)

                # Try to make sure we end on failure with no capture buffers
                self.__close_capture_buffers()
                self.__release_capture_buffers()

        # Thread will end, abandon state and log exit time
        self.capDev = None
        qCDebug(self.logCategory, "-- Result ready...")
        # debug_message("-- Result ready...")
        self.tThreadExit = time.time()
