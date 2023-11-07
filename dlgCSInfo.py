# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'csinfo.ui'
##
## Created by: Qt User Interface Compiler version 6.3.2
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QSizePolicy, QTextBrowser, QWidget)

class Ui_CSInfo(object):
    def setupUi(self, CSInfo):
        if not CSInfo.objectName():
            CSInfo.setObjectName(u"CSInfo")
        CSInfo.resize(200, 400)
        self.buttonBox = QDialogButtonBox(CSInfo)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(10, 358, 180, 32))
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Ok)
        self.textBrowser = QTextBrowser(CSInfo)
        self.textBrowser.setObjectName(u"textBrowser")
        self.textBrowser.setGeometry(QRect(10, 10, 180, 340))

        self.retranslateUi(CSInfo)
        self.buttonBox.accepted.connect(CSInfo.accept)
        self.buttonBox.rejected.connect(CSInfo.reject)

        QMetaObject.connectSlotsByName(CSInfo)
    # setupUi

    def retranslateUi(self, CSInfo):
        CSInfo.setWindowTitle(QCoreApplication.translate("CSInfo", u"Information", None))
        self.textBrowser.setHtml(QCoreApplication.translate("CSInfo", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"</style></head><body style=\" font-family:'Cantarell'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt; font-weight:700; text-decoration: underline;\">CSDevs</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Use CSDevs to capture images from a camera linux video device.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><br /></p"
                        ">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt; font-weight:700; font-style:italic;\">Usage</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Select a camera from the list and press the </span><span style=\" font-size:8pt; font-style:italic;\">Monitor</span><span style=\" font-size:8pt;\"> button. The controls for capture settings become available and the list of supported video formats and camera controls are filled.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">You must enter an image filename"
                        " to save captured frames to. Frame capture starts if you select a video format then select a frame size from the list of sizes the camera supports.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt; font-weight:700; font-style:italic;\">Information</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">It will take several frames for a camera to have stable images. The first frame will probably be whiteout and it will adjust from there. Set the </span><span style=\" font-size:8pt; font-style:italic;\">Capture nth frames</span><span style=\" font-size:8pt;\"> to a number high enough to obtain good frames. Then, at "
                        "the frequency indicated by the capture period the </span><span style=\" font-size:8pt; font-style:italic;\">nth</span><span style=\" font-size:8pt;\"> frame each time will always be the one captured.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Using </span><span style=\" font-size:8pt; font-style:italic;\">Stop </span><span style=\" font-size:8pt;\">or pressing </span><span style=\" font-size:8pt; font-style:italic;\">OK </span><span style=\" font-size:8pt;\">will not respond immediately if a frame capture has started. The effect should happen when the current capture finishes.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0"
                        "; text-indent:0px; font-size:8pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">It can take a long time to start and stop streaming frames from a camera, e.g. more than half a second for each. Waiting for the 80th frame at 30 frames per-second takes about two and a half seconds. Very short capture periods may not be useful, CSDevs will skip capturing a frame when a period has been reached but a previous frame capture is still in progress. Capturing the 80th frame </span><span style=\" font-size:8pt; text-decoration: underline;\">is</span><span style=\" font-size:8pt;\"> very conservative, but the combined time of starting and stopping the frame stream will probably still be over a second.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><br /></p>\n"
"<p style=\" "
                        "margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">When adjusting </span><span style=\" font-size:8pt; font-style:italic;\">Capture Period</span><span style=\" font-size:8pt;\"> or </span><span style=\" font-size:8pt; font-style:italic;\">Capture nth frames</span><span style=\" font-size:8pt;\"> experiment to ensure frame stability and utility of camera control settings made.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Take care with camera control settings. Most aren't expected to be adjusted much and big adjustments of some can create severe problems with the final image. Explore them with a video live feed application or exp"
                        "eriment with them in CSDevs and don't assume the first frame captured indicates the regular result.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt; font-weight:700;\">Location and Settings</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Use the </span><span style=\" font-size:8pt; font-style:italic; text-decoration: underline;\">Lat/Lon </span><span style=\" font-size:8pt;\">button to enter the location of the camera on earth by latitude and longitude. This allows the use of </span><span style=\" font-size:8pt; font-style:italic;\">Settings</span><span style=\" font-size:8pt;\"> to create different camer"
                        "a control settings for day and night. It's quite common for camera controls values useful during daytime to produce a nearly black frame if used at nighttime and for the camera control values useful during nighttime to produce a nearly white frame if used at daytime.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Use Settings to create an image caption with or without date or time stamps and to specify where the caption should appear in the frame.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt"
                        "-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">If the camera has adjustable countrols and you want to enable automatic image exposure (brightness, contrast, saturation) adjustment then use the Target tab in Settings to set target frame values (day and night if required) for brightness, contrast and saturation then use the Auto-Exposure tab to add the camera controls that adjust each image property for day (and night if required).</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">You can set minimum and maximum adjustment limits for each control. The control may go beyond the limit if it is used for more than one image property with different limits in each. You can also indicate that limits for a give"
                        "n control for given property should &quot;target limits&quot; which permits an adjustment if the control has exceeded the limits.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">You can also indicate that a camera control used for automatic exposure tuning's control value has an opposite effect on the property being tuned. For example, if the camera contrast control is being used to tune brightness but higher contrast control values make the image darker and lower contrast control values make the image lighter.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><br /></p>\n"
"<p style=\" margin-to"
                        "p:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">If the same control is listed to tune more than one image property and after an image capture all image properties that control is used for need to be adjusted the control will only be adjusted for one of the image properties.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">It may require experimenting to find a set of useful controls to tune image brightness, contrast and saturation plus the useful controls for each may differ in daytime from nighttime. A starting point is to only use a camera  brightness control to tune image brightness, a camera contrast control to tune image constrast a"
                        "nd a camera saturation control to tune image saturation. But when present, if controls like gain and gamma are not used for exposure tuning it can damage the usefulness of that simple starting point. Tuning gain usually affects only brightness but tuning gamma can affect brightness, contrast and saturation together.</span></p></body></html>", None))
    # retranslateUi

