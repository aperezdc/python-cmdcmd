# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2017 Adrian Perez <aperez@igalia.com>
# Copyright © 2010 Igalia S.L.
#
# Distributed under terms of the MIT license.

"""
Utilities to build command-line action-based programs.
"""

from inspect import isclass
from keyword import iskeyword
import optparse
import types
import sys
import os


def rst_to_plain_text(text):
    """Minimal converter of reStructuredText to plain text.

    Will work at least for command descriptions.

    :param text: Text to be converted.
    :rtype: str
    """
    import re
    lines = text.splitlines()
    result = []
    for line in lines:
        if line.startswith(":"):
            line = line[1:]
        elif line.endswith("::"):
            line = line[:-1]
        # Map :doc:`xxx-help` to ``help xxx``
        line = re.sub(":doc:`(.+)-help`", r"``help \1``", line)
        result.append(line)
    return "\n".join(result) + "\n"


class CommandError(RuntimeError):
    """An error occured running a command."""


class Option(object):
    """Describes a command line option.

    :ivar _short_name: If the option has a single-letter alias, this is
        defined. Otherwise this is None.
    """
    STD_OPTIONS = {}

    OPTIONS = {}

    def __init__(self, name, help="", type=None, argname=None,  # noqa: B002
                 short_name=None, param_name=None, custom_callback=None,
                 hidden=False):
        """Make a new action option.

        :param name: regular name of the command, used in the double-dash
            form and also as the parameter to the command's run()
            method (unless param_name is specified).

        :param help: help message displayed in command help

        :param type: function called to parse the option argument, or
            None (default) if this option doesn't take an argument.

        :param argname: name of option argument, if any

        :param short_name: short option code for use with a single -, e.g.
            short_name="v" to enable parsing of -v.

        :param param_name: name of the parameter which will be passed to
            the command's run() method.

        :param custom_callback: a callback routine to be called after normal
            processing. The signature of the callback routine is
            (option, name, new_value, parser).
        :param hidden: If True, the option should be hidden in help and
            documentation.
        """
        self.name = name
        self.help = help
        self.type = type
        self._short_name = short_name
        if type is None:
            if argname:
                raise ValueError("argname not valid for booleans")
        elif argname is None:
            argname = "ARG"
        self.argname = argname
        if param_name is None:
            self._param_name = self.name.replace("-", "_")
        else:
            self._param_name = param_name
        self.custom_callback = custom_callback
        self.hidden = hidden

    def get_short_name(self):
        """Return the short name of the option."""
        if self._short_name:
            return self._short_name

    def set_short_name(self, short_name):
        """Set the short name of the option."""
        self._short_name = short_name

    short_name = property(get_short_name, set_short_name,
                          doc="Short name of the option")

    def get_negation_name(self):
        """Return the negated name of the option."""
        if self.name.startswith("no-"):
            return self.name[3:]
        else:
            return "no-" + self.name

    negation_name = property(get_negation_name,
                             doc="Negated name of the option")

    def add_option(self, parser, short_name):
        """Add this option to an optparse parser."""
        option_strings = ["--" + self.name]
        if short_name is not None:
            option_strings.append("-" + short_name)
        if self.hidden:
            _help = optparse.SUPPRESS_HELP
        else:
            _help = self.help
        optargfn = self.type
        if optargfn is None:
            parser.add_option(action="callback",
                              callback=self._optparse_bool_callback,
                              callback_args=(True,),
                              help=_help,
                              *option_strings)
            negation_strings = ["--" + self.get_negation_name()]
            parser.add_option(action="callback",
                              callback=self._optparse_bool_callback,
                              callback_args=(False,),
                              help=optparse.SUPPRESS_HELP, *negation_strings)
        else:
            parser.add_option(action="callback",
                              callback=self._optparse_callback,
                              type="string", metavar=self.argname.upper(),
                              help=_help,
                              default=OptionParser.DEFAULT_VALUE,
                              *option_strings)

    def _optparse_bool_callback(self, option, opt_str, value, parser, bool_v):
        setattr(parser.values, self._param_name, bool_v)
        if self.custom_callback is not None:
            self.custom_callback(option, self._param_name, bool_v, parser)

    def _optparse_callback(self, option, opt, value, parser):
        v = self.type(value)
        setattr(parser.values, self._param_name, v)
        if self.custom_callback is not None:
            self.custom_callback(option, self.name, v, parser)

    def iter_switches(self):
        """Iterate through the list of switches provided by the option

        :return: an iterator of (name, short_name, argname, help)
        """
        argname = self.argname
        if argname is not None:
            argname = argname.upper()
        yield self.name, self.short_name(), argname, self.help


