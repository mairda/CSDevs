# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'csdsettings.ui'
##
## Created by: Qt User Interface Compiler version 6.4.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QAbstractScrollArea, QAbstractSpinBox, QApplication,
    QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QFontComboBox, QFrame, QGraphicsView,
    QGroupBox, QHBoxLayout, QLabel, QLayout,
    QLineEdit, QListWidget, QListWidgetItem, QPushButton,
    QRadioButton, QSizePolicy, QSpacerItem, QSpinBox,
    QTabWidget, QTextBrowser, QVBoxLayout, QWidget)

class Ui_SettingsDlg(object):
    def setupUi(self, SettingsDlg):
        if not SettingsDlg.objectName():
            SettingsDlg.setObjectName(u"SettingsDlg")
        SettingsDlg.resize(450, 602)
        self.buttonBox = QDialogButtonBox(SettingsDlg)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(30, 560, 401, 32))
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.horizontalLayoutWidget = QWidget(SettingsDlg)
        self.horizontalLayoutWidget.setObjectName(u"horizontalLayoutWidget")
        self.horizontalLayoutWidget.setGeometry(QRect(2, 3, 447, 537))
        self.hblTabHolder = QHBoxLayout(self.horizontalLayoutWidget)
        self.hblTabHolder.setObjectName(u"hblTabHolder")
        self.hblTabHolder.setContentsMargins(0, 0, 0, 0)
        self.twSettingsTabs = QTabWidget(self.horizontalLayoutWidget)
        self.twSettingsTabs.setObjectName(u"twSettingsTabs")
        self.twSettingsTabs.setEnabled(True)
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.twSettingsTabs.sizePolicy().hasHeightForWidth())
        self.twSettingsTabs.setSizePolicy(sizePolicy)
        self.twSettingsTabs.setMinimumSize(QSize(430, 480))
        self.tabAutoExposure = QWidget()
        self.tabAutoExposure.setObjectName(u"tabAutoExposure")
        self.tabAutoExposure.setMinimumSize(QSize(0, 504))
        self.tabAutoExposure.setMaximumSize(QSize(16777215, 504))
        self.verticalLayoutWidget_4 = QWidget(self.tabAutoExposure)
        self.verticalLayoutWidget_4.setObjectName(u"verticalLayoutWidget_4")
        self.verticalLayoutWidget_4.setGeometry(QRect(0, 1, 435, 813))
        self.verticalLayout_6 = QVBoxLayout(self.verticalLayoutWidget_4)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.textBrowser_5 = QTextBrowser(self.verticalLayoutWidget_4)
        self.textBrowser_5.setObjectName(u"textBrowser_5")
        self.textBrowser_5.setEnabled(True)
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.textBrowser_5.sizePolicy().hasHeightForWidth())
        self.textBrowser_5.setSizePolicy(sizePolicy1)
        self.textBrowser_5.setMinimumSize(QSize(433, 0))
        self.textBrowser_5.setMaximumSize(QSize(16777215, 138))
        font = QFont()
        font.setPointSize(8)
        self.textBrowser_5.setFont(font)
        self.textBrowser_5.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)

        self.verticalLayout_6.addWidget(self.textBrowser_5)

        self.gbTOD = QGroupBox(self.verticalLayoutWidget_4)
        self.gbTOD.setObjectName(u"gbTOD")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.gbTOD.sizePolicy().hasHeightForWidth())
        self.gbTOD.setSizePolicy(sizePolicy2)
        self.gbTOD.setMinimumSize(QSize(433, 0))
        self.gbTOD.setMaximumSize(QSize(16777215, 56))
        self.rbDayCtrls = QRadioButton(self.gbTOD)
        self.rbDayCtrls.setObjectName(u"rbDayCtrls")
        self.rbDayCtrls.setGeometry(QRect(6, 26, 52, 24))
        self.rbDayCtrls.setChecked(True)
        self.rbNightCtrls = QRadioButton(self.gbTOD)
        self.rbNightCtrls.setObjectName(u"rbNightCtrls")
        self.rbNightCtrls.setGeometry(QRect(60, 26, 64, 24))
        self.cbDayOnly = QCheckBox(self.gbTOD)
        self.cbDayOnly.setObjectName(u"cbDayOnly")
        self.cbDayOnly.setGeometry(QRect(130, 26, 117, 24))
        self.cbNightOnly = QCheckBox(self.gbTOD)
        self.cbNightOnly.setObjectName(u"cbNightOnly")
        self.cbNightOnly.setGeometry(QRect(249, 26, 129, 24))

        self.verticalLayout_6.addWidget(self.gbTOD)

        self.gbExposureControls = QGroupBox(self.verticalLayoutWidget_4)
        self.gbExposureControls.setObjectName(u"gbExposureControls")
        sizePolicy2.setHeightForWidth(self.gbExposureControls.sizePolicy().hasHeightForWidth())
        self.gbExposureControls.setSizePolicy(sizePolicy2)
        self.gbExposureControls.setMinimumSize(QSize(433, 300))
        self.gbExposureControls.setMaximumSize(QSize(16777215, 1677215))
        self.label_21 = QLabel(self.gbExposureControls)
        self.label_21.setObjectName(u"label_21")
        self.label_21.setGeometry(QRect(6, 30, 106, 18))
        self.cbImageProperty = QComboBox(self.gbExposureControls)
        self.cbImageProperty.addItem("")
        self.cbImageProperty.addItem("")
        self.cbImageProperty.addItem("")
        self.cbImageProperty.setObjectName(u"cbImageProperty")
        self.cbImageProperty.setGeometry(QRect(114, 26, 101, 26))
        self.label_22 = QLabel(self.gbExposureControls)
        self.label_22.setObjectName(u"label_22")
        self.label_22.setGeometry(QRect(6, 58, 283, 18))
        self.lwTuneCtrls = QListWidget(self.gbExposureControls)
        self.lwTuneCtrls.setObjectName(u"lwTuneCtrls")
        self.lwTuneCtrls.setGeometry(QRect(6, 80, 284, 214))
        self.pbAddTuneCtrl = QPushButton(self.gbExposureControls)
        self.pbAddTuneCtrl.setObjectName(u"pbAddTuneCtrl")
        self.pbAddTuneCtrl.setGeometry(QRect(296, 81, 87, 26))
        icon = QIcon()
        iconThemeName = u"list-add"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.pbAddTuneCtrl.setIcon(icon)
        self.pbAddTuneCtrl.setAutoDefault(False)
        self.pbRemoveTuneCtrl = QPushButton(self.gbExposureControls)
        self.pbRemoveTuneCtrl.setObjectName(u"pbRemoveTuneCtrl")
        self.pbRemoveTuneCtrl.setEnabled(False)
        self.pbRemoveTuneCtrl.setGeometry(QRect(296, 108, 87, 26))
        icon1 = QIcon()
        iconThemeName = u"list-remove"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.pbRemoveTuneCtrl.setIcon(icon1)
        self.pbRemoveTuneCtrl.setAutoDefault(False)
        self.cbPropCtrlMin = QCheckBox(self.gbExposureControls)
        self.cbPropCtrlMin.setObjectName(u"cbPropCtrlMin")
        self.cbPropCtrlMin.setGeometry(QRect(296, 136, 130, 24))
        self.cbPropCtrlMax = QCheckBox(self.gbExposureControls)
        self.cbPropCtrlMax.setObjectName(u"cbPropCtrlMax")
        self.cbPropCtrlMax.setGeometry(QRect(296, 189, 120, 24))
        self.sbPropCtrlMinVal = QSpinBox(self.gbExposureControls)
        self.sbPropCtrlMinVal.setObjectName(u"sbPropCtrlMinVal")
        self.sbPropCtrlMinVal.setEnabled(False)
        self.sbPropCtrlMinVal.setGeometry(QRect(316, 161, 71, 27))
        self.sbPropCtrlMinVal.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.sbPropCtrlMinVal.setMaximum(88888)
        self.sbPropCtrlMinVal.setValue(0)
        self.sbPropCtrlMaxVal = QSpinBox(self.gbExposureControls)
        self.sbPropCtrlMaxVal.setObjectName(u"sbPropCtrlMaxVal")
        self.sbPropCtrlMaxVal.setEnabled(False)
        self.sbPropCtrlMaxVal.setGeometry(QRect(316, 214, 71, 27))
        self.sbPropCtrlMaxVal.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.sbPropCtrlMaxVal.setMaximum(88888)
        self.sbPropCtrlMaxVal.setValue(0)
        self.cbNegativeEffect = QCheckBox(self.gbExposureControls)
        self.cbNegativeEffect.setObjectName(u"cbNegativeEffect")
        self.cbNegativeEffect.setGeometry(QRect(296, 267, 129, 24))
        self.cbEncourageLimits = QCheckBox(self.gbExposureControls)
        self.cbEncourageLimits.setObjectName(u"cbEncourageLimits")
        self.cbEncourageLimits.setGeometry(QRect(296, 242, 113, 24))
        self.cbAvailableControls = QComboBox(self.gbExposureControls)
        self.cbAvailableControls.setObjectName(u"cbAvailableControls")
        self.cbAvailableControls.setGeometry(QRect(262, 26, 161, 26))

        self.verticalLayout_6.addWidget(self.gbExposureControls)

        self.twSettingsTabs.addTab(self.tabAutoExposure, "")
        self.tabTargets = QWidget()
        self.tabTargets.setObjectName(u"tabTargets")
        self.verticalLayoutWidget = QWidget(self.tabTargets)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(0, 0, 447, 815))
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.textBrowser_2 = QTextBrowser(self.verticalLayoutWidget)
        self.textBrowser_2.setObjectName(u"textBrowser_2")
        self.textBrowser_2.setEnabled(True)
        sizePolicy2.setHeightForWidth(self.textBrowser_2.sizePolicy().hasHeightForWidth())
        self.textBrowser_2.setSizePolicy(sizePolicy2)
        self.textBrowser_2.setMinimumSize(QSize(433, 0))
        self.textBrowser_2.setMaximumSize(QSize(16777215, 16777215))
        self.textBrowser_2.setFont(font)
        self.textBrowser_2.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)

        self.verticalLayout.addWidget(self.textBrowser_2)

        self.gbDayTargets = QGroupBox(self.verticalLayoutWidget)
        self.gbDayTargets.setObjectName(u"gbDayTargets")
        self.gbDayTargets.setMinimumSize(QSize(440, 140))
        self.gbDayTargets.setMaximumSize(QSize(0, 64))
        self.verticalLayoutWidget_6 = QWidget(self.gbDayTargets)
        self.verticalLayoutWidget_6.setObjectName(u"verticalLayoutWidget_6")
        self.verticalLayoutWidget_6.setGeometry(QRect(2, 24, 443, 114))
        self.verticalLayout_8 = QVBoxLayout(self.verticalLayoutWidget_6)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.verticalLayout_8.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.verticalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.label_23 = QLabel(self.verticalLayoutWidget_6)
        self.label_23.setObjectName(u"label_23")
        self.label_23.setMinimumSize(QSize(430, 0))
        self.label_23.setMaximumSize(QSize(16777215, 430))
        self.label_23.setBaseSize(QSize(0, 430))

        self.verticalLayout_8.addWidget(self.label_23)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer_8 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_8)

        self.label_6 = QLabel(self.verticalLayoutWidget_6)
        self.label_6.setObjectName(u"label_6")

        self.horizontalLayout_2.addWidget(self.label_6)

        self.sbDayTgtBrightness = QSpinBox(self.verticalLayoutWidget_6)
        self.sbDayTgtBrightness.setObjectName(u"sbDayTgtBrightness")
        self.sbDayTgtBrightness.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.sbDayTgtBrightness.setMaximum(255)
        self.sbDayTgtBrightness.setValue(255)

        self.horizontalLayout_2.addWidget(self.sbDayTgtBrightness)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.label_7 = QLabel(self.verticalLayoutWidget_6)
        self.label_7.setObjectName(u"label_7")

        self.horizontalLayout_2.addWidget(self.label_7)

        self.sbDayTgtContrast = QSpinBox(self.verticalLayoutWidget_6)
        self.sbDayTgtContrast.setObjectName(u"sbDayTgtContrast")
        self.sbDayTgtContrast.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.sbDayTgtContrast.setMaximum(255)
        self.sbDayTgtContrast.setValue(255)

        self.horizontalLayout_2.addWidget(self.sbDayTgtContrast)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.label_8 = QLabel(self.verticalLayoutWidget_6)
        self.label_8.setObjectName(u"label_8")

        self.horizontalLayout_2.addWidget(self.label_8)

        self.sbDayTgtSaturation = QSpinBox(self.verticalLayoutWidget_6)
        self.sbDayTgtSaturation.setObjectName(u"sbDayTgtSaturation")
        self.sbDayTgtSaturation.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.sbDayTgtSaturation.setMaximum(255)
        self.sbDayTgtSaturation.setValue(255)

        self.horizontalLayout_2.addWidget(self.sbDayTgtSaturation)

        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_7)


        self.verticalLayout_8.addLayout(self.horizontalLayout_2)

        self.label_24 = QLabel(self.verticalLayoutWidget_6)
        self.label_24.setObjectName(u"label_24")

        self.verticalLayout_8.addWidget(self.label_24)

        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.horizontalLayout_11.setContentsMargins(0, 0, 0, 0)
        self.horizontalSpacer_20 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_11.addItem(self.horizontalSpacer_20)

        self.label_25 = QLabel(self.verticalLayoutWidget_6)
        self.label_25.setObjectName(u"label_25")

        self.horizontalLayout_11.addWidget(self.label_25)

        self.sbDayTgtBrightnessMin = QSpinBox(self.verticalLayoutWidget_6)
        self.sbDayTgtBrightnessMin.setObjectName(u"sbDayTgtBrightnessMin")
        self.sbDayTgtBrightnessMin.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.sbDayTgtBrightnessMin.setMaximum(255)
        self.sbDayTgtBrightnessMin.setValue(0)

        self.horizontalLayout_11.addWidget(self.sbDayTgtBrightnessMin)

        self.horizontalSpacer_23 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_11.addItem(self.horizontalSpacer_23)

        self.label_26 = QLabel(self.verticalLayoutWidget_6)
        self.label_26.setObjectName(u"label_26")

        self.horizontalLayout_11.addWidget(self.label_26)

        self.sbDayTgtContrastMin = QSpinBox(self.verticalLayoutWidget_6)
        self.sbDayTgtContrastMin.setObjectName(u"sbDayTgtContrastMin")
        self.sbDayTgtContrastMin.setMaximum(255)
        self.sbDayTgtContrastMin.setValue(0)

        self.horizontalLayout_11.addWidget(self.sbDayTgtContrastMin)

        self.horizontalSpacer_22 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_11.addItem(self.horizontalSpacer_22)

        self.label_27 = QLabel(self.verticalLayoutWidget_6)
        self.label_27.setObjectName(u"label_27")

        self.horizontalLayout_11.addWidget(self.label_27)

        self.sbDayTgtSaturationMin = QSpinBox(self.verticalLayoutWidget_6)
        self.sbDayTgtSaturationMin.setObjectName(u"sbDayTgtSaturationMin")
        self.sbDayTgtSaturationMin.setMaximum(255)
        self.sbDayTgtSaturationMin.setValue(0)

        self.horizontalLayout_11.addWidget(self.sbDayTgtSaturationMin)

        self.horizontalSpacer_21 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_11.addItem(self.horizontalSpacer_21)


        self.verticalLayout_8.addLayout(self.horizontalLayout_11)


        self.verticalLayout.addWidget(self.gbDayTargets)

        self.gbNightTargets = QGroupBox(self.verticalLayoutWidget)
        self.gbNightTargets.setObjectName(u"gbNightTargets")
        self.gbNightTargets.setMinimumSize(QSize(433, 140))
        self.gbNightTargets.setMaximumSize(QSize(16777215, 0))
        self.gbNightTargets.setCheckable(True)
        self.gbNightTargets.setChecked(False)
        self.verticalLayoutWidget_7 = QWidget(self.gbNightTargets)
        self.verticalLayoutWidget_7.setObjectName(u"verticalLayoutWidget_7")
        self.verticalLayoutWidget_7.setGeometry(QRect(4, 24, 437, 114))
        self.verticalLayout_9 = QVBoxLayout(self.verticalLayoutWidget_7)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.label_28 = QLabel(self.verticalLayoutWidget_7)
        self.label_28.setObjectName(u"label_28")

        self.verticalLayout_9.addWidget(self.label_28)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_5)

        self.label_9 = QLabel(self.verticalLayoutWidget_7)
        self.label_9.setObjectName(u"label_9")

        self.horizontalLayout_3.addWidget(self.label_9)

        self.sbNightTgtBrightness = QSpinBox(self.verticalLayoutWidget_7)
        self.sbNightTgtBrightness.setObjectName(u"sbNightTgtBrightness")
        self.sbNightTgtBrightness.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.sbNightTgtBrightness.setMaximum(255)
        self.sbNightTgtBrightness.setValue(255)

        self.horizontalLayout_3.addWidget(self.sbNightTgtBrightness)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)

        self.label_10 = QLabel(self.verticalLayoutWidget_7)
        self.label_10.setObjectName(u"label_10")

        self.horizontalLayout_3.addWidget(self.label_10)

        self.sbNightTgtContrast = QSpinBox(self.verticalLayoutWidget_7)
        self.sbNightTgtContrast.setObjectName(u"sbNightTgtContrast")
        self.sbNightTgtContrast.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.sbNightTgtContrast.setMaximum(255)
        self.sbNightTgtContrast.setValue(255)

        self.horizontalLayout_3.addWidget(self.sbNightTgtContrast)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_4)

        self.label_11 = QLabel(self.verticalLayoutWidget_7)
        self.label_11.setObjectName(u"label_11")

        self.horizontalLayout_3.addWidget(self.label_11)

        self.sbNightTgtSaturation = QSpinBox(self.verticalLayoutWidget_7)
        self.sbNightTgtSaturation.setObjectName(u"sbNightTgtSaturation")
        self.sbNightTgtSaturation.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.sbNightTgtSaturation.setMaximum(255)
        self.sbNightTgtSaturation.setValue(255)

        self.horizontalLayout_3.addWidget(self.sbNightTgtSaturation)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_6)


        self.verticalLayout_9.addLayout(self.horizontalLayout_3)

        self.label_32 = QLabel(self.verticalLayoutWidget_7)
        self.label_32.setObjectName(u"label_32")

        self.verticalLayout_9.addWidget(self.label_32)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer_25 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_25)

        self.label_33 = QLabel(self.verticalLayoutWidget_7)
        self.label_33.setObjectName(u"label_33")

        self.horizontalLayout.addWidget(self.label_33)

        self.sbNightTgtBrightnessMin = QSpinBox(self.verticalLayoutWidget_7)
        self.sbNightTgtBrightnessMin.setObjectName(u"sbNightTgtBrightnessMin")
        self.sbNightTgtBrightnessMin.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.sbNightTgtBrightnessMin.setMaximum(255)
        self.sbNightTgtBrightnessMin.setValue(0)

        self.horizontalLayout.addWidget(self.sbNightTgtBrightnessMin)

        self.horizontalSpacer_26 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_26)

        self.label_34 = QLabel(self.verticalLayoutWidget_7)
        self.label_34.setObjectName(u"label_34")

        self.horizontalLayout.addWidget(self.label_34)

        self.sbNightTgtContrastMin = QSpinBox(self.verticalLayoutWidget_7)
        self.sbNightTgtContrastMin.setObjectName(u"sbNightTgtContrastMin")
        self.sbNightTgtContrastMin.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.sbNightTgtContrastMin.setMaximum(255)
        self.sbNightTgtContrastMin.setValue(0)

        self.horizontalLayout.addWidget(self.sbNightTgtContrastMin)

        self.horizontalSpacer_27 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_27)

        self.label_35 = QLabel(self.verticalLayoutWidget_7)
        self.label_35.setObjectName(u"label_35")

        self.horizontalLayout.addWidget(self.label_35)

        self.sbNightTgtSaturationMin = QSpinBox(self.verticalLayoutWidget_7)
        self.sbNightTgtSaturationMin.setObjectName(u"sbNightTgtSaturationMin")
        self.sbNightTgtSaturationMin.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.sbNightTgtSaturationMin.setMaximum(255)
        self.sbNightTgtSaturationMin.setValue(0)

        self.horizontalLayout.addWidget(self.sbNightTgtSaturationMin)

        self.horizontalSpacer_24 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_24)


        self.verticalLayout_9.addLayout(self.horizontalLayout)


        self.verticalLayout.addWidget(self.gbNightTargets)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.twSettingsTabs.addTab(self.tabTargets, "")
        self.tabLimits = QWidget()
        self.tabLimits.setObjectName(u"tabLimits")
        self.tabLimits.setEnabled(True)
        self.verticalLayoutWidget_5 = QWidget(self.tabLimits)
        self.verticalLayoutWidget_5.setObjectName(u"verticalLayoutWidget_5")
        self.verticalLayoutWidget_5.setGeometry(QRect(0, 1, 433, 503))
        self.verticalLayout_7 = QVBoxLayout(self.verticalLayoutWidget_5)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.textBrowser = QTextBrowser(self.verticalLayoutWidget_5)
        self.textBrowser.setObjectName(u"textBrowser")
        sizePolicy3 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.textBrowser.sizePolicy().hasHeightForWidth())
        self.textBrowser.setSizePolicy(sizePolicy3)
        self.textBrowser.setMaximumSize(QSize(16777215, 98))

        self.verticalLayout_7.addWidget(self.textBrowser)

        self.groupBox = QGroupBox(self.verticalLayoutWidget_5)
        self.groupBox.setObjectName(u"groupBox")
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setMaximumSize(QSize(16777215, 56))
        self.rbLimitsDay = QRadioButton(self.groupBox)
        self.rbLimitsDay.setObjectName(u"rbLimitsDay")
        self.rbLimitsDay.setGeometry(QRect(6, 26, 52, 24))
        self.rbLimitsDay.setChecked(True)
        self.rbLimitsNight = QRadioButton(self.groupBox)
        self.rbLimitsNight.setObjectName(u"rbLimitsNight")
        self.rbLimitsNight.setGeometry(QRect(60, 26, 64, 24))

        self.verticalLayout_7.addWidget(self.groupBox)

        self.groupBox_2 = QGroupBox(self.verticalLayoutWidget_5)
        self.groupBox_2.setObjectName(u"groupBox_2")
        sizePolicy.setHeightForWidth(self.groupBox_2.sizePolicy().hasHeightForWidth())
        self.groupBox_2.setSizePolicy(sizePolicy)
        self.label_30 = QLabel(self.groupBox_2)
        self.label_30.setObjectName(u"label_30")
        self.label_30.setGeometry(QRect(6, 30, 55, 18))
        self.cbAvailableLimitControls = QComboBox(self.groupBox_2)
        self.cbAvailableLimitControls.setObjectName(u"cbAvailableLimitControls")
        self.cbAvailableLimitControls.setGeometry(QRect(63, 26, 161, 26))
        self.label_31 = QLabel(self.groupBox_2)
        self.label_31.setObjectName(u"label_31")
        self.label_31.setGeometry(QRect(6, 58, 292, 18))
        self.lwLimitCtrls = QListWidget(self.groupBox_2)
        self.lwLimitCtrls.setObjectName(u"lwLimitCtrls")
        self.lwLimitCtrls.setGeometry(QRect(6, 80, 284, 214))
        self.pbAddLimitCtrl = QPushButton(self.groupBox_2)
        self.pbAddLimitCtrl.setObjectName(u"pbAddLimitCtrl")
        self.pbAddLimitCtrl.setGeometry(QRect(227, 26, 87, 26))
        self.pbAddLimitCtrl.setIcon(icon)
        self.pbAddLimitCtrl.setAutoDefault(False)
        self.pbRemoveLimitCtrl = QPushButton(self.groupBox_2)
        self.pbRemoveLimitCtrl.setObjectName(u"pbRemoveLimitCtrl")
        self.pbRemoveLimitCtrl.setEnabled(False)
        self.pbRemoveLimitCtrl.setGeometry(QRect(319, 26, 87, 26))
        self.pbRemoveLimitCtrl.setIcon(icon1)
        self.pbRemoveLimitCtrl.setAutoDefault(False)
        self.cbLimitCtrlMax = QCheckBox(self.groupBox_2)
        self.cbLimitCtrlMax.setObjectName(u"cbLimitCtrlMax")
        self.cbLimitCtrlMax.setGeometry(QRect(296, 134, 120, 24))
        self.cbLimitCtrlMin = QCheckBox(self.groupBox_2)
        self.cbLimitCtrlMin.setObjectName(u"cbLimitCtrlMin")
        self.cbLimitCtrlMin.setGeometry(QRect(296, 81, 130, 24))
        self.sbLimitCtrlMaxVal = QSpinBox(self.groupBox_2)
        self.sbLimitCtrlMaxVal.setObjectName(u"sbLimitCtrlMaxVal")
        self.sbLimitCtrlMaxVal.setEnabled(False)
        self.sbLimitCtrlMaxVal.setGeometry(QRect(316, 159, 71, 27))
        self.sbLimitCtrlMaxVal.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.sbLimitCtrlMaxVal.setMaximum(88888)
        self.sbLimitCtrlMaxVal.setValue(0)
        self.sbLimitCtrlMinVal = QSpinBox(self.groupBox_2)
        self.sbLimitCtrlMinVal.setObjectName(u"sbLimitCtrlMinVal")
        self.sbLimitCtrlMinVal.setEnabled(False)
        self.sbLimitCtrlMinVal.setGeometry(QRect(316, 106, 71, 27))
        self.sbLimitCtrlMinVal.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.sbLimitCtrlMinVal.setMaximum(88888)
        self.sbLimitCtrlMinVal.setValue(0)
        self.cbLimitEncourage = QCheckBox(self.groupBox_2)
        self.cbLimitEncourage.setObjectName(u"cbLimitEncourage")
        self.cbLimitEncourage.setGeometry(QRect(296, 187, 113, 24))
        self.cbLimitPreferred = QCheckBox(self.groupBox_2)
        self.cbLimitPreferred.setObjectName(u"cbLimitPreferred")
        self.cbLimitPreferred.setGeometry(QRect(296, 212, 129, 24))
        self.sbLimitCtrlPreferredVal = QSpinBox(self.groupBox_2)
        self.sbLimitCtrlPreferredVal.setObjectName(u"sbLimitCtrlPreferredVal")
        self.sbLimitCtrlPreferredVal.setEnabled(False)
        self.sbLimitCtrlPreferredVal.setGeometry(QRect(314, 237, 71, 27))
        self.sbLimitCtrlPreferredVal.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.verticalLayout_7.addWidget(self.groupBox_2)

        self.twSettingsTabs.addTab(self.tabLimits, "")
        self.tabImage = QWidget()
        self.tabImage.setObjectName(u"tabImage")
        self.tabImage.setEnabled(True)
        self.verticalLayoutWidget_2 = QWidget(self.tabImage)
        self.verticalLayoutWidget_2.setObjectName(u"verticalLayoutWidget_2")
        self.verticalLayoutWidget_2.setGeometry(QRect(0, 0, 433, 249))
        self.verticalLayout_2 = QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.textBrowser_3 = QTextBrowser(self.verticalLayoutWidget_2)
        self.textBrowser_3.setObjectName(u"textBrowser_3")
        sizePolicy2.setHeightForWidth(self.textBrowser_3.sizePolicy().hasHeightForWidth())
        self.textBrowser_3.setSizePolicy(sizePolicy2)
        self.textBrowser_3.setFont(font)
        self.textBrowser_3.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)

        self.verticalLayout_2.addWidget(self.textBrowser_3)

        self.label_16 = QLabel(self.verticalLayoutWidget_2)
        self.label_16.setObjectName(u"label_16")
        self.label_16.setMaximumSize(QSize(16777215, 24))
        font1 = QFont()
        font1.setBold(False)
        self.label_16.setFont(font1)

        self.verticalLayout_2.addWidget(self.label_16)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_12 = QLabel(self.verticalLayoutWidget_2)
        self.label_12.setObjectName(u"label_12")

        self.horizontalLayout_4.addWidget(self.label_12)

        self.leCaptionText = QLineEdit(self.verticalLayoutWidget_2)
        self.leCaptionText.setObjectName(u"leCaptionText")
        sizePolicy4 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.leCaptionText.sizePolicy().hasHeightForWidth())
        self.leCaptionText.setSizePolicy(sizePolicy4)

        self.horizontalLayout_4.addWidget(self.leCaptionText)

        self.horizontalSpacer_12 = QSpacerItem(10, 20, QSizePolicy.Preferred, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_12)


        self.verticalLayout_2.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label_13 = QLabel(self.verticalLayoutWidget_2)
        self.label_13.setObjectName(u"label_13")

        self.horizontalLayout_5.addWidget(self.label_13)

        self.cbDateStamp = QCheckBox(self.verticalLayoutWidget_2)
        self.cbDateStamp.setObjectName(u"cbDateStamp")

        self.horizontalLayout_5.addWidget(self.cbDateStamp)

        self.cbTimeStamp = QCheckBox(self.verticalLayoutWidget_2)
        self.cbTimeStamp.setObjectName(u"cbTimeStamp")

        self.horizontalLayout_5.addWidget(self.cbTimeStamp)

        self.cbTwoFourHour = QCheckBox(self.verticalLayoutWidget_2)
        self.cbTwoFourHour.setObjectName(u"cbTwoFourHour")

        self.horizontalLayout_5.addWidget(self.cbTwoFourHour)

        self.horizontalSpacer_11 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_11)


        self.verticalLayout_2.addLayout(self.horizontalLayout_5)

        self.frame = QFrame(self.verticalLayoutWidget_2)
        self.frame.setObjectName(u"frame")
        self.frame.setAutoFillBackground(False)
        self.frame.setFrameShape(QFrame.NoFrame)
        self.frame.setFrameShadow(QFrame.Raised)
        self.layoutWidget = QWidget(self.frame)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(0, 2, 431, 28))
        self.horizontalLayout_7 = QHBoxLayout(self.layoutWidget)
        self.horizontalLayout_7.setSpacing(2)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.label_15 = QLabel(self.layoutWidget)
        self.label_15.setObjectName(u"label_15")

        self.horizontalLayout_7.addWidget(self.label_15)

        self.rbCaptionHLeft = QRadioButton(self.layoutWidget)
        self.rbCaptionHLeft.setObjectName(u"rbCaptionHLeft")
        self.rbCaptionHLeft.setChecked(True)

        self.horizontalLayout_7.addWidget(self.rbCaptionHLeft)

        self.rbCaptionHCenter = QRadioButton(self.layoutWidget)
        self.rbCaptionHCenter.setObjectName(u"rbCaptionHCenter")

        self.horizontalLayout_7.addWidget(self.rbCaptionHCenter)

        self.rbCaptionHRight = QRadioButton(self.layoutWidget)
        self.rbCaptionHRight.setObjectName(u"rbCaptionHRight")

        self.horizontalLayout_7.addWidget(self.rbCaptionHRight)

        self.horizontalSpacer_9 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_9)


        self.verticalLayout_2.addWidget(self.frame)

        self.frame_2 = QFrame(self.verticalLayoutWidget_2)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setEnabled(True)
        self.frame_2.setFrameShape(QFrame.NoFrame)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.layoutWidget_2 = QWidget(self.frame_2)
        self.layoutWidget_2.setObjectName(u"layoutWidget_2")
        self.layoutWidget_2.setGeometry(QRect(0, 0, 431, 28))
        self.horizontalLayout_6 = QHBoxLayout(self.layoutWidget_2)
        self.horizontalLayout_6.setSpacing(2)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.label_14 = QLabel(self.layoutWidget_2)
        self.label_14.setObjectName(u"label_14")

        self.horizontalLayout_6.addWidget(self.label_14)

        self.rbCaptionVBottom = QRadioButton(self.layoutWidget_2)
        self.rbCaptionVBottom.setObjectName(u"rbCaptionVBottom")
        self.rbCaptionVBottom.setChecked(True)

        self.horizontalLayout_6.addWidget(self.rbCaptionVBottom)

        self.rbCaptionVCenter = QRadioButton(self.layoutWidget_2)
        self.rbCaptionVCenter.setObjectName(u"rbCaptionVCenter")

        self.horizontalLayout_6.addWidget(self.rbCaptionVCenter)

        self.rbCaptionVTop = QRadioButton(self.layoutWidget_2)
        self.rbCaptionVTop.setObjectName(u"rbCaptionVTop")

        self.horizontalLayout_6.addWidget(self.rbCaptionVTop)

        self.horizontalSpacer_10 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_10)


        self.verticalLayout_2.addWidget(self.frame_2)

        self.horizontalLayoutWidget_4 = QWidget(self.tabImage)
        self.horizontalLayoutWidget_4.setObjectName(u"horizontalLayoutWidget_4")
        self.horizontalLayoutWidget_4.setGeometry(QRect(0, 330, 433, 72))
        self.horizontalLayout_8 = QHBoxLayout(self.horizontalLayoutWidget_4)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.label_17 = QLabel(self.horizontalLayoutWidget_4)
        self.label_17.setObjectName(u"label_17")

        self.horizontalLayout_8.addWidget(self.label_17)

        self.label_18 = QLabel(self.horizontalLayoutWidget_4)
        self.label_18.setObjectName(u"label_18")
        self.label_18.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_8.addWidget(self.label_18)

        self.sbCaptionTextR = QSpinBox(self.horizontalLayoutWidget_4)
        self.sbCaptionTextR.setObjectName(u"sbCaptionTextR")
        self.sbCaptionTextR.setMaximum(255)

        self.horizontalLayout_8.addWidget(self.sbCaptionTextR)

        self.label_19 = QLabel(self.horizontalLayoutWidget_4)
        self.label_19.setObjectName(u"label_19")
        self.label_19.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_8.addWidget(self.label_19)

        self.sbCaptionTextG = QSpinBox(self.horizontalLayoutWidget_4)
        self.sbCaptionTextG.setObjectName(u"sbCaptionTextG")
        self.sbCaptionTextG.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.sbCaptionTextG.setMaximum(255)

        self.horizontalLayout_8.addWidget(self.sbCaptionTextG)

        self.label_20 = QLabel(self.horizontalLayoutWidget_4)
        self.label_20.setObjectName(u"label_20")
        self.label_20.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_8.addWidget(self.label_20)

        self.sbCaptionTextB = QSpinBox(self.horizontalLayoutWidget_4)
        self.sbCaptionTextB.setObjectName(u"sbCaptionTextB")
        self.sbCaptionTextB.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.sbCaptionTextB.setMaximum(255)

        self.horizontalLayout_8.addWidget(self.sbCaptionTextB)

        self.wColorView = QGraphicsView(self.horizontalLayoutWidget_4)
        self.wColorView.setObjectName(u"wColorView")
        self.wColorView.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout_8.addWidget(self.wColorView)

        self.horizontalSpacer_18 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_18)

        self.horizontalLayoutWidget_8 = QWidget(self.tabImage)
        self.horizontalLayoutWidget_8.setObjectName(u"horizontalLayoutWidget_8")
        self.horizontalLayoutWidget_8.setGeometry(QRect(0, 250, 431, 43))
        self.horizontalLayout_13 = QHBoxLayout(self.horizontalLayoutWidget_8)
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.horizontalLayout_13.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.horizontalLayout_13.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self.horizontalLayoutWidget_8)
        self.label.setObjectName(u"label")
        sizePolicy2.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy2)

        self.horizontalLayout_13.addWidget(self.label)

        self.cbCaptionFont = QFontComboBox(self.horizontalLayoutWidget_8)
        self.cbCaptionFont.setObjectName(u"cbCaptionFont")
        sizePolicy5 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.cbCaptionFont.sizePolicy().hasHeightForWidth())
        self.cbCaptionFont.setSizePolicy(sizePolicy5)
        self.cbCaptionFont.setMinimumSize(QSize(100, 0))
        self.cbCaptionFont.setMaximumSize(QSize(320, 16777215))
        self.cbCaptionFont.setFont(font1)
        self.cbCaptionFont.setFontFilters(QFontComboBox.MonospacedFonts|QFontComboBox.ProportionalFonts|QFontComboBox.ScalableFonts)

        self.horizontalLayout_13.addWidget(self.cbCaptionFont)

        self.label_5 = QLabel(self.horizontalLayoutWidget_8)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_13.addWidget(self.label_5)

        self.sbCaptionFontSize = QSpinBox(self.horizontalLayoutWidget_8)
        self.sbCaptionFontSize.setObjectName(u"sbCaptionFontSize")
        self.sbCaptionFontSize.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.sbCaptionFontSize.setMinimum(4)
        self.sbCaptionFontSize.setMaximum(100)
        self.sbCaptionFontSize.setValue(16)

        self.horizontalLayout_13.addWidget(self.sbCaptionFontSize)

        self.horizontalSpacer_17 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_13.addItem(self.horizontalSpacer_17)

        self.horizontalLayoutWidget_9 = QWidget(self.tabImage)
        self.horizontalLayoutWidget_9.setObjectName(u"horizontalLayoutWidget_9")
        self.horizontalLayoutWidget_9.setGeometry(QRect(0, 294, 433, 35))
        self.horizontalLayout_14 = QHBoxLayout(self.horizontalLayoutWidget_9)
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.horizontalLayout_14.setContentsMargins(0, 0, 0, 0)
        self.label_2 = QLabel(self.horizontalLayoutWidget_9)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_14.addWidget(self.label_2)

        self.label_3 = QLabel(self.horizontalLayoutWidget_9)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setLayoutDirection(Qt.LeftToRight)
        self.label_3.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_14.addWidget(self.label_3)

        self.sbCaptionInsetX = QSpinBox(self.horizontalLayoutWidget_9)
        self.sbCaptionInsetX.setObjectName(u"sbCaptionInsetX")
        self.sbCaptionInsetX.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.sbCaptionInsetX.setMaximum(100)
        self.sbCaptionInsetX.setValue(10)

        self.horizontalLayout_14.addWidget(self.sbCaptionInsetX)

        self.label_4 = QLabel(self.horizontalLayoutWidget_9)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_14.addWidget(self.label_4)

        self.sbCaptionInsetY = QSpinBox(self.horizontalLayoutWidget_9)
        self.sbCaptionInsetY.setObjectName(u"sbCaptionInsetY")
        self.sbCaptionInsetY.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.sbCaptionInsetY.setMaximum(100)
        self.sbCaptionInsetY.setValue(6)

        self.horizontalLayout_14.addWidget(self.sbCaptionInsetY)

        self.label_29 = QLabel(self.horizontalLayoutWidget_9)
        self.label_29.setObjectName(u"label_29")

        self.horizontalLayout_14.addWidget(self.label_29)

        self.horizontalSpacer_19 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_14.addItem(self.horizontalSpacer_19)

        self.twSettingsTabs.addTab(self.tabImage, "")
        self.tabLatLon = QWidget()
        self.tabLatLon.setObjectName(u"tabLatLon")
        self.verticalLayoutWidget_3 = QWidget(self.tabLatLon)
        self.verticalLayoutWidget_3.setObjectName(u"verticalLayoutWidget_3")
        self.verticalLayoutWidget_3.setGeometry(QRect(0, 0, 433, 347))
        self.verticalLayout_3 = QVBoxLayout(self.verticalLayoutWidget_3)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.textBrowser_4 = QTextBrowser(self.verticalLayoutWidget_3)
        self.textBrowser_4.setObjectName(u"textBrowser_4")
        self.textBrowser_4.setEnabled(True)
        sizePolicy6 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.textBrowser_4.sizePolicy().hasHeightForWidth())
        self.textBrowser_4.setSizePolicy(sizePolicy6)
        self.textBrowser_4.setMinimumSize(QSize(0, 0))
        self.textBrowser_4.setMaximumSize(QSize(16777215, 16777215))
        self.textBrowser_4.setFont(font)
        self.textBrowser_4.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)

        self.verticalLayout_3.addWidget(self.textBrowser_4)

        self.gbLatLonFormat = QGroupBox(self.verticalLayoutWidget_3)
        self.gbLatLonFormat.setObjectName(u"gbLatLonFormat")
        self.gbLatLonFormat.setMaximumSize(QSize(16777215, 67))
        self.rbDMS = QRadioButton(self.gbLatLonFormat)
        self.rbDMS.setObjectName(u"rbDMS")
        self.rbDMS.setGeometry(QRect(20, 37, 205, 24))
        self.rbDMS.setChecked(True)
        self.rbFloat = QRadioButton(self.gbLatLonFormat)
        self.rbFloat.setObjectName(u"rbFloat")
        self.rbFloat.setGeometry(QRect(231, 37, 120, 24))

        self.verticalLayout_3.addWidget(self.gbLatLonFormat)

        self.gbLatitude = QGroupBox(self.verticalLayoutWidget_3)
        self.gbLatitude.setObjectName(u"gbLatitude")
        self.gbLatitude.setMaximumSize(QSize(16777215, 88))
        self.layoutWidget_3 = QWidget(self.gbLatitude)
        self.layoutWidget_3.setObjectName(u"layoutWidget_3")
        self.layoutWidget_3.setGeometry(QRect(0, 22, 433, 65))
        self.horizontalLayout_9 = QHBoxLayout(self.layoutWidget_3)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalLayout_9.setContentsMargins(3, 0, 0, 0)
        self.sbLatDegrees = QSpinBox(self.layoutWidget_3)
        self.sbLatDegrees.setObjectName(u"sbLatDegrees")
        self.sbLatDegrees.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.sbLatDegrees.setMinimum(0)
        self.sbLatDegrees.setMaximum(90)
        self.sbLatDegrees.setSingleStep(1)
        self.sbLatDegrees.setValue(0)

        self.horizontalLayout_9.addWidget(self.sbLatDegrees)

        self.lblLatDegrees = QLabel(self.layoutWidget_3)
        self.lblLatDegrees.setObjectName(u"lblLatDegrees")

        self.horizontalLayout_9.addWidget(self.lblLatDegrees)

        self.sbLatMinutes = QSpinBox(self.layoutWidget_3)
        self.sbLatMinutes.setObjectName(u"sbLatMinutes")
        self.sbLatMinutes.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.sbLatMinutes.setMaximum(59)
        self.sbLatMinutes.setValue(0)

        self.horizontalLayout_9.addWidget(self.sbLatMinutes)

        self.lblLatMinutes = QLabel(self.layoutWidget_3)
        self.lblLatMinutes.setObjectName(u"lblLatMinutes")

        self.horizontalLayout_9.addWidget(self.lblLatMinutes)

        self.sbLatSeconds = QSpinBox(self.layoutWidget_3)
        self.sbLatSeconds.setObjectName(u"sbLatSeconds")
        self.sbLatSeconds.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.sbLatSeconds.setMaximum(59)

        self.horizontalLayout_9.addWidget(self.sbLatSeconds)

        self.lblLatSeconds = QLabel(self.layoutWidget_3)
        self.lblLatSeconds.setObjectName(u"lblLatSeconds")

        self.horizontalLayout_9.addWidget(self.lblLatSeconds)

        self.horizontalSpacer_13 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_13)

        self.dsbLatFloat = QDoubleSpinBox(self.layoutWidget_3)
        self.dsbLatFloat.setObjectName(u"dsbLatFloat")
        self.dsbLatFloat.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.dsbLatFloat.setDecimals(8)
        self.dsbLatFloat.setMinimum(0.000000000000000)
        self.dsbLatFloat.setMaximum(90.000000000000000)
        self.dsbLatFloat.setSingleStep(0.000278000000000)
        self.dsbLatFloat.setStepType(QAbstractSpinBox.DefaultStepType)
        self.dsbLatFloat.setValue(0.000000000000000)

        self.horizontalLayout_9.addWidget(self.dsbLatFloat)

        self.lblLatFloat = QLabel(self.layoutWidget_3)
        self.lblLatFloat.setObjectName(u"lblLatFloat")

        self.horizontalLayout_9.addWidget(self.lblLatFloat)

        self.horizontalSpacer_14 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_14)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.rbLatNorth = QRadioButton(self.layoutWidget_3)
        self.rbLatNorth.setObjectName(u"rbLatNorth")
        self.rbLatNorth.setChecked(True)

        self.verticalLayout_4.addWidget(self.rbLatNorth)

        self.rbLatSouth = QRadioButton(self.layoutWidget_3)
        self.rbLatSouth.setObjectName(u"rbLatSouth")

        self.verticalLayout_4.addWidget(self.rbLatSouth)


        self.horizontalLayout_9.addLayout(self.verticalLayout_4)


        self.verticalLayout_3.addWidget(self.gbLatitude)

        self.bLongitude = QGroupBox(self.verticalLayoutWidget_3)
        self.bLongitude.setObjectName(u"bLongitude")
        self.bLongitude.setMaximumSize(QSize(16777215, 88))
        self.horizontalLayoutWidget_5 = QWidget(self.bLongitude)
        self.horizontalLayoutWidget_5.setObjectName(u"horizontalLayoutWidget_5")
        self.horizontalLayoutWidget_5.setGeometry(QRect(0, 22, 441, 65))
        self.horizontalLayout_10 = QHBoxLayout(self.horizontalLayoutWidget_5)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_10.setContentsMargins(2, 0, 4, 0)
        self.sbLonDegrees = QSpinBox(self.horizontalLayoutWidget_5)
        self.sbLonDegrees.setObjectName(u"sbLonDegrees")
        self.sbLonDegrees.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.sbLonDegrees.setMinimum(0)
        self.sbLonDegrees.setMaximum(180)
        self.sbLonDegrees.setSingleStep(1)
        self.sbLonDegrees.setValue(0)

        self.horizontalLayout_10.addWidget(self.sbLonDegrees)

        self.lblLonDegrees = QLabel(self.horizontalLayoutWidget_5)
        self.lblLonDegrees.setObjectName(u"lblLonDegrees")

        self.horizontalLayout_10.addWidget(self.lblLonDegrees)

        self.sbLonMinutes = QSpinBox(self.horizontalLayoutWidget_5)
        self.sbLonMinutes.setObjectName(u"sbLonMinutes")
        self.sbLonMinutes.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.sbLonMinutes.setMaximum(59)
        self.sbLonMinutes.setValue(0)

        self.horizontalLayout_10.addWidget(self.sbLonMinutes)

        self.lblLonMinutes = QLabel(self.horizontalLayoutWidget_5)
        self.lblLonMinutes.setObjectName(u"lblLonMinutes")

        self.horizontalLayout_10.addWidget(self.lblLonMinutes)

        self.sbLonSeconds = QSpinBox(self.horizontalLayoutWidget_5)
        self.sbLonSeconds.setObjectName(u"sbLonSeconds")
        self.sbLonSeconds.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.sbLonSeconds.setMaximum(59)

        self.horizontalLayout_10.addWidget(self.sbLonSeconds)

        self.lblLonSeconds = QLabel(self.horizontalLayoutWidget_5)
        self.lblLonSeconds.setObjectName(u"lblLonSeconds")

        self.horizontalLayout_10.addWidget(self.lblLonSeconds)

        self.horizontalSpacer_15 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_10.addItem(self.horizontalSpacer_15)

        self.dsbLonFloat = QDoubleSpinBox(self.horizontalLayoutWidget_5)
        self.dsbLonFloat.setObjectName(u"dsbLonFloat")
        self.dsbLonFloat.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.dsbLonFloat.setDecimals(8)
        self.dsbLonFloat.setMinimum(0.000000000000000)
        self.dsbLonFloat.setMaximum(180.000000000000000)
        self.dsbLonFloat.setSingleStep(0.000278000000000)
        self.dsbLonFloat.setStepType(QAbstractSpinBox.DefaultStepType)
        self.dsbLonFloat.setValue(0.000000000000000)

        self.horizontalLayout_10.addWidget(self.dsbLonFloat)

        self.lblLonFloat = QLabel(self.horizontalLayoutWidget_5)
        self.lblLonFloat.setObjectName(u"lblLonFloat")

        self.horizontalLayout_10.addWidget(self.lblLonFloat)

        self.horizontalSpacer_16 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_10.addItem(self.horizontalSpacer_16)

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.rbLonEast = QRadioButton(self.horizontalLayoutWidget_5)
        self.rbLonEast.setObjectName(u"rbLonEast")
        self.rbLonEast.setChecked(True)

        self.verticalLayout_5.addWidget(self.rbLonEast)

        self.rbLonWest = QRadioButton(self.horizontalLayoutWidget_5)
        self.rbLonWest.setObjectName(u"rbLonWest")
        sizePolicy7 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy7.setHorizontalStretch(0)
        sizePolicy7.setVerticalStretch(0)
        sizePolicy7.setHeightForWidth(self.rbLonWest.sizePolicy().hasHeightForWidth())
        self.rbLonWest.setSizePolicy(sizePolicy7)

        self.verticalLayout_5.addWidget(self.rbLonWest)


        self.horizontalLayout_10.addLayout(self.verticalLayout_5)


        self.verticalLayout_3.addWidget(self.bLongitude)

        self.twSettingsTabs.addTab(self.tabLatLon, "")

        self.hblTabHolder.addWidget(self.twSettingsTabs)

        QWidget.setTabOrder(self.twSettingsTabs, self.textBrowser_5)
        QWidget.setTabOrder(self.textBrowser_5, self.rbDayCtrls)
        QWidget.setTabOrder(self.rbDayCtrls, self.rbNightCtrls)
        QWidget.setTabOrder(self.rbNightCtrls, self.cbDayOnly)
        QWidget.setTabOrder(self.cbDayOnly, self.cbNightOnly)
        QWidget.setTabOrder(self.cbNightOnly, self.cbImageProperty)
        QWidget.setTabOrder(self.cbImageProperty, self.cbAvailableControls)
        QWidget.setTabOrder(self.cbAvailableControls, self.pbAddTuneCtrl)
        QWidget.setTabOrder(self.pbAddTuneCtrl, self.pbRemoveTuneCtrl)
        QWidget.setTabOrder(self.pbRemoveTuneCtrl, self.lwTuneCtrls)
        QWidget.setTabOrder(self.lwTuneCtrls, self.cbPropCtrlMin)
        QWidget.setTabOrder(self.cbPropCtrlMin, self.sbPropCtrlMinVal)
        QWidget.setTabOrder(self.sbPropCtrlMinVal, self.cbPropCtrlMax)
        QWidget.setTabOrder(self.cbPropCtrlMax, self.sbPropCtrlMaxVal)
        QWidget.setTabOrder(self.sbPropCtrlMaxVal, self.cbEncourageLimits)
        QWidget.setTabOrder(self.cbEncourageLimits, self.cbNegativeEffect)
        QWidget.setTabOrder(self.cbNegativeEffect, self.textBrowser_2)
        QWidget.setTabOrder(self.textBrowser_2, self.sbDayTgtBrightness)
        QWidget.setTabOrder(self.sbDayTgtBrightness, self.sbDayTgtContrast)
        QWidget.setTabOrder(self.sbDayTgtContrast, self.sbDayTgtSaturation)
        QWidget.setTabOrder(self.sbDayTgtSaturation, self.sbDayTgtBrightnessMin)
        QWidget.setTabOrder(self.sbDayTgtBrightnessMin, self.sbDayTgtContrastMin)
        QWidget.setTabOrder(self.sbDayTgtContrastMin, self.sbDayTgtSaturationMin)
        QWidget.setTabOrder(self.sbDayTgtSaturationMin, self.gbNightTargets)
        QWidget.setTabOrder(self.gbNightTargets, self.sbNightTgtBrightness)
        QWidget.setTabOrder(self.sbNightTgtBrightness, self.sbNightTgtContrast)
        QWidget.setTabOrder(self.sbNightTgtContrast, self.sbNightTgtSaturation)
        QWidget.setTabOrder(self.sbNightTgtSaturation, self.sbNightTgtBrightnessMin)
        QWidget.setTabOrder(self.sbNightTgtBrightnessMin, self.sbNightTgtContrastMin)
        QWidget.setTabOrder(self.sbNightTgtContrastMin, self.sbNightTgtSaturationMin)
        QWidget.setTabOrder(self.sbNightTgtSaturationMin, self.textBrowser)
        QWidget.setTabOrder(self.textBrowser, self.rbLimitsDay)
        QWidget.setTabOrder(self.rbLimitsDay, self.rbLimitsNight)
        QWidget.setTabOrder(self.rbLimitsNight, self.cbAvailableLimitControls)
        QWidget.setTabOrder(self.cbAvailableLimitControls, self.pbAddLimitCtrl)
        QWidget.setTabOrder(self.pbAddLimitCtrl, self.pbRemoveLimitCtrl)
        QWidget.setTabOrder(self.pbRemoveLimitCtrl, self.lwLimitCtrls)
        QWidget.setTabOrder(self.lwLimitCtrls, self.cbLimitCtrlMin)
        QWidget.setTabOrder(self.cbLimitCtrlMin, self.sbLimitCtrlMinVal)
        QWidget.setTabOrder(self.sbLimitCtrlMinVal, self.cbLimitCtrlMax)
        QWidget.setTabOrder(self.cbLimitCtrlMax, self.sbLimitCtrlMaxVal)
        QWidget.setTabOrder(self.sbLimitCtrlMaxVal, self.cbLimitEncourage)
        QWidget.setTabOrder(self.cbLimitEncourage, self.cbLimitPreferred)
        QWidget.setTabOrder(self.cbLimitPreferred, self.sbLimitCtrlPreferredVal)
        QWidget.setTabOrder(self.sbLimitCtrlPreferredVal, self.textBrowser_3)
        QWidget.setTabOrder(self.textBrowser_3, self.leCaptionText)
        QWidget.setTabOrder(self.leCaptionText, self.cbDateStamp)
        QWidget.setTabOrder(self.cbDateStamp, self.cbTimeStamp)
        QWidget.setTabOrder(self.cbTimeStamp, self.cbTwoFourHour)
        QWidget.setTabOrder(self.cbTwoFourHour, self.rbCaptionHLeft)
        QWidget.setTabOrder(self.rbCaptionHLeft, self.rbCaptionHCenter)
        QWidget.setTabOrder(self.rbCaptionHCenter, self.rbCaptionHRight)
        QWidget.setTabOrder(self.rbCaptionHRight, self.rbCaptionVBottom)
        QWidget.setTabOrder(self.rbCaptionVBottom, self.rbCaptionVCenter)
        QWidget.setTabOrder(self.rbCaptionVCenter, self.rbCaptionVTop)
        QWidget.setTabOrder(self.rbCaptionVTop, self.cbCaptionFont)
        QWidget.setTabOrder(self.cbCaptionFont, self.sbCaptionFontSize)
        QWidget.setTabOrder(self.sbCaptionFontSize, self.sbCaptionInsetX)
        QWidget.setTabOrder(self.sbCaptionInsetX, self.sbCaptionInsetY)
        QWidget.setTabOrder(self.sbCaptionInsetY, self.sbCaptionTextR)
        QWidget.setTabOrder(self.sbCaptionTextR, self.sbCaptionTextG)
        QWidget.setTabOrder(self.sbCaptionTextG, self.sbCaptionTextB)
        QWidget.setTabOrder(self.sbCaptionTextB, self.wColorView)
        QWidget.setTabOrder(self.wColorView, self.textBrowser_4)
        QWidget.setTabOrder(self.textBrowser_4, self.rbDMS)
        QWidget.setTabOrder(self.rbDMS, self.rbFloat)
        QWidget.setTabOrder(self.rbFloat, self.sbLatDegrees)
        QWidget.setTabOrder(self.sbLatDegrees, self.sbLatMinutes)
        QWidget.setTabOrder(self.sbLatMinutes, self.sbLatSeconds)
        QWidget.setTabOrder(self.sbLatSeconds, self.dsbLatFloat)
        QWidget.setTabOrder(self.dsbLatFloat, self.rbLatNorth)
        QWidget.setTabOrder(self.rbLatNorth, self.rbLatSouth)
        QWidget.setTabOrder(self.rbLatSouth, self.sbLonDegrees)
        QWidget.setTabOrder(self.sbLonDegrees, self.sbLonMinutes)
        QWidget.setTabOrder(self.sbLonMinutes, self.sbLonSeconds)
        QWidget.setTabOrder(self.sbLonSeconds, self.dsbLonFloat)
        QWidget.setTabOrder(self.dsbLonFloat, self.rbLonEast)
        QWidget.setTabOrder(self.rbLonEast, self.rbLonWest)

        self.retranslateUi(SettingsDlg)
        self.buttonBox.accepted.connect(SettingsDlg.accept)
        self.buttonBox.rejected.connect(SettingsDlg.reject)

        self.twSettingsTabs.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(SettingsDlg)
    # setupUi

    def retranslateUi(self, SettingsDlg):
        SettingsDlg.setWindowTitle(QCoreApplication.translate("SettingsDlg", u"CSDev Settings", None))
        self.textBrowser_5.setHtml(QCoreApplication.translate("SettingsDlg", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Cantarell'; font-size:8pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Set the controls that will be used to perform automatic exposure adjustment. List camera controls that affect the image properties Brightness, Contrast and Saturation. A given camera control can be used to adjust more than one image property, e.g. if a camera Gamma control affects Brightness and Contrast. If needed, set range limits for each camera control within each image property it is used in, e."
                        "g. if the whole range of a camera contrast control affects image Contrast set no Contrast/contrast range but half of the camera contrast control range also affects image Brightness set that range for Brightness/contrast. If increasing a control value decreases an image property it's listed in then use the &quot;Negative effect&quot; checkbox for that property/control. Enable daytime or nighttime only automatic exposure controls with the check-boxes and see the controls for daytime or nighttime automatic exposure using the radio buttons.</p></body></html>", None))
        self.gbTOD.setTitle(QCoreApplication.translate("SettingsDlg", u"Time Of Day", None))
