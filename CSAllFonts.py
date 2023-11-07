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
import time

from PySide6.QtCore import (QDirIterator, QLoggingCategory, QStandardPaths,
                            qCDebug, qCWarning)
from PySide6.QtGui import (QFont, QFontDatabase, QRawFont)

# from csdMessages import (disable_warnings, enable_warnings, disable_debug,
#                         enable_debug, warning_message, debug_message)


class CSAllFonts:
    '''
    This class is intended to look up font filenames from family names for use
    in PILlow ImageFont objects when giving the user a selection view by family.
    The ImageFont requires a filename and Qt view gives us family but not the
    filename of the font data

    It's very slow to run in-full on-demand because it loads every font it finds
    in default configuration locations for fonts and logs basic attributes for
    each font file found. When there are sub-directories of font paths the
    sub-tree is scanned too. Therefore, the class is designed to scan and build
    font information when initialized then be used based on the recorded data.
    Initialization can be re-executed on-demand but at least it isn't required
    for every lookup
    '''

    '''
    Lists of discovered fonts:
        unloadable: those that cannot be loaded as a QRawFont, their family
            name identified and found in the QFontDatabase
        accounted: those that can be loaded as a QRawFont, their family name
            identified and found in the QFontDatabase. It's a list of tuples
            with family name, path of font file, style of font and weight of
            font.
        familyToPath: a dictionary of family names to path names. Key is font
            family name and items are tuples of path of font file, style of font
            and weight of font
        allFamiliesToPath: a dictionary currently unused.
    '''
    unloadable = []
    accounted = []
    familyToPath = {}
    allFamiliesToPath = {}
    dbCount = 0

    '''
    Common filename extensions for font files that Qt/PILlow might support
    '''
    fontIDs = [".ttf", ".otf", ".otb", ".pfs", ".pfb", ".pcf.gz", ".pcf"]

    '''
    Common font style names used on linux font filenames to identify font weight
    instead of actual graphical library object. For example, a font filename
    containing Thin and a font filename containing Bold where both have the same
    family identity in the filename are probably different weights of the same
    font but a Qt font of each will have weight QFont.Normal in Qt. So we have
    to parse the filename and interpret the viewed weight based on presence of
    these in the filename
    '''
    fontStyles = ["Thin", "ExtraLight", "Light", "Regular", "Medium",\
                  "DemiBold", "Bold", "ExtraBold", "Black"]
    matchNone = 0
    matchName = 1
    matchNameAndStyle = 2

    logCategory = QLoggingCategory("csdevs.fonts.all")

    def __init__(self):
        '''
        Constructor, loads the list and dictionary of fonts
        '''
        # families = QFontDatabase.families()
        # debug_message("All known font families before parsing files: {}".format(len(families)))
        self.load_font_lists()

    def __track_font_file(self, fontPath):
        '''
        Verify if a file is a font and has a family in the QFontDatabase then
        keep a local record of the filename, family, weight and style
        information

        Parameters
        ----------
            fontPath: string
                Contains the name of a file assumed to be a font
        '''

        # Does the file have a file extension expected for a font
        for aFmt in self.fontIDs:
            if fontPath.endswith(aFmt):
                # Get a raw font from the file and get it's family
                aFont = QRawFont()
                aFont.loadFromFile(fontPath, 16,
                                   QFont.PreferDefaultHinting)
                fontFamily = aFont.familyName()

                # Does the family exist in the database
                if QFontDatabase.hasFamily(fontFamily):
                    self.dbCount += 1
                    # If we already know it then account more attributes
                    if fontFamily in self.familyToPath:
                        # Already accounted for as a family name but
                        # account more attributes
                        self.accounted.append((fontFamily, fontPath,
                                               aFont.style(),
                                               aFont.weight()))
                    else:
                        # Family not seen yet, log it keyed by
                        # family name
                        self.familyToPath[fontFamily] = (fontPath,
                                                         aFont.style(),
                                                         aFont.weight())
                else:
                    # Failed to add to the font database
                    self.unloadable.append(fontPath)

                # Used the file extension loop to a conclusion
                break

    def __add_to_font_database(self, fontPath):
        '''
        Add a named file to the QFontDatabase. If we did add it to the database
        then create a Qt font object to get some attributes for use in our own
        font information. If we didn't add it to the database then track the
        filename in the unloadable list

        Parameters
        ----------
            fontPath: string
                Contains the name of a file assumed to be a font
        '''

        # Does the file have a file extension expected for a font
        for aFmt in self.fontIDs:
            if fontPath.endswith(aFmt):
                idx = QFontDatabase.addApplicationFont(fontPath)
                if idx >= 0:
                    # Use a raw font to get default attributes
                    aFont = QRawFont()
                    aFont.loadFromFile(fontPath, 16,
                                       QFont.PreferDefaultHinting)

                    # Go through all font database family names in the added font
                    names = QFontDatabase.applicationFontFamilies(idx)
                    for n in names:
                        self.dbCount += 1
                        if n in self.familyToPath:
                            # Already accounted for as a family name but
                            # account more attributes
                            self.accounted.append((n, fontPath,
                                                   aFont.style(),
                                                   aFont.weight()))
                        else:
                            # Family not seen yet, log it keyed by
                            # family name
                            self.familyToPath[n] = (fontPath,
                                                    aFont.style(),
                                                    aFont.weight())
                else:
                    # Failed to add to the font database
                    self.unloadable.append(fontPath)

                # Used the file extension loop to a conclusion
                break

    def __scanFontPath(self, aPath):
        '''
        This is very slow, os.walk() is a few seconds faster than recursive
        os.scandir(). It's best to use this and initialize a class instance
        which is not (or is rarely) re-initialized, font install/remove is not
        frequent. It's then faster to look up a choice of font filename from the
        initialized instance. Use the member
        font_file_for_font_family_filtered() to find a font filename with
        restricted styles, e.g. not bold, not italic because there can be
        multiple font files to cover available styles for any family.
        font_file_for_font_family() only gives the first file found for the
        requested family, with no style restrictions. Use of yieldCurrentThread
        appears to either reduce the impact or, indeed, make this faster.

        Parameters
        ----------
            aPath: string
                Contains the name of a directory to scan for font files
        '''

        try:
            lastYield = time.time()
            t0 = lastYield
            yieldLimit = 0.4
            yieldCount = 0
            for root, dirs, files in os.walk(aPath):
                # Some of the "files" values cause a ValueError if accessed, so
                # use a length limited loop with exception handling to continue
                # past them. j is the successfully acessed count, k the count of
                # accesses that caused exceptions. The sum j + k is current
                # index
                i = len(files)
                j = 0
                k = 0
                while i > (j + k):
                    try:
                        aName = files[j + k]
                        j += 1
                        if not aName.startswith('.'):
                            t0 = time.time()
                            if (t0 - lastYield) >= yieldLimit:
                                self.yieldCurrentThread()
                                yieldCount += 1
                                lastYield = t0
                            try:
                                # The file may not be a font and we should get
                                # an exception in some cases
                                fontPath = os.path.join(root, aName)
                                # self.__add_to_font_database(fontPath)
                                self.__track_font_file(fontPath)
                            except:
                                # Parsing the path to font database or using it
                                # as a raw font failed, try the next entry
                                continue
                    except Exception as e:
                        msg = "Iterate {} files from {} failed at {}"
                        qCWarning(self.logCategory, msg)
                        qCDebug(self.logCategory,
                                "Failure is {}".format(type(e)))
                        # debug_message(msg.format(aPath, j + k))
                        # debug_message(
                        k += 1
        except:
            # Starting scan of the supplied directory failed, stop the exception
            # but don't fail or report it. Standard font directories aren't
            # required to contain anything and some are usually empty.
            pass

    # This is very slow so is best used to initialize an instance which is much
    # faster to look up a choice of font filename from. Use the member
    # font_file_for_font_family_filtered() to find a font filename with restricted
    # attributes, e.g. not bold, not italic because there can be multiple
    # font files for the same family to get the individual styles and
    # font_file_for_font_family() only gives the first file found for the requested
    # family, with no style restrictions.
    def __scanFontPathB(self, aPath):
        lastYield = time.time()
        t0 = lastYield
        yieldLimit = 0.4
        yieldCount = 0
        try:
            # Scan path
            with os.scandir(aPath) as it:
                for entry in it:
                    try:
                        if not entry.name.startswith('.'):
                            if entry.is_file():
                                t0 = time.time()
                                if (t0 - lastYield) >= yieldLimit:
                                    self.yieldCurrentThread()
                                    yieldCount += 1
                                    lastYield = t0
                                try:
                                    # Create a fully qualified filename
                                    fontPath = os.path.join(aPath, entry.name)
                                    # self.__add_to_font_database(fontPath)
                                    self.__track_font_file(fontPath)
                                except:
                                    # Parsing the path to font database failed,
                                    # try the next entry
                                    continue
                            elif entry.is_dir():
                                # Append directory name to path so-far and
                                # re-call ourselves to parse the new directory
                                newPath = aPath + "/" + entry.name
                                self.__scanFontPathB(newPath)
                    except:
                        # Parsing a directory entry failed, try the next
                        continue
        except:
            # Start scanning the supplied directory failed, stop
            pass

    # 2022/10/11: At least one python 3.10 has os.scandir() that returns
    # DirEntry objects that raise an AttributeError when entry.name is
    # accessed. Repeat the __scanFontPath implementation using Qt objects.
    # This version is probably the slowest, although the number of files ignored
    # by the raising of AttributeError might make the os.scandir() version only
    # appear faster
    def __scanFontPathQt(self, aPath):
        lastYield = time.time()
        yieldLimit = 0.4
        yieldCount = 0

        # Iterate from the supplied top-level directory recursively
        it = QDirIterator(aPath, QDirIterator.Subdirectories)
        while it.hasNext():
            fInfo = it.nextFileInfo()
            fName = it.fileName()

            # Only handle files that are not hidden
            if fInfo.isFile() and not fName.startswith("."):
                # self.__add_to_font_database(fInfo.filePath())
                # If it's a font and in the QFontDatabase keep track of the
                # relationship with the database entry and the full file path
                self.__track_font_file(fInfo.filePath())

                # Yield from time to time
                tNow = time.time()
                if (tNow - lastYield) > yieldLimit:
                    time.sleep(0)
                    yieldCount += 1
                    lastYield = tNow

    def __clear_font_lists(self):
        '''
        Reset the font lists, dictionary and font count to no fonts
        '''

        self.unloadable.clear()
        self.familyToPath.clear()
        self.accounted.clear()

        self.dbCount = 0

    def load_font_lists(self):
        '''
        Load the font lists, dictionary and count with information found in
        font directories
        '''

        msg = "Gathering system font data, this can take a while..."
        qCDebug(self.logCategory, msg)
        # debug_message(msg)

        # Start with no known font to file mappings
        self.__clear_font_lists()

        # We need to walk all fonts in configuration directories recursively.
        # Each directory is not required to exist or contain any files, it's
        # just a list of potential locations for fonts
        fPaths = QStandardPaths.standardLocations(QStandardPaths.FontsLocation)

        # tStart = time.time()
        for aPath in fPaths:
            self.__scanFontPathQt(aPath)
        # tEnd = time.time()
        # debug_message("Scan all font directory files took {}s".format(tEnd - tStart))
        # debug_message("\\ Families: {}, Accounted: {}, Unloadable: {}".format(len(self.familyToPath), len(self.accounted), len(self.unloadable)))

        msg = "Finished gathering system font data. {} ".format(self.dbCount)
        msg += "font files with family in font database."
        qCDebug(self.logCategory, msg)
        # debug_message(msg)
        # families = QFontDatabase.families()
        # debug_message("All known font families after parsing files: {}".format(len(families)))

    def dump_font_paths(self):
        '''
        Debugging function to list the loadable font family and filenames
        '''

        for item, key in enumerate(self.familyToPath):
            qCDebug(self.logCategory,
                    "FONT: {} is {}".format(key, self.familyToPath[key]))
            # debug_message("FONT: {} is {}".format(key, self.familyToPath[key]))

    def fontFileForFontFamily(self, family):
        '''
        Just get the first instance we found of the family, that could be any
        style/weight for that family

        Parameters
        ----------
            family: string
                Contains the name of a font family

        Errors:
            The result of retrieving a dictionary entry that doesn't exist is
            passed as-is to the caller
        '''

        # self.dump_font_paths()
        tFont = self.familyToPath[family]
        return tFont[0]

    def standard_weight_fit(self, weight):
        '''
        Get a pair of weights that a given weight is between in QFont standard
        weight names and that are centered on a standard weight with the result
        pair values centered between the standard weight either side of the
        center we chose. If no match is found then the result equivalent to
        a QFont.Normal weight is returned so that there is something to use.

        Parameters
        ----------
            weight: integer
                A required font weight caller wants to use

        Returns a tuple of a lower and upper weight numeric value that requested
        weight is between in standard weight names.

        For example:
        weight: 425 (supplied parameter)
        Normal standard weight: 400 (center weight that will be found in function)
        Light standard weight: 300 (nearest standard weight lower than Normal)
        Medium standard weight: 500 (nearest standard weight higher than Normal)
        Lower mid-point: 350 (half way between Light and Normal)
        Upper mid-point: 450 (half way between Normal and Medium)
        Result tuple: (Lower mid-point, Upper mid-point)
                  or: (350, 450)
        Which is a range that:
         * contains supplied weight: 425
         * is centered on a standard weight: Normal (400)
         * has low value half way from previous standard value to Normal
         * has a high value half way from Normal to next standard value

        NB: When considering lowest supported standard weight as a center point
        then low of range is minimum weight (1) and when considering highest
        supported standard weight as a center point then high of range is maximum
        weight (1000) so that we don't use absolute minimum supported weight and
        absolute maximum supported as center points for a supplied weight.

        '''

        # FIXME: Can the / 2 create int() values that can leave a gap of 1
        # between possible results. If all standard weights are integers then
        # the only fraction that can occur is w.5 for which both the loMid and
        # hiMid should round in the same direction, so don't think so

        # We have to try all standard weights until we find one that has
        # mid-points between the under and over standard weight that contains
        # the supplied weight
        weightFit = None
        centerWeight = QFont.Thin
        while centerWeight != 1000:
            # Get the standard weight under and over the current center weight
            if centerWeight == QFont.Thin:
                overWeight = QFont.ExtraLight
            elif centerWeight == QFont.ExtraLight:
                underWeight = QFont.Thin
                overWeight = QFont.Light
            elif centerWeight == QFont.Light:
                underWeight = QFont.ExtraLight
                overWeight = QFont.Normal
            elif centerWeight == QFont.Normal:
                underWeight = QFont.Light
                overWeight = QFont.Medium
            elif centerWeight == QFont.Medium:
                underWeight = QFont.Normal
                overWeight = QFont.DemiBold
            elif centerWeight == QFont.DemiBold:
                underWeight = QFont.Medium
                overWeight = QFont.Bold
            elif centerWeight == QFont.Bold:
                underWeight = QFont.DemiBold
                overWeight = QFont.ExtraBold
            elif centerWeight == QFont.ExtraBold:
                underWeight = QFont.Bold
                overWeight = QFont.Black
            elif centerWeight == QFont.Black:
                underWeight = QFont.ExtraBold

            # Get the mid-points between under and center also between center
            # and over
            # Don't use mid-point under lowest standard and mid-point over
            # highest standard
            if centerWeight != QFont.Thin:
                loMid = centerWeight - int((centerWeight - underWeight) / 2)
            else:
                loMid = 1
            if centerWeight != QFont.Black:
                hiMid = centerWeight + int((overWeight - centerWeight) / 2)
            else:
                hiMid = 1000

            # Check if the supplied weight is within current range
            if (weight >= loMid) and (weight <= hiMid):
                # Found, use the mid-points between standard values as the
                # result and end the loop
                weightFit = (loMid, hiMid)
                break

            # Next center weight to test is current over weight
            centerWeight = overWeight

        # If we have no weight fit found then supplied weight is out-of-range
        # for all standard weights or otherwise unrecognized, assume normal
        # FIXME: Should this raise a ValueError exception instead?
        if weightFit is None:
            weightFit = self.standard_weight_fit(QFont.Normal)

        return weightFit

    def __font_weight_style(self, weight):
        '''
        Get the style text we'd expect a font filename to have appended to
        indicate the given content weight

        This is not an accurate method as a font creator can use any style name
        for any weight but it is reasonably accurate for most fonts.

        Parameters
        ----------
            weight: integer
                The weight number the style equivalent is wanted for

        Returns a string containing the font style normally used for the
        supplied weight value. Or returns None if supplied weight doesn't match
        the weight range of any standard font.
        '''

        weightFit = self.standard_weight_fit(weight)
        if (weightFit[0] <= QFont.Thin) and (weightFit[1] >= QFont.Thin):
            needStyle = self.fontStyles[0]
        elif (weightFit[0] <= QFont.ExtraLight) and (weightFit[1] >= QFont.ExtraLight):
            needStyle = self.fontStyles[1]
        elif (weightFit[0] <= QFont.Light) and (weightFit[1] >= QFont.Light):
            needStyle = self.fontStyles[2]
        elif (weightFit[0] <= QFont.Normal) and (weightFit[1] >= QFont.Normal):
            needStyle = self.fontStyles[3]
        elif (weightFit[0] <= QFont.Medium) and (weightFit[1] >= QFont.Medium):
            needStyle = self.fontStyles[4]
        elif (weightFit[0] <= QFont.DemiBold) and (weightFit[1] >= QFont.DemiBold):
            needStyle = self.fontStyles[5]
        elif (weightFit[0] <= QFont.Bold) and (weightFit[1] >= QFont.Bold):
            needStyle = self.fontStyles[6]
        elif (weightFit[0] <= QFont.ExtraBold) and (weightFit[1] >= QFont.ExtraBold):
            needStyle = self.fontStyles[7]
        elif (weightFit[0] <= QFont.Black) and (weightFit[1] >= QFont.Black):
            needStyle = self.fontStyles[8]
        else:
            needStyle = None

        return needStyle

    def __file_bare_name(self, fPath):
        '''
        Given some kind of filename, return the name without any preceding path
        and without any filename extension.

        Only the last extension element is removed, so provding a file with
        multiple extensions will result in the name up to the second last
        extension.

        Parameters
        ----------
            fPath: string
                Contains some kind of filename to get the "bare" filename from.
                It can be something from a fully qualified path and filename or
                a relative path and filename or even a bare name already.

        Returns a string containing the name of the file element only from the
        supplied name, i.e. path elements and file extension are removed.
        '''

        sofn = fPath.rfind("/")
        if sofn != -1:
            sofn += 1
            fName = fPath[sofn:]
        else:
            fName = fPath
        eofn = fName.find(".")
        if eofn > 0:
            fontFile = fName[:eofn]
        else:
            fontFile = fName

        return fontFile

    def __name_has_font_style(self, aName, needStyle):
        '''
        Return True if aName has needStyle contained in it but only if needStyle
        is one of the texts we expect to indicate a font file weight style, else
        returns False.

        Parameters
        ----------
            aName: string
                Contains the name of a font file. Should usually be a result of
                using __file_bare_name() on the filename for a font.
            needStyle: string
                Contains the needed font style
        '''

        # FIXME: This might be better as: if needStyle in self.fontStyle and
        # needStyle in aName, i.e. needStyle is a known style in one step and if
        # it is then in the supplied name as well.

        # First of all does the name have any style
        hasStyle = False
        for aStyle in self.fontStyles:
            # debug_message("Checking for style {} in {}".format(aStyle, aName))
            if aName.find(aStyle) != -1:
                hasStyle = True
                break

        # if hasStyle:
        #     debug_message("{} has a font style".format(fontFile))
        if hasStyle:
            if aName.find(needStyle) != -1:
                return True

        return False

    def __font_attr_match(self, tFont, weight, style, exactWeight):
        '''
        Given information about a font file indicate how well it matches the
        other parameters (weight, style). Handles cases where the weight might
        be expressed as part of the filename, e.g. Raleway-Black.ttf is not for
        drawing at a Qt.Normal weight of 400, that should probably be drawn with
        Raleway-Regular.ttf

        Parameters
        ----------
            tFont: tuple
                Is the same format as used for the familyToPath dictionary
                items:
                    tuple of path of font file, style of font and weight of font
            weight: integer
                A desired weight to use for output
            style: string
                Contains a standard font style name (see the fontstyles member)
            exactWeight: boolean
                If True, requires that the font with filename tFont have a
                weight that exactly matches the weight parameter

        Returns an integer indicating the level of match. There are three
        levels, see the match* member variables. matchNone indicated no match,
        matchName indicates the font matches name but not style. matchStyle
        indicates the font matches the required name and style.
        '''

        # We have to handle the weight twice, once to match it literally against
        # the weight argument but there are often fonts with a name, e.g.
        # NiceFont that have multiple filenames with font styles such as
        # ExtraBold, SemiBold, Medium, Light, ExtraLight, Thin and Bold where
        # the style is an implied weight. So try to match styles like those with
        # the requested weight using the QFont.Weight named values
        needStyle = self.__font_weight_style(weight)
        if needStyle is not None:
            # Get the filename itself
            fontFile = self.__file_bare_name(tFont[0])

            # Does the filename contain the style of the requested weight
            foundStyle = self.__name_has_font_style(fontFile, needStyle)
        else:
            foundStyle = False

        # Style when a raw font was created from file
        if tFont[1] is not None:
            if tFont[1] != style:
                return self.matchNone

        # Weight when a raw font was created from file
        if tFont[2] > 0:
            if exactWeight:
                # The font's default weight must exactly match the supplied
                # weight
                if weight != tFont[2]:
                    return self.matchNone
            else:
                # The requested weight is considered a match for a font's
                # default weight if requested weight is in the range containing
                # the font's weight that's centered at a standard weight and
                # extends from the mid-points between previous standard weight
                # to center weight and center weight to next standard weight,
                # e.g.:
                #
                # w = requested weight
                # f = font default weight
                # | = Qt standard weight values (Light, Normal, Medium, etc)
                # x = min/max of range w is tested against
                #
                # (x are half way between the two | values either side of
                #  the nearest | to f)
                #
                # |____x__w_|__f_x____|_________|_________| MATCH
                #
                # |_______w_|____x__f_|____x____|_________| NO MATCH
                #
                weightFit = self.standard_weight_fit(tFont[2])
                if (weight < weightFit[0]) or (weight > weightFit[1]):
                    directWeight = False
                else:
                    directWeight = True

        # tFont matches supplied weight and style with font filename style
        # text if found
        if foundStyle:
            return self.matchNameAndStyle
        elif directWeight is True:
            return self.matchNameAndStyle

        # FIXME: Was there anything that could be called a verification of the
        # name?
        return self.matchName

    def font_file_for_font_family_filtered(self, family, weight, style,
                                           testFileStyle=True,
                                           exactWeight=False, lastResort=True):
        '''
        There can be multiple files having the same font family, e.g. normal,
        bold italic, etc. Try to find a suitable one. Take available font files
        for the requested family and verify a default QRawFont using it has the
        requested weight and style.

        Parameters
        ----------
            family: string
                Contains the name of the font family a font file is to be found
                for
            weight: integer
                A Required font weight to be used for output
            style: string
                Contains the name of a font style to be found (see the
                fontStyles member)
            testFileStyle: boolean
                If True, successful results must match supplied family name and
                style. If False any font that matches the family name is a
                successful match.
            exactWeight: boolean
                If True a successfully found file must have aweight attribute
                that exactly matches this function's weight parameter. Else a
                match is successful if the weight parameter is in a range around
                the standard weight containing the font's weight attribute
            lastResort: boolean
                If True then in the absence of any match the first filename
                found for the family paramter is returned

        Returns a list of matching fonts on success or None on failure. The list
        members are tuples in the same format used for the familyToPath
        dictionary: path of font file, style of font, weight of font
        '''

        # self.dump_font_paths()
        fontSet = []

        # Consider any already accounted families
        for tAccFont in self.accounted:
            # Ignore non-matching families
            if tAccFont[0] != family:
                continue

            # Create a new tuple of the same format as the familyToPath
            tFont = (tAccFont[1], tAccFont[2], tAccFont[3])

            # Check if it matches requested attributes, list it if yes
            match = self.__font_attr_match(tFont, weight, style, exactWeight)
            if testFileStyle and (match == self.matchNameAndStyle):
                # Match family, weight, style and/or file style, put at head
                # of results
                fontSet.insert(0, tFont)
            elif match >= self.matchName:
                # Family, weight and non-file style match - append to results
                fontSet.append(tFont)

        # Consider at least a matching case in familyToPath. The presence in it
        # has no special priority over a match in accounted.
        if family in self.familyToPath:
            tFont = self.familyToPath[family]
            if len(fontSet) > 0:
                # We already found a family/attribute match check if
                # familyToPath also matches requested attributes, list it if yes
                match = self.__font_attr_match(tFont, weight, style, exactWeight)
                if testFileStyle and (match == self.matchNameAndStyle):
                    # Match family, weight style and/or file style, put at head
                    # of results
                    fontSet.insert(0, tFont)
                elif match >= self.matchName:
                    # Family, weight and non-file style match - append to results
                    fontSet.append(tFont)

            elif lastResort:
                # No match found, treat the first case of only the family that
                # existed when scanning files as the best effort (if lastResort)
                fontSet.append(tFont)

        # If we found any fonts
        if len(fontSet) > 0:
            # Take the head tuple and return the filename from it
            tFont = fontSet[0]
            # debug_message("Using font file: {}".format(tFont[0]))
            return tFont[0]

        # Definately no family match. If not lastResort then no weight or style
        # match either
        return None
