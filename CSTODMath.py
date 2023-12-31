# This Python file uses the following encoding: utf-8

# Permit calculation of the switching between day and night targets based
# on the sunrise/sunset times without user intervention. This is based on
# spreadsheet based examples published by the NOAA organization at the
# following location:
#     https://www.esrl.noaa.gov/gmd/grad/solcalc/calcdetails.html
#
# Version: 2.0 - re-implented as a python class
# Copyright (C) 2022/05/14 David A. Mair
# This file is part of
# CSDevs
# Version: 1.0
# Copyright (C) 2020/09/21 David A. Mair
# This file is part of
# QtSunsetter<https://github.com/mairda/QtSunsetter.git>.
#
# CSDevs is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# CSDevs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CSDevs.  If not, see <http://www.gnu.org/licenses/>.
#

import time
import datetime

from math import sin, cos, tan, asin, acos, atan, atan2, degrees, radians, pi

from PySide6.QtCore import (QLoggingCategory, qCDebug, qCWarning)

# from csdMessages import (debug_message)


# CSTODMath - Worldwide Time-Of-Day information calculator that only requires
# that a latitude/longitude and timezone offset be provided for full operation.
# Use to calculate things like sunrise/sunset, day/night duration, whether it's
# current daytime or nighttime, position of sun in the sky, etc. Works in
# decimal fraction of day/night or hours minutes for time and seconds and
# decimal degrees or degrees, minutes & seconds for positions.
class CSTODMath:
    # Global state
    doDBug = False
    doTest = False

    HomeLat = 0.0
    HomeLong = 0.0
    # HomeLat = 29.976634
    # HomeLong = -101.766673
    # HomeLat = 55.8
    # HomeLong = -4.5
    Today = datetime.date.today()
    systemTime = time.localtime()
    HomeTZ = ((1.0 * systemTime.tm_gmtoff) / 3600.0)
    # HomeTZ = 0.0

    CorrectForSysTZ = False

    logCategory = QLoggingCategory("csdevs.math.TOD")

    def __init__(self):
        pass

    # Get the current time
    # Returns a daytime type (h:m:s)
    def get_time_now(self):
        systemTime = time.localtime()

        return datetime.time(systemTime[3], systemTime[4], systemTime[5])

    # Get the current time and correct from system timezone to a saved timezone
    # Returns a daytime type (h:m:s)
    def get_time_now_with_correction(self):
        timeNow = self.get_time_now()
        correctHour = timeNow.hour
        if self.CorrectForSysTZ is True:
            systemTime = time.localtime()
            sysTZ = 1.0 * systemTime.tm_gmtoff
            sysTZ /= 3600.0
            usingTZ = self.get_home_TZ()

            correction = int(sysTZ - usingTZ)
            qCDebug(self.logCategory,
                    "TZ: Clock {}, Home {}".format(sysTZ, usingTZ))
            qCDebug(self.logCategory,
                    "Time {} correction {}".format(correctHour, correction))
            # debug_message("TZ: Clock {}, Home {}".format(sysTZ, usingTZ))
            # debug_message("Time {} correction {}".format(correctHour, correction))

            correctHour += correction
            while correctHour < 0:
                correctHour += 24
            while correctHour > 23:
                correctHour -= 24

        # debug_message("CT: {}:{}:{}".format(correctHour, timeNow.minute,
        #                                    timeNow.second))

        correctedTime = datetime.time(correctHour,
                                      timeNow.minute,
                                      timeNow.second)
        # msg = "UsingTZ: {}, SysTZ: {}, ".format(usingTZ, sysTZ)
        # msg += "Correction: {}, ".format(correction)
        # msg += "Hour: {} => {}".format(timeNow.hour, correctHour)
        # debug_message(msg)

        return correctedTime

    # Get the current time as a fraction of a 24 hour day
    # Returns a float in the range zero to one inclusive
    def get_time_now_fraction_of_day(self):
        timeNow = self.get_time_now_with_correction()
        y = timeNow.hour * 3600.0
        y += timeNow.minute * 60.0
        y += timeNow.second

        # debug_message("Seconds used in day: {}".format(y))

        return (y / 86400.0)

    # Returns the fraction of the day that is daytime
    # Returns a float with value greater than zero and less than one
    def daytime_fraction_of_day(self):
        Today = datetime.date.today()
        aTime = datetime.time(0, 6, 0)

        r = self.local_sunrise(Today, aTime)
        s = self.local_sunset(Today, aTime)

        return (s - r)

    # Get the fraction of the day that is nighttime
    # Returns a float with value greater than zero and less than one
    # NB: Returns the amount of night during this day, i.e. before today's
    # sunrise plus after today's sunset. Not a continuous time of night
    def nighttime_fraction_of_day(self):
        return (1.0 - self.daytime_fraction_of_day())

    # Get today's sunrise time as a fraction of a 24 hour day
    # Returns a float in the range zero to one inclusive
    def get_sunrise_fraction_of_day(self):
        Today = datetime.date.today()
        aTime = datetime.time(0, 6, 0)

        # debug_message("Local sunrise: {}".format(self.local_sunrise(Today, aTime)))

        return self.local_sunrise(Today, aTime)

    # Get today's sunrise time
    # Returns a datetime object (h:m:s)
    def get_sunrise_time(self):
        x = self.get_sunrise_fraction_of_day()

        # debug_message("Sunrise fraction: {}".format(x))

        return self.time_from_day_fraction(x)

    # Get today's sunrise time
    # Returns a timedelta object
    def get_sunrise_delta(self):
        sRise = self.get_sunrise_time()

        return datetime.timedelta(hours=sRise.hour,
                                  minutes=sRise.minute,
                                  seconds=sRise.second)

    # Get today's sunset time as a fraction of a 24 hour day
    # Returns a float in the range zero to one inclusive
    def get_sunset_fraction_of_day(self):
        Today = datetime.date.today()
        aTime = datetime.time(0, 6, 0)

        # debug_message("Sunset fraction has local sunset: {}".format(self.local_sunset(Today, aTime)))

        return self.local_sunset(Today, aTime)

    # Get today's sunset time
    # Returns a datetime object (h:m:s)
    def get_sunset_time(self):
        x = self.get_sunset_fraction_of_day()

        # debug_message("Sunset fraction: {}".format(x))

        return self.time_from_day_fraction(x)

    # Get today's sunset time
    # Returns a timedelta object
    def get_sunset_delta(self):
        sSet = self.get_sunset_time()

        return datetime.timedelta(hours=sSet.hour,
                                  minutes=sSet.minute,
                                  seconds=sSet.second)

    # Get the current time and correct from system timezone to a saved timezone
    # Returns a timedelta object
    def get_time_now_delta_with_correction(self):
        TimeNow = self.get_time_now_with_correction()

        # debug_message("dT: {}:{}:{}".format(TimeNow.hour, TimeNow.minute,
        #                                     TimeNow.second))

        return datetime.timedelta(hours=TimeNow.hour,
                                  minutes=TimeNow.minute,
                                  seconds=TimeNow.second)

    # Returns true if it's after sunset but before midnight
    # Returns a bool
    def its_after_sunset_today(self):
        ssDelta = self.get_sunset_fraction_of_day()
        nowDelta = self.get_time_now_fraction_of_day()
        if nowDelta > ssDelta:
            return True

        return False

    # Returns true if the time now is in today's daytime
    # Returns a bool
    def its_daytime(self):
        srDelta = self.get_sunrise_delta()
        ssDelta = self.get_sunset_delta()
        nowDelta = self.get_time_now_delta_with_correction()

        # debug_message("Time Deltas:")
        # debug_message("\\_ Sunrise: {}".format(srDelta))
        # debug_message("\\_  Sunset: {}".format(ssDelta))
        # debug_message("\\_     Now: {}".format(nowDelta))

        return (nowDelta >= srDelta) and (nowDelta < ssDelta)

    # Returns true if the time now is in today's nighttime
    # Returns a bool
    def its_nighttime(self):
        # Implicitly not daytime
        return not self.its_daytime()

    # Get the current time as a fraction of the light period it is within
    # e.g. if it's daytime, what fraction of daytime has elapsed at current
    # time Automatically chooses daytime or nighttime
    # Returns a float in the range zero to one
    def get_time_now_fraction_of_light_period(self):
        srDelta = self.get_sunrise_fraction_of_day()
        ssDelta = self.get_sunset_fraction_of_day()
        nowDelta = self.get_time_now_fraction_of_day()
        # debug_message("Time deltas getting fraction of light period:")
        # debug_message("\\_ Sunrise: {}".format(srDelta))
        # debug_message("\\_  Sunset: {}".format(ssDelta))
        # debug_message("\\_     now: {}".format(nowDelta))
        if self.its_daytime():
            # debug_message("Compute fraction of DAY")
            # Subtract sunrise from now, all as a fraction of ratio of daytime
            elapsedFraction = nowDelta - srDelta
            elapsedFraction /= self.daytime_fraction_of_day()
        else:
            # debug_message("Compute fraction of NIGHT")
            # Night crosses midnight, take care
            if self.its_after_sunset_today():
                # debug_message("\\_ MORNING")
                # Evening, subtract sunset
                elapsedFraction = nowDelta - ssDelta
            else:
                # debug_message("\\_ EVENING")
                # Morning, Add whole evening to current part of morning
                elapsedFraction = 1.0 - ssDelta + nowDelta

            # As a fraction of nighttime
            elapsedFraction /= self.nighttime_fraction_of_day()

        # msg = "time now as a fraction of "
        # msg += "current light period: {}".format(elapsedFraction)
        # debug_message(msg)

        return elapsedFraction

    def ref_days(self, aDate):
        # baseDate = datetime.date(1900, 1, 14)
        baseDate = datetime.date(1899, 12, 30)
        deltaDate = abs(aDate - baseDate)
        return deltaDate.days
    # ref_days

    def frac_of_local_day(self, aTime):
        # Get second of the day from the time
        fDay = aTime.hour * 3600.0
        fDay += aTime.minute * 60.0
        fDay += aTime.second * 1.0

        # Fraction of day is the second of the day divided by seconds in a day
        fDay /= 86400.0

        return fDay
    # frac_of_local_day

    def time_from_day_fraction(self, fracOfDay):
        if (fracOfDay < 0.0) or (fracOfDay >= 1.0):
            # Bad fraction of the day, use midnight
            print("Bad fraction of day: {}, using midnight".format(fracOfDay))
            fracOfDay = 0.0

        # Convert to second of the day
        fracOfDay *= 86400.0

        # Get the h:m:s
        h = int(fracOfDay / 3600.0)
        m = int((fracOfDay - (3600.0 * h)) / 60.0)
        s = int(fracOfDay) % 60
        t = datetime.time(h, m, s)

        return t
    # time_from_day_fraction

    def julian_day(self, aDate, aTime=datetime.time(0, 0, 0)):
        jDay = self.ref_days(aDate) + 2415018.5 +\
                self.frac_of_local_day(aTime) - self.HomeTZ / 24.0
        # =D2+2415018.5+E2-$B$5/24

        return jDay
    # julian_day

    def julian_century(self, aDate, aTime=datetime.time(0, 0, 0)):
        jCent = self.julian_day(aDate, aTime)
        jCent -= 2451545.0
        jCent /= 36525.0
        # =(F2-2451545)/36525

        return jCent
    # julian_century

    def sun_geom_mean_long(self, aDate, aTime=datetime.time(0, 0, 0)):
        jCent = self.julian_century(aDate, aTime)
        mLong = (280.46646 + jCent * (36000.76983 + jCent * 0.0003032)) % 360
        # =MOD(280.46646+G2*(36000.76983+G2*0.0003032),360)

        return mLong
    # sun_geom_mean_long

    def sun_geom_mean_anom(self, aDate, aTime=datetime.time(0, 0, 0)):
        jCent = self.julian_century(aDate, aTime)
        mAnom = 357.52911 + jCent * (35999.05029 - 0.0001537 * jCent)
        # =357.52911+G2*(35999.05029-0.0001537*G2)

        return mAnom
    # sun_geom_mean_anom

    def sun_eq_of_ctr(self, aDate, aTime=datetime.time(0, 0, 0)):
        jCent = self.julian_century(aDate, aTime)
        mAnom = self.sun_geom_mean_anom(aDate, aTime)
        sEqC = sin(radians(mAnom))
        sEqC *= (1.914602 - jCent * (0.004817 + 0.000014 * jCent))
        sEqC += sin(radians(2 * mAnom)) * (0.019993 - 0.000101 * jCent)
        sEqC += sin(radians(3 * mAnom)) * 0.000289
        # =SIN(RADIANS(J2))*(1.914602-G2*(0.004817+0.000014*G2))+SIN(RADIANS(2*J2))*(0.019993-0.000101*G2)+SIN(RADIANS(3*J2))*0.000289

        return sEqC
    # sun_eq_of_ctr

    def sun_true_long(self, aDate, aTime=datetime.time(0, 0, 0)):
        tLong = self.sun_geom_mean_long(aDate, aTime) +\
                self.sun_eq_of_ctr(aDate, aTime)
        # =I2+L2

        return tLong
    # sun_true_long

    def sun_true_anom(self, aDate, aTime=datetime.time(0, 0, 0)):
        tAnom = self.sun_geom_mean_anom(aDate, aTime) +\
                self.sun_eq_of_ctr(aDate, aTime)
        # =J2+L2

        return tAnom
    # sun_true_anom

    def sun_rad_vector(self, aDate, aTime=datetime.time(0, 0, 0)):
        oEccent = self.earth_orbit_eccent(aDate, aTime)
        tAnom = self.sun_true_anom(aDate, aTime)
        rVec = (1.000001018 * (1 - oEccent * oEccent))
        rVec /= (1 + oEccent * cos(radians(tAnom)))
        # =(1.000001018*(1-K2*K2))/(1+K2*COS(RADIANS(N2)))

        return rVec
    # sun_rad_vector

    def sun_app_long_degrees(self, aDate, aTime=datetime.time(0, 0, 0)):
        jCent = self.julian_century(aDate, aTime)
        tLong = self.sun_true_long(aDate, aTime)
        aLong = tLong - 0.00569 - 0.00478 *\
            sin(radians(125.04 - 1934.136 * jCent))
        # =M2-0.00569-0.00478*SIN(RADIANS(125.04-1934.136*G2))

        return aLong
    # sun_app_long_degrees

    def sun_right_ascension(self, aDate, aTime=datetime.time(0, 0, 0)):
        aLong = radians(self.sun_app_long_degrees(aDate, aTime))
        oCorr = radians(self.obliq_corr_degrees(aDate, aTime))

        x = cos(aLong)
        y = cos(oCorr) * sin(aLong)

        rAscRad = atan2(y, x)
        rAscDeg = degrees(rAscRad)

        # aLong = 84.61
        # oCorr = 23.44
        # rAsc = degrees(atan2(cos(radians(aLong)),
        #                cos(radians(oCorr)) * sin(radians(aLong))))

        # =DEGREES(ATAN2(COS(RADIANS(P2)),COS(RADIANS(R2))*SIN(RADIANS(P2))))
        # For atan2:
        # x is COS(RADIANS(P2))
        # y is COS(RADIANS(R2))*SIN(RADIANS(P2))
        # In python math function is atan2(y, x)
        # In LibreOffice function is atan2(x, y)

        return rAscDeg
    # sun_right_ascension

    def sun_declination(self, aDate, aTime=datetime.time(0, 0, 0)):
        aLong = self.sun_app_long_degrees(aDate, aTime)
        oCorr = self.obliq_corr_degrees(aDate, aTime)
        sDec = degrees(asin(sin(radians(oCorr)) * sin(radians(aLong))))
        # =DEGREES(ASIN(SIN(RADIANS(R2))*SIN(RADIANS(P2))))

        return sDec
    # sun_declination

    def sun_variance(self, aDate, aTime=datetime.time(0, 0, 0)):
        oCorr = self.obliq_corr_degrees(aDate, aTime)
        sVar = tan(radians(oCorr / 2)) * tan(radians(oCorr / 2))
        # =TAN(RADIANS(R2/2))*TAN(RADIANS(R2/2))

        return sVar
    # sun_variance

    def HA_sunrise(self, aDate, aTime=datetime.time(0, 0, 0)):
        sDecRad = radians(self.sun_declination(aDate, aTime))
        homeLatRad = radians(self.HomeLat)
        haRiseIn = acos(cos(radians(90.833)) / (cos(homeLatRad) *
                        cos(sDecRad)) - tan(homeLatRad) *
                        tan(sDecRad))
        haRise = degrees(haRiseIn)
        # haRise = degrees(acos(cos(radians(90.833)) / (cos(radians(self.HomeLat)) * cos(radians(self.sun_declination(aDate, aTime)))) - tan(radians(self.HomeLat)) * tan(radians(self.sun_declination(aDate, aTime)))))
        # =DEGREES(ACOS(COS(RADIANS(90.833))/(COS(RADIANS($B$3))*COS(RADIANS(T2)))-TAN(RADIANS($B$3))*TAN(RADIANS(T2))))

        return haRise
    # HA_sunrise

    def mean_obliq_ecliptic(self, aDate, aTime=datetime.time(0, 0, 0)):
        jCent = self.julian_century(aDate, aTime)
        mObEcclip = 23 + (26 + ((21.448 - jCent * (46.815 + jCent * (0.00059 -
                                jCent * 0.001813)))) / 60) / 60
        # =23+(26+((21.448-G2*(46.815+G2*(0.00059-G2*0.001813))))/60)/60

        return mObEcclip
    # mean_obliq_ecliptic

    def obliq_corr_degrees(self, aDate, aTime=datetime.time(0, 0, 0)):
        jCent = self.julian_century(aDate, aTime)
        mObEcclip = self.mean_obliq_ecliptic(aDate, aTime)
        oCorr = mObEcclip + 0.00256 * cos(radians(125.04 - 1934.136 * jCent))
        # =Q2+0.00256*COS(RADIANS(125.04-1934.136*G2))

        return oCorr
    # obliq_corr_degrees

    def earth_orbit_eccent(self, aDate, aTime=datetime.time(0, 0, 0)):
        jCent = self.julian_century(aDate, aTime)
        oEccent = 0.016708634 - jCent * (0.000042037 + 0.0000001267*jCent)
        # =0.016708634-G2*(0.000042037+0.0000001267*G2)

        return oEccent
    # earth_orbit_eccent

    # Eq of Time (minutes)
    def eq_of_time(self, aDate, aTime=datetime.time(0, 0, 0)):
        mLong = self.sun_geom_mean_long(aDate, aTime)
        mAnom = self.sun_geom_mean_anom(aDate, aTime)
        oEccent = self.earth_orbit_eccent(aDate, aTime)
        sVary = self.sun_variance(aDate, aTime)
        # eTime = -1
        eTime = 4 * degrees(sVary * sin(2 * radians(mLong)) - 2 * oEccent *
                            sin(radians(mAnom)) + 4 * oEccent * sVary *
                            sin(radians(mAnom)) * cos(2 * radians(mLong)) -
                            0.5 * sVary * sVary * sin(4 * radians(mLong)) -
                            1.25 * oEccent * oEccent * sin(2 * radians(mAnom)))
        # =4*DEGREES(U2*SIN(2*RADIANS(I2))-2*K2*SIN(RADIANS(J2))+4*K2*U2*SIN(RADIANS(J2))*COS(2*RADIANS(I2))-0.5*U2*U2*SIN(4*RADIANS(I2))-1.25*K2*K2*SIN(2*RADIANS(J2)))

        return eTime
    # eq_of_time

    def solar_noon(self, aDate, aTime=datetime.time(0, 0, 0)):
        # rDays = ref_days(aDate)
        eTime = self.eq_of_time(aDate, aTime)
        sNoon = (720 - 4 * self.HomeLong - eTime + self.HomeTZ * 60) / 1440
        # =(720-4*$B$4-V2+$B$5*60)/1440

        return sNoon
    # solar_noon

    def local_sunrise(self, aDate, aTime=datetime.time(0, 0, 0)):
        hRise = abs(self.HA_sunrise(aDate, aTime))
        sNoon = abs(self.solar_noon(aDate, aTime))
        lRise = sNoon - hRise * 4 / 1440
        # =X2-W2*4/1440

        return lRise
    # local_sunrise

    def local_sunset(self, aDate, aTime=datetime.time(0, 0, 0)):
        hRise = abs(self.HA_sunrise(aDate, aTime))
        sNoon = abs(self.solar_noon(aDate, aTime))
        lSet = sNoon + hRise * 4 / 1440
        # =X2+W2*4/1440

        return lSet
    # local_sunset

    def sunlight_duration(self, aDate, aTime=datetime.time(0, 0, 0)):
        sDur = 8 * self.HA_sunrise(aDate, aTime)
        # =8*W2

        return sDur
    # sunlight_duration

    def test_function(self, aTime):
        Today = datetime.date.today()
        if self.doDBug is True:
            x = self.julian_day(Today, aTime)
            print("julian_day: {}".format(x))
            x = self.julian_century(Today, aTime)
            print("julian_century: {}".format(x))
            x = self.sun_geom_mean_long(Today, aTime)
            print("sun_geom_mean_long: {}".format(x))
            x = self.sun_geom_mean_anom(Today, aTime)
            print("sun_geom_mean_anom: {}".format(x))
            x = self.earth_orbit_eccent(Today, aTime)
            print("earth_orbit_eccent: {}".format(x))
            x = self.sun_eq_of_ctr(Today, aTime)
            print("sun_eq_of_ctr: {}".format(x))
            x = self.sun_true_long(Today, aTime)
            print("sun_true_long: {}".format(x))
            x = self.sun_true_anom(Today, aTime)
            print("sun_true_anom: {}".format(x))
            x = self.sun_rad_vector(Today, aTime)
            print("sun_rad_vector: {}".format(x))
            x = self.sun_app_long_degrees(Today, aTime)
            print("sun_app_long_degrees: {}".format(x))
            x = self.mean_obliq_ecliptic(Today, aTime)
            print("mean_obliq_ecliptic: {}".format(x))
            x = self.obliq_corr_degrees(Today, aTime)
            print("obliq_corr_degrees: {}".format(x))
            x = self.sun_right_ascension(Today, aTime)
            print("sun_right_ascension: {}".format(x))
            x = self.sun_declination(Today, aTime)
            print("sun_declination: {}".format(x))
            x = self.sun_variance(Today, aTime)
            print("sun_variance: {}".format(x))
            x = self.eq_of_time(Today, aTime)
            print("eq_of_time: {}".format(x))
            x = self.HA_sunrise(Today, aTime)
            print("HA_sunrise: {}".format(x))