#if QT_CONFIG(tooltip)
        self.rbDayCtrls.setToolTip(QCoreApplication.translate("SettingsDlg", u"View camera daytime control settings for current image property", None))
#endif // QT_CONFIG(tooltip)
        self.rbDayCtrls.setText(QCoreApplication.translate("SettingsDlg", u"Day", None))
#if QT_CONFIG(tooltip)
        self.rbNightCtrls.setToolTip(QCoreApplication.translate("SettingsDlg", u"View camera nighttime control settings for current image property", None))
#endif // QT_CONFIG(tooltip)
        self.rbNightCtrls.setText(QCoreApplication.translate("SettingsDlg", u"Night", None))
#if QT_CONFIG(tooltip)
        self.cbDayOnly.setToolTip(QCoreApplication.translate("SettingsDlg", u"Check to only provide daytime controls to adjust image properties", None))
#endif // QT_CONFIG(tooltip)
        self.cbDayOnly.setText(QCoreApplication.translate("SettingsDlg", u"Daytime Only", None))
#if QT_CONFIG(tooltip)
        self.cbNightOnly.setToolTip(QCoreApplication.translate("SettingsDlg", u"Check to only provide nighttime controls to adjust image properties", None))
#endif // QT_CONFIG(tooltip)
        self.cbNightOnly.setText(QCoreApplication.translate("SettingsDlg", u"NIghttime Only", None))
        self.gbExposureControls.setTitle(QCoreApplication.translate("SettingsDlg", u"Exposure Controls", None))
        self.label_21.setText(QCoreApplication.translate("SettingsDlg", u"Image property:", None))
        self.cbImageProperty.setItemText(0, QCoreApplication.translate("SettingsDlg", u"Brightness", None))
        self.cbImageProperty.setItemText(1, QCoreApplication.translate("SettingsDlg", u"Contrast", None))
        self.cbImageProperty.setItemText(2, QCoreApplication.translate("SettingsDlg", u"Saturation", None))

