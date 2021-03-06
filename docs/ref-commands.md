---
id: commands
title: Commands
---

<AUTOGENERATED_TABLE_OF_CONTENTS>


## General Behavior

Some of the commands that can potentially affect the entire set of languages and
projects share common flags.

### Narrowing Down Scope

#### `--language`, `--project`

With the `--language` and `--project` parameters, the scope of some commands can
be narrowed down so that they only have effect on specific languages and/or
projects of the server.

### Synchronous mode

#### `--no-rq`

Some of the commands work asynchronously and will schedule jobs to RQ workers,
rather than running them in the command process. You can change this behaviour
using the `--no-rq` command line option.

This can be useful for running zing commands in bash scripts or automating
installation/upgrade/migration.

#### `--noinput`

If there are RQ workers running, the command will ask for confirmation before
proceeding. This can be overridden using the `--noinput` flag, in
which case the command will run even if there are.


## Reference


## File Synchronization

These commands perform tasks related to file synchronization.

### `sync_stores`

Save all translations currently in the database to the file system, thereby
bringing the files under the `ZING_TRANSLATION_DIRECTORY` directory
in sync with the Zing database. Disabled projects are skipped.

You must run this command before taking backups or running scripts that modify
the translation files directly on the file system, otherwise you might miss out
on translations that are in the database but not yet saved to disk. In
other words, **translations are saved to disk only when you explicitly do
so** using this command.

For every file being synced, the in-DB `Store` will be updated to
reflect the latest revision across the units in the file at the time of
syncing. This allows Zing to make optimizations when syncing and
updating files, ignoring files that haven't changed.

The default behavior of `sync_stores` can be altered by specifying these
parameters:

#### `--force`

Synchronizes files even if nothing changed in the database.

#### `--overwrite`

Copies the current state of the DB stores (not only translations, but also
metadata) regardless if they have been modified since the last sync or not. This
operation will (over)write existing on-disk files.

#### `--skip-missing`

Ignores files missing on disk, and no new files will be created.


### `update_stores`

Load translation files currently on the file system into the database, thereby
bringing the Zing database in sync with the files under the
`ZING_TRANSLATION_DIRECTORY` directory.

Zing will not detect changes in the file system on its own. This is the opposite
of `sync_stores`.

> Note: Disabled projects are skipped.

It also discovers new units, files and translation projects that were added on
disk:

- Projects that exist in the DB but ceased to exist on disk will
  be **disabled** (not deleted). If a project is recovered on disk it can be
  enabled via the admin UI only.

- Translation projects will be scanned for new files and
  directories. In-DB files and directories that no longer exist on disk
  will be **marked as obsolete**. Also any in-DB directory will be
  **marked as obsolete** if this directory is empty or contains empty
  directories only.

- In-DB stores will be updated with the contents of the on-disk files.
  New units will be **added** to the store, units that ceased to exist
  will be **marked as obsolete**. Translations that were updated on-disk
  will be reflected in the DB.

You must run this command after running scripts that modify translation files
directly on the file system.

`update_stores` accepts several options:

#### `--force`

Updates in-DB translations even if the on-disk file hasn't been changed
since the last sync operation.

#### `--overwrite`

Mirrors the on-disk contents of the file. If there have been changes in
the database **since the last sync operation**, these will be
overwritten.

> If files on the file system are corrupt, translations might be deleted from
> the database. Handle with care!


### `revision`

Print the latest revision number.

The revision is a common system-wide counter for units, and is used to determine
which units need synchronization.

The counter is incremented with every translation action made from the browser.
Zero length units that have been auto-translated also increment the unit
revision.

#### `--restore`

The revision counter is stored in the database but also in cache for faster
retrieval. If for some reason the revision counter was removed or got
corrupted, passing the `--restore` flag to the command will restore the
counter's value based on the revision data available on the relational DB
backend. You shouldn't need to ever run this, but if for instance you deleted
your cache you will need to restore the counter to ensure correct operation.


## Translation Memory

