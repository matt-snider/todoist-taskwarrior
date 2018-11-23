import re
from datetime import datetime

""" Priorities """

PRIORITY_MAP = {1: None, 2: 'L', 3: 'M', 4: 'H'}

def parse_priority(priority):
    """ Converts a priority from Todoist to Taskwarrior.

    Todoist saves priorities as 1, 2, 3, 4, whereas Taskwarrior uses L, M, H.
    These values map very easily to eachother, as Todoist priority 1 indicates that
    no priority has been set.
    """
    return PRIORITY_MAP[priority]


""" Dates """

def parse_date(date):
    """ Converts a date from Todoist to Taskwarrior.

    Todoist: Fri 26 Sep 2014 08:25:05 +0000 (what is this called)?
    taskwarrior: ISO-8601
    """
    if not date:
        return None

    return datetime.strptime(date, '%a %d %b %Y %H:%M:%S %z').isoformat()


def parse_recur(date_string):
    """ Parses a Todoist `date_string` to extract a `recur` string for Taskwarrior.

    Field:
    - Todoist: date_string
    - taskwarrior: recur

    Examples:
    - every other `interval` `period` -> 2 `period`
    - every `interval` `period`       -> `interval` `period`
    - every `day of week`             -> weekly

    _Note_: just because Todoist sets `date_string` doesn't mean
    that the task is repeating. Mostly it just indicates that the
    user input via string and not date selector.
    """
    if not date_string:
        return
    return _match_every(date_string) or _match_weekly(date_string)


RE_INTERVAL = 'other|\d+'
RE_PERIOD = 'day|week|month|year|morning|evening|weekday|workday|last\s+day'
RE_REPEAT_EVERY = re.compile(
    f'^\s*ev(ery)?\s+((?P<interval>{RE_INTERVAL})\s+)?(?P<period>{RE_PERIOD})s?\s*$'
)

def _match_every(desc):
    match =  RE_REPEAT_EVERY.match(desc.lower())
    if not match:
        return

    interval = match.group('interval')
    period = match.group('period')

    # every other <period> -> every 2 <period>
    if interval == 'other':
        interval = 2
    # every morning -> every 1 day at 9am (the time will be stored in `due`)
    # every evening -> every 1 day at 7pm (the time will be stored in `due`)
    elif period == 'morning' or period == 'evening':
        interval = 1
        period = 'day'
    # every weekday -> weekdays
    elif period == 'weekday' or period == 'workday':
        interval = ''
        period = 'weekdays'

    return f'{interval} {period}'


RE_REPEAT_WEEKLY = re.compile(
    '^\s*every\s+(mon|monday|tues|tuesday|weds|wednesday|thurs|thursday|fri|friday|sat|saturday|sun|sunday)\s*'
)

def _match_weekly(desc):
    return ('weekly' if RE_REPEAT_WEEKLY.match(desc.lower()) else None)

