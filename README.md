# AMAP website scraper

This is a simple information collector for the french AMAP network. It scrapes the AMAP website and returns a structured object list.

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

The cli is built with [Typer](https://typer.tiangolo.com/), you can explore command parameters via the `--help` modifier. See details below.

`--department` The department zip code (available options: 75, 77, 78, 91, 92, 93, 94, 95)  [default: 75]

`--zip-code` The french zip code to search around (when specified, it fully **overrides** the `--department` parameter)

`--km-radius` The Search radius in km (available options: 2, 5, 10, 15, 20) [default: 2]

`--output-file` The otput file path (.json or .csv)

`--help` It summarizes all these parameters and exit

**Note:** Results are shown by default in the standard output, unless a file path is specified via the `--output-file` modifier (`JSON` and `CSV` formats are only supported).

## Examples

### Example 1:

Retrieving all AMAP points in central Paris which is in the 75th department, across a radius of 10 km, and see results in the standard output:

```bash
  uv run python main.py --department 75 --km_radius 10
```

### Example 2:

Retrieving all AMAP points around the 12th arrondissement of Paris (zip code 75012), and see results in the standard output:

```bash
  uv run python main.py --zip_code 75
```

### Example 3:

Retrieving all AMAP points in Montreuil (Seine-Saint-Denis) which is in the 93rd department and see results in the standard output:

```bash
  uv run python main.py --department 93 
```

### Example 5:

Like the previous one, but saving the output iton a JSON file:

```bash
  uv run python main.py --department 93 --output-file /tmp/amaps_department93.json
```

# Docker containerization

## Build

...

## Run

...

# Run tests

...
