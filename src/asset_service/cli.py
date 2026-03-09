"""
Command-line interface for the Asset Service.
"""

import sys
from pathlib import Path

import click


@click.group()
@click.option("--registry", required=False, help="Path to registry database")
@click.pass_context
def cli(ctx, registry):
    """Asset Validation & Registration Service CLI"""
    # this is here as a quick hack to get the CLI to work in a shell
    # and from the tests on my machine. How this works in production
    # will depend on the actual deployment mechanism
    ctx.ensure_object(dict)
    working_folder = Path(__file__).resolve().parent.parent
    print(working_folder)
    if working_folder not in sys.path:
        sys.path.append(str(working_folder))
    from asset_service import api, db

    ctx.obj.update({"service": api, "registry": db.AssetRegistry(registry)})


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.pass_context
def load(ctx, file_path):
    """Load assets from a JSON file."""
    _service = ctx.obj["service"]
    file_path = Path(file_path).resolve()
    click.echo(f"Loading assets from: {file_path}")
    if not _service.load_from_json(file_path, registry=ctx.obj["registry"]):
        sys.exit(f"Failed to load assets from: {file_path}")


@cli.command()
@click.argument("asset_name")
@click.argument("asset_type")
@click.pass_context
def add(ctx, asset_name, asset_type):
    """Add an asset from a JSON file."""
    _service = ctx.obj["service"]
    click.echo(f"Adding asset: {asset_name}/{asset_type}")
    if _service.add_asset(asset_name, asset_type, registry=ctx.obj["registry"]) is None:
        sys.exit(f"Failed to add asset: {asset_name}/{asset_type}")


@cli.command()
@click.argument("asset_name")
@click.argument("asset_type")
@click.pass_context
def get(ctx, asset_name, asset_type):
    """Get an asset by name and type."""
    _service = ctx.obj["service"]
    asset = _service.get_asset(asset_name, asset_type, registry=ctx.obj["registry"])
    if asset is None:
        sys.exit(f"Asset not found: {asset_name}/{asset_type}")
    click.echo(f"Found Asset: {asset_name}/{asset_type}")


@cli.command(name="list")
@click.option(
    "--asset-name",
    "asset_name",
    required=False,
    default=None,
    help="Filter by asset name",
)
@click.option(
    "--asset-type",
    "asset_type",
    required=False,
    default=None,
    help="Filter by asset type",
)
@click.pass_context
def list_cmd(ctx, asset_name, asset_type):
    """List all assets."""
    _service = ctx.obj["service"]
    click.echo(
        f"Listing Assets: name='{asset_name or ''}' asset_type='{asset_type or ''}'"
    )
    results = list(
        _service.get_assets(asset_name, asset_type, registry=ctx.obj["registry"])
    )
    for result in results:
        click.echo(f"Found Asset: {result.name}/{result.asset_type}")
    sys.exit(0 if results else 1)


@cli.group()
def versions():
    """CLI group to manage asset version subcommands"""
    pass


@versions.command("add")
@click.argument("asset_name")
@click.argument("asset_type")
@click.argument("department")
@click.argument("version_num", type=int)
@click.argument("status")
@click.pass_context
def versions_add(ctx, asset_name, asset_type, department, version_num, status):
    """Add an asset version from a JSON file."""
    _service = ctx.obj["service"]
    click.echo(f"Adding asset: {asset_name}/{asset_type}")
    asset = _service.add_asset(asset_name, asset_type, registry=ctx.obj["registry"])
    if not asset:
        sys.exit(f"Failed to add asset: {asset_name}/{asset_type}")
    click.echo(f"Adding version: {department}/{version_num} - {status}")
    if (
        _service.add_version(
            asset, department, version_num, status, registry=ctx.obj["registry"]
        )
        is None
    ):
        sys.exit(f"Failed to add version: {department}/{version_num} - {status}")


@versions.command("get")
@click.argument("asset_name")
@click.argument("asset_type")
@click.argument("department")
@click.argument("version_num", type=int)
@click.pass_context
def versions_get(ctx, asset_name, asset_type, department, version_num):
    """Get a specific asset version."""
    _service = ctx.obj["service"]
    result = _service.get_version(
        asset_name, asset_type, department, version_num, registry=ctx.obj["registry"]
    )
    if result is None:
        sys.exit(
            f"Version not found: {asset_name}/{asset_type} - {department}:{version_num}"
        )
    click.echo(
        f"Found Version: {asset_name}/{asset_type} - {department}:{version_num} = {result.state.status}"
    )


@versions.command("list")
@click.argument("asset_name")
@click.argument("asset_type")
@click.option("--department", required=False, default=None, help="Filter by department")
@click.option("--status", required=False, default=None, help="Filter by status")
@click.option(
    "--version", required=False, default=None, type=int, help="Filter by version"
)
@click.pass_context
def versions_list(ctx, asset_name, asset_type, department, status, version):
    """List all versions of an asset."""
    _service = ctx.obj["service"]


def main():
    """Entry point for the CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()
