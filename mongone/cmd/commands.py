import os
import click
import yaml
from datetime import datetime
from rich import box
from rich.table import Table
from rich.panel import Panel
import glob
from inquirer import prompt, List, Confirm



from mongone.core.config import load_config, save_config
from mongone.core.report_generator import (
    generate_report_logic,
    transform_force_data_to_expected_structure,
)
from mongone.utils.rendering import render_html_report, display_summary
from mongone.utils.helpers import validate_file_exists, Console
from mongone.optimization.plans import generate_plans
from mongone.optimization.execute import execute_plan

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
        "autoscaling_defaults": {
            "provider_name": "AWS",
            "region_name": "US_GOV_WEST_1",
            "max_instance_size": "M40",
            "min_instance_size": "M10",
        },
    }
    save_config(config)
    console.print("[green]Configuration file 'mongone.yaml' created successfully.[/]")

    # Create example 'force-data.yaml' for generating sample data
    force_data_example = {
        "projects": [
            {
                "name": "Example Project",
                "environment": "staging",
                "clusters": [
                    {
                        "name": "example-cluster-1",
                        "last_access_time": "2024-01-01T12:00:00",
                        "autoscaling_compute": False,
                        "autoscaling_disk": True,
                        "cost": 100.0,
                    },
                    {
                        "name": "example-cluster-2",
                        "last_access_time": None,
                        "autoscaling_compute": True,
                        "autoscaling_disk": False,
                        "cost": 150.0,
                    },
                ],
            }
        ]
    }

    with open("force-data.yaml", "w") as file:
        yaml.dump(force_data_example, file)

    console.print("[green]Example 'force-data.yaml' file created successfully.[/]")


@cli.command()
@click.option(
    "--force",
    is_flag=True,
    help="Use force data file instead of fetching from MongoDB Atlas",
)
@click.option(
    "--test",
    is_flag=True,
    help="Use test data file instead of fetching from MongoDB Atlas",
)
@click.option(
    "--period", default=30, help="Period (in days) to consider databases as unused."
)
def generate_report(force, test, period):
    """Generate a usage report for all projects in the MongoDB Atlas organization."""
    config = load_config()

    if force:
        if not validate_file_exists("force-data.yaml"):
            console.print(f"[red]Force data file 'force-data.yaml' not found.[/]")
            return
        # Load data from force-data.yaml
        with open("force-data.yaml", "r") as file:
            data = yaml.safe_load(file)
        # Ensure the data structure matches the expected format
        data = transform_force_data_to_expected_structure(data)
    elif test:
        if not validate_file_exists("test-data.yaml"):
            console.print(f"[red]Test data file 'test-data.yaml' not found.[/]")
            return
        # Load data from test-data.yaml
        with open("test-data.yaml", "r") as file:
            data = yaml.safe_load(file)
        # Ensure the data structure matches the expected format
        data = transform_force_data_to_expected_structure(data)
    else:
        data = generate_report_logic(config, period)

    # Render the HTML report
    render_html_report(data)

    generate_plans(config, data)

    # Display summary in the console
    display_summary(data)


@cli.command()
@click.option(
    "--plan-type", 
    type=click.Choice(["autoscaling_computation", "autoscaling_disk", "scale_to_free_tier", "delete_clusters"]),
    help="Type of plan to execute."
)
@click.option(
    "--environment", 
    type=click.Choice(["staging", "production", "unknown"]),
    help="Environment to execute the plan in."
)
def execute(plan_type, environment):
    """Execute a specific plan for the given environment."""

    # If plan_type is not provided, prompt the user to select one
    if not plan_type:
        plan_options = [
            ("autoscaling_computation", "Enable Autoscaling for Computation"),
            ("autoscaling_disk", "Enable Autoscaling for Disk"),
            ("scale_to_free_tier", "Scale to Free Tier"),
            ("delete_clusters", "Delete Clusters")
        ]
        questions = [
            List(
                "plan_type",
                message="Select plan type:",
                choices=[option[0] for option in plan_options]
            )
        ]
        answers = prompt(questions)
        plan_type = answers.get("plan_type")

    # If environment is not provided, prompt the user to select one
    if not environment:
        env_options = [
            ("staging", "Staging Environment"),
            ("production", "Production Environment"),
            ("unknown", "Unknown Environment")
        ]
        questions = [
            List(
                "environment",
                message="Select environment:",
                choices=[option[0] for option in env_options]
            )
        ]
        answers = prompt(questions)
        environment = answers.get("environment")

    # Find all plan files for the selected type and environment
    plans_dir = f"./plans/{environment}"
    plan_files = glob.glob(f"{plans_dir}/{plan_type}_plan_*.yaml")

    if not plan_files:
        console.print(f"[red]No plan files found for {plan_type} in environment {environment}. Skipping execution.[/]")
        return

    # Display available plans and ask the user to select one
    console.print(Panel("[bold]Available Plans:[/]", style="blue"))
    plan_files.sort()
    options = [(str(idx + 1), plan_file) for idx, plan_file in enumerate(plan_files)]
    questions = [
        List(
            "selected_plan",
            message="Select a plan to execute:",
            choices=[f"{idx}: {plan_file}" for idx, plan_file in options]
        )
    ]
    answers = prompt(questions)
    selected_index = int(answers.get("selected_plan").split(":")[0])
    selected_plan_file = plan_files[selected_index - 1]

    # Display the selected plan in a Terraform-like format
    with open(selected_plan_file, "r") as plan_file:
        plan_content = yaml.safe_load(plan_file)
        table = Table(title="Plan Preview", box=box.SIMPLE, highlight=True)
        table.add_column("Environment", style="magenta")
        table.add_column("Action", style="cyan")
        table.add_column("Cluster Details", style="green")

        for cluster in plan_content.get('clusters', []):
            action = plan_content.get('action', 'Unknown Action')
            environment = environment.capitalize()
            cluster_details = f"Cluster Name: {cluster['cluster_name']}, Project Name: {cluster['project_name']}, Project ID: {cluster['project_id']}, Org ID: {cluster['org_id']}"
            table.add_row(environment, action, cluster_details)

        console.print(table)

    # Confirm execution
    questions = [
        Confirm(
            "execute",
            message="Do you want to execute this plan?"
        )
    ]
    answers = prompt(questions)
    if answers.get("execute"):
        execute_plan(plan_type, environment, selected_plan_file)
    else:
        console.print("[yellow]Execution aborted by user.[/]")

if __name__ == "__main__":
    cli()
