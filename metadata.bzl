"""One distribution contract for the wheel and direct source installation."""

load("@rules_python//python:packaging.bzl", "py_package", "py_wheel")
load("@sonic_build_infra//python:site_packages.bzl", "site_packages")

# These fields reproduce the effective setup.py declaration, including no scripts.
_METADATA = dict(
    distribution = "swsssdk",
    version = "2.0.1",
    python_tag = "py3",
    requires = [
        'redis>=4.5.4;python_version >= "3.0"',
        'redis>=3.5.3;python_version < "3.0"',
        "redis-dump-load",
    ],
    extra_requires = {"high_perf": ["hiredis>=0.1.4"]},
    entry_points = {},
    license = "Apache 2.0",
    author = "SONiC Team",
    author_email = "linuxnetdev@microsoft.com",
    maintainer = "Thomas Booth",
    maintainer_email = "thomasbo@microsoft.com",
    summary = "Switch State service Python utility library.",
    classifiers = [
        "Intended Audience :: Developers",
        "Operating System :: Linux",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python",
    ],
    license_files = ["LICENSE"],
    extra_distinfo_files = {"LICENSE": "licenses/LICENSE"},
    regular_file_mode = "0644",
)

def distribution_targets():
    py_package(
        name = "package_contents",
        packages = ["src.swsssdk"],
        deps = [":swsssdk"],
    )
    py_wheel(
        name = "swsssdk.wheel",
        deps = [":package_contents"],
        strip_path_prefixes = ["src"],
        **_METADATA
    )
    site_packages(
        name = "swsssdk.runtime",
        files = {
            "src/swsssdk/__init__.py": "swsssdk/__init__.py",
            "src/swsssdk/configdb.py": "swsssdk/configdb.py",
            "src/swsssdk/dbconnector.py": "swsssdk/dbconnector.py",
            "src/swsssdk/exceptions.py": "swsssdk/exceptions.py",
            "src/swsssdk/interface.py": "swsssdk/interface.py",
            "src/swsssdk/port_util.py": "swsssdk/port_util.py",
            "src/swsssdk/sonic_db_dump_load.py": "swsssdk/sonic_db_dump_load.py",
            "src/swsssdk/util.py": "swsssdk/util.py",
            "src/swsssdk/config/database_config.json": "swsssdk/config/database_config.json",
        },
        site_packages = "/usr/local/lib/python3.13/dist-packages",
        scripts = "/usr/local/bin",
        headers = "/usr/local/include",
        data_prefix = "/usr/local",
        interpreter = "/usr/bin/python3",
        runtime_deps = ["@redis_dump_load//:install"],
        **_METADATA
    )
