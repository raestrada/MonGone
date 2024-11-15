import click
from mongone.core.config import load_config, save_config
from mongone.core.report_generator import generate_report_logic
from mongone.utils.rendering import render_html_report, display_summary
from mongone.utils.helpers import validate_file_exists, Console

console = Console()


@click.group()
def cli():
    """MonGone CLI - Optimize MongoDB Atlas usage and generate reports."""
    pass


@cli.command()
@click.option("--atlas_org_id", required=True, help="MongoDB Atlas Organization ID")
@click.option("--report_period_days", default=30, help="Default report period in days")
def init(atlas_org_id, report_period_days):
    """Initialize the mongone configuration file and create an example force data file."""
    config = {
        "atlas_org_id": atlas_org_id,
        "report_period_days": report_period_days,
        "environment_patterns": {
            "staging": r".*staging.*",
            "production": r".*production.*",
        },
    }
    save_config(config)
    console.print("[green]Configuration file 'mongone.yaml' created successfully.[/]")
    # Additional logic for generating force-data.yaml if required


@cli.command()
@click.option(
    "--force",
    is_flag=True,
    help="Use force data file instead of fetching from MongoDB Atlas",
)
@click.option(
    "--period", default=30, help="Period (in days) to consider databases as unused."
)
def generate_report(force, period):
    """Generate a usage report for all projects in the MongoDB Atlas organization."""
    if force:
        if not validate_file_exists("force-data.yaml"):
            console.print(f"[red]Force data file 'force-data.yaml' not found.[/]")
            return
        # Logic for using force data
    else:
        config = load_config()
        data = generate_report_logic(config, period)

    # Render the HTML report
    render_html_report(data)
    # Display summary in the console
    display_summary(data)


if __name__ == "__main__":
    cli()
