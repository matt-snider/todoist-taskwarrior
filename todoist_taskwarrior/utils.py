import click
import re
from datetime import datetime
from .errors import UnsupportedRecurrence

""" Validation """

def validate_map(ctx, param, value):
    map_project = {}
    for mapping in value:
        try:
            src, dst = mapping.split('=', 2)
        except ValueError:
            raise click.BadParameter('--map-project needs to be of the form SRC=DST')

        if dst == '':
            dst = None
        map_project[src] = dst
    return map_project


""" Mappings """

def try_map(m, value):
    """Maps/translates `value` if it is present in `m`. """
    if value in m:
        return m[value]
    else:
        return value


""" Priorities """

PRIORITY_MAP = {1: None, 2: 'L', 3: 'M', 4: 'H'}

def parse_priority(priority):
    """ Converts a priority from Todoist to Taskwarrior.

    Todoist saves priorities as 1, 2, 3, 4, whereas Taskwarrior uses L, M, H.
    These values map very easily to eachother, as Todoist priority 1 indicates that
    no priority has been set.
    """
    return PRIORITY_MAP[int(priority)]

""" Strings """

def maybe_quote_ws(value):
    """Surrounds a value with single quotes if it contains whitespace. """
    if any(x == ' ' or x == '\t' for x in value):
        return "'" + value + "'"
    return value


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
    # Normalize:
    # - trim leading, trailing, and, duplicate spaces
    # - convert to lowercase
    date_string = ' '.join(date_string.lower().strip().split())
    result = (
        _recur_single_cycle(date_string) or
        _recur_multi_cycle(date_string) or
        _recur_day_of_week(date_string) or
        _recur_day_of_month(date_string) or
        _recur_special(date_string)
    )
    if not result:
        raise UnsupportedRecurrence(date_string)
    return result


# Atoms
_PERIOD = r'(?P<period>hour|day|week|month|year)s?'
_EVERY = r'ev(ery)?'
_CYCLES = r'((?P<cycles>\d+)(st|nd|rd|th)?)'
_SIMPLE = r'(?P<simple>daily|weekly|monthly|yearly)'
_DOW = (
    r'((?P<dayofweek>('
    r'mo(n(day)?)?'
    r'|tu(e(s(day)?)?)?'
    r'|we(d(s|(nes(day)?)?)?)?|th(u(rs(day)?)?)?'
    r'|fr(i(day)?)?'
    r'|sa(t(urday)?)?'
    r'|su(n(day)?)?'
    r')))'
)

# A single cycle recurrence is one of:
# - daily, weekly, monthly, yearly
# - every day, every week, every month, every year
# - every 1 day, every 1 week, every 1 month, every 1 year
RE_SINGLE_CYCLE = re.compile(
    fr'^(({_EVERY}\s(1\s)?{_PERIOD})|{_SIMPLE})$'
)

# A multi cycle recurrence is of the form: every N <period>s
RE_MULTI_CYCLE = re.compile(
    fr'^{_EVERY}\s({_CYCLES}|other)\s{_PERIOD}$'
)


# A day of week recurrence is of the form:
# - every (monday | tuesday | ...)
# - every Nth (monday | tuesday | ...)
RE_EVERY_DOW = re.compile(
    fr'^{_EVERY}\s({_CYCLES}\s)?{_DOW}$'
)


# A day of month recurrence is of the form: every Nth
RE_EVERY_DOM = re.compile(
    fr'^{_EVERY}\s{_CYCLES}$'
)


# Other patterns that don't fit in with the others
RE_SPECIAL = re.compile(
    fr'^{_EVERY}\s(?P<label>morning|evening|weekday|workday|last\sday)$'
)


PERIOD_TO_SIMPLE = {
    'hour': 'hourly',
    'day': 'daily',
    'week': 'weekly',
    'month': 'monthly',
    'year': 'yearly',
}


def _recur_single_cycle(date_string):
    match = RE_SINGLE_CYCLE.match(date_string)
    if not match:
        return None

    groups = match.groupdict()
    if groups['simple']:
        return match.group('simple')

    period = match.group('period')
    return PERIOD_TO_SIMPLE[period]


def _recur_multi_cycle(date_string):
    match =  RE_MULTI_CYCLE.match(date_string)
    if not match:
        return

    groups = match.groupdict()
    period = groups['period']
    if groups['cycles']:
        cycles = groups['cycles']
    else:
        # 'other' matched
        cycles = 2

    return f'{cycles} {period}s'


def _recur_day_of_week(date_string):
    match =  RE_EVERY_DOW.match(date_string)
    if not match:
        return

    groups = match.groupdict()
    day_of_week = groups['dayofweek']
    if groups['cycles']:
        cycles = groups['cycles']
    else:
        cycles = 1
    return 'weekly' if cycles == 1 else f'{cycles} weeks'


def _recur_day_of_month(date_string):
    match =  RE_EVERY_DOM.match(date_string)
    if not match:
        return
    return 'monthly'


def _recur_special(date_string):
    match =  RE_SPECIAL.match(date_string)
    if not match:
        return

    label = match.group('label')
    if label == 'morning' or label == 'evening':
        return 'daily'
    elif label == 'weekday' or label == 'workday':
        return 'weekdays'
    elif label == 'last day':
        return 'monthly'

