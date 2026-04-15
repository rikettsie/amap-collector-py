from pathlib import Path
from typing import Optional

import typer

from amap_scraper.core.client import Client, ClientError
from amap_scraper.core.validations import DEFAULT_DEPT, DEFAULT_RADIUS, ValidationError
from amap_scraper.cli.output import OutputError, write_output

app = typer.Typer(add_completion=False)


@app.command()
def run(
    department: str = typer.Option(DEFAULT_DEPT, "--department", help="Department code (75, 77, 78, 91, 92, 93, 94, 95)"),
    km_radius: str = typer.Option(DEFAULT_RADIUS, "--km-radius", help="Search radius in km (2, 5, 10, 15, 20)"),
    zip_code: Optional[str] = typer.Option(None, "--zip-code", help="French zip code to search around"),
    coordinates: Optional[tuple[float, float]] = typer.Option((None, None), "--coordinates", help="Latitude and longitude", show_default=False),
    output_file: Optional[Path] = typer.Option(None, "--output-file", help="Output file path (.json or .csv)"),
) -> None:
    if output_file is not None and output_file.suffix not in (".json", ".csv"):
        typer.echo("Error: --output-file must have a .json or .csv extension", err=True)
        raise typer.Exit(code=1)

    try:
        client = Client().with_department(department).with_km_radius(km_radius)

        if zip_code:
            client = client.with_zip_code(zip_code)

        lat, lng = coordinates or (None, None)
        if lat is not None and lng is not None:
            client = client.with_coordinates(str(lat), str(lng))

        results = client.get_amap_list()

    except (ValidationError, ClientError, OutputError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

    write_output(results, output_file)

    if output_file is not None:
        typer.echo(f"Saved {len(results)} entries to {output_file}")
