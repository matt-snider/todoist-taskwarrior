import click
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
        project = todoist.projects.get_by_id(task['project_id'])

        if interactive and not click.confirm(f"Import '{name}'?"):
            continue

        add_task(tid, name, project)


def add_task(tid, name, project):
    """Add a taskwarrior task from todoist task

    Returns the taskwarrior task.
    """
    project_name = project['name'] if project else None
    info(f"Importing '{name}' ({project_name}) - ", nl=False)
    try:
        tw_task = taskwarrior.task_add(name, project=project_name)
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
    cli()

