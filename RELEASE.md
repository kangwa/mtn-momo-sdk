# Publishing `mtn-momo-python`

The distribution name is **`mtn-momo-python`**; the Python import is `mtn_momo`. The
repository name is not the package name. `mtn-momo-sdk`, `mtn-momo-client`, and
`mtnmomo` on PyPI belong to other projects, and `mtn-momo` itself is rejected by
PyPI's similarity rule because it normalizes to the same value as `mtnmomo`. Confirm
the name is still available before a release; a missing project page alone does not
guarantee a name can be registered.

## One-time account setup

1. Create/sign in to the intended [PyPI account](https://pypi.org/) and enable 2FA.
   Keep recovery codes somewhere secure.
2. In **GitHub → kangwa/mtn-momo-sdk → Settings → Environments**, create `pypi`.
   Configure a required reviewer where your GitHub plan supports it, ideally
   prevent self-review, and restrict deployment refs to the intended release tags.
   The workflow's environment reference alone does not create an approval gate.
3. On PyPI, configure a [pending Trusted Publisher](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
   for the first upload:

   | Field | Value |
   | --- | --- |
   | Project name | `mtn-momo-python` |
   | GitHub owner | `kangwa` |
   | Repository | `mtn-momo-sdk` |
   | Workflow filename | `publish.yml` |
   | Environment | `pypi` |

   Once the project exists, manage the publisher from its Publishing settings.
   Workflow filename and environment must match exactly. No permanent PyPI token
   or repository publishing secret is needed; only the publish job gets OIDC
   `id-token: write` permission.
4. TestPyPI is optional, with a separate account/publisher and upload destination.
   The supplied workflow publishes to real PyPI, not TestPyPI.

## Validate without publishing

From this SDK checkout (not a consuming backend):

```bash
uv sync --locked --dev
uv run ruff check .
uv run ruff format --check
uv run mypy src
uv run pytest -m "not sandbox"
uv build --no-sources
uv run twine check dist/*
uv run python scripts/check_dist.py --version "$(uv version --short)"
```

Build into an empty distribution directory: stale wheels/source archives fail
validation instead of being uploaded accidentally. `uv build` builds the wheel
from its source distribution. The checker verifies package/version consistency,
the licence, typing marker, console entry point, source coverage of wheel files,
and common accidental private/local paths. It does not replace a manual review of
the release contents or a secret scanner.

CI also installs the wheel in a fresh Python 3.10 environment outside the checkout,
checks the import/typing marker and runs the provisioning CLI's `--help`. These
checks do not contact MTN or provision credentials. Unit tests run on Python
3.10–3.14; live sandbox tests remain excluded.

After merging the workflows, manually run **Publish to PyPI → Run workflow** to
run verification and produce artifacts **without publishing**. `workflow_dispatch`
never enters the publish job. Inspect the `python-distributions` artifact.

## First and subsequent releases

1. Review the code and API; choose the intended version in `pyproject.toml`
   (currently `0.1.0`). Update the changelog for the actual release. For later
   releases, `uv version <version>` updates project metadata/lock state.
2. Run the checks, review and commit the release changes, then push them through
   your normal review process. Never tag unreviewed code or include `.env`/keys.
3. Create the matching tag, e.g. `v0.1.0`, at that reviewed commit. Publish a GitHub
   release for it **only when you intend to upload to real PyPI**. A draft release
   is not sufficient; publishing the release triggers the workflow.
4. Verification reruns against that release commit and requires an exact
   `v<project version>` tag. The publish job waits for successful verification and
   configured `pypi` environment approval. It downloads the already validated
   artifacts, does not rebuild them, and uses PyPI Trusted Publishing.
5. Verify the PyPI project and install the pinned release in a fresh environment:

   ```bash
   uv run --no-project --with mtn-momo-python==0.1.0 python -c "import mtn_momo"
   ```

   Run that outside this checkout. Check the console entry point too. Only after
   successful publication, replace the README's source-only installation note
   with `pip install mtn-momo-python` (or `uv add mtn-momo-python`).

Published files cannot be replaced. Fixes need a new version; do not reuse a
version/tag with different artifacts. If an upload is interrupted, inspect PyPI
before retrying. A workflow rerun rebuilds, so identical-artifact checks may reject
a partially uploaded release; retain the original workflow artifacts for recovery
instead of publishing different bytes under the same version.

This repository preparation does not create PyPI accounts/publishers, configure
GitHub environment protection, commit/tag/push code, publish a release or upload
anything. Those are deliberate maintainer actions.
