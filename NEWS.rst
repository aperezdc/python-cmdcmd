cmdcmd v3 (2022-04-26)
======================

Features
--------

- It is now possible to use types derived from `Enum
  <https://docs.python.org/3/library/enum.html>`__ as types for ``Option``, as
  long as the values of each enumeration item are strings. For example, the
  following can be used to parse Git's ``--strategy=`` option:

  .. code:: python

      class Strategy(enum.Enum):
          OCTOPUS = "octopus"
          OURS = "ours"
          RECURSIVE = "recursive"
          RESOLVE = "resolve"
          SUBTREE = "subtree"

      opt_strategy = Option("strategy", type=Strategy)


Deprecations and Removals
-------------------------

- Support for versions of Python older than 3.6 has been removed.
