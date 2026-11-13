# Bazel build

This component targets SONiC's Python 3.13 environment with Bazel 8.5.1.
The Python distribution remains `swsssdk` version `2.0.1`.

```sh
bazel build //:swsssdk //:swsssdk.wheel //:swsssdk.runtime //:swsssdk.runtime_metadata
bazel test //:upstream_tests
```

Public targets:

- `:swsssdk`: Python source library and package configuration resource.
- `:swsssdk.wheel`: pure Python `swsssdk-2.0.1-py3-none-any.whl`.
- `:swsssdk.runtime`: this distribution's installation TAR and PythonRuntimeInfo.
  Files install under `/usr/local/lib/python3.13/dist-packages`. The runtime
  provider also associates the separate `redis-dump-load` installation and its
  metadata; its payload is not duplicated in this TAR.
- `:swsssdk.runtime_metadata`: transitive source distribution metadata JSON.

Wheel and installation targets share package contents and distribution metadata.
The installation target consumes source files directly. Image/rootfs consumers
resolve third-party runtime packages from the declared Requires-Dist constraints
and consume source distribution installation TARs separately.

The deprecated package intentionally raises ImportError during ordinary import.
The upstream suite checks that behavior. Its existing test-mode import exceptions
remain unchanged. `setup.py` passes empty entry_points, so this distribution
exports no console scripts. The historical Python 2 Make branch is disabled in
bookworm/trixie and is outside this Python 3 target environment.

## Tests and dependency lock

`:upstream_tests` runs all upstream pytest modules, with the existing coverage,
verbosity and JUnit options. Reports go to Bazel's test outputs. The subprocess
used by the deprecation test runs the managed Python interpreter.

`requirements-test.in` fixes the Redis dependency used by the source library and
the upstream test environment. `requirements-test.lock` fixes their transitive
versions and hashes. Update it with uv 0.12.18:

```sh
uv pip compile requirements-test.in --python-version 3.13 --generate-hashes --no-emit-index-url --output-file requirements-test.lock
```

Repeat that command and check that the lock stays unchanged. Production wheel
metadata preserves upstream dependency ranges, markers and the high_perf extra;
the test lock does not replace an image's runtime dependency resolution.

`tests/bazel_consumer` is an independent consumer module. It checks wheel and
installation contents against the effective upstream setup.py declaration, RECORD
hashes, resource bytes, metadata queries, the deprecated import, and transitive
source package metadata. For development, its root MODULE may temporarily use
`local_path_override(module_name = "sonic-py-swsssdk", path = "/absolute/source")`.
Update the consumer bazel_dep to the published commit-qualified version and
remove that override when validating a published registry version.

Local cache and registry settings can be placed in the ignored `.bazelrc.user`.

The GitHub Bazel workflow builds the public targets, runs the upstream suite,
and verifies the same checkout through the independent consumer module.
