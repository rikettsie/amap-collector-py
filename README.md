# AMAP website scraper

This is a simple information collector for the french AMAP network. It scrapes the [AMAP website](https://amap-idf.org/les-amap/trouver-une-amap-en-idf) and returns a structured object list.

# Usage

The scraper can be imported as a package or launched in the command line via the cli.

## Package usage

The typical use case is importing the `AmapClient` in your code and the `AmapClientError` class eventually.

An `AmapClient` object exposes a fluent interface to easily set the target parameters. Here below an import example (please see the documentation for parameter detailed description).

```Python
from amap_scraper.core import AmapClient

c = AmapClient().with_department(75).with_km_radius(10)
results = c.get_amap_list()

=> [
    {
        "name": "AMAP Coquéron",
        "status": "available_places",
        "website": "",
        "contact": {
        "name": "Agnès",
        "emails": [
            "email1@gmail.com",
            "email2@sauvegarde-paris.fr"
        ],
        "phones": [
            "01 XX XX XX XX",
            "07 XX XX XX XX"
        ]
        },
            "place": {
            "name": "Sauvegarde Paris",
            "address": "3 rue Coq Héron, 75001 PARIS",
            "delivery_time": "Mardi 17H-19H"
        },
        "comment": "Venez nombreux"
    },
    {
        ...
    },
   ...
   ]
```

## Cli usage

The cli is built with [Typer](https://typer.tiangolo.com/), you can explore command parameters via the `--help` modifier:

`--department` The department zip code (available options: 75, 77, 78, 91, 92, 93, 94, 95)  [default: 75]

`--zip-code` The french zip code to search around (when specified, it fully **overrides** the `--department` parameter)

`--km-radius` The Search radius in km (available options: 2, 5, 10, 15, 20) [default: 2]

`--output-file` The otput file path (.json or .csv)

`--help` It summarizes all these parameters and exit

**Note 1:** Results are shown by default in the standard output, unless a file path is specified via the `--output-file` modifier (`JSON` and `CSV` formats are only supported).

**Note 2:** The executable command name exposed after package installation is `amap_list`.

# Docker containerization

## Build

```bash
docker build -t amap-scraper .
```

## Run

Pass any `amap_list` option directly after the image name:

```bash
# stdout — all AMAPs in dept 93 within 5 km
docker run --rm amap-scraper --department 93 --km-radius 5

# save to a JSON file on the host
docker run --rm -v /tmp:/out amap-scraper --department 75 --output-file /out/amaps.json

# narrow search by zip code
docker run --rm amap-scraper --zip-code 75012
```

# Run tests

Tests require the dev dependencies. Run them with:

```bash
uv run pytest
```

To run a specific test file:

```bash
uv run pytest tests/core/test_parser.py -v
```

# Run linter

Using [ruff](https://docs.astral.sh/ruff/) for linting:

```bash
docker run --rm amap-scraper uv run --with ruff ruff check .
```
