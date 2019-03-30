""" Priority Tests

Test conversions between Todoist and Taskwarrior priorities.
"""
import pytest
from todoist_taskwarrior import utils


def test_priorities():
    assert utils.parse_priority(1) == None
    assert utils.parse_priority(2) == 'L'
    assert utils.parse_priority(3) == 'M'
    assert utils.parse_priority(4) == 'H'

def test_priorities_str():
    assert utils.parse_priority('1') == None
    assert utils.parse_priority('2') == 'L'
    assert utils.parse_priority('3') == 'M'
    assert utils.parse_priority('4') == 'H'

