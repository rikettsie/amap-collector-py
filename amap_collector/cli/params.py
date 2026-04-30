import asyncio
from pathlib import Path
from typing import Optional
import typer

from amap_collector.core.router import AmapClientBuilderError
from amap_collector.core.collector import collect, CollectionError, MAX_CONCURRENT
from amap_collector.cli.output import OutputError, write_output

app = typer.Typer(add_completion=False)


@app.command()
def run(
    area_code: str = typer.Argument(help="French department code (2 digits) or zip code (5 digits); the latter (zip code) is only applicable to Île-de-France departments"),
    km_radius: str = typer.Option(None, "--km-radius", help="Search radius in km (2, 5, 10, 15, 20), only applicable to Île-de-France departments"),
    output_file: Optional[Path] = typer.Option(None, "--output-file", help="Output file path (.json or .csv)"),
    farms_only: bool = typer.Option(False, "--farms-only", help="Collect only farm information (applicable to Haute-Normandie and Loire-Atlantique only)"),
    max_concurrent: int = typer.Option(MAX_CONCURRENT, "--max-concurrent", help="Maximum number of departments collected in parallel"),
) -> None:
    if output_file is not None and output_file.suffix not in (".json", ".csv"):
        typer.echo("Error: --output-file must have a .json or .csv extension", err=True)
        raise typer.Exit(code=1)

    codes = list({c.strip() for c in area_code.split(',')})
    try:
        results = asyncio.run(collect(codes, km_radius, farms_only, max_concurrent))
    except (AmapClientBuilderError, CollectionError, OutputError, RuntimeError) as e:
        typer.echo(e, err=True)
        raise typer.Exit(code=1)

    write_output(results, output_file)

    if output_file is not None:
        typer.echo(f"Saved {len(results)} entries to {output_file}")
