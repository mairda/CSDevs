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

from threading import Lock

from fcntl import ioctl

from v4l2py.device import Device
from v4l2py.raw import (v4l2_input, v4l2_queryctrl, V4L2_CID_BASE,
                        V4L2_CID_LASTP1, V4L2_CTRL_FLAG_DISABLED,
                        V4L2_INPUT_TYPE_CAMERA, VIDIOC_ENUMINPUT,
                        VIDIOC_QUERYCTRL)

from PySide6.QtCore import (QLoggingCategory, qCDebug, qCWarning)

# from csdMessages import (disable_warnings, enable_warnings, disable_debug,
#                          enable_debug, warning_message, debug_message)


# FIXME: All the remove/add pairs are locked but that won't protect access
# between a remove and add. Do we need a lock to protect read and even iterate.
# In the case of iterate it must lock only in the step itself otherwise only
# one iterator would proceed to completion at a time
# FIXME: ctrlsLock needs to be reviewed to be sure that it protects internal
# iterations without blocking the class iterator unnecessarilly
class v4l2CameraControlList:
    '''
    Class to provide access to video for linux 2 camera controls. Conversion
    between ID and name and the reverse are provided. Access to control value
    is provided. Range limits can be set and can differ during day and night
    periods. Controls are video source (camera) specific. The class has a lock
    for update control.
    '''

    cameraName = ""

    # We can have control management for all day (empty string), daytime
    # ("Day") and nighttime ("Night")
    validTODs = ["", "Day", "Night"]
    todPeriod = ""

    logCategory = QLoggingCategory("csdevs.camera.control.list")

    '''
    List of information for camera controls. Each item is a tuple containing:
        Control Name: string
        Query Control: v4l2_queryctrl (contents include the control ID)
        Runtime Minimum: number to be used as the minimum value for the control
        Runtime Maximum: number to be used as the maximum value for the control
        Runtime Default: number to be used as the default value for the control
        Use Minimum: boolean indicating if the runtime minimum is in-use
        Use Maximum: boolean indicating if the runtime maxumum is in-use
        Negative effect: boolean indicating if the minimum represents the
                         highest application of the control's property
        Encourage limits: boolean indicating if the minimum and maximum are to
                          be enforced without permitting attempt to drive the
                          controls property towards being in the range
    '''
    cameraControls = []

    '''
    Access control for threads
    '''
    ctrlsLock = Lock()

    # def __init__(self):
    #     pass

    def __iter__(self):
        '''
        Object constructer. Returns a constructed instance of this class.
        '''

        return v4l2CameraControlListIterator(self)

    @property
    def camera_name(self):
        '''
        Access the camera name in an instance of this class as a property member
        '''

        return self.cameraName

    def set_camera_name(self, newName):
        '''
        Set the camera name in an instance of this class
        '''

        self.cameraName = newName

    @property
    def TOD_period(self):
        '''
        Access the time-of-day period name for an instance of this class as a
        property member
        '''

        if not (self.todPeriod in self.validTODs):
            # Unrecognized TOD, reset to all-day
            self.todPeriod = self.validTODs[0]

        return self.todPeriod

    def set_TOD_period(self, newTOD):
        '''
        Set the time-of-day period for an instance of this class

        Parameters
        ----------
            newTOD: string
                The text name of the new time-of-day period to use, e.g. "Day"
                or "Night". "", the empty string is supported to indicate no
                specific named time-of-day, e.g. all-day but can also be used
                for things like a copy of an instance of this class to intend
                no specific time-of-day or not something that needs to be known
                in this instance.
        '''

        if not (newTOD in self.validTODs):
            raise NameError

        self.todPeriod = newTOD

    def list_item_by_name(self, ctrlName):
        '''
        Get the list entry for a camera control by Name (allows getting runtime
        limits by name)

        Parameters
        ----------
            ctrlName: string
                The name of the control object to find in the list

        Returns an entry in the control list which is an instance of the tuple
        described as member of the cameraControls list.

        Errors: Raises a NameError exception if the supplied control name is not
        found in the current camera control list.
        '''
        for aCtrl in self.cameraControls:
            # "Scanning control list {} == {}?".format(aCtrl[0], ctrlName)
            if aCtrl[0] == ctrlName:
                return aCtrl

        raise NameError

    def query_control_by_name(self, ctrlName):
        '''
        Get the v4l2_queryctrl for a named control, using the pre-exiting
        implementation to get the list entry

        Parameters
        ----------
            ctrlName: string
                The name of the control to get the query control structure for

        Returns the v4l2_queryctrl structure from the internal list for the
        first control found with the supplied name.

        Errors: Allows lookup errors, passing any NameError exception to the
        caller if the name is not found
        '''
        aCtrl = self.list_item_by_name(ctrlName)

        return aCtrl[1]

    # Get the list entry for a camera control by ID (allows getting name and
    # runtime limits by ID)
    def list_item_by_ID(self, ctrlID):
        '''
        Get the list entry for a camera control by V4L2 Control ID number
        (allows getting runtime limits by control ID)

        Parameters
        ----------
            ctrlID: integer
                The control ID of the control object to find in the list

        Returns an entry in the control list which is an instance of the tuple
        described as member of the cameraControls list.

        Errors: Raises a ValueError exception if the supplied control name is
        not found in the current camera control list.
        '''

        for aCtrl in self.cameraControls:
            if aCtrl[1].id == ctrlID:
                return aCtrl

        raise ValueError

    def query_control_by_ID(self, ctrlID):
        '''
        Get the v4l2_queryctrl for a control by ID, using the pre-exiting
        implementation to get the list entry

        Parameters
        ----------
            ctrlID: integer
                The ID of the control to get the query control structure for

        Returns the v4l2_queryctrl structure from the internal list for the
        first control found with the supplied ID.

        Errors: Allows lookup errors, passing any ValueError exception to the
        caller if the ID is not found
        '''

        aCtrl = self.list_item_by_ID(ctrlID)
        return aCtrl[1]

    def control_name_exists(self, ctrlName):
        '''
        Simple does a control exist with a given name

        Parameters
        ----------
            ctrlName: string
                The name of the control to verify exists in the control list in
                an instance of the class

        Returns True if the named control exists in the control list, False if
        it does not
        '''

        try:
            self.query_control_by_name(ctrlName)
            return True
        except NameError:
            return False

    def control_ID_exists(self, ctrlID):
        '''
        Simple does a control exist with a given ID

        Parameters
        ----------
            ctrlID: string
                The ID of the control to verify exists in the control list in
                an instance of the class

        Returns True if a control with the ID exists in the control list, False
        if it does not
        '''

        try:
            self.query_control_by_ID(ctrlID)
            return True
        except ValueError:
            return False

    # Provide class based access to the members of the v4l2_queryctrl by name
    # and by ID. If the supplied name or ID doesn't exist the attempt to find
    # the v4l2_queryctrl with the requested propery raises an exception, let
    # it continue to the caller

    def name_by_ID(self, ctrlID):
        '''
        Get the control name for a control ID

        Parameters
        ----------
            ctrlID: integer
                The control ID number to get the name for

        Returns a string containing the name of the control with the supplied ID
        in an instance of the class

        Errors: Passes to the caller any ValueError exception from a failure to
        find the control ID in the object
        '''

        aCtrl = self.list_item_by_ID(ctrlID)
        return aCtrl[0]

    def ID_by_name(self, ctrlName):
        '''
        Get the control ID for a control name

        Parameters
        ----------
            ctrlName: string
                The control name to get the ID for

        Returns an integer containing the ID of the control with the supplied
        name in an instance of the class

        Errors: Passes to the caller any NameError exception from a failure to
        find the control name in the object
        '''

        ctrl = self.query_control_by_name(ctrlName)
        return ctrl.id

    def type_by_name(self, ctrlName):
        '''
        Get the control type for a given control name

        Parameters
        ----------
            ctrlName: string
                The text name of the control to get the type of

        Returns the V4L2 numeric control type value for the named control

        Errors: If the name cannot be found in the used object then the
        NameError exception from the lookup is passed to the caller
        '''

        ctrl = self.query_control_by_name(ctrlName)
        return ctrl.type

    def type_by_ID(self, ctrlID):
        '''
        Get the control type for a given control ID

        Parameters
        ----------
            ctrlID: integer
                The ID of the control to get the type of

        Returns the V4L2 numeric control type value for the control ID

        Errors: If the ID cannot be found in the used object then the
        ValueError exception from the lookup is passed to the caller
        '''

        ctrl = self.query_control_by_ID(ctrlID)
        return ctrl.type

    def minimum_by_name(self, ctrlName):
        '''
        Get the control's minimum value for a given control name. This is not
        the runtime minimum to be applied, it is the the minimum value the
        control supports

        Parameters
        ----------
            ctrlName: string
                The name of the control to get the minimum value of

        Returns the V4L2 numeric control minimum value for the named control

        Errors: If the name cannot be found in the used object then the
        NameError exception from the lookup is passed to the caller
        '''

        ctrl = self.query_control_by_name(ctrlName)
        return ctrl.minimum

    def minimum_by_ID(self, ctrlID):
        '''
        Get the control's minimum value for a given control ID. This is not
        the runtime minimum to be applied, it is the the minimum value the
        control supports

        Parameters
        ----------
            ctrlID: integer
                The ID of the control to get the minimum value of

        Returns the V4L2 numeric control minimum value for the control with the
        given ID

        Errors: If the ID cannot be found in the used object then the
        ValueError exception from the lookup is passed to the caller
        '''

        ctrl = self.query_control_by_ID(ctrlID)
        return ctrl.minimum

    def maximum_by_name(self, ctrlName):
        '''
        Get the control's maximum value for a given control name. This is not
        the runtime maximum to be applied, it is the the maximum value the
        control supports

        Parameters
        ----------
            ctrlName: string
                The name of the control to get the maximum value of

        Returns the V4L2 numeric control maximum value for the named control

        Errors: If the name cannot be found in the used object then the
        NameError exception from the lookup is passed to the caller
        '''

        ctrl = self.query_control_by_name(ctrlName)
        return ctrl.maximum

    def maximumByID(self, ctrlID):
        '''
        Get the control's maximum value for a given control ID. This is not
        the runtime maximum to be applied, it is the the maximum value the
        control supports

        Parameters
        ----------
            ctrlID: integer
                The ID of the control to get the maximum value of

        Returns the V4L2 numeric control maximum value for the control with the
        given ID

        Errors: If the ID cannot be found in the used object then the
        ValueError exception from the lookup is passed to the caller
        '''

        ctrl = self.query_control_by_ID(ctrlID)
        return ctrl.maximum

    def stepByName(self, ctrlName):
        '''
        Get the control's value step for a given control name.

        Parameters
        ----------
            ctrlName: string
                The name of the control to get the value step of

        Returns the V4L2 numeric control step value for the control with the
        given name

        Errors: If the name cannot be found in the used object then the
        NameError exception from the lookup is passed to the caller
        '''

        ctrl = self.query_control_by_name(ctrlName)
        return ctrl.step

    def stepByID(self, ctrlID):
        '''
        Get the control's value step for a given control ID.

        Parameters
        ----------
            ctrlID: integer
                The ID of the control to get the value step of

        Returns the V4L2 numeric control step value for the control with the
        given ID

        Errors: If the ID cannot be found in the used object then the
        ValueError exception from the lookup is passed to the caller
        '''

        ctrl = self.query_control_by_ID(ctrlID)
        return ctrl.step

    def default_by_name(self, ctrlName):
        '''
        Get the default value for a given control by name.

        Parameters
        ----------
            ctrlName: string
                The name of the control to get the default value of

        Returns the V4L2 default value for the control with the given name

        Errors: If the name cannot be found in the used object then the
        NameError exception from the lookup is passed to the caller
        '''

        ctrl = self.query_control_by_name(ctrlName)
        return ctrl.default_value

    def default_by_ID(self, ctrlID):
        '''
        Get the default value for a given control by ID.

        Parameters
        ----------
            ctrlID: integer
                The ID of the control to get the default value of

        Returns the V4L2 control default value for the control with the
        given ID

        Errors: If the ID cannot be found in the used object then the
        ValueError exception from the lookup is passed to the caller
        '''

        ctrl = self.query_control_by_ID(ctrlID)
        return ctrl.default_value

    def flags_by_name(self, ctrlName):
        '''
        Get the control flags for a given control by name.

        Parameters
        ----------
            ctrlName: string
                The name of the control to get the control flags of

        Returns the V4L2 control flags value for the control with the given name

        Errors: If the name cannot be found in the used object then the
        NameError exception from the lookup is passed to the caller
        '''

        ctrl = self.query_control_by_name(ctrlName)
        return ctrl.flags

    def flags_by_ID(self, ctrlID):
        '''
        Get the control flags for a given control by ID.

        Parameters
        ----------
            ctrlID: integer
                The ID of the control to get the control flags of

        Returns the V4L2 control flags value for the control with the given ID

        Errors: If the name cannot be found in the used object then the
        NameError exception from the lookup is passed to the caller
        '''

        ctrl = self.query_control_by_ID(ctrlID)
        return ctrl.flags

    def runtime_minimum_by_name(self, ctrlName):
        '''
        Get a runtime minimum to use for a given control by name. This is not
        enforced by V4L2 and is a record of a value the application should
        enforce. This is intended to allow the application to restrict control
        value range.

        Parameters
        ----------
            ctrlName: string
                The name of the control to get the runtime minimum for

        Returns the runtime minimum value to use for the control with the given
        name

        Errors: If the name cannot be found in the used object then the
        NameError exception from the lookup is passed to the caller
        '''

        aCtrl = self.list_item_by_name(ctrlName)
        return aCtrl[2]

    def runtime_minimum_by_ID(self, ctrlID):
        '''
        Get a runtime minimum to use for a given control by ID. This is not
        enforced by V4L2 and is a record of a value the application should
        enforce. This is intended to allow the application to restrict control
        value range.

        Parameters
        ----------
            ctrlID: integer
                The ID of the control to get the runtime minimum for

        Returns the runtime minimum value to use for the control with the given
        ID

        Errors: If the ID cannot be found in the used object then the
        ValueError exception from the lookup is passed to the caller
        '''

        aCtrl = self.list_item_by_ID(ctrlID)
        return aCtrl[2]

    def runtime_minimum_by_name_in_use(self, ctrlName):
        '''
        Get a boolean value indicating if the runtime minimum for a given
        control by name is enabled.

        Parameters
        ----------
            ctrlName: string
                The name of the control to get the runtime minimum in-use state
                for

        Returns the in-use state of the runtime minimum for the control with the
        given name

        Errors: If the name cannot be found in the used object then the
        NameError exception from the lookup is passed to the caller
        '''

        aCtrl = self.list_item_by_name(ctrlName)
        return aCtrl[5]

    def runtime_minimum_by_ID_in_use(self, ctrlID):
        '''
        Get a boolean value indicating if the runtime minimum for a given
        control by ID is enabled.

        Parameters
        ----------
            ctrlID: integer
                The ID of the control to get the runtime minimum in-use state
                for

        Returns the in-use state of the runtime minimum for the control with the
        given ID

        Errors: If the ID cannot be found in the used object then the
        ValueError exception from the lookup is passed to the caller
        '''

        aCtrl = self.list_item_by_ID(ctrlID)
        return aCtrl[5]

    def runtime_maximum_by_name(self, ctrlName):
        '''
        Get a runtime maximum to use for a given control by name. This is not
        enforced by V4L2 and is a record of a value the application should
        enforce. This is intended to allow the application to restrict control
        value range.

        Parameters
        ----------
            ctrlName: string
                The name of the control to get the runtime maximum for

        Returns the runtime maximum value to use for the control with the given
        name

        Errors: If the name cannot be found in the used object then the
        NameError exception from the lookup is passed to the caller
        '''

        aCtrl = self.list_item_by_name(ctrlName)
        return aCtrl[3]

    def runtime_maximum_by_ID(self, ctrlID):
        '''
        Get a runtime maximum to use for a given control by ID. This is not
        enforced by V4L2 and is a record of a value the application should
        enforce. This is intended to allow the application to restrict control
        value range.

        Parameters
        ----------
            ctrlID: integer
                The ID of the control to get the runtime maximum for

        Returns the runtime maximum value to use for the control with the given
        ID

        Errors: If the ID cannot be found in the used object then the
        ValueError exception from the lookup is passed to the caller
        '''

        aCtrl = self.list_item_by_ID(ctrlID)
        return aCtrl[3]

    def runtime_maximum_by_name_in_use(self, ctrlName):
        '''
        Get a boolean value indicating if the runtime maximum for a given
        control by name is enabled.

        Parameters
        ----------
            ctrlName: string
                The name of the control to get the runtime maximum in-use state
                for

        Returns the in-use state of the runtime maximum for the control with the
        given name

        Errors: If the name cannot be found in the used object then the
        NameError exception from the lookup is passed to the caller
        '''

        aCtrl = self.list_item_by_name(ctrlName)
        return aCtrl[6]

    def runtime_maximum_by_ID_in_use(self, ctrlID):
        '''
        Get a boolean value indicating if the runtime maximum for a given
        control by ID is enabled.

        Parameters
        ----------
            ctrlID: integer
                The ID of the control to get the runtime maximum in-use state
                for

        Returns the in-use state of the runtime maximum for the control with the
        given ID

        Errors: If the ID cannot be found in the used object then the
        ValueError exception from the lookup is passed to the caller
        '''

        aCtrl = self.list_item_by_ID(ctrlID)
        return aCtrl[6]

    def runtime_default_by_name(self, ctrlName):
        '''
        Get a runtime default value for a given control by name. This is not
        enforced by V4L2 and is intended as a value the application should
        enforce itself.

        Parameters
        ----------
            ctrlName: string
                The name of the control to get the runtime maximum value for

        Returns the runtime default value to use for the control with the
        given name

        Errors: If the name cannot be found in the used object then the
        NameError exception from the lookup is passed to the caller
        '''

        aCtrl = self.list_item_by_name(ctrlName)
        return aCtrl[4]

    def runtime_default_by_ID(self, ctrlID):
        '''
        Get a runtime default value for a given control by ID. This is not
        enforced by V4L2 and is intended as a value the application should
        enforce itself.

        Parameters
        ----------
            ctrlID: integer
                The ID of the control to get the runtime maximum value for

        Returns the runtime default value to use for the control with the
        given ID

        Errors: If the ID cannot be found in the used object then the
        ValueError exception from the lookup is passed to the caller
        '''

        aCtrl = self.list_item_by_ID(ctrlID)
        return aCtrl[4]

    def negative_effect_by_name(self, ctrlName):
        '''
        Get a boolean indicating if the control range for a given control by
        name has a negative effect on the property the control represents. For
        example, if increasing the brightness control value decreases the
        brightness of image data, etc. This can't be determined from V4L2 and
        must be information supplied by the application using objects of this
        class.

        Parameters
        ----------
            ctrlName: string
                The name of the control to get the state of negative effect for

        Returns the state of negative effect the control with the given name has

        Errors: If the name cannot be found in the used object then the
        NameError exception from the lookup is passed to the caller
        '''

        aCtrl = self.list_item_by_name(ctrlName)
        return aCtrl[7]

    def negative_effect_by_ID(self, ctrlID):
        '''
        Get a boolean indicating if the control range for a given control by
        ID has a negative effect on the property the control represents. For
        example, if increasing the brightness control value decreases the
        brightness of image data, etc. This can't be determined from V4L2 and
        must be information supplied by the application using objects of this
        class.

        Parameters
        ----------
            ctrlID: integer
                The ID of the control to get the state of negative effect for

        Returns the state of negative effect the control with the given name has

        Errors: If the ID cannot be found in the used object then the
        ValueError exception from the lookup is passed to the caller
        '''

        aCtrl = self.list_item_by_ID(ctrlID)
        return aCtrl[7]

    def encourage_limits_by_name(self, ctrlName):
        '''
        Get a boolean indicating if the runtime minimum/maximm for a given
        control by name should be enforced on the control value or if the
        control should be allowed to progress towards the runtime
        minimum/maximum. Like the runtime minimum/maximum themselves this is not
        V4L2 state and is intended for the application to use to decide it's own
        behavior.

        Parameters
        ----------
            ctrlName: string
                The name of the control to get the state of encourage limits for

        Returns the state of encourage limis for the control with the given name

        Errors: If the name cannot be found in the used object then the
        NameError exception from the lookup is passed to the caller
        '''

        aCtrl = self.list_item_by_name(ctrlName)
        return aCtrl[8]

    def encourage_limits_by_ID(self, ctrlID):
        '''
        Get a boolean indicating if the runtime minimum/maximm for a given
        control by ID should be enforced on the control value or if the
        control should be allowed to progress towards the runtime
        minimum/maximum. Like the runtime minimum/maximum themselves this is not
        V4L2 state and is intended for the application to use to decide it's own
        behavior.

        Parameters
        ----------
            ctrlID: integer
                The ID of the control to get the state of encourage limits for

        Returns the state of encourage limis for the control with the given ID

        Errors: If the ID cannot be found in the used object then the
        ValueError exception from the lookup is passed to the caller
        '''

        aCtrl = self.list_item_by_ID(ctrlID)
        return aCtrl[8]

    def __valid_query_control(self, qCtrl):
        '''
        Do some common-sense validation of a supplied v4l2_queryctrl. It's not
        absolute verification that it's valid, more like validation that it's
        believable or plausible.

        Parameters
        ----------
            qCtrl: v4l2_queryctrl
                A V4L2 query control structure to validate the contents of

        Returns True if validation is successful, False if not.
        '''

        # The query control is not None and has an ID in the expected range is
        # considered valid.
        if qCtrl is not None:
            if (qCtrl.id >= V4L2_CID_BASE) and (qCtrl.id < V4L2_CID_LASTP1):
                return True

        return False

    def __is_valid_control_value(self, value, min, max, step):
        '''
        Check that a value is valid given minimum, maximum and step values.
        Value is only checked for being on a step if the supplied step is
        greater than zero

        Parameters
        ----------
            value: integer
                The value to be validated
            min: integer
                The minimum value the value can have
            max: integer
                The maximum value the value can have
            step: integer
                The step between supported values

        Returns True if the value is in the range min through max is on a step
        (if step greater than zero)
        '''

        if (value >= min) and (value <= max):
            if step <= 0:
                return True

            # Align range with zero to use mod for step
            rOffset = 0 - min
            zValue = value + rOffset
            if (zValue % step) == 0:
                return True

        return False

    def is_valid_control_value_by_name(self, ctrlName, value):
        '''
        Check that a given value is in-range and on-step for a given control
        by name

        Parameters
        ----------
            ctrlName: string
                The name of a control to check the value is in-range and on-step
                for
            value: integer
                The value to check

        Returns True if the value is in-range and on-step for the named control,
        else returns False

        Errors: If looking up the named control's minimum, maximum or step fails
        to find the named control the NameError exception from that operation
        is allowed to pass to the caller.
        '''

        min = self.minimum_by_name(ctrlName)
        max = self.maximum_by_name(ctrlName)
        step = self.stepByName(ctrlName)

        return self.__is_valid_control_value(value, min, max, step)

    def is_valid_control_value_by_ID(self, ctrlID, value):
        '''
        Check that a given value is in-range and on-step for a given control
        by ID

        Parameters
        ----------
            ctrlID: integer
                The ID of a control to check the value is in-range and on-step
                for
            value: integer
                The value to check

        Returns True if the value is in-range and on-step for the control with
        the given ID, else returns False

        Errors: If looking up the minimum, maximum or step for the control with
        the supplied ID fails to find the control the ValueError exception from
        that operation is allowed to pass to the caller.
        '''

        min = self.minimum_by_ID(ctrlID)
        max = self.maximumByID(ctrlID)
        step = self.stepByID(ctrlID)
        return self.__is_valid_control_value(value, min, max, step)

    # Runtime values can be set after adding the control
    # FIXME these should check value type is fit for ctrl.type as well as
    # in-range, on-step
    def set_runtime_minimum_by_name(self, ctrlName, value):
        '''
        Set a runtime minimum for a named control. This can be set after the
        control itself has been added to the object and can be modified over
        time. It isn't necessary to set a value to prevent a runtime minimum
        being used. That can be enabled/disabled with the
        set_runtime_minimum_usage() function.

        Paramters
        ---------
            ctrlName: string
                The control name to set a runtime minimum value for
            value: integer
                The value to use for the runtime minimum for the named control.
                It is an integer because the value for all V4L2 control types
                are implemented as integers but it is the caller's
                responsibility to ensure any value is in the valid range for any
                control's V4L2 type

        Errors:
            Can raise a ValueError if the value is discovered not valid for
            the control. This usually only happens in cases where the caller is
            a Qt slot for a list and valueChanged for the related control
            precedes currentItemChanged. This has the chance of the old curent
            item's control range/step being used to test the new current item's
            maximum value

            Will pass to the caller any NameError exception from a failure
            looking up the control by name in an object instance.
        '''

        if self.is_valid_control_value_by_name(ctrlName, value):
            # Since we'll need all the other properties to use modify we can
            # also optimize by checking for a change
            aCtrl = self.list_item_by_name(ctrlName)

            # If we know it is a change, make one without re-checking
            if aCtrl[2] != value:
                # This will do the lock/remove/append itself
                self.__modify_camera_control(True, aCtrl[1], value, aCtrl[3],
                                             aCtrl[4], aCtrl[5], aCtrl[6],
                                             aCtrl[7], aCtrl[8])
        else:
            # Can happen if caller is Qt slot for a list and valueChanged for
            # related controls precedes the currentItemChanged
            # debug_message("Min invalid control {} or value {}".format(ctrlName,
            #                                                            value))
            raise ValueError

    def set_runtime_minimum_by_ID(self, ctrlID, value):
        '''
        Set a runtime minimum for a control by ID. This can be set after the
        control itself has been added to the object and can be modified over
        time. It isn't necessary to set a value to prevent a runtime minimum
        being used. That can be enabled/disabled with the
        set_runtime_minimum_usage() function.

        Paramters
        ---------
            ctrlID: integer
                The ID of the control to set a runtime minimum value for
            value: integer
                The value to use for the runtime minimum for the named control.
                It is an integer because the value for all V4L2 control types
                are implemented as integers but it is the caller's
                responsibility to ensure any value is in the valid range for any
                control's V4L2 type

        Errors:
            Can raise a ValueError if the value is discovered not valid for
            the control. This usually only happens in cases where the caller is
            a Qt slot for a list and valueChanged for the related control
            precedes currentItemChanged.  This has the chance of the old curent
            item's control range/step being used to test the new current item's
            minimum value

            Will pass to the caller any ValueError exception from a failure
            looking up the control by ID in an object instance.
        '''

        if self.is_valid_control_value_by_ID(ctrlID, value):
            # Since we'll need all the other properties to use modify we can
            # also optimize by checking for a change
            aCtrl = self.list_item_by_ID(ctrlID)

            # If we know it is a change, make one without re-checking
            if aCtrl[2] != value:
                # This will do the lock/remove/append itself
                self.__modify_camera_control(True, aCtrl[1], value, aCtrl[3],
                                             aCtrl[4], aCtrl[5], aCtrl[6],
                                             aCtrl[7], aCtrl[8])
        else:
            # Can happen if caller is Qt slot for a list and valueChanged for
            # related controls precedes the currentItemChanged
            raise ValueError

    def set_runtime_minimum_by_name_usage(self, ctrlName, enable=False):
        '''
        Enable or disable use of the runtime minimum for a named control.

        Parameters
        ----------
            ctrlName: string
                The name of the control to enable/disable use of the runtime
                minimum for
            enable: boolean
                True to enable the use of the runtime minimum, False to disable
                it. Defaults to False.

        Errors: Allows any NameError exception from failure  looking up the
        control by name in the current object to pass to the caller
        '''

        # Since we'll need all the other properties to use modify we can
        # also optimize by checking for a change
        aCtrl = self.list_item_by_name(ctrlName)

        # If we know it is a change, make one without re-checking
        if aCtrl[5] != enable:
            # This will do the lock/remove/append itself
            self.__modify_camera_control(True, aCtrl[1], aCtrl[2], aCtrl[3],
                                         aCtrl[4], enable, aCtrl[6], aCtrl[7],
                                         aCtrl[8])

    def set_runtime_minimum_by_ID_usage(self, ctrlID, enable=False):
        '''
        Enable or disable use of the runtime minimum for a control by ID.

        Parameters
        ----------
            ctrlID: integer
                The ID of the control to enable/disable use of the runtime
                minimum for
            enable: boolean
                True to enable the use of the runtime minimum, False to disable
                it. Defaults to False.

        Errors: Allows any ValueError exception from failure looking up the
        control by ID in the current object to pass to the caller
        '''

        # Since we'll need all the other properties to use modify we can
        # also optimize by checking for a change
        aCtrl = self.list_item_by_ID(ctrlID)

        # If we know it is a change, make one without re-checking
        if aCtrl[2] != enable:
            # This will do the lock/remove/append itself
            # FIXME: This should probably check that the runtime minimum is
            # valid for the control by ID
            self.__modify_camera_control(True, aCtrl[1], aCtrl[2], aCtrl[3],
                                         aCtrl[4], enable, aCtrl[6], aCtrl[7],
                                         aCtrl[8])

    def set_runtime_maximum_by_name(self, ctrlName, value):
        '''
        Set a runtime maximum for a named control. This can be set after the
        control itself has been added to the object and can be modified over
        time. It isn't necessary to set a value to prevent a runtime maximum
        being used. That can be enabled/disabled with the
        set_runtime_maximum_usage() function.

        Paramters
        ---------
            ctrlName: string
                The control name to set a runtime maximum value for
            value: integer
                The value to use for the runtime maximum for the named control.
                It is an integer because the value for all V4L2 control types
                are implemented as integers but it is the caller's
                responsibility to ensure any value is in the valid range for any
                control's V4L2 type

        Errors:
            Can raise a ValueError if the value is discovered not valid for
            the control. This usually only happens in cases where the caller is
            a Qt slot for a list and valueChanged for the related control
            precedes currentItemChanged. This has the chance of the old curent
            item's control range/step being used to test the new current item's
            maximum value

            Will pass to the caller any NameError exception from a failure
            looking up the control by name in an object instance.
        '''

        if self.is_valid_control_value_by_name(ctrlName, value):
            # Since we'll need all the other properties to use modify we can
            # also optimize by checking for a change
            aCtrl = self.list_item_by_name(ctrlName)

            # If we know it is a change, make one without re-checking
            if aCtrl[3] != value:
                # This will do the lock/remove/append itself
                self.__modify_camera_control(True, aCtrl[1], aCtrl[2], value,
                                             aCtrl[4], aCtrl[5], aCtrl[6],
                                             aCtrl[7], aCtrl[8])
        else:
            # Can happen if caller is Qt slot for a list and valueChanged for
            # related controls precedes the currentItemChanged
            raise ValueError

    def set_runtime_maximum_by_ID(self, ctrlID, value):
        '''
        Set a runtime maximum for a control by ID. This can be set after the
        control itself has been added to the object and can be modified over
        time. It isn't necessary to set a value to prevent a runtime maximum
        being used. That can be enabled/disabled with the
        set_runtime_maximum_usage() function.

        Paramters
        ---------
            ctrlID: integer
                The ID of the control to set a runtime maximum value for
            value: integer
                The value to use for the runtime maximum for the named control.
                It is an integer because the value for all V4L2 control types
                are implemented as integers but it is the caller's
                responsibility to ensure any value is in the valid range for any
                control's V4L2 type

        Errors:
            Can raise a ValueError if the value is discovered not valid for
            the control. This usually only happens in cases where the caller is
            a Qt slot for a list and valueChanged for the related control
            precedes currentItemChanged.  This has the chance of the old curent
            item's control range/step being used to test the new current item's
            maximum value

            Will pass to the caller any ValueError exception from a failure
            looking up the control by ID in an object instance.
        '''

        if self.is_valid_control_value_by_ID(ctrlID, value):
            # Since we'll need all the other properties to use modify we can
            # also optimize by checking for a change
            aCtrl = self.list_item_by_ID(ctrlID)

            # If we know it is a change, make one without re-checking
            if aCtrl[3] != value:
                # This will do the lock/remove/append itself
                self.__modify_camera_control(True, aCtrl[1], aCtrl[2], value,
                                             aCtrl[4], aCtrl[5], aCtrl[6],
                                             aCtrl[7], aCtrl[8])
        else:
            # Can happen if caller is Qt slot for a list and valueChanged for
            # related controls precedes the currentItemChanged
            raise ValueError

    def set_runtime_maximum_by_name_usage(self, ctrlName, enable=False):
        '''
        Enable or disable use of the runtime maximum for a named control.

        Parameters
        ----------
            ctrlName: string
                The name of the control to enable/disable use of the runtime
                maximum for
            enable: boolean
                True to enable the use of the runtime maximum, False to disable
                it. Defaults to False.

        Errors: Allows any NameError exception from failure looking up the
        control by name in the current object to pass to the caller
        '''

        # Since we'll need all the other properties to use modify we can
        # also optimize by checking for a change
        aCtrl = self.list_item_by_name(ctrlName)

        # If we know it is a change, make one without re-checking
        if aCtrl[6] != enable:
            # This will do the lock/remove/append itself
            self.__modify_camera_control(True, aCtrl[1], aCtrl[2], aCtrl[3],
                                         aCtrl[4], aCtrl[5], enable, aCtrl[7],
                                         aCtrl[8])

    def set_runtime_maximum_by_ID_usage(self, ctrlID, enable=False):
        '''
        Enable or disable use of the runtime maximum for a control by ID.

        Parameters
        ----------
            ctrlID: integer
                The ID of the control to enable/disable use of the runtime
                maximum for
            enable: boolean
                True to enable the use of the runtime maximum, False to disable
                it. Defaults to False.

        Errors: Allows any ValueError exception from failure looking up the
        control by ID in the current object to pass to the caller
        '''

        # Since we'll need all the other properties to use modify we can
        # also optimize by checking for a change
        aCtrl = self.list_item_by_ID(ctrlID)

        # If we know it is a change, make one without re-checking
        if aCtrl[6] != enable:
            # This will do the lock/remove/append itself
            self.__modify_camera_control(True, aCtrl[1], aCtrl[2], aCtrl[3],
                                         aCtrl[4], aCtrl[5], enable, aCtrl[7],
                                         aCtrl[8])

    def set_runtime_default_by_name(self, ctrlName, value):
        '''
        Set a runtime default value for a control. This has no effect on V4L2
        and the use of this class requires that the caller use any runtime
        default.

        Parameters
        ----------
            ctrlName: string
                The name of the control to set a runtime default value for
            value: integer
                The value to use as the runtime default. V4L2 implements all
                type valies as integers with the range containing the type
                restrictions, e.e. V4L2_CTRL_TYPE_BOOLEAN supports integer
                values 0 and 1. It's the caller's responsibility to implement
                these limits for runtime control restrictions.

        Errors:
            Can raise a ValueError if the value is discovered not valid for
            the control. This usually only happens in cases where the caller is
            a Qt slot for a list and valueChanged for the related control
            precedes currentItemChanged.  This has the chance of the old curent
            item's control range/step being used to test the new current item's
            default value

            Will pass to the caller any NameError exception from a failure
            looking up the control by name in an object instance.
        '''

        if self.is_valid_control_value_by_name(ctrlName, value):
            # Since we'll need all the other properties to use modify we can
            # also optimize by checking for a change
            aCtrl = self.list_item_by_name(ctrlName)

            # If we know it is a change, make one without re-checking
            if aCtrl[4] != value:
                # This will do the lock/remove/append itself
                self.modify_camera_control(True, aCtrl[1], aCtrl[2], aCtrl[3],
                                           value, aCtrl[5], aCtrl[6], aCtrl[7],
                                           aCtrl[8])
        else:
            # Can happen if caller is Qt slot for a list and valueChanged for
            # related controls precedes the currentItemChanged
            raise ValueError

    def set_runtime_default_by_ID(self, ctrlID, value):
        '''
        Set a runtime default for a control by ID. This can be set after the
        control itself has been added to the object and can be modified over
        time.

        Paramters
        ---------
            ctrlID: integer
                The ID of the control to set a runtime default value for
            value: integer
                The value to use for the runtime default for the named control.
                It is an integer because the value for all V4L2 control types
                are implemented as integers but it is the caller's
                responsibility to ensure any value is in the valid range for any
                control's V4L2 type

        Errors:
            Can raise a ValueError if the value is discovered not valid for
            the control. This usually only happens in cases where the caller is
            a Qt slot for a list and valueChanged for the related control
            precedes currentItemChanged.  This has the chance of the old curent
            item's control range/step being used to test the new current item's
            default value

            Will pass to the caller any ValueError exception from a failure
            looking up the control by ID in an object instance.
        '''

        if self.is_valid_control_value_by_ID(ctrlID, value):
            # Since we'll need all the other properties to use modify we can
            # also optimize by checking for a change
            aCtrl = self.list_item_by_ID(ctrlID)

            # If we know it is a change, make one without re-checking
            if aCtrl[4] != value:
                # This will do the lock/remove/append itself
                self.__modify_camera_control(True, aCtrl[1], aCtrl[2], aCtrl[3],
                                             value, aCtrl[5], aCtrl[6], aCtrl[7],
                                             aCtrl[8])
        else:
            # Can happen if caller is Qt slot for a list and valueChanged for
            # related controls precedes the currentItemChanged
            raise ValueError

    def set_negative_effect_by_name(self, ctrlName, enable=False):
        '''
        Set the state of negative effect for a control by name. Negative effect,
        when on (True) is the condition where increasing the value of the named
        control decreases the property that control represents, e.g. if
        increasing the value of a "Brightness" control made the image darker.
        This has no direct effect on V4L2 but allows a user of the class to
        store this behavior and use it when adjusting the control value.

        Parameters
        ----------
            ctrlName: string
                The name of the control to set negative effect for
            enable: boolean
                True if the named control has a value with a negative effect,
                else False

        Errors: Will pass to the caller any NameError exception from a failure
        looking up the control by name in an object instance.
        '''

        # Since we'll need all the other properties to use modify we can
        # also optimize by checking for a change
        aCtrl = self.list_item_by_name(ctrlName)

        # If we know it is a change, make one without re-checking
        if aCtrl[7] != enable:
            # This will do the lock/remove/append itself
            self.__modify_camera_control(True, aCtrl[1], aCtrl[2], aCtrl[3],
                                         aCtrl[4],aCtrl[5], aCtrl[6], enable,
                                         aCtrl[8])

    def set_negative_effect_by_ID(self, ctrlID, enable=False):
        '''
        Set the state of negative effect for a control by ID. Negative effect,
        when on (True) is the condition where increasing the value of the named
        control decreases the property that control represents, e.g. if
        increasing the value of a "Brightness" control made the image darker.
        This has no direct effect on V4L2 but allows a user of the class to
        store this behavior and use it when adjusting the control value.

        Parameters
        ----------
            ctrlID: integer
                The ID of the control to set negative effect for
            enable: boolean
                True if the named control has a value with a negative effect,
                else False

        Errors: Will pass to the caller any ValueError exception from a failure
        looking up the control by name in an object instance.
        '''

        # Since we'll need all the other properties to use modify we can
        # also optimize by checking for a change
        aCtrl = self.list_item_by_ID(ctrlID)

        # If we know it is a change, make one without re-checking
        if aCtrl[7] != enable:
            # This will do the lock/remove/append itself
            self.__modify_camera_control(True, aCtrl[1], aCtrl[2], aCtrl[3],
                                         aCtrl[4], aCtrl[5], aCtrl[6], enable,
                                         aCtrl[8])

    def set_encourage_limits_by_name(self, ctrlName, enable=True):
        '''
        Set the state of encourage limits for a control by name. Encourage
        limits, when on (True) is the condition where a control value should be
        restricted to the range from runtime minimum to runtime maximum. If
        encourage limits is not enabled but runtime limits exist a control value
        should be directed towards the range from runtime minimum to runtime
        maximum without restricting it. This has no direct effect on V4L2 but
        allows a user of the class to store a choice of behavior for runtime
        limits and use it when adjusting the control value.

        Parameters
        ----------
            ctrlName: string
                The name of the control to set encourage limits for
            enable: boolean
                True if the encourage limits is enable, else False

        Errors: Will pass to the caller any NameError exception from a failure
        looking up the control by name in an object instance.
        '''

        # Since we'll need all the other properties to use modify we can
        # also optimize by checking for a change
        aCtrl = self.list_item_by_name(ctrlName)

        # If we know it is a change, make one without re-checking
        if aCtrl[8] != enable:
            # This will do the lock/remove/append itself
            self.__modify_camera_control(True, aCtrl[1], aCtrl[2], aCtrl[3],
                                         aCtrl[4], aCtrl[5], aCtrl[6], aCtrl[7],
                                         enable)

    def set_encourage_limits_by_ID(self, ctrlID, enable=True):
        '''
        Set the state of encourage limits for a control by ID. Encourage
        limits, when on (True) is the condition where a control value should be
        restricted to the range from runtime minimum to runtime maximum. If
        encourage limits is not enabled but runtime limits exist a control value
        should be directed towards the range from runtime minimum to runtime
        maximum without restricting it. This has no direct effect on V4L2 but
        allows a user of the class to store a choice of behavior for runtime
        limits and use it when adjusting the control value.

        Parameters
        ----------
            ctrlID: integer
                The ID of the control to set encourage limits for
            enable: boolean
                True if the encourage limits is enable, else False

        Errors: Will pass to the caller any ValueError exception from a failure
        looking up the control by name in an object instance.
        '''

        # Since we'll need all the other properties to use modify we can
        # also optimize by checking for a change
        aCtrl = self.list_item_by_ID(ctrlID)

        # If we know it is a change, make one without re-checking
        if aCtrl[8] != enable:
            # This will do the lock/remove/append itself
            self.__modify_camera_control(aCtrl[1], aCtrl[2], aCtrl[3], aCtrl[4],
                                         aCtrl[5], aCtrl[6], aCtrl[7], enable)

    def __add_camera_control(self, qCtrl, rtMin, rtMax, rtDefault, rtMinUse,
                             rtMaxUse, negativeEffect, encourageLimits):
        '''
        Append a control to the camera control list without performing any
        locking. It does require that the caller has already locked the object.
        The function is for internal use only, e.g. to avoid multiple lock
        attempts when performing several operations that must be synchronized
        by allowing the caller to only perform one lock/unlock around them all.

        Paramters
        ---------
            qCtrl: a v4l2_queryctrl
                The query control for the control being added
            rtMin: integer
                A runtime minimum value for the control
            rtMax: integer
                A runtime maximum for the control
            rtDefault: integer
                A runtime default for the control
            rtMinUse: boolean
                True if the runtime minimum is enabled, else False
            rtMaxUse: boolean
                True if the runtime maximum is enabled, else False
            negativeEffect: boolean
                True if changes in the the control value have a negative effect
                on the control property (e.g. if increasing a brightness control
                value causes the image to get darker)
            encourageLimits: boolean
                True if control values are to be limited to enabled rtMin/rtMax,
                else False

        Errors: Will raise a RuntimeError if the object lock is not already held
        when called.
        '''

        # debug_message("Internal adding control to camera control list")
        if not self.ctrlsLock.locked():
            raise RuntimeError

        # Looks like a valid control, convert the name to python
        # string to reduce access by name overhead
        ctrlName = qCtrl.name.decode('utf-8')
        # debug_message("Adding {} to a control list".format(ctrlName))

        # Store it, the query control and runtime limits as a tuple
        # in the control list
        newCtrl = (ctrlName, qCtrl, rtMin, rtMax, rtDefault,
                   rtMinUse, rtMaxUse, negativeEffect,
                   encourageLimits)
        self.cameraControls.append(newCtrl)

    # Given a v4l2_queryctrl add a list entry for a single control. We can have
    # a known runtime min or max but not use it, hence rtUseMin, rtUseMax
    def add_camera_control(self, qCtrl, rtMin=None, rtMax=None, rtDefault=None,
                         rtMinUse=False, rtMaxUse=False, negativeEffect=False,
                         encourageLimits=True):
        '''
        Append a control to the camera control list without performing any
        locking. It does require that the caller has already locked the object.
        The function is for internal use only, e.g. to avoid multiple lock
        attempts when performing several operations that must be synchronized
        by allowing the caller to only perform one lock/unlock around them all.

        Paramters
        ---------
            qCtrl: a v4l2_queryctrl
                The query control for the control being added
            rtMin: integer
                A runtime minimum value for the control
            rtMax: integer
                A runtime maximum for the control
            rtDefault: integer
                A runtime default for the control
            rtMinUse: boolean
                True if the runtime minimum is enabled, else False
            rtMaxUse: boolean
                True if the runtime maximum is enabled, else False
            negativeEffect: boolean
                True if changes in the the control value have a negative effect
                on the control property (e.g. if increasing a brightness control
                value causes the image to get darker)
            encourageLimits: boolean
                True if control values are to be limited to enabled rtMin/rtMax,
                else False

        Errors: Will allow a RuntimeError from the internal append of the control to
        be passed to the caller if the append happens without the object lock.
        '''

        # debug_message("Adding a query control to camera control list")
        # Is it a valid v4l2_queryctrl
        if self.__valid_query_control(qCtrl):
            # Make sure it doesn't already exist
            if not self.control_ID_exists(qCtrl.id):
                # For unsupplied runtime limits, use the qCtrl values, don't
                # need to use __best_of_three() because there is no previous
                # value for all and the bool arguments already have default
                # bool values. So we have two potential sources only for the
                # integer arguments and only one source for the bool
                # argumewnts, not the three that __best_of_three() exists to
                # deal with
                # debug_message("add_camera_control {}, {}, {}, {}, {}, {}, {}, {}".format(qCtrl.name, rtMin, rtMax, rtDefault, rtMinUse, rtMaxUse, negativeEffect, encourageLimits))
                if rtMin is None:
                    rtMin = qCtrl.minimum
                if rtMax is None:
                    rtMax = qCtrl.maximum
                if rtDefault is None:
                    rtDefault = qCtrl.default_value
                # debug_message("\\ add_camera_control {}, {}, {}, {}, {}, {}, {}, {}".format(qCtrl.name, rtMin, rtMax, rtDefault, rtMinUse, rtMaxUse, negativeEffect, encourageLimits))

                # Get the saved state for the control in configuration
                # DWH

                # Take the lock and create a control list entry for it
                with self.ctrlsLock:
                    self.__add_camera_control(qCtrl, rtMin, rtMax,
                                              rtDefault, rtMinUse, rtMaxUse,
                                              negativeEffect, encourageLimits)

    # Choose first that's not None from a, b or c (or c inevitably)
    def __best_of_three(self, a, b, c):
        '''
        Return the first of a, b or c that is not None (in that order).
        If all are None then None is returned (taken from c)

        Parameters
        ----------
            a:
                The preferred case to return
            b:
                The second preferred case to return
            c:
                The least preferred case to return

        Returns the value of one of a, b or c
        '''

        if a is not None:
            return a

        if b is not None:
            return b

        return c


    def __modify_camera_control(self, isChanged, qCtrl, rtMin, rtMax, rtDefault,
                                rtMinUse, rtMaxUse, negativeEffect,
                                encourageLimits):
        '''
        Private function to modify a camera control. It can be told that a
        change is present in the content. We'll only get here if the control
        exists. Caller will always supply a value not None for every parameter.

        Parameters
        ----------
            isChanged: boolean
                True if the caller knows the content is changed, else False and
                the parameters will be checked to see if they change the listed
                control
            qCtrl: a v4l2_queryctrl
                The query control for the control being added
            rtMin: integer
                A runtime minimum value for the control
            rtMax: integer
                A runtime maximum for the control
            rtDefault: integer
                A runtime default for the control
            rtMinUse: boolean
                True if the runtime minimum is enabled, else False
            rtMaxUse: boolean
                True if the runtime maximum is enabled, else False
            negativeEffect: boolean
                True if changes in the the control value have a negative effect
                on the control property (e.g. if increasing a brightness control
                value causes the image to get darker)
            encourageLimits: boolean
                True if control values are to be limited to enabled rtMin/rtMax,
                else False

        Errors: Will allow any ValueError exception from failure finding the
        listed control using the ID in qCtrl.
        '''

        # debug_message("Modifying a control in camera control list")

        # Find it in the existing list using the control ID, if it
        # fails caller will get a ValueError
        aCtrl = self.list_item_by_ID(qCtrl.id)

        # convert the name to python string to reduce access by name
        # overhead
        ctrlName = qCtrl.name.decode('utf-8')

        # If we don't know there is a change, check for one
        if not isChanged:
            isChanged = (aCtrl[0] != ctrlName) or (aCtrl[2] != rtMin) or\
                (aCtrl[3] != rtMax) or (aCtrl[4] != rtDefault) or\
                (aCtrl[5] != rtMinUse) or (aCtrl[5] != rtMaxUse) or\
                (aCtrl[7] != negativeEffect) or\
                (aCtrl[8] != encourageLimits) or\
                (aCtrl[1].minimum != qCtrl.minimum) or\
                (aCtrl[1].maximum != qCtrl.maximum) or\
                (aCtrl[1].step != qCtrl.step) or\
                (aCtrl[1].flags != qCtrl.falgs)
        if isChanged:
            # Take the lock, remove the existing control list entry and
            # append one with the changes
            with self.ctrlsLock:
                self.__remove_camera_control_by_ID(qCtrl.id)
                self.__add_camera_control(qCtrl, rtMin, rtMax, rtDefault,
                                          rtMinUse, rtMaxUse, negativeEffect,
                                          encourageLimits)

    def modify_camera_control(self, qCtrl, rtMin=None, rtMax=None,
                              rtDefault=None, rtMinUse=None, rtMaxUse=None,
                              negativeEffect=None, encourageLimits=None):
        '''
        Public modify existing camera control. The control modified will be one
        listed that has the ID matching the ID in the qCtrl parameter. Will
        prefer a pre-existing value over parameters with a None value.

        Parameters
        ----------
            qCtrl: a v4l2_queryctrl
                The query control for the control being added
            rtMin: integer
                A runtime minimum value for the control
            rtMax: integer
                A runtime maximum for the control
            rtDefault: integer
                A runtime default for the control
            rtMinUse: boolean
                True if the runtime minimum is enabled, else False
            rtMaxUse: boolean
                True if the runtime maximum is enabled, else False
            negativeEffect: boolean
                True if changes in the the control value have a negative effect
                on the control property (e.g. if increasing a brightness control
                value causes the image to get darker)
            encourageLimits: boolean
                True if control values are to be limited to enabled rtMin/rtMax,
                else False

        Errors: Will allow any ValueError exception from failure finding the
        listed control using the ID in qCtrl.
        '''

        # Is it a valid v4l2_queryctrl
        if self.__valid_query_control(qCtrl):
            # Find it in the existing list using the control ID, if it
            # fails caller will get a ValueError
            aCtrl = self.list_item_by_ID(qCtrl.id)

            # For unsupplied runtime limits, use the previous values or
            # the qCtrl values
            rtMin = self.__best_of_three(rtMin,
                                         self.runtime_minimum_by_ID(qCtrl.id),
                                         qCtrl.minimum)
            rtMax = self.__best_of_three(rtMax,
                                         self.runtime_maximum_by_ID(qCtrl.id),
                                         qCtrl.maximum)
            rtDefault = self.__best_of_three(rtDefault,
                                             self.default_by_ID(qCtrl.id),
                                             qCtrl.default_value)

            # The bool values can't have boolean defaults in this function
            # if they are None, use the previous instance or then the
            # defaults used in add_camera_control()
            rtMinUse = self.__best_of_three(rtMinUse,
                                            self.runtime_minimum_by_ID_in_use(qCtrl.id),
                                            False)
            rtMaxUse = self.__best_of_three(rtMaxUse,
                                            self.runtime_maximum_by_ID_in_use(qCtrl.id),
                                            False)
            negativeEffect = self.__best_of_three(negativeEffect,
                                                  self.negative_effect_by_ID(qCtrl.id),
                                                  False)
            encourageLimits = self.__best_of_three(encourageLimits,
                                                   self.encourage_limits_by_ID(qCtrl.id),
                                                   True)

            # We don't know if there are any changes, modify if needed, this
            # will take the lock, remove and append a record if needed
            self.__modify_camera_control(False, qCtrl, rtMin, rtMax, rtDefault,
                                         rtMinUse, rtMaxUse, negativeEffect,
                                         encourageLimits)

    # Reset the modifiable state for a control
    def __reset_camera_control(self, aCtrl):
        '''
        Reset the runtime values to the defaults, e.g. runtime values are set
        to the control values.

        Parameters
        ----------
            aCtrl: A tuple of the type used in the control list for this class

        Errors: Any failure finding a listed control with the same ID as the
        one in the quert control item in the aCtrl parameterwill cause a lookup
        failure generating a ValueError exception that will be allowed to pass
        to the caller.
        '''

        if aCtrl is not None:
            qCtrl = aCtrl[1]
            rtMin = qCtrl.minimum
            rtMax = qCtrl.maximum
            rtDefault = qCtrl.default

            # We don't know if there are any changes, modify if needed, this
            # will take the lock, remove and append a record if needed
            self.__modify_camera_control(False, qCtrl, rtMin, rtMax,
                                         rtDefault, False, False, False,
                                         True)

    def reset_camera_control_by_name(self, ctrlName):
        '''
        Public reset of runtime values of a camera control with a supplied name

        Parameters
        ----------
            ctrlName: string
                The name of the control to reset the runtime values of
        '''

        try:
            aCtrl = self.list_item_by_name(ctrlName)
        except NameError:
            aCtrl = None

        self.__reset_camera_control(aCtrl)

    def reset_camera_control_by_ID(self, ctrlID):
        '''
        Public reset of runtime values of a camera control with a supplied ID

        Parameters
        ----------
            ctrlID: integer
                The ID of the control to reset the runtime values of
        '''

        try:
            aCtrl = self.list_item_by_ID(ctrlID)
        except ValueError:
            aCtrl = None

        self.__reset_camera_control(aCtrl)

    def reset_camera_controls(self):
        '''
        Public reset of the runtime values of all camera controls
        '''
        # We only need to reset the modifiable properties
        curID = V4L2_CID_BASE
        while curID < V4L2_CID_LASTP1:
            try:
                aCtrl = self.list_item_by_ID(curID)
            except ValueError:
                aCtrl = None

            self.__reset_camera_control(aCtrl)

            curID += 1

    def __remove_camera_control_by_tuple_index_and_value(self, tIndex, tVal):
        '''
        Internal remove of a camera control from the list. Caller is required
        to have locked the object. Exists to permit locking once around multiple
        operations that require synchronization.

        Parameters
        ----------
            tIndex: integer
                Zero if using the first field in the listed tuple as the name to
                match with tVal
                One if using the ID in the query control as the ID to match
                with tVal
            tVal:
                The named control or a control ID to remove from the list

        Errors: Raises a NameError if the supplied control name is not found in
        the list
        '''

        i = 0
        for aCtrl in self.cameraControls:
            if tIndex == 0:
                found = (aCtrl[tIndex] == tVal)
            elif tIndex == 1:
                qCtrl = aCtrl[tIndex]
                found = (qCtrl.id == tVal)
            else:
                found = False

            if found:
                del self.cameraControls[i]
                return

            i += 1

        # Name not found
        raise NameError

    def __remove_camera_control_by_name(self, ctrlName):
        '''
        Private method to remove a camera control by name from the list

        Parameters
        ----------
            ctrlName: string
                The name of the control to remove from the list

        Errors: Allows any NameError from the private removal to pass to the
        caller
        '''

        self.__remove_camera_control_by_tuple_index_and_value(0, ctrlName)

    def remove_camera_control_by_name(self, ctrlName):
        '''
        Public method to remove a camera control by name from the list

        Parameters
        ----------
            ctrlName: string
                The name of the control to remove from the list
        '''

        self.ctrlsLock.acquire()
        try:
            self.__remove_camera_control_by_name(ctrlName)
        except NameError:
            # Don't need to re-raise it since it doesn't exist removal is
            # implicitly successful
            pass
        except:
            # Pass on anything other than NameError
            self.ctrlsLock.release()
            raise
        self.ctrlsLock.release()

    def __remove_camera_control_by_ID(self, ctrlID):
        '''
        Private method to remove a camera control by ID from the list

        Parameters
        ----------
            ctrlID: integer
                The ID of the control to remove from the list

        Errors: Allows any NameError from the private removal to pass to the
        caller
        '''

        self.__remove_camera_control_by_tuple_index_and_value(1, ctrlID)

    def remove_camera_control_by_ID(self, ctrlID):
        '''
        Public method to remove a camera control by ID from the list

        Parameters
        ----------
            ctrlID: integer
                The ID of the control to remove from the list
        '''

        self.ctrlsLock.acquire()
        try:
            self.__remove_camera_control_by_ID(ctrlID)
        except NameError:
            # Don't need to re-raise it since it doesn't exist removal is
            # implicitly successful
            pass
        except:
            self.ctrlsLock.release()
            raise
        self.ctrlsLock.release()

    def load_controls_from_FD(self, fd):
        '''
        Given a file-descriptor verify it's a camera and load it's control list

        Parameters
        ----------
            fd: file descriptor
                A file-descriptor for an open V4L2 camera type device
        '''

        index = 0
        while True:
            vInput = v4l2_input(index)
            try:
                # Find out the input tuple and only deal with cameras
                ioctl(fd, VIDIOC_ENUMINPUT, vInput)
                if vInput.type == V4L2_INPUT_TYPE_CAMERA:
                    break
            except OSError:
                msg = "Unable to access camera via "
                msg += "file descriptor {}".format(fd)
                qCDebug(self.logCategory, msg)
                # debug_message(msg)
                # Make it not a camera
                vInput.type = 0 - V4L2_INPUT_TYPE_CAMERA
            except (IndexError):
                # No camera found
                vInput.type = 0 - V4L2_INPUT_TYPE_CAMERA
            index += 1

        if vInput.type == V4L2_INPUT_TYPE_CAMERA:
            # Start with a fresh control list
            self.cameraControls.clear()

            # Walk all control IDs
            curID = V4L2_CID_BASE
            while curID < V4L2_CID_LASTP1:
                # Create a query control object for the ID
                queryctrl = v4l2_queryctrl(curID)
                try:
                    ioctl(fd, VIDIOC_QUERYCTRL, queryctrl)

                    # Ignore disabled controls
                    if queryctrl.flags & V4L2_CTRL_FLAG_DISABLED:
                        queryctrl = None
                except (OSError):
                    # Don't parse what error occurred, just assume we can't use
                    # the control ID
                    queryctrl = None

                if queryctrl is not None:
                    self.add_camera_control(queryctrl)

                # Next ID
                curID += 1

    def load_controls_from_camera(self, camFilename):
        '''
        Given a camera filename create a device object then load the controls
        from it via the device file-desriptor

        Parameter
        ---------
            camFilename: string
                The filename of a V$L2 camera type device
        '''

        try:
            capDev = Device(camFilename)
        except (OSError, ValueError):
            qCWarning(self.logCategory,
                      "Unable to open {} as a camera".format(camFilename))
            # debug_message("Unable to open {} as a camera".format(camFilename))
            return

        self.loadControlFromFD(capDev.fileno())
        capDev.close()

    # Save controls that have configurations that are not the same as those for
    # the camera. For example, we don't care that the control value can change
    # but we do care that the limits are not the limits for the device
    #         newCtrl = (ctrlName, qCtrl, rtMin, rtMax, rtDefault,
    #                    rtMinUse, rtMaxUse, negativeEffect,
    #                    encourageLimits)
    def saveConfiguredControlsB(self):
        mySet = QSettings()

        # We also have to have a nested group for the time-of-day if the
        # class has one
        if self.todPeriod in self.validTODs:
            if self.todPeriod != "":
                mySet.beginGroup(self.todPeriod)

                # There has to be a camera name for it to matter, we couldn't
                # have loadable configuration without knowing the device with
                # the control names it applies to
                if self.cameraName != "":
                    mySet.beginGroup(self.cameraName)

                # We can save

                # End of camera
                mySet.endGroup()

                # End of TOD
                mySet.endGroup()

    def dump_control_list(self, label):
        '''
        Debug function to dump the control list

        Parameters
        ----------
            label: string
                Some text to output at the top of the dumped control list
        '''

        qCDebug(self.logCategory, "DUMPING CONTROL LIST: {}".format(label))
        # debug_message("DUMPING CONTROL LIST: {}".format(label))
        curID = V4L2_CID_BASE
        while curID < V4L2_CID_LASTP1:
            try:
                aCtrl = self.list_item_by_ID(curID)
                for i in range(len(aCtrl)):
                    qCDebug(self.logCategory, "{} = {}".format(i, aCtrl[i]))
                    # debug_message("{} = {}".format(i, aCtrl[i]))
            except ValueError:
                aCtrl = None
            curID += 1


