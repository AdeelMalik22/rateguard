# How to Build and Publish RequestGuard

This guide explains how to build your package and upload it to PyPI whenever you make changes.

---

## 1. Update the Version
Before creating a new build, you must increase the version number so PyPI knows it's a new release.

1. Open `pyproject.toml`.
2. Find `version = "0.1.0"`.
3. Change it to the next logical version (e.g., `version = "0.1.1"`).

---

## 2. Clean Old Builds
It's best practice to delete the old distribution files to avoid uploading the wrong ones.

```bash
rm -rf dist/
```

---

## 3. Create the Build
Use Python's build tool to generate the `.whl` (wheel) and `.tar.gz` (source) files.

```bash
venv/bin/python -m build
```
*You will see a `dist/` directory generated with your new version files.*

---

## 4. Upload to PyPI
Use `twine` to securely upload your new build to the PyPI registry.

```bash
venv/bin/twine upload dist/*
```

*Twine will automatically use the API tokens you configured in `~/.pypirc`.*

---

## 5. Verify the Release
Go to [PyPI](https://pypi.org/project/requestguard/) and verify your new version is live! Users can now update the package using:

```bash
pip install requestguard --upgrade
```
