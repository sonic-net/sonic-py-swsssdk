"""Check upstream setup.py's distribution and installed-package contracts."""
import base64
import configparser
import csv
import email
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import runpy
import subprocess
import sys
import tarfile
import tempfile
import types
import unittest
from unittest.mock import patch
import zipfile

WHEEL, RUNTIME, SETUP = map(Path, sys.argv[1:4])
RUNTIME_METADATA = list(map(Path, sys.argv[4:]))
del sys.argv[1:]
SITE = "usr/local/lib/python3.13/dist-packages/"


def setup_contract():
    captured = {}
    setuptools = types.ModuleType("setuptools")
    setuptools.setup = lambda **kwargs: captured.update(kwargs)
    with patch.dict(sys.modules, {"setuptools": setuptools}):
        runpy.run_path(str(SETUP))
    return captured


def requirement(value):
    # Whitespace, quote style and redundant grouping do not change these markers.
    return re.sub(r"[\s()]", "", value).replace("'", '"')


class DistributionContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = setup_contract()
        cls.dist_info = cls.contract["name"] + "-" + cls.contract["version"] + ".dist-info/"
        root = SETUP.parent
        cls.payload = {}
        for package in cls.contract["packages"]:
            source = root / cls.contract["package_dir"][package]
            for path in source.glob("*.py"):
                cls.payload[package + "/" + path.name] = path.read_bytes()
            for pattern in cls.contract["package_data"].get(package, []):
                for path in source.glob(pattern):
                    cls.payload[package + "/" + path.relative_to(source).as_posix()] = path.read_bytes()
        with zipfile.ZipFile(WHEEL) as archive:
            names = [name for name in archive.namelist() if not name.endswith("/")]
            if len(names) != len(set(names)):
                raise AssertionError("duplicate wheel members")
            for info in archive.infolist():
                if not info.is_dir() and (info.external_attr >> 16) & 0o777 != 0o644:
                    raise AssertionError("incorrect wheel file mode: " + info.filename)
            cls.wheel = {name: archive.read(name) for name in names}
        with tarfile.open(RUNTIME) as archive:
            cls.members = {}
            cls.installed = {}
            for member in archive.getmembers():
                name = member.name.removeprefix("./")
                if member.isdir():
                    if (member.mode & 0o777, member.uid, member.gid) != (0o755, 0, 0):
                        raise AssertionError("incorrect directory attributes: " + name)
                    continue
                if not member.isfile() or name in cls.members:
                    raise AssertionError("duplicate or non-file TAR member: " + name)
                cls.members[name] = member
                cls.installed[name] = archive.extractfile(member).read()

    def check_metadata(self, files, prefix):
        metadata = email.message_from_bytes(files[prefix + self.dist_info + "METADATA"])
        for source, field in {
            "name": "Name", "version": "Version", "description": "Summary",
            "license": "License", "author": "Author", "author_email": "Author-email",
            "maintainer": "Maintainer", "maintainer_email": "Maintainer-email",
        }.items():
            self.assertEqual(metadata[field], self.contract[source], field)
        self.assertEqual(metadata.get_all("Classifier"), self.contract["classifiers"])
        self.assertIsNone(metadata["Requires-Python"])
        expected = list(self.contract["install_requires"])
        for extra, dependencies in self.contract["extras_require"].items():
            expected.extend(dependency + '; extra == "' + extra + '"' for dependency in dependencies)
        self.assertCountEqual(list(map(requirement, metadata.get_all("Requires-Dist", []))),
                              list(map(requirement, expected)))
        self.assertCountEqual(metadata.get_all("Provides-Extra", []), self.contract["extras_require"])
        entries = configparser.ConfigParser()
        entries.read_string(files.get(prefix + self.dist_info + "entry_points.txt", b"").decode())
        self.assertEqual(entries.sections(), list(self.contract["entry_points"]))
        for license_file in metadata.get_all("License-File", []):
            self.assertEqual(files[prefix + self.dist_info + "licenses/" + license_file],
                             (SETUP.parent / license_file).read_bytes())
        wheel = email.message_from_bytes(files[prefix + self.dist_info + "WHEEL"])
        self.assertEqual(wheel["Root-Is-Purelib"].lower(), "true")
        self.assertEqual(wheel.get_all("Tag"), ["py3-none-any"])

    def check_record(self, files, prefix):
        record = prefix + self.dist_info + "RECORD"
        seen = set()
        for name, digest, size in csv.reader(io.StringIO(files[record].decode())):
            path = posixpath.normpath(prefix + name)
            self.assertNotIn(path, seen)
            seen.add(path)
            self.assertIn(path, files)
            if path == record:
                self.assertEqual((digest, size), ("", ""))
            else:
                self.assertEqual(int(size), len(files[path]))
                algorithm, encoded = digest.split("=", 1)
                self.assertEqual(algorithm, "sha256")
                self.assertEqual(encoded, base64.urlsafe_b64encode(
                    hashlib.sha256(files[path]).digest()).rstrip(b"=").decode())
        self.assertEqual(seen, set(files))

    def test_distributions(self):
        for files, prefix in [(self.wheel, ""), (self.installed, SITE)]:
            with self.subTest(prefix=prefix):
                self.check_metadata(files, prefix)
                self.check_record(files, prefix)
                actual = {name.removeprefix(prefix): content for name, content in files.items()
                          if name.startswith(prefix + "swsssdk/")}
                self.assertEqual(actual, self.payload)
                # The sole package owns these files; dependencies have their own TARs.
                self.assertTrue(all(name.startswith(prefix + "swsssdk/") or
                                    name.startswith(prefix + self.dist_info) for name in files))
                licenses = [value for name, value in files.items()
                            if name.startswith(prefix + self.dist_info) and name.endswith("/LICENSE")]
                self.assertIn((SETUP.parent / "LICENSE").read_bytes(), licenses)
        for name, member in self.members.items():
            self.assertEqual((member.mode & 0o777, member.uid, member.gid), (0o644, 0, 0), name)

    def test_runtime_metadata(self):
        values = [json.loads(path.read_text()) for path in RUNTIME_METADATA]
        self.assertCountEqual([value["distribution"] for value in values], ["swsssdk", "redis-dump-load"])
        own = next(value for value in values if value["distribution"] == "swsssdk")
        self.assertEqual(own["version"], self.contract["version"])
        self.assertEqual(own["entry_points"], self.contract["entry_points"])
        self.assertCountEqual(own["extras"], self.contract["extras_require"])
        metadata = email.message_from_bytes(self.wheel[self.dist_info + "METADATA"])
        self.assertCountEqual(list(map(requirement, own["requires_dist"])),
                              list(map(requirement, metadata.get_all("Requires-Dist", []))))
        dependency = next(value for value in values if value["distribution"] == "redis-dump-load")
        self.assertEqual(dependency["version"], "1.1")
        self.assertEqual(dependency["requires_dist"], ["redis"])

    def test_installed_package(self):
        with tempfile.TemporaryDirectory() as temporary:
            site = Path(temporary) / SITE
            for name, content in self.installed.items():
                self.assertFalse(PurePosixPath(name).is_absolute())
                self.assertNotIn("..", PurePosixPath(name).parts)
                path = Path(temporary) / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            distribution = next(importlib.metadata.distributions(path=[str(site)]))
            self.assertEqual(distribution.metadata["Name"], self.contract["name"])
            self.assertEqual(distribution.version, self.contract["version"])
            self.assertEqual(list(distribution.entry_points), [])
            self.assertEqual(json.loads((site / "swsssdk/config/database_config.json").read_text()),
                             json.loads(self.payload["swsssdk/config/database_config.json"]))
            # -I removes source/runfiles PYTHONPATH; this imports only the installation.
            code = "import sys;sys.path.insert(0, sys.argv[1]);import swsssdk"
            result = subprocess.run([sys.executable, "-I", "-c", code, str(site)],
                                    cwd=temporary, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ImportError: sonic-py-swsssdk been deprecated, please switch to sonic-swss-common.",
                          result.stderr)


if __name__ == "__main__":
    unittest.main()