class ListOption(Option):
    """Option used to provide a list of values.

    On the command line, arguments are specified by a repeated use of the
    option. '-' is a special argument that resets the list. For example,
      --foo=a --foo=b
    sets the value of the 'foo' option to ['a', 'b'], and
      --foo=a --foo=b --foo=- --foo=c
    sets the value of the 'foo' option to ['c'].
    """

    def add_option(self, parser, short_name):
        """Add this option to an Optparse parser."""
        option_strings = ["--" + self.name]
        if short_name is not None:
            option_strings.append("-" + short_name)
        parser.add_option(action="callback",
                          callback=self._optparse_callback,
                          type="string", metavar=self.argname.upper(),
                          help=self.help, default=[],
                          *option_strings)

    def _optparse_callback(self, option, opt, value, parser):
        values = getattr(parser.values, self._param_name)
        if value == "-":
            del values[:]
        else:
            values.append(self.type(value))
        if self.custom_callback is not None:
            self.custom_callback(option, self._param_name, values, parser)


class OptionParser(optparse.OptionParser):
    """OptionParser that raises exceptions instead of exiting"""

    DEFAULT_VALUE = object()

    def error(self, message):
        raise CommandError(message)


def get_optparser(options):
    """Generate an optparse parser for bzrlib-style options"""

    parser = OptionParser()
    parser.remove_option("--help")
    for option in options.values():
        option.add_option(parser, option.short_name)
    return parser


def _standard_option(name, **kwargs):
    """Register a standard option."""
    # All standard options are implicitly 'global' ones
    Option.STD_OPTIONS[name] = Option(name, **kwargs)
    Option.OPTIONS[name] = Option.STD_OPTIONS[name]


def _global_option(name, **kwargs):
    """Register a global option."""
    Option.OPTIONS[name] = Option(name, **kwargs)


# Declare standard options
_standard_option("help", short_name="h",
                 help="Show help message")
_standard_option("usage",
                 help="Show usage message and options")


def _squish_command_name(name):
    """Gets a valid identifier from a command name.

    :param name: Command name.
    :rtype: str
    """
    return "cmd_" + name.replace("-", "_")


def _unsquish_command_name(identifier):
    """Gets a command name given its identifier.

    :param identifier: Command identifier.
    :rtype: str
    """
    return identifier[4:].replace("_", "-")


