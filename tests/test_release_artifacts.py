"""Exercise release guards with tiny synthetic archives, without registry access."""

import io
import tarfile
import zipfile
from pathlib import Path

import pytest

from scripts.check_dist import check_dist


def distributions(directory: Path, *, wheel_extra=None, source_extra=None, missing=None):
    """Create the minimum release pair expected by the checker."""
    stem = "mtn_momo_python-0.1.0"
    info = f"{stem}.dist-info"
    metadata = b"Name: mtn-momo-python\nVersion: 0.1.0\nRequires-Python: >=3.10\n\n"
    package = {"mtn_momo/__init__.py": b"", "mtn_momo/py.typed": b""}
    wheel = {
        **package,
        f"{info}/METADATA": metadata,
        f"{info}/WHEEL": b"Tag: py3-none-any\n",
        f"{info}/entry_points.txt": (
            b"[console_scripts]\nmtn-momo-provision = mtn_momo.provisioning:main\n"
        ),
        f"{info}/licenses/LICENSE.md": b"Synthetic license\n",
    }
    wheel.update(wheel_extra or {})
    if missing:
        wheel.pop(missing)
    with zipfile.ZipFile(directory / f"{stem}-py3-none-any.whl", "w") as archive:
        for name, content in wheel.items():
            archive.writestr(name, content)
    source = {
        f"{stem}/PKG-INFO": metadata,
        f"{stem}/pyproject.toml": b"[project]\nname = 'mtn-momo-python'\n",
        f"{stem}/README.md": b"Synthetic README\n",
        f"{stem}/LICENSE.md": b"Synthetic license\n",
        **{f"{stem}/src/{name}": content for name, content in package.items()},
    }
    source.update(source_extra or {})
    with tarfile.open(directory / f"{stem}.tar.gz", "w:gz") as archive:
        for name, content in source.items():
            member = tarfile.TarInfo(name)
            member.size = len(content)
            archive.addfile(member, io.BytesIO(content))


def test_valid_pair_and_matching_tag(tmp_path):
    distributions(tmp_path)
    (tmp_path / ".gitignore").write_text("*\n")
    wheel, source = check_dist(tmp_path, "0.1.0", "v0.1.0")
    assert wheel.suffix == ".whl"
    assert source.name.endswith(".tar.gz")
    check_dist(tmp_path, "0.1.0")


def test_tag_must_match_project_version(tmp_path):
    distributions(tmp_path)
    with pytest.raises(ValueError, match="Release tag"):
        check_dist(tmp_path, "0.1.0", "v0.2.0")


@pytest.mark.parametrize(
    "entry", ["mtn_momo/.env", "mtn_momo/__pycache__/x.pyc", "mtn_momo/key.pem", "../secret.py"]
)
def test_private_or_unsafe_wheel_paths_are_rejected(tmp_path, entry):
    distributions(tmp_path, wheel_extra={entry: b"Synthetic private file"})
    with pytest.raises(ValueError, match="private/local"):
        check_dist(tmp_path, "0.1.0")


def test_source_credentials_are_rejected(tmp_path):
    distributions(
        tmp_path, source_extra={"mtn_momo_python-0.1.0/.env.production": b"Synthetic secret"}
    )
    with pytest.raises(ValueError, match="private/local"):
        check_dist(tmp_path, "0.1.0")


@pytest.mark.parametrize(
    "missing", ["mtn_momo/py.typed", "mtn_momo_python-0.1.0.dist-info/licenses/LICENSE.md"]
)
def test_required_wheel_files_are_present(tmp_path, missing):
    distributions(tmp_path, missing=missing)
    with pytest.raises(ValueError, match="Missing required wheel"):
        check_dist(tmp_path, "0.1.0")


def test_stale_artifacts_are_rejected(tmp_path):
    distributions(tmp_path)
    (tmp_path / "old.whl").write_bytes(b"Synthetic stale wheel")
    with pytest.raises(ValueError, match="exactly one"):
        check_dist(tmp_path, "0.1.0")


def test_metadata_version_must_match(tmp_path):
    distributions(
        tmp_path,
        wheel_extra={
            "mtn_momo_python-0.1.0.dist-info/METADATA": (
                b"Name: mtn-momo-python\nVersion: 0.2.0\nRequires-Python: >=3.10\n"
            ),
        },
    )
    with pytest.raises(ValueError, match="metadata"):
        check_dist(tmp_path, "0.1.0")


def test_console_entry_point_is_checked(tmp_path):
    distributions(
        tmp_path,
        wheel_extra={"mtn_momo_python-0.1.0.dist-info/entry_points.txt": b"[console_scripts]\n"},
    )
    with pytest.raises(ValueError, match="entry point"):
        check_dist(tmp_path, "0.1.0")


def test_wheel_does_not_bundle_unrelated_packages(tmp_path):
    distributions(tmp_path, wheel_extra={"unrelated/__init__.py": b""})
    with pytest.raises(ValueError, match="outside the SDK"):
        check_dist(tmp_path, "0.1.0")


def test_wheel_files_must_exist_in_source_archive(tmp_path):
    distributions(tmp_path, wheel_extra={"mtn_momo/missing_from_source.py": b""})
    with pytest.raises(ValueError, match="Source archive is missing"):
        check_dist(tmp_path, "0.1.0")