class v4l2CameraControlListIterator:
    '''
    Iterates the controls in a v4l2CameraControlList with the control ID of each
    control in the list as the item obtained from each step.  The iteration is
    also by v4l2 control ID, not by index of items in the  controlList member of
    the v4l2CameraControlList object because modifying an item removes it from
    the list and appends a modied memver. So walking the list by simple index in
    the list while modifies happen could permit items to be skipped because
    their index would drop by one for each modify overlapping iteration. Also,
    it could permit the same control to be returned more than once because
    it re-appears at the end of the list when a modify overlaps iteration.
    Therefore, iterate the range of valid v4l2 control IDs and return those
    present (skipping unsupported controls for this device).
    '''

    def __init__(self, ctrlList):
        '''
        Constructor for an instance of this class
        '''

        # v4l2CameraControlList object reference
        self._ctrlList = ctrlList
        # member variable to keep track of current index. BUT, use the v4l2
        # control ID list as the index, not the actual index in the
        # cameraControls member of the v4l2CameraControlList class
        self._index = V4L2_CID_BASE

    def __next__(self):
        '''
        Iterate to the next V4L2 control ID the contained in the list class and
        return the ID.

        Errors: Raises StopIteration exception if all V4L2 IDs have been
        iterated
        '''

        # The actual index of a given ID in the controlList member of the
        # v4l2CameraControlList can change so we need to find each item
        # from scratch and also skip not used IDs
        while self._index < V4L2_CID_LASTP1:
            try:
                aCtrl = self._ctrlList.list_item_by_ID(self._index)
            except ValueError:
                aCtrl = None
            self._index += 1
            if aCtrl is not None:
                return aCtrl[1].id

        raise StopIteration
