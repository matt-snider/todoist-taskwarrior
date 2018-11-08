import click
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
        creation_date = taskwarrior_date(task['date_added'])

        if interactive and not click.confirm(f"Import '{name}'?"):
            continue

        add_task(tid, name, project, tags, priority, creation_date)


def add_task(tid, name, project, tags, priority, creation_date):
    """Add a taskwarrior task from todoist task

    Returns the taskwarrior task.
    """
    info(f"Importing '{name}' ({project}) - ", nl=False)
    try:
        tw_task = taskwarrior.task_add(name, project=project, tags=tags,
                priority=priority, entry=creation_date)
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
    """ Converts a date from Todist to taskwarrior

    Todoist: Fri 26 Sep 2014 08:25:05 +0000 (what is this called)?
    taskwarrior: ISO-8601
    """
    return datetime.strptime(date, '%a %d %b %Y %H:%M:%S %z').isoformat()

""" Entrypoint """

if __name__ == '__main__':
    cli()

