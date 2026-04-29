from pathlib import Path
from typing import Optional

import typer

from amap_collector.core.router import AmapClientBuilder, AmapClientBuilderError
from amap_collector.cli.output import OutputError, write_output

app = typer.Typer(add_completion=False)


@app.command()
def run(
    area_code: str = typer.Argument(help="French department code (2 digits) or zip code (5 digits); the latter (zip code) is only applicable on Île-de-France departments"),
    km_radius: str = typer.Option(None, "--km-radius", help="Search radius in km (2, 5, 10, 15, 20), only applicable on Île-de-France departments"),
    output_file: Optional[Path] = typer.Option(None, "--output-file", help="Output file path (.json or .csv)"),
) -> None:
    if output_file is not None and output_file.suffix not in (".json", ".csv"):
        typer.echo("Error: --output-file must have a .json or .csv extension", err=True)
        raise typer.Exit(code=1)

    try:
        client_builder = AmapClientBuilder(area_code)
        client = client_builder.get_client()

        client.with_department(client_builder.target()["dept"])

        if client_builder.is_idf():
            if zip_code := client_builder.target()["zip_code"]:
                client.with_zip_code(zip_code)

            if km_radius:
                client.with_km_radius(km_radius)

        results = client.get_amap_list()

    except (AmapClientBuilderError, OutputError, RuntimeError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

    write_output(results, output_file)

    if output_file is not None:
        typer.echo(f"Saved {len(results)} entries to {output_file}")
