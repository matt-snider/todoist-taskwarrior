""" Validation Tests

Test argument/option validations
"""
import click
import pytest
from todoist_taskwarrior import validation


def validate(fn, value):
    """Calls the validation with None for `ctx` and `param`.

    Note: This could definitely be an issue for validations that
    use either param, but at the moment it's a simplification
    which works.
    """
    return fn(None, None, value)


def test_validate_map():
    # Simple
    assert validate(validation.validate_map, ('HELLO=WORLD',)) == {'HELLO': 'WORLD'}

    # Missing DST
    assert validate(validation.validate_map, ('HELLO=',)) == {'HELLO': None}

    # Multiple
    assert validate(validation.validate_map, ('FOO=BAR', 'BAR=BAZZ')) == {'FOO': 'BAR', 'BAR': 'BAZZ'}

    # Invalid, no '='
    with pytest.raises(click.BadParameter):
        assert validate(validation.validate_map, ('FOO',)) == None

    # Hierarchical src
    assert validate(validation.validate_map, ('foo.bar=bazz',)) == {'foo.bar': 'bazz'}
    assert validate(validation.validate_map, ('foo bar.bazz=bazz',)) == {'foo bar.bazz': 'bazz'}
