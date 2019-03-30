""" Validation Tests

Test argument/option validations
"""
import click
import pytest
from todoist_taskwarrior import utils


def validate(fn, value):
    """Calls the validation with None for `ctx` and `param`.

    Note: This could definitely be an issue for validations that
    use either param, but at the moment it's a simplification
    which works.
    """
    return fn(None, None, value)


def test_validate_map_project():
    # Simple
    assert validate(utils.validate_map_project, ('HELLO=WORLD',)) == {'HELLO': 'WORLD'}

    # Missing DST
    assert validate(utils.validate_map_project, ('HELLO=',)) == {'HELLO': None}

    # Multiple
    assert validate(utils.validate_map_project, ('FOO=BAR', 'BAR=BAZZ')) == {'FOO': 'BAR', 'BAR': 'BAZZ'}

    # Invalid, no '='
    with pytest.raises(click.BadParameter):
        assert validate(utils.validate_map_project, ('FOO',)) == None

