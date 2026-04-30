# AMAP collector

This scraper collects the fragmented information of the french AMAP network from several web sources: 

- [AMAP Île-de-France](https://amap-idf.org);
- [AMAP Haute-Normandie](https://reseau-amap-hn.com);
- [Inter AMAP 44 (Nantes et Loire-Atlantique)](https://www.amap44.org);
- [AMAP for the rest of France](https://www.avenir-bio.fr);

It returns the targeted information in JSON or CSV formats.

# Usage

The client can be imported as a package or launched in the command line via the cli. See the embedded *docstrings* for full documentation on parameters or read this README further.

## Package usage

The typical use case is importing a specific AMAP client (e.g. `IdfAmapClient`, `HnAmapClient`, etc) in your code, and its error class eventually.

The AMAP client object exposes a fluent interface to easily set the target parameters. Here below an example of integration to fetch results around the 75th department (Paris area) over 10 km radius:

```python
from amap_collector.core.idf import IdfAmapClient

c = IdfAmapClient().with_department(75).with_km_radius(10)
results = c.get_amap_list()
```

where `results` is a list of `dict`s like:

```json
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
}
```

### Concurrent scraping

You can also run the scraper concurrently, on multiple area codes:

```python
import asyncio
from amap_collector.core.collector import collect

results = asyncio.run(collect(["75", "19", "80"], max_concurrent=4))
```

Or inside an async function:

```python
from amap_collector.core.collector import collect

async def main():
    results = await collect(["75", "19", "80"], max_concurrent=4)
```

**Note:** `max_concurrent` has a default equal to `8`.

## Cli usage

The cli is built with [Typer](https://typer.tiangolo.com/), you can explore command parameters and options via the `--help` modifier:

`area_code` A valid french department code or zip code; the latter (zip code) is applicable to the IDF scraper only

`--farms-only` Collect only farm information (applicable to HN and IA44 scrapers only)

`--km-radius` The Search radius in km (available options: 2, 5, 10, 15, 20) [default: 2]; this options is only valid for Île-de-France

`--output-file` The otput file path (.json or .csv)

`--help` It summarizes all these parameters and exit

**Note 1:** Results are shown by default in the standard output, unless a file path is specified via the `--output-file` modifier (`JSON` and `CSV` formats are only supported).

**Note 2:** The executable command name exposed after package installation is `amap_collector`.

# Docker containerization

## Build image

```bash
docker build -t amap-collector .
```

## Run the command

Pass any `amap_collector` option directly after the image name:

```bash
# stdout — all AMAPs in dept 93 within 5 km
docker run --rm amap-collector 93 --km-radius 5

# save to a JSON file on the host
docker run --rm -v /tmp:/out amap-collector 75 --output-file /out/amaps.json

# narrow search by zip code
docker run --rm amap-collector 75012
```

## Run tests

Tests require the dev dependencies. Run them with:

```bash
uv run pytest
```

To run a specific test file:

```bash
uv run pytest tests/core/test_parser.py -v
```

## Run the linter

Using [ruff](https://docs.astral.sh/ruff/) for linting:

```bash
docker run --rm amap-collector uv run --with ruff ruff check .
```
