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
@click.option('-i', '--interactive', default=False)
def migrate(interactive):
    important('Starting migration...')
    # todoist.sync()
    tasks = todoist.items.all()

    info(f'Todoist tasks: {len(todoist.items.all())}')
    for task in todoist.items.all():
        tid = task['id']
        name = task['content']
        info(f'Importing task #{tid}: {name}')
        taskwarrior.task_add(name)

""" Utils """

def important(msg):
    click.echo(click.style(msg, fg='blue', bold=True))


def info(msg):
    click.echo(msg)


""" Entrypoint """

if __name__ == '__main__':
    cli()

