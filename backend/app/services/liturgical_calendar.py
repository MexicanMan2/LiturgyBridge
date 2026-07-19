"""
LiturgyBridge Liturgical Calendar Service.

Computes Julian/Gregorian dates, calculates the date of Orthodox Pascha (Easter)
using Meeus' Luni-Solar algorithm, determines the weekly Tone (Oktoechos 1-8 cycle),
and maps dynamic daily scripture readings (Epistle/Gospel) and commemorations.
"""

from datetime import date, datetime, timedelta
from typing import Dict, Any

def calculate_orthodox_pascha(year: int) -> date:
    """
    Computes the Gregorian date of Orthodox Pascha (Easter) for a given year
    using Meeus' Luni-Solar Julian algorithm, converted to Gregorian calendar (+13 days).
    """
    a = year % 19
    b = year % 4
    c = year % 7
    d = (19 * a + 15) % 30
    e = (2 * b + 4 * c + 6 * d + 6) % 7
    f = d + e
    
    # Julian calendar date:
    if f <= 9:
        month = 3
        day = 22 + f
    else:
        month = 4
        day = f - 9
        
    julian_date = date(year, month, day)
    
    # Gregorian calendar is 13 days ahead of Julian calendar for years 1900-2099
    gregorian_date = julian_date + timedelta(days=13)
    return gregorian_date

def get_tone_for_date(d: date) -> int:
    """
    Calculates the current Tone (1 to 8) for a given date in the Oktoechos cycle.
    The Tone cycle starts on Thomas Sunday (1 week after Pascha) with Tone 1,
    and rotates weekly on Sundays.
    """
    pascha_this_year = calculate_orthodox_pascha(d.year)
    if d >= pascha_this_year:
        pascha_ref = pascha_this_year
    else:
        pascha_ref = calculate_orthodox_pascha(d.year - 1)
        
    days_since = (d - pascha_ref).days
    weeks_since = days_since // 7
    
    # Pascha week (Bright Week, weeks_since == 0) is treated as Tone 1 (or special)
    if weeks_since == 0:
        return 1
        
    # Thomas Sunday (weeks_since == 1) is Tone 1. Thomas Sunday is Tone 1, next is Tone 2, etc.
    return ((weeks_since - 1) % 8) + 1

def get_liturgical_day_info(dt: datetime) -> Dict[str, Any]:
    """
    Calculates the Tone of the week, name of the liturgical day,
    and references for the daily Epistle and Gospel readings.
    """
    d = dt.date()
    pascha_this_year = calculate_orthodox_pascha(d.year)
    
    # Determine the reference Pascha date
    if d >= pascha_this_year:
        pascha_ref = pascha_this_year
        pascha_year = d.year
    else:
        pascha_ref = calculate_orthodox_pascha(d.year - 1)
        pascha_year = d.year - 1
        
    days_since = (d - pascha_ref).days
    weeks_since = days_since // 7
    weekday = d.weekday()  # 0=Monday, 6=Sunday
    
    # Oktoechos Tone rotation
    tone = get_tone_for_date(d)
    
    # Default outputs
    day_name = "Ordinary Day"
    epistle = "Hebrews 11:33-12:2"
    gospel = "Matthew 10:32-38"
    
    # Liturgical cycle calculations
    if days_since == 0:
        day_name = "Pascha Sunday (Resurrection of Christ)"
        epistle = "Acts 1:1-8"
        gospel = "John 1:1-17"
    elif weeks_since == 0:
        day_name = f"Bright {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][weekday-1]}"
        epistle = "Acts 1:12-17,21-26" if weekday == 1 else "Acts 2:14-21"
        gospel = "John 1:18-28" if weekday == 1 else "John 2:1-11"
    elif weeks_since == 1 and weekday == 6:
        day_name = "Thomas Sunday (2nd Sunday of Pascha)"
        epistle = "Acts 5:12-20"
        gospel = "John 20:19-31"
    elif weeks_since == 7 and weekday == 6:
        day_name = "Pentecost Sunday"
        epistle = "Acts 2:1-11"
        gospel = "John 7:37-52"
    elif weekday == 6:
        # Sundays after Pentecost starting after All Saints Sunday (Pentecost + 1 week)
        pentecost_sunday = pascha_ref + timedelta(weeks=7)
        sundays_after_pentecost = ((d - pentecost_sunday).days // 7)
        
        if sundays_after_pentecost == 0:
            day_name = "All Saints Sunday (1st Sunday after Pentecost)"
            epistle = "Hebrews 11:33-12:2"
            gospel = "Matthew 10:32-38, 19:27-30"
        elif sundays_after_pentecost == 5:
            # 5th Sunday after Pentecost
            day_name = "5th Sunday after Pentecost"
            epistle = "Romans 10:1-10"
            gospel = "Matthew 8:28-9:1"
        elif sundays_after_pentecost == 6:
            # 6th Sunday after Pentecost
            day_name = "6th Sunday after Pentecost"
            epistle = "Romans 12:6-14"
            gospel = "Matthew 9:1-8"
        elif sundays_after_pentecost == 7:
            # 7th Sunday after Pentecost (19.07.2026)
            day_name = "7th Sunday after Pentecost"
            epistle = "Romans 15:1-7"
            gospel = "Matthew 9:27-35"
        else:
            day_name = f"{sundays_after_pentecost}th Sunday after Pentecost"
            epistle = f"Romans {sundays_after_pentecost + 5}:1-10"
            gospel = f"Matthew {sundays_after_pentecost + 5}:1-15"

    # Fixed feasts overrides (e.g. St. Nicholas on Dec 6)
    if d.month == 12 and d.day == 6:
        day_name = "Feast of St. Nicholas the Wonderworker"
        epistle = "Hebrews 13:17-21"
        gospel = "Luke 6:17-23"

    # Old Style (Julian Calendar) calculation (-13 days for 1900-2099)
    julian_d = d - timedelta(days=13)
    german_months = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]
    old_style_date_str = f"{julian_d.day:02d}. {german_months[julian_d.month - 1]} {julian_d.year}"
    
    # Commemorations of the day
    saints_of_day = "Tagesheilige"
    if d.month == 7 and d.day == 19:
        saints_of_day = "Frommer Vater Sisoes der Große"

    german_day_name = day_name
    if "7th Sunday after Pentecost" in day_name:
        german_day_name = "7. Sonntag nach Pfingsten"

    return {
        "date": d.isoformat(),
        "old_style_date": old_style_date_str,
        "pascha_date": pascha_ref.isoformat(),
        "weeks_since_pascha": weeks_since,
        "tone": tone,
        "liturgical_day_name": day_name,
        "german_day_name": german_day_name,
        "saints_of_day": saints_of_day,
        "epistle_ref": epistle,
        "gospel_ref": gospel,
    }