class Command(object):
    """Base class for commands.

    You should define subclasses of this to create a set of commands which
    then can be grouped using a :class:`cli`.

    The docstring for an actual command should give a single-line summary,
    then a complete description of the command. For commands taking options
    and arguments, a small grammar and a description of the options will be
    automatically inserted in the help text as needed.

    :cvar takes_options: List of options that may be given for this command,
        either strings referring to globally-defined options, or instances
        of :class:`Option`.
    :cvar takes_args: List of arguments, marking them as *optional*
        (``arg?``) or repeated (``arg+``, ``arg*``). Those will be passed as
        keyword arguments to the command's :meth:`run` method.
    :cvar aliases: Other names which may be used to refer to this command.
    :cvar exceptions: Either a single class or a list of classes of
        exceptions which will cause the command to exit with non-zero
        status, printing just the exception message to standard error
        instead of a full traceback.
    """
    takes_options = ()
    takes_args = ()
    aliases = ()
    hidden = False
    exceptions = None
    __cmd_param__ = {}

    def __init__(self, **param):
        assert self.__doc__ != Command.__doc__, \
            "No help message set for {!r}".format(self)
        self.supported_std_options = []
        self.param = param

    def _usage(self):
        """Return a single-line grammar for this action.

        Only describes arguments, not options.
        """
        result = self.name() + " "
        for aname in self.takes_args:
            aname = aname.upper()
            if aname[-1] in ("$", "+"):
                aname = aname[:-1] + "..."
            elif aname[-1] == "?":
                aname = "[" + aname[:-1] + "]"
            elif aname[-1] == "*":
                aname = "[" + aname[:-1] + "...]"
            result += aname + " "
        result = result[:-1]  # Remove last space
        return result

    def prepare(self):
        """Prepare for execution.

        This is a hook method intended to be redefined in subclasses.
        By default it does nothing.
        """
        pass

    def cleanup(self):
        """Clean up after execution.

        This is a hook method intended to be redefined in subclasses.
        By default it does nothing.
        """
        pass

    def run(self):
        """Actually run the command.

        This is invoked with the options and arguments bound to keyword
        parameters.

        Return 0 or None if the command was successful, or a non-zero shell
        error code if not. It is okay for this method to raise exceptions.
        """
        raise NotImplementedError("No implementation of command {!r}".format(self.name()))

    def get_config_file(self):
        """Guess the name of the configuration file.

        This will work if at least ``cmd:config_file`` is defined in the
        command parameters. If ``cmd:config_env_var`` is there it is assumed
        to be the name of an environment variable which could point to an
        alternative path for the configuration file.

        :return: Path to configuration file, or ``None``.
        """
        env_var = self.param.get("cmd:config_env_var", None)
        cfgfile = self.param.get("cmd:config_file", None)

        if env_var and (env_var in os.environ):
            cfgfile = os.environ[env_var]

        return cfgfile

    def name(self):
        """Return the name of the action."""
        if isclass(self):
            name = self.__name__
        else:
            name = self.__class__.__name__
        return _unsquish_command_name(name)

    name = classmethod(name)

    def help(self):
        """Return help message for this action."""
        from inspect import getdoc
        if self.__doc__ is Command.__doc__:
            return None
        return getdoc(self)

    def options(self):
        """Return dict of valid options for this action.

        Maps from long option name to option object.
        """
        result = Option.STD_OPTIONS.copy()
        std_names = result.keys()
        for opt in self.takes_options:
            if isinstance(opt, str):
                opt = Option.OPTIONS[opt]
            result[opt.name] = opt
            if opt.name in std_names:
                self.supported_std_options.append(opt.name)
        return result

    def run_argv_aliases(self, argv, alias_argv=None):
        """Parse the command line and run with extra aliases in alias_argv."""
        assert argv is not None

        args, opts = parse_args(self, argv, alias_argv)

        # Process the standard options
        if "help" in opts:  # e.g. command add --help
            sys.stdout.write(self.get_help_text())
            return 0
        if "usage" in opts:  # e.g. command add --usage
            sys.stdout.write(self.get_help_text(verbose=False))
            return 0

        # mix arguments and options into one dictionary
        cmdargs = _match_argform(self.name(), self.takes_args, args)
        cmdopts = {}
        for k, v in opts.items():
            if iskeyword(k):
                k = "_" + k
            cmdopts[k.replace("-", "_")] = v

        all_cmd_args = cmdargs.copy()
        all_cmd_args.update(cmdopts)

        return self.run_direct(**all_cmd_args)

    def run_direct(self, *args, **kwargs):
        """Call run directly with objects (without parsing an argv list).
        """
        try:
            try:
                # If prepare() returns something, it is assumed to be a non-zero
                # exit code or an error string -- so we do not execute run().
                #
                ret = self.prepare()
                if not ret:
                    ret = self.run(*args, **kwargs)
            except:
                # In this case, don't even other of calling sys.exc_info()
                if self.exceptions is None:
                    raise

                value = sys.exc_info()[1]
                if isinstance(value, self.exceptions):
                    return value
                else:
                    raise
        finally:
            # Ensure that cleanup() is executed.
            self.cleanup()

        return ret

    def get_help_text(self, plain=True, verbose=True):
        """Return a text string with help for this command.

        :param additional_see_also: Additional help topics to be
            cross-referenced.
        :param plain: if False, raw help (reStructuredText) is
            returned instead of plain text.
        :param see_also_as_links: if True, convert items in 'See also'
            list to internal links (used by bzr_man rstx generator)
        :param verbose: if True, display the full help, otherwise
            leave out the descriptive sections and just display
            usage help (e.g. Purpose, Usage, Options) with a
            message explaining how to obtain full help.
        """
        doc = self.help()
        if doc is None:
            raise NotImplementedError("sorry, no detailed help yet for {!r}".format(self.name()))

        # Extract the summary (purpose) and sections out from the text
        purpose, sections, order = self._get_help_parts(doc)

        # If a custom usage section was provided, use it
        if "Usage" in sections:
            usage = sections.pop("Usage")
        else:
            usage = self._usage()

        # The header is the purpose and usage
        result = ""
        result += ":Purpose: {!s}\n".format(purpose)
        if usage.find("\n") >= 0:
            result += ":Usage:\n{!s}\n".format(usage)
        else:
            result += ":Usage:   {!s}\n".format(usage)
        result += "\n"

        # Add the options
        #
        # XXX: optparse implicitly rewraps the help, and not always perfectly,
        # so we get <https://bugs.launchpad.net/bzr/+bug/249908>.  -- mbp
        # 20090319
        options = get_optparser(self.options()).format_option_help()
        if options.startswith("Options:"):
            result += ":" + options
        elif options.startswith("options:"):
            # Python 2.4 version of optparse
            result += ":Options:" + options[len("options:"):]
        else:
            result += options
        result += "\n"

        if verbose:
            # Add the description, indenting it 2 spaces
            # to match the indentation of the options
            if None in sections:
                text = sections.pop(None)
                text = "\n  ".join(text.splitlines())
                result += ":Description:\n  {!s}\n\n".format(text)

            # Add the custom sections (e.g. Examples). Note that there's no need
            # to indent these as they must be indented already in the source.
            if sections:
                for label in order:
                    if label in sections:
                        result += ":{!s}:\n{!s}\n".format(label, sections[label])
                result += "\n"
        else:
            result += "See \"help {!s}\" for more details and examples.\n\n".format(self.name())

        # Add the aliases, source (plug-in) and see also links, if any
        if self.aliases:
            result += ":Aliases: "
            result += ", ".join(self.aliases) + "\n"

        # If this will be rendered as plain text, convert it
        if plain:
            result = rst_to_plain_text(result)
        return result

    def _get_help_parts(text):
        """Split help text into a summary and named sections.

        :return: (summary,sections,order) where summary is the top line and
            sections is a dictionary of the rest indexed by section name.
            order is the order the section appear in the text.
            A section starts with a heading line of the form ":xxx:".
            Indented text on following lines is the section value.
            All text found outside a named section is assigned to the
            default section which is given the key of None.
        """
        def save_section(sections, order, label, section):
            if len(section) > 0:
                if label in sections:
                    sections[label] += "\n" + section
                else:
                    order.append(label)
                    sections[label] = section

        lines = text.rstrip().splitlines()
        summary = lines.pop(0) if len(lines) else ""
        sections = {}
        order = []
        label, section = None, ""
        for line in lines:
            if line.startswith(":") and line.endswith(":") and len(line) > 2:
                save_section(sections, order, label, section)
                label, section = line[1:-1], ""
            elif (label is not None) and len(line) > 1 and not line[0].isspace():
                save_section(sections, order, label, section)
                label, section = None, line
            else:
                if len(section) > 0:
                    section += "\n" + line
                else:
                    section = line
        save_section(sections, order, label, section)
        return summary, sections, order

    _get_help_parts = staticmethod(_get_help_parts)


