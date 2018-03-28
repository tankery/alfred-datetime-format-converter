# -*- coding: utf-8 -*-

import alfred
import calendar
import re
from delorean import utcnow, parse, epoch
from dateutil.tz import tzlocal
from dateutil.tz import tzoffset

def process(query_str):
    """ Entry point """
    value, timezone = parse_query_value(query_str)
    if value is not None:
        results = alfred_items_for_value(value, timezone)
        xml = alfred.xml(results) # compiles the XML answer
        alfred.write(xml) # writes the XML back to Alfred

def parse_query_value(query_str):
    """ Return value for the query string """
    REGEX_TIMESTAMP = re.compile(r'^(?P<time>\d+)\s*(?P<timezone>(?P<sign>[\+\-])((?P<h>\d\d)(?P<m>\d\d)|(?P<hour>\d{1,2})))?$')
    try:
        query_str = str(query_str).strip('"\' ')
        m = REGEX_TIMESTAMP.match(query_str)
        if query_str == 'now':
            return utcnow(), tzlocal()
        elif not m:
            # Parse datetime string
            d = parse(str(query_str))
            return d, d.timezone()

        time = m.group('time')
        timezone = m.group('timezone')

        d = epoch(float(time))

        # Parse timezone of query string
        if timezone:
            sign = m.group('sign')
            hours = m.group('h')
            minutes = m.group('m')
            only_hour = m.group('hour')
            h = float(hours) if hours else float(only_hour)
            m = float(minutes) if minutes else 0
            offset = h * 3600 + m * 60
            if sign == '-':
                offset = -offset
            z = tzoffset('UTC%s' % timezone, offset)
        else:
            z = tzlocal()
    except (TypeError, ValueError):
        d = None
        z = None
    return d, z

def alfred_items_for_value(value, timezone):
    """
    Given a delorean datetime object, return a list of
    alfred items for each of the results
    """

    index = 0
    results = []

    # First item as timestamp
    item_value = calendar.timegm(value.datetime.utctimetuple())
    results.append(alfred.Item(
        title=str(item_value),
        subtitle=u'UTC Timestamp',
        attributes={
            'uid': alfred.uid(index), 
            'arg': item_value,
        },
        icon='icon.png',
    ))
    index += 1

    # Various formats
    formats = [
        # 1937-01-01 12:00:27
        ("%Y-%m-%d %H:%M:%S", ''),
        # 19 May 2002 15:21:36
        ("%d %b %Y %H:%M:%S", ''), 
        # Sun, 19 May 2002 15:21:36
        ("%a, %d %b %Y %H:%M:%S", ''), 
        # 1937-01-01T12:00:27
        ("%Y-%m-%dT%H:%M:%S", ''),
        # 1996-12-19T16:39:57-0800
        ("%Y-%m-%dT%H:%M:%S%z", ''),
    ]
    for format, description in formats:
        # Shift to specific timezone for display -Tankery
        item_value = value.datetime.astimezone(timezone).strftime(format)
        results.append(alfred.Item(
            title=str(item_value),
            subtitle=description,
            attributes={
                'uid': alfred.uid(index), 
                'arg': item_value,
            },
        icon='icon.png',
        ))
        index += 1

    return results

if __name__ == "__main__":
    try:
        query_str = alfred.args()[0]
    except IndexError:
        query_str = None
    process(query_str)