#if QT_CONFIG(tooltip)
        self.cbImageProperty.setToolTip(QCoreApplication.translate("SettingsDlg", u"Current image property to set usable camera controls for", None))
#endif // QT_CONFIG(tooltip)
        self.label_22.setText(QCoreApplication.translate("SettingsDlg", u"Automatically Use These Camera Controls:", None))
#if QT_CONFIG(tooltip)
        self.lwTuneCtrls.setToolTip(QCoreApplication.translate("SettingsDlg", u"Camera controls that affect the current image property", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.pbAddTuneCtrl.setToolTip(QCoreApplication.translate("SettingsDlg", u"Add a control for tuning the current image property", None))
#endif // QT_CONFIG(tooltip)
        self.pbAddTuneCtrl.setText(QCoreApplication.translate("SettingsDlg", u"Add", None))
#if QT_CONFIG(tooltip)
        self.pbRemoveTuneCtrl.setToolTip(QCoreApplication.translate("SettingsDlg", u"Remove the selected control for tuning the current image property", None))
#endif // QT_CONFIG(tooltip)
        self.pbRemoveTuneCtrl.setText(QCoreApplication.translate("SettingsDlg", u"Remove", None))
#if QT_CONFIG(tooltip)
        self.cbPropCtrlMin.setToolTip(QCoreApplication.translate("SettingsDlg", u"Check to allow setting a minimum control value to use for image exposure", None))
#endif // QT_CONFIG(tooltip)
        self.cbPropCtrlMin.setText(QCoreApplication.translate("SettingsDlg", u"Use Minimum", None))
#if QT_CONFIG(tooltip)
        self.cbPropCtrlMax.setToolTip(QCoreApplication.translate("SettingsDlg", u"Check to allow setting a maximum control value to use for image exposure", None))
#endif // QT_CONFIG(tooltip)
        self.cbPropCtrlMax.setText(QCoreApplication.translate("SettingsDlg", u"Use Maximum", None))
#if QT_CONFIG(tooltip)
        self.sbPropCtrlMinVal.setToolTip(QCoreApplication.translate("SettingsDlg", u"Minimum value to allow control when adjusting the current image property (check \"Use Minimum\" to enable)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.sbPropCtrlMaxVal.setToolTip(QCoreApplication.translate("SettingsDlg", u"Maximum value to allow control when adjusting the current image property (check \"Use Maximum\" to enable)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.cbNegativeEffect.setToolTip(QCoreApplication.translate("SettingsDlg", u"Check to changing camera control value in one direction has opposite value effect on current image property", None))
#endif // QT_CONFIG(tooltip)
        self.cbNegativeEffect.setText(QCoreApplication.translate("SettingsDlg", u"Negative Effect", None))
#if QT_CONFIG(tooltip)
        self.cbEncourageLimits.setToolTip(QCoreApplication.translate("SettingsDlg", u"If control value exceeds specified range due to another property's control, allow this property's control to adjust towards nearest limit but not away from it", None))
#endif // QT_CONFIG(tooltip)
        self.cbEncourageLimits.setText(QCoreApplication.translate("SettingsDlg", u"Target Limits", None))
        self.twSettingsTabs.setTabText(self.twSettingsTabs.indexOf(self.tabAutoExposure), QCoreApplication.translate("SettingsDlg", u"Auto-exposure", None))
        self.textBrowser_2.setHtml(QCoreApplication.translate("SettingsDlg", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Cantarell'; font-size:8pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Set the target brightness, contrast and saturation you hope captured images to have. You can set different values for daytime and nighttime. Note that these are only the &quot;goal&quot; to aim for. Whether or not they can be achieved for any frame depends on a lot of factors. Value for each is in the range 0 (minimum) to 255 (maximum).</p></body></html>", None))
        self.gbDayTargets.setTitle(QCoreApplication.translate("SettingsDlg", u"Day:", None))
        self.label_23.setText(QCoreApplication.translate("SettingsDlg", u"Maximum:", None))
        self.label_6.setText(QCoreApplication.translate("SettingsDlg", u"Brightness:", None))
        self.label_7.setText(QCoreApplication.translate("SettingsDlg", u"Contrast:", None))
        self.label_8.setText(QCoreApplication.translate("SettingsDlg", u"Saturation:", None))
        self.label_24.setText(QCoreApplication.translate("SettingsDlg", u"Minimum:", None))
        self.label_25.setText(QCoreApplication.translate("SettingsDlg", u"Brightness:", None))
        self.label_26.setText(QCoreApplication.translate("SettingsDlg", u"Contrast:", None))
        self.label_27.setText(QCoreApplication.translate("SettingsDlg", u"Saturation:", None))
        self.gbNightTargets.setTitle(QCoreApplication.translate("SettingsDlg", u"Night:", None))
        self.label_28.setText(QCoreApplication.translate("SettingsDlg", u"Maximum:", None))
        self.label_9.setText(QCoreApplication.translate("SettingsDlg", u"Brightness:", None))
        self.label_10.setText(QCoreApplication.translate("SettingsDlg", u"Contrast:", None))
        self.label_11.setText(QCoreApplication.translate("SettingsDlg", u"Saturation:", None))
        self.label_32.setText(QCoreApplication.translate("SettingsDlg", u"Minimum:", None))
        self.label_33.setText(QCoreApplication.translate("SettingsDlg", u"Brightness:", None))
        self.label_34.setText(QCoreApplication.translate("SettingsDlg", u"Contrast:", None))
        self.label_35.setText(QCoreApplication.translate("SettingsDlg", u"Saturation:", None))
        self.twSettingsTabs.setTabText(self.twSettingsTabs.indexOf(self.tabTargets), QCoreApplication.translate("SettingsDlg", u"Targets", None))
        self.textBrowser.setHtml(QCoreApplication.translate("SettingsDlg", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Cantarell'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Use this to set range limits and preferred target value for controls. This allows for things like setting a limited focus range and a preferred focus value, for a camera that supports focus. Equally, you can set different range limits for daytime and nightime focus. Take care if using this to set control range limits for controls you have also set as Auto-exposure con"
                        "trols. It can make sense to have limits for, say, gamma or saturation controls to avoid severity effects problems but it may cause auto-exposure failures.</span></p></body></html>", None))
        self.groupBox.setTitle(QCoreApplication.translate("SettingsDlg", u"Time Of Day", None))
        self.rbLimitsDay.setText(QCoreApplication.translate("SettingsDlg", u"Day", None))
        self.rbLimitsNight.setText(QCoreApplication.translate("SettingsDlg", u"Night", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("SettingsDlg", u"Control Limits", None))
        self.label_30.setText(QCoreApplication.translate("SettingsDlg", u"Control:", None))
        self.label_31.setText(QCoreApplication.translate("SettingsDlg", u"Automatically Limit These Camera Controls:", None))
#if QT_CONFIG(tooltip)
        self.lwLimitCtrls.setToolTip(QCoreApplication.translate("SettingsDlg", u"Camera controls that affect the current image property", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.pbAddLimitCtrl.setToolTip(QCoreApplication.translate("SettingsDlg", u"Add a control for tuning the current image property", None))
#endif // QT_CONFIG(tooltip)
        self.pbAddLimitCtrl.setText(QCoreApplication.translate("SettingsDlg", u"Add", None))
#if QT_CONFIG(tooltip)
        self.pbRemoveLimitCtrl.setToolTip(QCoreApplication.translate("SettingsDlg", u"Remove the selected control for tuning the current image property", None))
#endif // QT_CONFIG(tooltip)
        self.pbRemoveLimitCtrl.setText(QCoreApplication.translate("SettingsDlg", u"Remove", None))
#if QT_CONFIG(tooltip)
        self.cbLimitCtrlMax.setToolTip(QCoreApplication.translate("SettingsDlg", u"Check to allow setting a maximum control value to use for image exposure", None))
#endif // QT_CONFIG(tooltip)
        self.cbLimitCtrlMax.setText(QCoreApplication.translate("SettingsDlg", u"Use Maximum", None))
#if QT_CONFIG(tooltip)
        self.cbLimitCtrlMin.setToolTip(QCoreApplication.translate("SettingsDlg", u"Check to allow setting a minimum control value to use for image exposure", None))
#endif // QT_CONFIG(tooltip)
        self.cbLimitCtrlMin.setText(QCoreApplication.translate("SettingsDlg", u"Use Minimum", None))
#if QT_CONFIG(tooltip)
        self.sbLimitCtrlMaxVal.setToolTip(QCoreApplication.translate("SettingsDlg", u"Maximum value to allow control when adjusting the current image property (check \"Use Maximum\" to enable)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.sbLimitCtrlMinVal.setToolTip(QCoreApplication.translate("SettingsDlg", u"Minimum value to allow control when adjusting the current image property (check \"Use Minimum\" to enable)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.cbLimitEncourage.setToolTip(QCoreApplication.translate("SettingsDlg", u"If control value exceeds specified range due to another property's control, allow this property's control to adjust towards nearest limit but not away from it", None))
#endif // QT_CONFIG(tooltip)
        self.cbLimitEncourage.setText(QCoreApplication.translate("SettingsDlg", u"Target Limits", None))
        self.cbLimitPreferred.setText(QCoreApplication.translate("SettingsDlg", u"Preferred Value", None))
        self.twSettingsTabs.setTabText(self.twSettingsTabs.indexOf(self.tabLimits), QCoreApplication.translate("SettingsDlg", u"Limits", None))
        self.textBrowser_3.setHtml(QCoreApplication.translate("SettingsDlg", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Cantarell'; font-size:8pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">You can configure some things about the captured image. You can add a small amount of caption, or loggng text and include a date, timestamp, etc.</p></body></html>", None))
        self.label_16.setText(QCoreApplication.translate("SettingsDlg", u"Image Caption:", None))
        self.label_12.setText(QCoreApplication.translate("SettingsDlg", u"Text:", None))
        self.label_13.setText(QCoreApplication.translate("SettingsDlg", u"Stamp:", None))
        self.cbDateStamp.setText(QCoreApplication.translate("SettingsDlg", u"Date", None))
        self.cbTimeStamp.setText(QCoreApplication.translate("SettingsDlg", u"Time", None))
        self.cbTwoFourHour.setText(QCoreApplication.translate("SettingsDlg", u"24 Hour", None))
        self.label_15.setText(QCoreApplication.translate("SettingsDlg", u"Horizontal Location:", None))
        self.rbCaptionHLeft.setText(QCoreApplication.translate("SettingsDlg", u"Left", None))
        self.rbCaptionHCenter.setText(QCoreApplication.translate("SettingsDlg", u"Center", None))
        self.rbCaptionHRight.setText(QCoreApplication.translate("SettingsDlg", u"Right", None))
        self.label_14.setText(QCoreApplication.translate("SettingsDlg", u"Vertical Location:", None))
        self.rbCaptionVBottom.setText(QCoreApplication.translate("SettingsDlg", u"Bottom", None))
        self.rbCaptionVCenter.setText(QCoreApplication.translate("SettingsDlg", u"Center", None))
        self.rbCaptionVTop.setText(QCoreApplication.translate("SettingsDlg", u"Top", None))
        self.label_17.setText(QCoreApplication.translate("SettingsDlg", u"Text Color:", None))
        self.label_18.setText(QCoreApplication.translate("SettingsDlg", u"Red:", None))
        self.label_19.setText(QCoreApplication.translate("SettingsDlg", u"Green:", None))
        self.label_20.setText(QCoreApplication.translate("SettingsDlg", u"Blue:", None))
        self.label.setText(QCoreApplication.translate("SettingsDlg", u"Font:", None))
        self.label_5.setText(QCoreApplication.translate("SettingsDlg", u"Size:", None))
        self.label_2.setText(QCoreApplication.translate("SettingsDlg", u"Caption text inset:", None))
        self.label_3.setText(QCoreApplication.translate("SettingsDlg", u"X", None))
        self.label_4.setText(QCoreApplication.translate("SettingsDlg", u"Y", None))
        self.label_29.setText(QCoreApplication.translate("SettingsDlg", u"pixels", None))
        self.twSettingsTabs.setTabText(self.twSettingsTabs.indexOf(self.tabImage), QCoreApplication.translate("SettingsDlg", u"Caption", None))
        self.textBrowser_4.setHtml(QCoreApplication.translate("SettingsDlg", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Cantarell'; font-size:8pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Set the location of the cameras on earth using latitude and longitude co-ordinates. This is used to calculate the times of sunrise and sunset to properly use Day/Night targets for image attributes and Day/Night ranges for controls that affect those image attributes.</p></body></html>", None))
        self.gbLatLonFormat.setTitle(QCoreApplication.translate("SettingsDlg", u"Latitude, Longitude Format", None))
        self.rbDMS.setText(QCoreApplication.translate("SettingsDlg", u"Degrees, Minutes, Seconds", None))
        self.rbFloat.setText(QCoreApplication.translate("SettingsDlg", u"Floating Point", None))
        self.gbLatitude.setTitle(QCoreApplication.translate("SettingsDlg", u"Latitude", None))
        self.lblLatDegrees.setText(QCoreApplication.translate("SettingsDlg", u"\u00b0", None))
        self.lblLatMinutes.setText(QCoreApplication.translate("SettingsDlg", u"m", None))
        self.lblLatSeconds.setText(QCoreApplication.translate("SettingsDlg", u"s", None))
        self.lblLatFloat.setText(QCoreApplication.translate("SettingsDlg", u"\u00b0", None))
        self.rbLatNorth.setText(QCoreApplication.translate("SettingsDlg", u"North", None))
        self.rbLatSouth.setText(QCoreApplication.translate("SettingsDlg", u"South", None))
        self.bLongitude.setTitle(QCoreApplication.translate("SettingsDlg", u"Longitude", None))
        self.lblLonDegrees.setText(QCoreApplication.translate("SettingsDlg", u"\u00b0", None))
        self.lblLonMinutes.setText(QCoreApplication.translate("SettingsDlg", u"m", None))
        self.lblLonSeconds.setText(QCoreApplication.translate("SettingsDlg", u"s", None))
        self.lblLonFloat.setText(QCoreApplication.translate("SettingsDlg", u"\u00b0", None))
        self.rbLonEast.setText(QCoreApplication.translate("SettingsDlg", u"East", None))
        self.rbLonWest.setText(QCoreApplication.translate("SettingsDlg", u"West", None))
        self.twSettingsTabs.setTabText(self.twSettingsTabs.indexOf(self.tabLatLon), QCoreApplication.translate("SettingsDlg", u"Lat/Lon", None))
    # retranslateUi