def parse_args(cmd, argv, alias_argv=None):
    """Parse command line.

    Arguments and options are parsed at this level before being passed
    down to specific command handlers.  This routine knows, from a
    lookup table, something about the available options, what optargs
    they take, and which commands will accept them.
    """
    # TODO: make it a method of the command?
    parser = get_optparser(cmd.options())
    if alias_argv is not None:
        args = alias_argv + argv
    else:
        args = argv

    options, args = parser.parse_args(args)
    opts = {k: v for k, v in options.__dict__.items() if v is not OptionParser.DEFAULT_VALUE}
    return args, opts


def _match_argform(cmd, takes_args, args):
    argdict = {}

    # step through args and takes_args, allowing appropriate 0-many matches
    for ap in takes_args:
        argname = ap[:-1]
        if ap[-1] == "?":
            if args:
                argdict[argname] = args.pop(0)
        elif ap[-1] == "*":  # all remaining arguments
            if args:
                argdict[argname + "_list"] = args[:]
                args = []
            else:
                argdict[argname + "_list"] = ()
        elif ap[-1] == "+":
            if not args:
                raise CommandError("command {!r} needs one or more {!s}".format(cmd, argname.upper()))
            else:
                argdict[argname + "_list"] = args[:]
                args = []
        elif ap[-1] == "$":  # all but one
            if len(args) < 2:
                raise CommandError("command {!r} needs one or more {!s}".format(cmd, argname.upper()))
            argdict[argname + "_list"] = args[:-1]
            args[:-1] = []
        else:
            # just a plain arg
            argname = ap
            if not args:
                raise CommandError("command {!r} requires argument {!s}".format(cmd, argname.upper()))
            else:
                argdict[argname] = args.pop(0)

    if args:
        raise CommandError("extra argument to command {!r}: {!s}".format(cmd, args[0]))

    return argdict


