import click
import os
import sys

from taskw import TaskWarrior
from todoist.api import TodoistAPI
from . import utils, io


# This is the location where the todoist
# data will be cached.
TODOIST_CACHE = '~/.todoist-sync/'


todoist = None
taskwarrior = None


""" CLI Commands """

@click.group()
def cli():
    """Manage the migration of data from Todoist into Taskwarrior. """
    pass


@cli.command()
def synchronize():
    """Update the local Todoist task cache.

    This command accesses Todoist via the API and updates a local
    cache before exiting. This can be useful to pre-load the tasks,
    and means `migrate` can be run without a network connection.

    NOTE - the local Todoist data cache is usually located at:

        ~/.todoist-sync
    """
    with io.with_feedback('Syncing tasks with todoist'):
        todoist.sync()


@cli.command()
@click.confirmation_option(prompt=f'Are you sure you want to delete {TODOIST_CACHE}?')
def clean():
    """Remove the data stored in the Todoist task cache.

    NOTE - the local Todoist data cache is usually located at:

        ~/.todoist-sync
    """
    cache_dir = os.path.expanduser(TODOIST_CACHE)

    # Delete all files in directory
    for file_entry in os.scandir(cache_dir):
        with io.with_feedback(f'Removing file {file_entry.path}'):
            os.remove(file_entry)

    # Delete directory
    with io.with_feedback(f'Removing directory {cache_dir}'):
        os.rmdir(cache_dir)


@cli.command()
@click.option('-i', '--interactive', is_flag=True, default=False,
        help='Interactively choose which tasks to import and modify them '
             'during the import.')
@click.option('--sync/--no-sync', default=True,
        help='Enable/disable Todoist synchronization of the local task cache.')
@click.option('-p', '--map-project', metavar='SRC=DST', multiple=True,
        callback=utils.validate_map,
        help='Project names specified will be translated from SRC to DST. '
             'If DST is omitted, the project will be unset when SRC matches.')
@click.option('-t', '--map-tag', metavar='SRC=DST', multiple=True,
        callback=utils.validate_map,
        help='Tags specified will be translated from SRC to DST. '
             'If DST is omitted, the tag will be removed when SRC matches.')
@click.pass_context
def migrate(ctx, interactive, sync, map_project, map_tag):
    """Migrate tasks from Todoist to Taskwarrior.

    By default this command will synchronize with the Todoist servers
    and then migrate all tasks to Taskwarrior.

    Pass --no-sync to skip synchronization.

    Passing -i or --interactive allows more control over the import, putting
    the user into an interactive command loop. Per task, the user can decide
    whether to skip, rename, change the priority, or change the tags, before
    moving on to the next task.

    Use --map-project to change or remove the project. Project hierarchies will
    be period-delimited during conversion. For example in the following,
    'Work Errands' and 'House Errands' will be both be changed to 'errands',
    'Programming.Open Source' will be changed to 'oss', and the project will be
    removed when it is 'Taxes':
    \r
    --map-project 'Work Errands'=errands
    --map-project 'House Errands'=errands
    --map-project 'Programming.Open Source'=oss
    --map-project Taxes=

    This command can be run multiple times and will not duplicate tasks.
    This is tracked in Taskwarrior by setting and detecting the
    `todoist_id` property on the task.
    """

    if sync:
        ctx.invoke(synchronize)

    tasks = todoist.items.all()
    io.important(f'Starting migration of {len(tasks)} tasks...')
    for idx, task in enumerate(tasks):
        data = {}
        tid = data['tid'] = task['id']
        name = data['name'] = task['content']

        # Project
        p = todoist.projects.get_by_id(task['project_id'])
        project_hierarchy = [p]
        while p['parent_id']:
            p = todoist.projects.get_by_id(p['parent_id'])
            project_hierarchy.insert(0, p)

        project_name = '.'.join(p['name'] for p in project_hierarchy)
        project_name = utils.try_map(
            map_project,
            project_name
        )
        data['project'] = utils.maybe_quote_ws(project_name)

        # Priority
        data['priority'] = utils.parse_priority(task['priority'])

        # Tags
        data['tags'] = [
            utils.try_map(map_tag, todoist.labels.get_by_id(l_id)['name'])
            for l_id in task['labels']
        ]

        # Dates
        data['entry'] = utils.parse_date(task['date_added'])
        data['due'] = utils.parse_date(task['due_date_utc'])
        data['recur'] = utils.parse_recur(task['date_string'])

        io.important(f'Task {idx + 1} of {len(tasks)}: {name}')

        if check_task_exists(tid):
            io.info(f'Already exists (todoist_id={tid})')
        elif not interactive:
            add_task(**data)
        else:
            add_task_interactive(**data)


def check_task_exists(tid):
    """ Given a Taskwarrior ID, check if the task exists """
    taskwarrior_id, _ = taskwarrior.get_task(todoist_id=tid)
    return taskwarrior_id is not None


def add_task(tid, name, project, tags, priority, entry, due, recur):
    """Add a taskwarrior task from todoist task

    Returns the taskwarrior task.
    """
    with io.with_feedback(f"Importing '{name}' ({project})"):
        return taskwarrior.task_add(
            name,
            project=project,
            tags=tags,
            priority=priority,
            entry=entry,
            due=due,
            recur=recur,
            todoist_id=tid,
        )


def add_task_interactive(**task_data):
    """Interactively add tasks

    y - add task
    n - skip task
    r - rename task
    p - change priority
    t - change tags
    q - quit immediately
    ? - print help
    """
    callbacks = {
        'y': lambda: task_data,
        'n': lambda: task_data,

        # Rename
        'r': lambda: {
            **task_data,
            'name': io.prompt(
                'Set name',
                default=task_data['name'],
                value_proc=lambda x: x.strip(),
            ),
        },

        # Edit tags
        't': lambda: {
            **task_data,
            'tags': io.prompt(
                'Set tags (space delimited)',
                default=' '.join(task_data['tags']),
                show_default=False,
                value_proc=lambda x: x.split(' '),
            ),
        },

        # Edit priority
        'p': lambda: {
            **task_data,
            'priority': io.prompt(
                'Set priority',
                default='',
                show_default=False,
                type=click.Choice(['L', 'M', 'H', '']),
            ),
        },

        # Quit
        'q': lambda: exit(1),

        # Help message
        # Note: this echoes prompt help and then returns the
        # task_data unchanged.
        '?': lambda: io.warn('\n'.join([
            x.strip() for x in
            add_task_interactive.__doc__.split('\n')
        ])) or task_data,
    }

    response = None
    while response not in ('y', 'n'):
        io.task(task_data)
        response = io.prompt(
            "Import this task?",
            type=click.Choice(callbacks.keys()),
            show_choices=True,
        )

        # Execute operation
        task_data = callbacks[response]()

    if response == 'n':
        io.warn('Skipping task')
        return

    return add_task(**task_data)


""" Entrypoint """

if __name__ == '__main__':
    is_help_cmd = '-h' in sys.argv or '--help' in sys.argv
    todoist_api_key = os.getenv('TODOIST_API_KEY')
    if todoist_api_key is None and not is_help_cmd:
        io.error('TODOIST_API_KEY environment variable not specified. Exiting.')
        exit(1)

    todoist = TodoistAPI(todoist_api_key, cache=TODOIST_CACHE)

    # Create the TaskWarrior client, overriding config to
    # create a `todoist_id` field which we'll use to
    # prevent duplicates
    taskwarrior = TaskWarrior(config_overrides={
        'uda.todoist_id.type': 'string',
    })
    cli()

