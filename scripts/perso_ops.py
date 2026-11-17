"""Shared primitives for Perso's small, side-effecting operator CLIs."""
from pathlib import Path


def read_environment(path: Path) -> dict[str, str]:
    """Read a simple private KEY=VALUE file without expanding secrets."""
    values: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith('#'):
            key, sep, value = line.partition('=')
            if not sep or key.strip() in values:
                raise ValueError('Invalid or duplicate environment assignment')
            values[key.strip()] = value.strip()
    return values