def ignore_pipe_err(func):
    """Decorator that suppresses pipe/interrupt errors.

    :param func: Function to decorate.
    """
    def ignore_pipe(*args, **kwargs):
        import errno
        try:
            result = func(*args, **kwargs)
            sys.stdout.flush()
            return result
        except IOError as e:
            if getattr(e, "errno", None) is None:
                raise
            if e.errno != errno.EPIPE:
                # Win32 raises IOError with errno=0 on a broken pipe
                if sys.platform != "win32" or (e.errno not in (0, errno.EINVAL)):
                    raise
            pass
        except KeyboardInterrupt:
            pass
    return ignore_pipe


class cmd_help(Command):
    """Show help on a command."""

    takes_args = ["topic?"]
    aliases = ["?", "--help", "-?", "-h"]

    def run(self, topic=None, long=False):
        if topic is None:
            if long:
                topic = "commands"
            else:
                topic = "help"
        if "cmd:help_output" in self.param:
            self.param["cmd:help_output"](topic)

    run = ignore_pipe_err(run)


_cli_top_level_help_text = """\
Usage: %s <command> [flags...] [arguments...]

Available commands:
%s
Getting more help:
   help commands   Get a list of available commands.
   help <command>  Show help on the given <command>.
"""


class CLI(object):
    """Groups commands and provides a command line interface to them.

    :ivar _registry: Dictionary containing all registered commands, mapping
        names to :class:`Command` instances.
    """

    def scan_commands(module, klass=None, **param):
        """Scans a module for commands of a given class.

        :param module: Module to scan commands in. If a string is given, it
            is assumed to be a module name and it will be imported.
        :param klass: Specify a base class of which subclasses will be
            searched for.
        :param param: Keyword arguments passed to commands when
            instantiating them.
        :return: Generator which yields *(name, command)* pairs.
        """
        if isinstance(module, str):
            module = __import__(module, {}, {}, "dummy")
        if isinstance(module, types.ModuleType):
            module = module.__dict__

        if klass is None:
            klass = Command

        assert isinstance(module, dict)

        for item in module.values():
            if item is klass or not isclass(item):
                continue
            if issubclass(item, klass) and item.__name__.startswith("cmd_"):
                item.__cmd_param__ = param
                yield (item.name(), item)

    scan_commands = staticmethod(scan_commands)

    def from_tool_name(toolname, **param):
        """Creates a CLI for a given tool name.

        This generates the names of the configuration file and environment
        variable used to override it from the name of the tool.

        :param toolname: Name of the tool.
        :rtype: :class:`CLI`
        """
        if "cli_commands_module" in param:
            modname = param["cli_commands_module"]
            del param["cli_commands_module"]
        else:
            modname = toolname.replace("-", "")

        if "cli_config_file_envvar" in param:
            envvar = param["cli_config_file_envvar"]
            del param["cli_config_file_envvar"]
        else:
            envvar = toolname.replace("-", "_").upper() + "_CONF"

        if "cli_config_file_path" in param:
            conffile = param["cli_config_file_path"]
            del param["cli_config_file_path"]
        else:
            conffile = "/etc/{!s}.conf".format(toolname)

        return CLI(name=toolname, config_file=conffile, config_env_var=envvar,
                   commands=modname, **param)

    from_tool_name = staticmethod(from_tool_name)

    def __init__(self, name=None, config_file=None, config_env_var=None,
                 commands=None, *arg, **param):
        """Create a new command line interface controller.

        :param name: Tool name. If not given, the base name of
            ``sys.argv[0]`` will be used, which usually will be the desired
            behavior.
        :param config_file: Path to the configuration file.
        :param config_env_var: Environment variable name which can be used
            to override the location of the configuration file.
        :param commands: List of modules (or strings with module names) from
            which commands will be used. As an option, you may directly pass
            a dictionary mapping names to instances of :class:`Command`. If
            not given, the module from which the class is being instantiated
            will be used.
        """
        self.name = name or sys.argv[0]
        self._registry = {}

        param["cmd:help_output"] = self._output_help
        param["cmd:tool_name"] = self.name

        if isinstance(config_env_var, str) and config_env_var:
            param["cmd:config_env_var"] = config_env_var
        if isinstance(config_file, str) and config_file:
            param["cmd:config_file"] = config_file

        self.add_commands(commands, **param)

        # Add our built-in commands ("help" for now)
        self.add_command(cmd_help, **param)

    def add_command(self, command, **param):
        """Adds a single command to the command registry.
        """
        assert issubclass(command, Command)
        self.add_commands((command,), **param)

    def add_commands(self, commands=None, *arg, **kw):
        """Register commands.

        :param commands: List of modules (or strings with module names) from
            which commands will be used. As an option, you may directly pass
            a dictionary mapping names to instances of :class:`Command`. If
            not give, the module from which the class is being instantiated
            will be used.
        """
        kw["cmd:help_output"] = self._output_help

        if commands is None:
            commands = [sys._getframe(2).f_globals]
        elif isinstance(commands, (list, tuple)):
            commands = {c.name(): c for c in commands}
        if isinstance(commands, (dict, str, types.ModuleType)):
            commands = [commands]

        for item in commands:
            self._registry.update(self.scan_commands(item, *arg, **kw))

    def _output_help_commands(self, hidden=False, indent=0):
        """Generate text output for 'help commands'

        :param hidden: Whether to include hidden commands in the output.
        :param indent: Indent each line with the given amount of spaces.
        """
        cmdnames = [n for n, c in self._registry.items()
                    if c.hidden == hidden]

        if not cmdnames:
            return ""

        max_name = max((len(n) for n in cmdnames))
        result = []

        # It is better to have the output sorted by name.
        cmdnames.sort()

        if indent:
            indent = " " * indent
        else:
            indent = ""

        cmdformat = indent + "%-*s  %s\n"

        for name in cmdnames:
            cmd = self.get_command(name)
            helptext = cmd.help()
            if helptext:
                firstline = helptext.split("\n", 1)[0]
            else:
                firstline = ""

            result.append(cmdformat % (max_name, name, firstline))

        return "".join(result)

    def _output_help(self, topic):
        """Print out help for a given topic.

        :param topic: A command name, or one of ``commands`` or
            ``hidden-commands`` strings.
        """
        if topic == "help":
            text = _cli_top_level_help_text % (self.name,
                                               self._output_help_commands(indent=3))
        elif topic == "commands":
            text = self._output_help_commands()
        elif topic == "hidden-commands":
            text = self._output_help_commands(hidden=True)
        elif self.has_command(topic):
            text = self.get_command(topic).get_help_text()
        else:
            text = "{!s}: Unavailable help topic '{!s}'\n".format(self.name, topic)

        sys.stdout.write(text)

    def get_command(self, name, alias=True):
        """Obtain a command given its name.

        :param name: Name of the command.
        :param alias: Allow searching for aliases.
        :rtype: :class:`Command`
        """
        assert self._registry

        command = None
        if name in self._registry:
            command = self._registry[name]

        if command:
            return command(**command.__cmd_param__)
        elif alias:
            for command in self._registry.values():
                if name in command.aliases:
                    return command(**command.__cmd_param__)

        raise KeyError("No such command {!r}".format(name))

    def has_command(self, name, alias=True):
        """Check whether a command exists given its name.

        :param name: Name of the command.
        :param alias: Allow searching for aliases.
        :rtype: bool
        """
        assert self._registry

        if alias:
            for command in self._registry.values():
                if name in command.aliases:
                    return True

        return name in self._registry

    def run(self, argv=None):
        """Run the command line tool.

        :param argv: Command line arguments, being the first one interpreted
            as command name. If not given, then ``sys.argv[1:]`` will be
            used.
        """
        if argv is None:
            argv = [item.decode("utf-8")
                    if isinstance(item, bytes) else item
                    for item in sys.argv[1:]]

        try:
            cmd = argv and argv.pop(0) or "help"
            cmd = self.get_command(cmd)
        except KeyError:
            return "{!s}: command '{!s}' does not exist.".format(self.name, cmd)

        try:
            return cmd.run_argv_aliases(argv) or 0
        except CommandError as e:
            return "{!s}: {!s}".format(self.name, e)


def main(toolname=None, argv=None, **kw):
    """Convenience function to run a command line tool.

    This will create a :class:`CLI`, scan for commands in a module name
    determined given the tool name, and then run it.

    :param toolname: Command line tool name. If not given, then
        ``sys.argv[0]`` will be used.
    :param argv: Command line arguments. If not given, then
        ``sys.argv[1:]`` will be used.
    """
    if toolname is None:
        if argv is None:
            toolname = os.path.basename(sys.argv[0])
            argv = sys.argv[1:]
        else:
            toolname = argv.pop()

    raise SystemExit(CLI.from_tool_name(toolname, **kw).run(argv) or 0)


__all__ = ["CLI", "Command", "Option"]
