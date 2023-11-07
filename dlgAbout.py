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

from PySide6.QtCore import (Slot)
from PySide6.QtWidgets import QDialog, QDialogButtonBox

from dlgCSAbout import Ui_dlgAbout


class dlgAbout(QDialog):
    pbClose = None

    def __init__(self):
        super(dlgAbout, self).__init__()

        self.ui = Ui_dlgAbout()
        self.ui.setupUi(self)

        # Prepare for close
        self.pbClose = self.ui.buttonBox.button(QDialogButtonBox.Close)
        if self.pbClose.clicked is not None:
            self.pbClose.clicked.connect(self.aboutAccepted)

    @Slot()
    def aboutAccepted(self):
        self.accept()
