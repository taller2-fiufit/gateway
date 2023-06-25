# Gateway

[![CI](https://github.com/taller2-fiufit/gateway/actions/workflows/ci.yml/badge.svg)](https://github.com/taller2-fiufit/gateway/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/taller2-fiufit/gateway/branch/main/graph/badge.svg?token=2PZDX6J4XX)](https://codecov.io/gh/taller2-fiufit/gateway)

## Dependencies

- make
- python3.11
- poetry

## Installation

After installing dependencies, run:

```bash
make install
```

## How to run

Run app locally with:

```bash
make run
```

***Note**: this will also install dependencies with poetry*

## Development pipeline

This project uses the *black* formatter, *flake8* linter, *mypy* static type checker, and *pytest* test suite in the CI pipeline.
To run all of these locally, use the command `make all`, or use one of the following make targets: `format`, `lint`, `mypy`, `test`.

## Documentation

Information about the API and the repository structure can be found in the [docs](./docs) folder.
