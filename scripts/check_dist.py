"""Validate release artifacts without importing the SDK or reading credentials."""

import argparse
import configparser
import re
import tarfile
import zipfile
from email.parser import BytesParser
from pathlib import Path, PurePosixPath


def _check_paths(names: set[str]) -> None:
    """Catch unsafe archive paths and common accidental local/credential files."""
    forbidden = {".env", ".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache"}
    for name in names:
        path = PurePosixPath(name)
        if (
            path.is_absolute()
            or ".." in path.parts
            or forbidden.intersection(path.parts)
            or path.suffix.lower() in {".pyc", ".pyo", ".pem", ".key", ".p12", ".pfx"}
            or any(part.startswith(".env.") for part in path.parts)
        ):
            raise ValueError(f"Unexpected private/local archive entry: {name}")


def _check_metadata(content: bytes, version: str) -> None:
    """Require consistent package identity, version and declared Python support."""
    metadata = BytesParser().parsebytes(content)
    name = re.sub(r"[-_.]+", "-", metadata.get("Name", "")).lower()
    if name != "mtn-momo" or metadata.get("Version") != version:
        raise ValueError("Distribution metadata does not match mtn-momo and the project version.")
    if metadata.get("Requires-Python") != ">=3.10":
        raise ValueError("Distribution must declare the supported Python minimum (>=3.10).")


def check_dist(directory: Path, version: str, tag: str = "") -> tuple[Path, Path]:
    """Check one wheel/sdist pair and, for a release, an exact v<version> tag."""
    if tag and tag != f"v{version}":
        raise ValueError(f"Release tag {tag!r} must match project version v{version}.")
    wheels = sorted(directory.glob("*.whl"))
    sources = sorted(directory.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sources) != 1:
        raise ValueError(
            "Expected exactly one wheel and one source archive; use an empty output directory."
        )
    wheel, source = wheels[0], sources[0]
    if any(
        path.name != ".gitignore" and path not in (wheel, source) for path in directory.iterdir()
    ):
        raise ValueError("Unexpected extra files in the release output directory.")
    stem = f"mtn_momo-{version}"
    if wheel.name != f"{stem}-py3-none-any.whl" or source.name != f"{stem}.tar.gz":
        raise ValueError(
            "Artifact filenames do not match the project version and pure-Python wheel."
        )
    info = f"{stem}.dist-info"
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        _check_paths(names)
        if any(PurePosixPath(name).parts[0] not in {"mtn_momo", info} for name in names):
            raise ValueError("Wheel contains files outside the SDK and its metadata.")
        required = {
            "mtn_momo/__init__.py",
            "mtn_momo/py.typed",
            f"{info}/METADATA",
            f"{info}/WHEEL",
            f"{info}/entry_points.txt",
            f"{info}/licenses/LICENSE.md",
        }
        if not required.issubset(names):
            raise ValueError(f"Missing required wheel files: {sorted(required - names)}")
        _check_metadata(archive.read(f"{info}/METADATA"), version)
        entry_points = configparser.ConfigParser()
        entry_points.read_string(archive.read(f"{info}/entry_points.txt").decode())
        if (
            entry_points.get("console_scripts", "mtn-momo-provision", fallback="")
            != "mtn_momo.provisioning:main"
        ):
            raise ValueError("Wheel is missing the expected provisioning console entry point.")
        package_files = {
            name for name in names if name.startswith("mtn_momo/") and not name.endswith("/")
        }
    with tarfile.open(source, "r:gz") as archive:
        names = set(archive.getnames())
        _check_paths(names)
        if any(PurePosixPath(name).parts[0] != stem for name in names):
            raise ValueError("Source archive contains files outside its versioned root.")
        if any(member.issym() or member.islnk() for member in archive.getmembers()):
            raise ValueError("Source archive must not contain symlinks or hard links.")
        required = {
            f"{stem}/pyproject.toml",
            f"{stem}/PKG-INFO",
            f"{stem}/README.md",
            f"{stem}/LICENSE.md",
        }
        required.update(f"{stem}/src/{name}" for name in package_files)
        if not required.issubset(names):
            raise ValueError(
                f"Source archive is missing required files: {sorted(required - names)}"
            )
        metadata_file = archive.extractfile(f"{stem}/PKG-INFO")
        if metadata_file is None:
            raise ValueError("Source archive PKG-INFO is not a regular file.")
        with metadata_file:
            _check_metadata(metadata_file.read(), version)
    return wheel, source


def main() -> None:
    """Run locally, on normal CI, or with a release tag supplied by GitHub."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--version", required=True)
    parser.add_argument("--tag", default="")
    args = parser.parse_args()
    try:
        wheel, source = check_dist(args.dist, args.version, args.tag)
    except (ValueError, OSError, zipfile.BadZipFile, tarfile.TarError) as exc:
        parser.error(str(exc))
    print(f"Validated {wheel.name} and {source.name}")


if __name__ == "__main__":
    main()
