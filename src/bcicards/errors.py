"""Project-specific exceptions."""


class DependencyMissingError(RuntimeError):
    """Raised when an optional scientific dependency is required but missing."""


def missing_dependency_message(package: str, extra: str = "bci") -> str:
    return (
        f"Missing optional dependency '{package}'. Install the BCI dependencies with "
        f"`py -m pip install -e .[{extra}]` from the project directory."
    )

