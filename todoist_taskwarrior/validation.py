import click
from . import errors, utils


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


def validate_recur(value):
    try:
        return utils.parse_recur_string(value)
    except errors.UnsupportedRecurrence as e:
        raise click.BadParameter(e)
