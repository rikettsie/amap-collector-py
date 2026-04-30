from pathlib import Path
from typing import Optional

import typer

from amap_collector.core.router import AmapClientBuilder, AmapClientBuilderError
from amap_collector.cli.output import OutputError, write_output

app = typer.Typer(add_completion=False)


@app.command()
def run(
    area_code: str = typer.Argument(help="French department code (2 digits) or zip code (5 digits); the latter (zip code) is only applicable to Île-de-France departments"),
    km_radius: str = typer.Option(None, "--km-radius", help="Search radius in km (2, 5, 10, 15, 20), only applicable to Île-de-France departments"),
    output_file: Optional[Path] = typer.Option(None, "--output-file", help="Output file path (.json or .csv)"),
    farms_only: bool = typer.Option(False, "--farms-only", help="Collect only farm information (applicable to Haute-Normandie and Loire-Atlantique only)"),
) -> None:
    if output_file is not None and output_file.suffix not in (".json", ".csv"):
        typer.echo("Error: --output-file must have a .json or .csv extension", err=True)
        raise typer.Exit(code=1)

    try:
        client_builder = AmapClientBuilder(area_code)
        zip_code: Optional[str] = client_builder.target()["zip_code"]

        client = client_builder.get_client()

        if farms_only and not client_builder.supports_farm_list():
            typer.echo("Error: --farms-only is not supported for this region", err=True)
            raise typer.Exit(code=1)
        
        if km_radius:
            if client_builder.supports_km_radius():
                client.with_km_radius(km_radius)
            else:
                typer.echo("Error: --km_radius is not supported for this region", err=True)
                raise typer.Exit(code=1)
        
        if zip_code:
            if client_builder.supports_zip_code():
                client.with_zip_code(zip_code)
            else:
                typer.echo("Error: zip_code scraping is not supported for this region", err=True)
                raise typer.Exit(code=1)
        
        client.with_department(client_builder.target()["dept"])
        results = client.get_farm_list() if farms_only else client.get_amap_list()

    except (AmapClientBuilderError, OutputError, RuntimeError) as e:
        typer.echo(e, err=True)
        raise typer.Exit(code=1)

    write_output(results, output_file)

    if output_file is not None:
        typer.echo(f"Saved {len(results)} entries to {output_file}")
