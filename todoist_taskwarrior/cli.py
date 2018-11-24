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
    important(f'Starting migration of {len(tasks)}...\n')
    for idx, task in enumerate(tasks):
        data = {}
        data['tid'] = task['id']
        data['name'] = task['content']
        data['project'] = todoist.projects.get_by_id(task['project_id'])['name']
        data['priority'] = utils.parse_priority(task['priority'])
        data['tags'] = [
            todoist.labels.get_by_id(l_id)['name']
            for l_id in task['labels']
        ]
        data['entry'] = utils.parse_date(task['date_added'])
        data['due'] = utils.parse_date(task['due_date_utc'])
        data['recur'] = utils.parse_recur(task['date_string'])

        if not interactive:
            add_task(**data)
        else:
            task_prompt(idx + 1, len(tasks), **data)


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


def task_prompt(task_num, tasks_total, **task_data):
    """Interactively add tasks

    y - add task
    n - skip task
    r - rename task
    p - change priority
    t - change tags
    ? - print help
    """
    callbacks = {
        'y': lambda: task_data,
        'n': lambda: task_data,

        # Rename
        'r': lambda: {
            **task_data,
            'name': name_prompt(task_data['name']),
        },

        # Edit tags
        't': lambda: {
            **task_data,
            'tags': tags_prompt(task_data['tags']),
        },

        # Edit priority
        'p': lambda: {
            **task_data,
            'priority': priority_prompt(task_data['priority']),
        },

        # Help message
        '?': lambda: task_prompt_help() or task_data,
    }

    response = None
    while response not in ('y', 'n'):
        click.echo(important_msg(f'Task {task_num} of {tasks_total}'))
        prompt_text = (
            stringify_task(**task_data)
            + important_msg(f"\nImport this task?")
        )
        response = click.prompt(
            prompt_text,
            type=click.Choice(callbacks.keys()),
            show_choices=True,
        )

        # Execute operation
        task_data = callbacks[response]()

    if response == 'n':
        error('Skipping task\n')
        return

    return add_task(**task_data)


def task_prompt_help():
    lines = [
        x.strip() for x in
        task_prompt.__doc__.split('\n')
    ]
    error('\n'.join(lines))


def tags_prompt(tags):
    return click.prompt(
        important_msg('Set tags'),
        default=' '.join(tags),
        show_default=False,
        value_proc=lambda x: x.split(' ')
    )


def priority_prompt(priority):
    return click.prompt(
        important_msg('Set priority'),
        default='',
        type=click.Choice([None, 'L', 'M', 'H']),
        value_proc=lambda x: None if '' else x,
        show_default=False,
    )


def name_prompt(name):
    return click.prompt(
        important_msg('Set name'),
        default=name,
        value_proc=lambda x: x.strip()
    )


""" Output Utils """

def important(msg, **kwargs):
    click.echo(important_msg(msg), **kwargs)

def important_msg(msg):
    return click.style(msg, fg='blue', bold=True)

def info(msg, **kwargs):
    click.echo(msg, **kwargs)

def success(msg, **kwargs):
    click.echo(click.style(msg, fg='green', bold=True))

def error(msg, **kwargs):
    click.echo(click.style(msg, fg='red', bold=True))

def stringify_task(**task_data):
    string = ''
    for key, value in task_data.items():
        key = click.style(key, underline=True)
        if isinstance(value, list):
            value = ' '.join(value)
        elif value is None:
            value = ''
        string += f'{key}: {value}\n'
    return string


""" Entrypoint """

if __name__ == '__main__':
    is_help_cmd = '-h' in sys.argv or '--help' in sys.argv
    todoist_api_key = os.getenv('TODOIST_API_KEY')
    if todoist_api_key is None and not is_help_cmd:
        exit('TODOIST_API_KEY environment variable not specified. Exiting.')

    todoist = TodoistAPI(todoist_api_key)
    taskwarrior = TaskWarrior()
    cli()

