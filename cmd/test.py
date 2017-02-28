# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2012-2017 Adrian Perez <aperez@igalia.com>
#
# Distributed under terms of the MIT license.

"""
Test suite for the cmd.cmd module.
"""

import unittest
from . import cmd
from inspect import isclass


class cmd_foo(cmd.Command):
    """Does foo."""
    def run(self):
        return 0


class cmd_bar(cmd.Command):
    """Does bar."""
    def run(self):
        return 0


class cmd_spam(cmd.Command):
    """Does spam, has an alias."""
    aliases = ("eggs",)

    def run(self):
        return 0


class TestCmdCommand(unittest.TestCase):

    def assertIsCommand(self, command, cmdclass=None):
        self.assertFalse(isclass(command))
        self.assertTrue(isinstance(command, cmd.Command))
        if cmdclass is not None:
            self.assertTrue(isinstance(command, cmdclass))

    def test_get_unexistant_cmd(self):
        cli = cmd.CLI("foobar", commands=(cmd_foo, cmd_bar))
        self.assertRaises(KeyError, cli.get_command, "baz", True)
        self.assertRaises(KeyError, cli.get_command, "baz", False)
        # Make sure adding a command with aliases does not messes things up
        cli.add_command(cmd_spam)
        self.assertRaises(KeyError, cli.get_command, "baz", True)
        self.assertRaises(KeyError, cli.get_command, "baz", False)

    def test_get_cmd(self):
        cli = cmd.CLI("foobar", commands=(cmd_foo, cmd_bar))
        self.assertIsCommand(cli.get_command("foo", True), cmd_foo)
        self.assertIsCommand(cli.get_command("foo", False), cmd_foo)

    def test_get_cmd_alias(self):
        cli = cmd.CLI("foobar", commands=(cmd_foo, cmd_bar, cmd_spam))
        self.assertIsCommand(cli.get_command("eggs", True), cmd_spam)
        self.assertIsCommand(cli.get_command("spam", True), cmd_spam)
        self.assertIsCommand(cli.get_command("spam", False), cmd_spam)
        self.assertRaises(KeyError, cli.get_command, "eggs", False)
