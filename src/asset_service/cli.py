"""
Command-line interface for the Asset Service.
"""

import sys
from pathlib import Path

import click


@click.group()
@click.pass_context
def cli(ctx):
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

    ctx.obj.update({"service": api, "db": db})


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.pass_context
def load(ctx, file_path):
    """Load assets from a JSON file."""
    _service = ctx.obj["service"]
    file_path = Path(file_path).resolve()
    click.echo(f"Loading assets from: {file_path}")
    if not _service.load_from_json(file_path):
        sys.exit(f"Failed to load assets from: {file_path}")


@cli.command()
@click.argument("asset_name")
@click.argument("asset_type")
@click.pass_context
def add(ctx, asset_name, asset_type):
    """Add an asset from a JSON file."""
    _service = ctx.obj["service"]
    click.echo(f"Adding asset: {asset_name}/{asset_type}")
    if _service.add_asset(asset_name, asset_type) is None:
        sys.exit(f"Failed to add asset: {asset_name}/{asset_type}")


@cli.command()
@click.argument("asset_name")
@click.argument("asset_type")
@click.pass_context
def get(ctx, asset_name, asset_type):
    """Get an asset by name and type."""
    _service = ctx.obj["service"]


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
    _db = ctx.obj["db"]
    click.echo(f"Adding asset: {asset_name}/{asset_type}")
    registry = _db.AssetRegistry()
    asset = _service.add_asset(asset_name, asset_type, registry=registry)
    if not asset:
        sys.exit(f"Failed to add asset: {asset_name}/{asset_type}")
    click.echo(f"Adding version: {department}/{version_num} - {status}")
    if (
        _service.add_version(asset, department, version_num, status, registry=registry)
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