#            sDecRad = radians(self.sun_declination(Today, aTime))
#            homeLatRad = radians(self.get_latitude())
#            homeLongRad = radians(self.get_longitude())
#            print("\\_ Declination: {} radians".format(sDecRad))
#            print("\\_ Home latitude: {} radians".format(homeLatRad))
#            print("\\_ Home longitude: {} radians".format(homeLongRad))

            x = self.solar_noon(Today, aTime)
            x *= 24 * 3600
            h = int(x / 3600)
            m = int((x - (3600 * h)) / 60)
            s = int(x) % 60
            t = datetime.time(h, m, s)
            # t = datetime.time(0, 0, 0)
            print("solar_noon: {} - {}:{}:{} - {}".format(x, h, m, s, t))
            x = abs(self.local_sunrise(Today, aTime))
            x *= 24 * 3600
            h = int(x / 3600)
            m = int((x - (3600 * h)) / 60)
            s = int(x) % 60
            t = datetime.time(h, m, s)
            # t = datetime.time(0, 0, 0)
            print("local_sunrise: {} - {}:{}:{} - {}".format(x, h, m, s, t))
            x = abs(self.local_sunset(Today, aTime))
            x *= 24 * 3600
            h = int(x / 3600)
            m = int((x - (3600 * h)) / 60)
            s = int(x) % 60
            t = datetime.time(h, m, s)
            # t = datetime.time(0, 0, 0)
            print("local_sunset: {} - {}:{}:{} - {}".format(x, h, m, s, t))
            x = self.sunlight_duration(Today, aTime)
            print("sunlight_duration: {}".format(x))
    # test_function

    def get_angle_degrees(self, angle):
        return int(angle)

    def get_angle_minutes(self, angle):
        fracAng = angle - self.get_angle_degrees(angle)
        return int(fracAng * 60.0)

    def get_angle_seconds(self, angle):
        fracAng = angle - self.get_angle_degrees(angle)
        fracAng -= self.get_angle_minutes(angle) / 60.0
        return int(fracAng * 3600.0)

    def get_DMS_angle_float(self, degrees, minutes, seconds):
        # FIXME: Does negative degrees mean the minutes and negatives are
        # implicitly negative? IOW, -54 degrees, 10 minutes and 34 seconds is
        # a larger negative degrees than 54.0. What then if minutes and/or
        # seconds is negative?
        # For now, I say sign of degrees is applied to minutes and seconds and
        # the -54d10m34s example is -54.1761 degrees
        fracAng = degrees
        if degrees >= 0:
            dSign = 1.0
        else:
            dSign = -1.0
        fracAng += dSign * minutes / 60.0
        fracAng += dSign * seconds / 3600.0

        return fracAng

    def get_latitude(self):
        return self.HomeLat

    def get_abs_latitude(self):
        return abs(self.get_latitude())

    def get_latitude_degrees(self):
        return self.get_angle_degrees(self.get_abs_latitude())

    def get_latitude_minutes(self):
        return self.get_angle_minutes(self.get_abs_latitude())

    def get_latitude_seconds(self):
        return self.get_angle_seconds(self.get_abs_latitude())

    def set_latitude(self, newLat):
        if (newLat >= -90.0) and (newLat <= 90.0):
            self.HomeLat = newLat

    def get_longitude(self):
        return self.HomeLong

    def get_abs_longitude(self):
        return abs(self.get_longitude())

    def get_longitude_degrees(self):
        return self.get_angle_degrees(self.get_abs_longitude())

    def get_longitude_minutes(self):
        return self.get_angle_minutes(self.get_abs_longitude())

    def get_longitude_seconds(self):
        return self.get_angle_seconds(self.get_abs_longitude())

    def set_longitude(self, newLon):
        if (newLon >= -180.0) and (newLon <= 180.0):
            self.HomeLong = newLon

    def set_system_time(self):
        self.systemTime = time.localtime()

    def get_home_TZ(self):
        return self.HomeTZ

    def set_home_TZ(self, tzOffset):
        if tzOffset < 86400.0:
            self.HomeTZ = 1.0 * tzOffset
            self.HomeTZ /= 3600.0

    def set_local_TZ(self):
        self.HomeTZ = 1.0 * self.systemTime.tm_gmtoff
        self.HomeTZ /= 3600.0

        # print("TZ: {}".format(HomeTZ))

    def ss_math_debug(self):
        return self.doDBug

    def ss_math_test(self):
        return self.doTest
