import click
import re
from datetime import datetime
from taskw import TaskWarrior
from todoist.api import TodoistAPI

todoist = None
taskwarrior = None

""" CLI Commands """

@click.group()
@click.option('--todoist-api-key', envvar='TODOIST_API_KEY', required=True)
def cli(todoist_api_key):
    # Just do some initialization
    global todoist
    global taskwarrior
    todoist = TodoistAPI(todoist_api_key)
    taskwarrior = TaskWarrior()


@cli.command()
@click.option('-i', '--interactive', is_flag=True, default=False)
@click.option('--no-sync', is_flag=True, default=False)
def migrate(interactive, no_sync):
    if not no_sync:
        important('Syncing tasks with todoist... ', nl=False)
        todoist.sync()
        success('OK')

    tasks = todoist.items.all()
    important(f'Starting migration of {len(tasks)}...')
    for task in todoist.items.all():
        tid = task['id']
        name = task['content']
        project = todoist.projects.get_by_id(task['project_id'])['name']
        priority = taskwarrior_priority(task['priority'])
        tags = [
            todoist.labels.get_by_id(l_id)['name']
            for l_id in task['labels']
        ]
        entry = taskwarrior_date(task['date_added'])
        due = taskwarrior_date(task['due_date_utc'])
        recur = taskwarrior_recur(task['date_string'])

        if interactive and not click.confirm(f"Import '{name}'?"):
            continue

        add_task(tid, name, project, tags, priority, entry, due, recur)


def add_task(tid, name, project, tags, priority, entry, due, recur):
    """Add a taskwarrior task from todoist task

    Returns the taskwarrior task.
    """
    info(f"Importing '{name}' ({project}) - ", nl=False)
    try:
        tw_task = taskwarrior.task_add(name, project=project, tags=tags,
                priority=priority, entry=entry, due=due, recur=recur)
    except:
        error('FAILED')
    else:
        success('OK')
        return tw_task


""" Utils """

def important(msg, **kwargs):
    click.echo(click.style(msg, fg='blue', bold=True), **kwargs)

def info(msg, **kwargs):
    click.echo(msg, **kwargs)

def success(msg, **kwargs):
    click.echo(click.style(msg, fg='green', bold=True))

def error(msg, **kwargs):
    click.echo(click.style(msg, fg='red', bold=True))

PRIORITIES = {1: None, 2: 'L', 3: 'M', 4: 'H'}
def taskwarrior_priority(priority):
    """Converts a priority from Todiost (1-4) to taskwarrior (None, L, M, H) """
    return PRIORITIES[priority]

def taskwarrior_date(date):
    """ Converts a date from Todoist to taskwarrior

    Todoist: Fri 26 Sep 2014 08:25:05 +0000 (what is this called)?
    taskwarrior: ISO-8601
    """
    if not date:
        return None
    return datetime.strptime(date, '%a %d %b %Y %H:%M:%S %z').isoformat()


def taskwarrior_recur(desc):
    """ Converts a repeating interval from Todoist to taskwarrior.

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
    if not desc:
        return
    return _match_every(desc) or _match_weekly(desc)


RE_INTERVAL = 'other|\d+'
RE_PERIOD = 'day|week|month|year'
RE_REPEAT_EVERY = re.compile(
    f'^\s*every\s+((?P<interval>{RE_INTERVAL})\s+)?(?P<period>{RE_PERIOD})s?\s*$'
)

def _match_every(desc):
    match =  RE_REPEAT_EVERY.match(desc.lower())
    if not match:
        return

    interval = match.group('interval')
    period = match.group('period')
    if interval == 'other':
        interval = 2
    return f'{interval} {period}'


RE_REPEAT_WEEKLY = re.compile(
    '^\s*every\s+(mon|monday|tues|tuesday|weds|wednesday|thurs|thursday|fri|friday|sat|saturday|sun|sunday)\s*'
)

def _match_weekly(desc):
    return ('weekly' if RE_REPEAT_WEEKLY.match(desc.lower()) else None)


""" Entrypoint """

if __name__ == '__main__':
    cli()

