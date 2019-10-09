# todoist-taskwarrior

A tool for migrating Todoist tasks to Taskwarrior.

```sh
$ python -m todoist_taskwarrior.cli --help
Usage: cli.py [OPTIONS] COMMAND [ARGS]...

  Manage the migration of data from Todoist into Taskwarrior.

Options:
  --todoist-api-key TEXT  [required]
  --tw-config-file TEXT
  --debug
  --help                  Show this message and exit.

Commands:
  clean        Remove the data stored in the Todoist task cache.
  migrate      Migrate tasks from Todoist to Taskwarrior.
  synchronize  Update the local Todoist task cache.
```

## Usage

Running the tool requires that your Todoist API key is available from the
environment under the name `TODOIST_API_KEY`. The key can be found or created in
the [Todoist Integrations Settings](https://todoist.com/prefs/integrations).

The main task is `migrate` which will import all tasks. Since Todoist's internal
ID is saved with the task, subsequent runs will detect and skip duplicates.

To try things out without clobbering your normal taskwarrior install, you can point
to the taskwarrior directory in `sandbox/` by using `--tw-config-file=./sandbox/.taskrc`.

Using the `--interactive` (or `-i`) flag will prompt the user for input for each task,
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

## Other tools

* A fork that has been extended with synchronization: [webmeisterei/todoist-taskwarrior/](https://git.webmeisterei.com/webmeisterei/todoist-taskwarrior/) by [@pcdummy](https://github.com/pcdummy)

## Debugging

Running the tool in debug mode will give more detailed output:

```sh
$ python -m todoist_taskwarrior.cli --debug [command...]
```

Note: because it's a global option, it comes before the command and command options/arguments.

It can also be useful to use this in combination with the sandbox/ directory to save migrated
tasks in a well known place, and prevent messing up the global taskwarrior:

```sh
$ python -m todoist_taskwarrior.cli \
    --debug \
    --tw-config-file=./sandbox/.taskrc \
    migrate
```

## Development

### Testing

```sh
$ python -m pytest tests
```

