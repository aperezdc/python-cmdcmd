#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2017 Adrian Perez <aperez@igalia.com>
#
# Distributed under terms of the MIT license.

from cmdcmd import Command, Option, CLI


#
# Options can be created once and be used by multiple commands.
#
opt_verbose = Option("verbose", short_name="v",
                     help="Be verbose.")
opt_dry_run = Option("dry-run", short_name="n",
                     help="Don't actually perform any operation, just show what would be done.")
opt_patch = Option("patch", short_name="p",
                   help="Use the interactive patch selection interface to chose which changes to include.")


class cmd_add(Command):
    """
    Add file contents to the index.

    This command updates the index using the current content found in the
    working tree, to prepare the content staged for the next commit. It
    typically adds the current content of existing paths as a whole, but with
    some options it can also be used to add content with only part of the
    changes made to the working tree files applied, or remove paths that do
    not exist in the working tree anymore.

    The "index" holds a snapshot of the content of the working tree, and it is
    this snapshot that is taken as contents of the next commit. Thus after
    making changes to the working tree, and before running the commit command,
    you must use the doc:`cmd-add` command to add any new or modified files to
    the index.
    """
    takes_args = ("pathspec*",)  # Takes zero or some paths (*).
    takes_options = (opt_verbose, opt_dry_run)  # Previously defined options.

    # Note how the arguments that take multiple values have a "_list" suffix.
    def run(self, pathspec_list, verbose=False, dry_run=False):
        return locals()


class cmd_commit(Command):
    """
    Record changes to the repository.

    Stores the current contents of the index in a new commit along with a log
    message from the user describing the changes.
    """
    aliases = ("ci",)  # Using "git.py ci" works as well.
    takes_args = ("pathspec*",)
    takes_options = (
        # Reuse some previously defined options.
        opt_dry_run,
        opt_patch,
        opt_verbose,
        # Plus some options specific to "commit".
        Option("message", short_name="m", type=str, help="Commit message."),
        Option("edit", short_name="e", help="Force edit of commit message."),
    )

    # Both the reused options and the ones defined solely for this command
    # are all passed as function arguments.
    def run(self, pathspec_list, dry_run=False, patch=False, verbose=False,
            edit=False, message=None):
        return locals()


class cmd_rebase(Command):
    """
    Reapply commits on top of abother base tip.

    If <branch> is specified, git rebase will perform an automatic ``git
    checkout <branch>`` before doing anything else. Otherwise it remains on
    the current branch.

    If <upstream> is not specified, the upstream configured in
    branch.<name>.remote and branch.<name>.merge options will be used (see
    :doc:`cmd-config` for details) and the ``--fork-point`` option is assumed.
    If you are currently not on any branch or if the current branch does not
    have a configured upstream, the rebase will abort.

    All changes made by commits in the current branch but that are not in
    <upstream> are saved to a temporary area. This is the same set of commits
    that would be shown by ``git log <upstream>..HEAD``; or by ``git log
    'fork_point'..HEAD``, if ``--fork-point`` is active (see the description
    on ``--fork-point`` below); or by git log HEAD, if the ``--root`` option
    is specified.

    The current branch is reset to <upstream>, or <newbase> if the --onto
    option was supplied. This has the exact same effect as git reset --hard
    <upstream> (or <newbase>). ORIG_HEAD is set to point at the tip of the
    branch before the reset.

    The commits that were previously saved into the temporary area are then
    reapplied to the current branch, one by one, in order. Note that any
    commits in HEAD which introduce the same textual changes as a commit in
    HEAD..<upstream> are omitted (i.e., a patch already accepted upstream with
    a different commit message or timestamp will be skipped).

    It is possible that a merge failure will prevent this process from being
    completely automatic. you will have to resolve any such merge failure and
    run ``git rebase --continue``. Another option is to bypass the commit that
    caused the merge failure with ``git rebase --skip``. To check out the
    original <branch> and remove the .git/rebase-apply working files, use the
    command ``git rebase --abort`` instead.
    """
    takes_args = ("upstream?", "branch?")  # Two optional positional arguments.
    takes_options = (
        # Here we are not reusing any previously-defined option.
        Option("continue", help="Continue a rebase operation."),
        Option("skip", help="Skip current patch and continue."),
        Option("abort", help="Abort and check out the original branch."),
        Option("strategy", short_name="s", type=str, argname="strategy",
               help="Use the given merge strategy."),
    )

    def run(self, upstream=None, branch=None, _continue=False, skip=False,
            abort=False, strategy="recursive"):
        return locals()


if __name__ == "__main__":
    raise SystemExit(CLI().run() or 0)
