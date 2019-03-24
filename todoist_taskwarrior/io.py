"""Utilities for pretty output """

import contextlib
from click import echo, prompt as cprompt, style


_success = lambda msg, bold: style(msg, fg='green', bold=bold)
_important = lambda msg, bold: style(msg, fg='blue', bold=bold)
_warning = lambda msg, bold: style(msg, fg='yellow', bold=bold)
_error = lambda msg, bold: style(msg, fg='red', bold=bold)


def info(msg, bold=False, nl=True):
    echo(msg, nl=nl)


def success(msg, bold=True, nl=True):
    echo(_success(msg, bold), nl=nl)


def important(msg, bold=True, nl=True):
    echo(_important(msg, bold), nl=nl)


def warn(msg, bold=True, nl=True):
    echo(_warning(msg, bold), nl=nl)


def error(msg, bold=True, nl=True):
    echo(_error(msg, bold), nl=nl)


def prompt(msg, **kwargs):
    return cprompt(_important(msg, True), **kwargs)


def task(task):
    """Pretty print a task to stdout """

    output = ''

    for key, value in task.items():
        key = style(key, underline=True)
        if isinstance(value, list):
            value = ' '.join(value)
        elif value is None:
            value = ''
        output += f'{key}: {value}\n'

    echo(output)


@contextlib.contextmanager
def with_feedback(description, success_status='OK', error_status='FAILED'):
    info(f'{description}... ', nl=False)
    try:
        yield
    except Exception as e:
        error(f'{error_status} ({e})')
        raise
    else:
        success(success_status)

