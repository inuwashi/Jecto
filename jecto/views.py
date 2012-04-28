# Views for Jecto

from datetime import date as Date, timedelta as TimeDelta

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response

from jecto.models import *

# Helpers

def spew(obj):
    return HttpResponse(repr(obj))

def parseDate(year, month, day):
    try:
        year = int(year)
        month = int(month)
        day = int(day)
        return Date(year, month, day)
    except (ValueError, TypeError), t:
        raise ValueError(t)

def injectionHistory(startDay, numDays=30):
    earliestDay = startDay + TimeDelta(days = -numDays)
    relevantInjections = Injection.objects.filter(date__lte = startDay).filter(date__gt = earliestDay)
    return relevantInjections.order_by("date").reverse()  # Newest to oldest

def datesToColors(dates):
    """
    Returns a list of (Date, color) ordered by Date.
    """
    allDates = dates
    dates = [date for date in allDates if date is not None]
    addNones = [(None, "#CCF")] * (len(allDates) - len(dates))
    dates.sort()
    if not dates: return addNones
    if len(dates) == 1: return addNones + [(dates[0], "#F00")]
    lowest = dates[0]
    highest = dates[-1]
    dateRange = float((highest - lowest).days)
    res = []
    for day in dates:
        unTensity = int(255.0 * (highest - day).days / dateRange)
        color = "#FF%s" % (hex(unTensity)[-2:] * 2)
        res.append((day, color))
    return addNones + res


# Actual views

def home(request):
    """
    Redirect via HTTP with generic parameters to the main view.
    """
    return HttpResponseRedirect(Date.today().strftime("history/%Y/%m/%d"))

def history(request, year, month, day):
    """
    Injection History
    Output: Use month.html template and render a dictionary:
    keys are the last 30 days (including input)
    values are the injection for that day or None
    """
    try:
        startDay = parseDate(year, month, day)
    except ValueError, t:
        #return "main failed: " + repr(t)
        startDay = Date.today()

    numDays = 30  # XXX Where does this belong?

    # Collect dates
    backOneDay = TimeDelta(days = -1)
    days = [startDay]
    res = { startDay:None }  # day -> injection or None
    for i in range(numDays - 1):
        day = days[-1] + backOneDay
        res[day] = None
        days.append(day)

    # Update the days that have injections
    injections = injectionHistory(startDay)
    for injection in injections:
        res[injection.date] = injection

    # Render and return the result
    res = sorted(res.items(), reverse=True)
    ctx = dict(history=res)
    return render_to_response("history.html", ctx)

def zones(request, year, month, day):
    """
    Zones View
    Output: List of (zone, last injection date or None, color code)
    ordered by weight -- start with one greater than the latest injection's weight, go up and then wrap around.
    """
    try:
        startDay = parseDate(year, month, day)
    except ValueError, t:
        return spew("zones failed: " + repr(t))

    allZones = list(Zone.objects.all().order_by("weight", "name"))

    zoneSet = set()
    injectedZones = []
    todayZone = []
    injections = injectionHistory(startDay)  # Newest to oldest
    for injection in injections:
        zone = injection.zone
        name = zone.name
        if injection.date == startDay:
            zoneSet.add(name)
            todayZone.append((injection.date, zone))
        elif name not in zoneSet:
            zoneSet.add(name)
            injectedZones.append((injection.date, zone))
    injectedZones.reverse()     # Oldest to newest
    dateToColor = dict(datesToColors([None] + [date for date, zone in injectedZones]))
    dateToColor[startDay] = "#FF0"

    negZones = []
    unusedZones = []
    for zone in allZones:
        if zone.name in zoneSet: continue
        if zone.weight < 0:
            negZones.append((None, zone))
        else:
            unusedZones.append((None, zone))

    res = [(zone, date, dateToColor[date]) for date, zone in todayZone + unusedZones + injectedZones + negZones]

    ctx = dict(zones=res, date=startDay)
    return render_to_response("zones.html", ctx)

def sections(request, year, month, day, zoneId):
    """
    Get Sections
    Output: List of (injection, color code)
    ordered by last injection date ascending (oldest first)
    """
    try:
        startDay = parseDate(year, month, day)
    except ValueError, t:
        return spew("sections failed on date: " + repr(t))

    try:
        zone = Zone.objects.get(id=zoneId)
    except Zone.DoesNotExist, t:
        return spew("sections failed on zone: " + repr(t))

    allZoneCoords = [(y, x) for x in range(zone.width) for y in range(zone.height)]
    coordMap = {}               # (y, x) --> info for most recent injection
    for coords in allZoneCoords:
        coordMap[coords] = None

    injections = injectionHistory(startDay, numDays=60).filter(zone = zone)  # Newest to oldest
    for injection in injections:
        coords = injection.posY, injection.posX
        if coordMap[coords] is None:
            coordMap[coords] = injection
        else:
            # We already have a newer injection recorded for this section
            pass

    dates = []
    for injection in coordMap.values():
        if injection is not None and injection.date != startDay:
            dates.append(injection.date)
        else:
            dates.append(None)
    dateToColor = dict(datesToColors(dates))
    dateToColor[startDay] = "#FF0"

    res = []
    for y in range(zone.height):
        row = []
        for x in range(zone.width):
            injection = coordMap[y, x]
            if injection is None:
                date = None
            else:
                date = injection.date
            item = dict(injection = injection,
                        color = dateToColor[date],
                        posX = x,
                        posY = y)
            row.append(item)
        res.append(row)
    ctx = dict(items=res, date=startDay, zone=zone)
    return render_to_response("sections.html", ctx)

def inject(request, year, month, day, zoneId, posX, posY):
    """
    Add/insert an injection
    Output: OK or verbose error
    """
    try:
        injectDay = parseDate(year, month, day)
    except ValueError, t:
        return spew("inject failed on date: " + repr(t))
    try:
        zone = Zone.objects.get(id=zoneId)
    except Zone.DoesNotExist, t:
        return spew("inject failed on zone: " + repr(t))
    try:
        posX = int(posX)
        posY = int(posY)
        if not (0 <= posX < zone.width) or not (0 <= posY < zone.height):
            raise ValueError("Invalid section coords (%s, %s)" % (posX, posY))
    except (KeyError, ValueError), t:
        return spew("inject failed on section: " + repr(t))

    try:
        injection = Injection.objects.get(date=injectDay)
        injection.zone = zone
        injection.posX = posX
        injection.posY = posY
        disposition = "Updated"
    except Injection.DoesNotExist:
        injection = Injection(date=injectDay, zone=zone, posX=posX, posY=posY)
        disposition = "Inserted"

    injection.save()

    return HttpResponse("OK %s %s %s\n<a href='/'>continue</a>" % (disposition, injection.id, injection.zone.name))