These commands allow you to setup and manage [Translation
Memory](feat-editor.md#translation-memory).


### `update_tmserver`

Updates the TM server contents to reflect what the database of translations
contains.

By default, the command indexes new translations only.

#### `--refresh`

Use the `--refresh` option to index new translations and also update existing
translations that have been changed.

#### `--rebuild`

Use the `--rebuild` option to completely remove the TM and rebuild it from
scratch, indexing all existing translations.

#### `--include-disabled-projects`

By default, translations from disabled projects are not indexed in the TM, and
this can be changed by specifying `--include-disabled-projects`.

#### `--dry-run`

Use the `--dry-run` option to see how many units would be indexed. The TM will
be left unchanged.


## Reports and Invoicing


### `generate_invoices`

Generates invoices out of user activity. Before using it, please check the
[documentation on invoices](feat-invoices.md) to learn more about how it works
and how to configure it.

Running `generate_invoices` without any arguments will generate invoices for
the previous month. A specific month can be specified by passing the
`--month=<YYYY-MM>` argument. Invoices will be generated under the
`$ZING_INVOICES_DIRECTORY/<YYYY-MM>/` folder.

The list of users for whom invoices will be generated can be limited to a subset
of the configured users by passing the `--users <user1 user2... userN>`
argument. Note all users defined in the configuration need to exist, otherwise
the command will complain and create no invoices at all.

Optionally a report can be created in JSON format by passing the
`--generate-report` flag. The report includes the date and time the invoices
were generated at, as well as a list of individual invoice information, with
their identifier, amount and extra metadata from the configuration file.

Invoices will also be sent by email if the `--send-emails` flag is set. There
are a couple more options to control how email will be sent:

  * `--bcc`: allows manually specifying BCC recipients.
  * `--override-to`: manually overrides who the invoice will be sent to. This
    is a debugging feature, and it omits sending copies to anyone plus enables
    extra output in email messages when using the default templates.


## Server Management


### `refresh_stats`

Recalculates all file statistics for active projects, ensuring they are
up-to-date.

A background process will create a task for every file to make sure calculated
statistics data is up to date. When the task for a file completes then further
tasks will be created for the files' parents.

> When users open a page that needs to
display stats but they haven't been calculated yet, a banner will be displayed
indicating that stats are out-of-date and in the process of being calculated.

#### `--include-disabled-projects`

By default, statistics for disabled projects are not calculated, and this can be
changed by specifying `--include-disabled-projects`.


### `retry_failed_jobs`

Requeue failed RQ jobs.

Background RQ jobs can fail for various reasons. To push them back into the
queue you can run this command.

Examine the RQ worker logs for tracebacks before trying to requeue your jobs.


### `calculate_checks`

This command will create a background job to go through all units and
recalculate quality checks. This will go through units in disabled projects too.

`calculate_checks` will flush existing caches and update the quality
checks cache.

This command is rarelly need. It's needed only when new quality checks are
available as part of an update.

The time it takes to complete the whole process will vary depending on the
number of units you have in the database.

#### `--check <check-name>`

Use the `--check` option to force calculation of a specified check. Multiple
checks can be specified in one go by passing the `--check` option multiple
times.


### `flush_cache`

Flushes the cache.

> You must first **stop the workers** if you flush `stats` or `redis` caches.

#### `--django-cache`

Use the `--django-cache` option to flush the `default` cache which keeps Django
templates, project permissions etc.

#### `--rqdata`

Use the `--rqdata` option to flush all data contained in `redis` cache: pending
jobs, dirty flags, revision (which will be automatically restored), all data
from queues.

#### `--stats`

Use the `--stats` option to flush only statistics data.

#### `--all`

Use the `--all` option to flush data from all caches (`default`, `redis`, `stats`).


### `refresh_scores`

Recalculates the scores for all users.

#### `--reset`

When the `--reset` option is used, all score log data is removed and a _zero_
score is set for all users.


## Managing Users


### `merge_user`

This can be used if you have a user with two accounts and need to merge one
account into another. This will re-assign all submissions, units and
suggestions, but not any of the user's profile data.

This command requires 2 mandatory arguments, `src_username` and
`target_username`, both should be valid usernames for users of your site.
Submissions from the first are re-assigned to the second. The users' profile
data is not merged.

#### `--no-delete`

By default `src_username` will be deleted after the contributions have been
merged. You can prevent this by using the `--no-delete` option.

```shell
zing merge_user src_username target_username
```


### `purge_user`

This command can be used if you wish to permanently remove a user and revert
the edits, comments and reviews that the user has made. This is useful for
removing a spam account or other malicious user.

This command requires a mandatory `username` argument, which should be a valid
username for a user of your site.


```shell
zing purge_user username [username ...]
```


### `verify_user`

Verify a user without the user having to go through email verification process.

This is useful if you are migrating users that have already been verified, or
if you want to create a superuser that can log in immediately.

This command requires either mandatory `username` arguments, which should be
valid username(s) for user(s) on your site, or the `--all` flag if you
wish to verify all users of your site.


```shell
zing verify_user username [username ...]
```

Available options:

#### `--all`

Verify all users of the site


## Manual Installation

These commands expose the database installation and upgrade process from the
command line.

### `init`

Create the initial configuration for Zing.

Available options:

#### `--config`

The configuration file to write to.

Default: `~/.zing/zing.conf`.

#### `--db`

Default: `sqlite`.

The database backend that you are using

Available options: `sqlite`, `mysql`, `postgresql`.

#### `--db-name`

Default for sqlite: ``dbs/zing.db``.
Default for mysql/postgresql: ``zingdb``.

The database name or path to database file if you are using sqlite.

#### `--db-user`

Default: ``zing``.

Name of the database user. Not used with sqlite.

#### `--db-host`

Default: `localhost`.

Database host to connect to. Not used with sqlite.

#### `--db-port`

Port to connect to database on. Defaults to database backend's default port.
Not used with sqlite.


### `initdb`

Initializes a new Zing installation.

This is an optional part of Zing's install process, it creates the default
_admin_ user, populates the language table with several languages, initializes
the terminology project, and creates the tutorial project among other tasks. The
projects will be empty until `update_stores` is run.

`initdb` can only be run after `migrate`.

`initdb` accepts the following option:

#### `--no-projects`

Don't create the default `terminology` and `tutorial` projects.
