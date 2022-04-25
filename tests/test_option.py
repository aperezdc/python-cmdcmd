# noqa: INP001
#
# -*- coding: utf-8 -*-
#
# Copyright © 2022 Adrian Perez de Castro <aperez@igalia.com>
#
# Distributed under terms of the MIT license.

from cmdcmd import cmd
from enum import Enum


class Protocol(Enum):
    UDP = "udp"
    TCP = "tcp"
    ICMP = "icmp"
    ARP = "arp"


class cmd_foo(cmd.Command):
    takes_options = (
        cmd.Option("protocol", short_name="p", help="Protocol", type=Protocol),
    )

    def run(self, protocol=Protocol.ARP):
        assert isinstance(protocol, Protocol)
        return protocol


def test_enum_option():
    cli = cmd.CLI("foobar", commands=(cmd_foo,))
    assert cli.run(["foo"]) == Protocol.ARP
    assert cli.run(["foo", "-p", "tcp"]) == Protocol.TCP
    assert cli.run(["foo", "--protocol=udp"]) == Protocol.UDP
    assert cli.run(["foo", "--protocol", "udp"]) == Protocol.UDP


def test_enum_option_invalid_value():
    cli = cmd.CLI("foobar", commands=(cmd_foo,))
    assert "invalid choice" in cli.run(["foo", "-p", "bananas"])
    assert "invalid choice" in cli.run(["foo", "--protocol=bananas"])
    assert "invalid choice" in cli.run(["foo", "--protocol", "bananas"])
