""" Recur Tests

Tests parsing `recur` strings from Todoist `date_string`s
"""
import pytest
from todoist_taskwarrior import utils
from todoist_taskwarrior import errors


def test_parse_due_object():
    assert utils.parse_recur(None) == None
    assert utils.parse_recur({'is_recurring': False}) == None
    assert utils.parse_recur({'is_recurring': True, 'string': 'every day'}) == 'daily'
    assert utils.parse_recur({'is_recurring': True, 'string': 'every week'}) == 'weekly'
    assert utils.parse_recur({'is_recurring': True, 'string': 'every month'}) == 'monthly'


def test_hourly():
    assert utils.parse_recur_string('every hour') == 'hourly'
    assert utils.parse_recur_string('every 1 hour') == 'hourly'
    assert utils.parse_recur_string('every 2 hour') == '2 hours'
    assert utils.parse_recur_string('every 2 hours') == '2 hours'
    assert utils.parse_recur_string('every 3 hour') == '3 hours'
    assert utils.parse_recur_string('every 3 hours') == '3 hours'


def test_every_n_days():
    assert utils.parse_recur_string('daily') == 'daily'
    assert utils.parse_recur_string('every day') == 'daily'
    assert utils.parse_recur_string('every 1 day') == 'daily'
    assert utils.parse_recur_string('every 1 days') == 'daily'
    assert utils.parse_recur_string('every other day') == '2 days'
    assert utils.parse_recur_string('every 3 day') == '3 days'
    assert utils.parse_recur_string('every 3 days') == '3 days'

    # With time (which should be ignored since it's encoded in due_date anyways)
    assert utils.parse_recur_string('every day at 19:00') == 'daily'


def test_special():
    # Indicates daily at 9am - the time is saved in the `due` property
    assert utils.parse_recur_string('every morning') == 'daily'
    # Indicates daily at 7pm - the time is saved in the `due` property
    assert utils.parse_recur_string('every evening') == 'daily'

    # Weekdays
    assert utils.parse_recur_string('every weekday') == 'weekdays'
    assert utils.parse_recur_string('every workday') == 'weekdays'


def test_weekly():
    assert utils.parse_recur_string('every week') == 'weekly'
    assert utils.parse_recur_string('every 1 week') == 'weekly'
    assert utils.parse_recur_string('every 1 weeks') == 'weekly'
    assert utils.parse_recur_string('weekly') == 'weekly'
    assert utils.parse_recur_string('every other week') == '2 weeks'
    assert utils.parse_recur_string('every 3 week') == '3 weeks'
    assert utils.parse_recur_string('every 3 weeks') == '3 weeks'


def test_monthly():
    assert utils.parse_recur_string('every month') == 'monthly'
    assert utils.parse_recur_string('every 1 month') == 'monthly'
    assert utils.parse_recur_string('every 1 months') == 'monthly'
    assert utils.parse_recur_string('monthly') == 'monthly'
    assert utils.parse_recur_string('every other month') == '2 months'
    assert utils.parse_recur_string('every 2 months') == '2 months'

    # ordinal
    assert utils.parse_recur_string('every 2nd month') == '2 months'
    assert utils.parse_recur_string('every 3rd month') == '3 months'


DAYS_OF_WEEK = [
    # Monday
    'mo',
    'mon',
    'monday',

    # Tuesday
    'tu',
    'tue',
    'tues',
    'tuesday',

    # Wednesday
    'we',
    'wed',
    'weds',
    'wednesday',

    # Thursday
    'th',
    'thu',
    'thurs',
    'thursday',

    # Friday
    'fr',
    'fri',
    'friday',

    # Saturday
    'sa',
    'sat',
    'saturday',

    # Sunday
    'su',
    'sun',
    'sunday',
]


@pytest.mark.parametrize('dow', DAYS_OF_WEEK)
def test_every_dow_has_weekly_recurrence(dow):
    """ The actual day should be indicated in the `due` property, so here
        we just need to ensure that the recurrence is correct.
    """
    assert utils.parse_recur_string(f'ev {dow}') == 'weekly'
    assert utils.parse_recur_string(f'every {dow}') == 'weekly'
    assert utils.parse_recur_string(f'every other {dow}') == '2 weeks'

    # With time (which should be ignored since it's encoded in due_date anyways)
    assert utils.parse_recur_string(f'every {dow} at 17:00') == 'weekly'

@pytest.mark.parametrize('ordinal', [
    ('2', 2),
    ('2nd', 2),
    ('3', 3),
    ('3rd', 3),
    ('4', 4),
    ('4th', 4),
])
@pytest.mark.parametrize('dow', DAYS_OF_WEEK)
def test_every_dow_ordinal_recurrence(ordinal, dow):
    ordinal, expected = ordinal
    assert utils.parse_recur_string(f'ev {ordinal} {dow}') == f'{expected} weeks'
    assert utils.parse_recur_string(f'every {ordinal} {dow}') == f'{expected} weeks'


def test_day_of_week_short_forms():
    assert utils.parse_recur_string('every mo') == 'weekly'
    assert utils.parse_recur_string('every mon') == 'weekly'

    assert utils.parse_recur_string('every tu') == 'weekly'
    assert utils.parse_recur_string('every tue') == 'weekly'
    assert utils.parse_recur_string('every tues') == 'weekly'

    assert utils.parse_recur_string('every we') == 'weekly'
    assert utils.parse_recur_string('every wed') == 'weekly'
    assert utils.parse_recur_string('every weds') == 'weekly'

    assert utils.parse_recur_string('every th') == 'weekly'
    assert utils.parse_recur_string('every thu') == 'weekly'
    assert utils.parse_recur_string('every thurs') == 'weekly'

    assert utils.parse_recur_string('every fr') == 'weekly'
    assert utils.parse_recur_string('every fri') == 'weekly'

    assert utils.parse_recur_string('every sa') == 'weekly'
    assert utils.parse_recur_string('every sat') == 'weekly'

    assert utils.parse_recur_string('every su') == 'weekly'
    assert utils.parse_recur_string('every sun') == 'weekly'


def test_day_of_month():
    """ The actual due date should be indicated by the `due` property, so here
    we just need to ensure a monthly recurrence.
    """
    assert utils.parse_recur_string('every 1st') == 'monthly'
    assert utils.parse_recur_string('every 2nd') == 'monthly'
    assert utils.parse_recur_string('every 3rd') == 'monthly'
    assert utils.parse_recur_string('every 4th') == 'monthly'
    assert utils.parse_recur_string('every 21st') == 'monthly'
    assert utils.parse_recur_string('every 22nd') == 'monthly'
    assert utils.parse_recur_string('every 23rd') == 'monthly'
    assert utils.parse_recur_string('every 24th') == 'monthly'
    assert utils.parse_recur_string('every last day') == 'monthly'


def test_annually():
    assert utils.parse_recur_string('every year') == 'yearly'
    assert utils.parse_recur_string('every 2 year') == '2 years'
    assert utils.parse_recur_string('every 2 years') == '2 years'


def test_unsupported():
    with pytest.raises(errors.UnsupportedRecurrence):
        utils.parse_recur_string('every mon,tues,weds')

    with pytest.raises(errors.UnsupportedRecurrence):
        utils.parse_recur_string('every monday,tuesday,wednesday')

