# todoist-taskwarrior

A tool for migrating Todoist tasks to Taskwarrior.

## Usage

Running the tool requires that your Todoist API key is available from the
environment under the name `TODOIST_API_KEY`. The key can be found or created in
the [Todoist Integrations Settings](https://todoist.com/prefs/integrations).

The main task is `migrate` which will import all tasks. Since Todoist's internal
ID is saved with the task, subsequent runs will detect and skip duplicates:

```sh
$ python -m todoist_taskwarrior.cli migrate --help
Usage: cli.py migrate [OPTIONS]

Options:
  -i, --interactive
  --no-sync
  --help             Show this message and exit.
```

Using the `--interactive` flag will prompt the user for input for each task,
allowing the task to be modified before import:

```sh
$ python -m todoist_taskwarrior.cli migrate --interactive
Task 1 of 315: Work on an open source project

tid: 142424242
name: Work on an open source project
project: Open Source
priority:
tags:
entry: 2019-01-18T12:00:00+00:00
due: 2019-01-21T17:00:00+00:00
recur: 3 days
```

By default, `migrate` will refetch all tasks from Todoist on each run. To skip
this step and use the cached data without refetching, use the --no-sync flag.

The flags `--map-project` and `--map-tag` can be specified multiple times to translate or completely remove specific flags

```sh
$ python -m todoist_taskwarrior.cli migrate \
    --map-project Errands=chores \
    --map-project 'XYZ Corp'=work \
    --map-tag     books=reading
```

## Development

### Testing

```sh
$ python -m pytest tests
```

