import nox
from itertools import product
from pathlib import Path

py_default = "3.10"
py_envs = (py_default, "3.5")

nox.options.error_on_external_run = True
nox.options.sessions = (
    "clean", *map("-".join, product(("test",), py_envs)), "report",
)


@nox.session(python=py_default)
def clean(session):
    session.notify("test")
    session.install("coverage[toml]")
    session.run("coverage", "erase")


@nox.session(python=py_default)
def lint(session):
    """Run static code checks."""
    session.install("flakeheaven")
    args = session.posargs or ("lint", "src", "tests", "noxfile.py")
    session.run("flakeheaven", *args)


@nox.session(python=py_envs)
def test(session):
    """Run unit tests, produce coverage data."""
    session.notify("report")
    session.install("coverage[toml]", "pytest", ".")
    session.run("coverage", "run", "-m", "pytest", "-vv", *session.posargs)


@nox.session(python=py_default)
def report(session):
    session.install("coverage[toml]")
    session.run("coverage", "combine", "--append")
    session.run("coverage", "report")


@nox.session(python=py_default)
def build(session):
    # XXX: distpath will be wrong if there is -o/--outdir in posargs
    distpath = Path("dist").resolve()
    session.install("build", "check-wheel-contents", "twine")
    session.run("pyproject-build", *session.posargs)
    session.run("twine", "check", *map(str, distpath.iterdir()))
    wheels = tuple(map(str, distpath.glob("*.whl")))
    if len(wheels) > 0:
        session.run("check-wheel-contents", *wheels)
