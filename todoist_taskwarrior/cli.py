import click
import os
import sys

from taskw import TaskWarrior
from todoist.api import TodoistAPI
from . import utils

todoist = None
taskwarrior = None


""" CLI Commands """

@click.group()
def cli():
    pass


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
        priority = utils.parse_priority(task['priority'])
        tags = [
            todoist.labels.get_by_id(l_id)['name']
            for l_id in task['labels']
        ]
        entry = utils.parse_date(task['date_added'])
        due = utils.parse_date(task['due_date_utc'])
        recur = utils.parse_recur(task['date_string'])

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


""" Entrypoint """

if __name__ == '__main__':
    is_help_cmd = '-h' in sys.argv or '--help' in sys.argv
    todoist_api_key = os.getenv('TODOIST_API_KEY')
    if todoist_api_key is None and not is_help_cmd:
        exit('TODOIST_API_KEY environment variable not specified. Exiting.')

    todoist = TodoistAPI(todoist_api_key)
    taskwarrior = TaskWarrior()
    cli()

