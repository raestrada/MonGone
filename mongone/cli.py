import os
import click
import yaml
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from jinja2 import Environment, FileSystemLoader
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
from mongone.clusters import fetch_cluster_last_access, fetch_clusters, is_cluster_autoscaling
from mongone.invoices import get_latest_invoice_id, get_cluster_cost, fetch_invoice_csv
from mongone.projects import fetch_projects
from mongone.enviroments import detect_environment

console = Console()

CONFIG_FILE = "mongone.yaml"
DEFAULT_PERIOD = 30  # days
DEFAULT_ENV_PATTERNS = {"staging": r".*staging.*", "production": r".*production.*"}


def process_project(project, env_patterns, csv_data, cutoff_date):
    project_name = project["name"]
    environment = detect_environment(project_name, env_patterns)
    clusters = fetch_clusters(project["id"])

    if not clusters:
        return None

    project_report = {
        "name": project_name,
        "environment": environment,
        "clusters": [],
    }

    unused_clusters = []

    for cluster in clusters:
        cluster_name = cluster["name"]
        last_access_time = fetch_cluster_last_access(project["id"], cluster_name)
        cluster_unused = True
        autoscaling_compute, autoscaling_disk = is_cluster_autoscaling(project["id"], cluster_name)
        cluster_report = {
            "name": cluster_name,
            "last_access_time": (
                last_access_time.strftime("%Y-%m-%d %H:%M:%S")
                if last_access_time
                else "N/A"
            ),
            "databases": [],
            "cost": get_cluster_cost(csv_data, project_name, cluster_name),  # Updated to include project_name
            "autoscaling_compute": autoscaling_compute,
            "autoscaling_disk": autoscaling_disk,
        }

        if (
            last_access_time
            and last_access_time.replace(tzinfo=None) >= cutoff_date
        ):
            cluster_unused = False

        if cluster_unused:
            unused_clusters.append(cluster_name)

        project_report["clusters"].append(cluster_report)

    return project_report, unused_clusters


@click.group()
def cli():
    """MonGone CLI - Optimize MongoDB Atlas usage and generate reports."""
    pass


@cli.command()
@click.option("--atlas_org_id", required=True, help="MongoDB Atlas Organization ID")
@click.option(
    "--report_period_days", default=DEFAULT_PERIOD, help="Default report period in days"
)
def init(atlas_org_id, report_period_days):
    """Initialize the mongone configuration file."""
    config = {
        "atlas_org_id": atlas_org_id,
        "report_period_days": report_period_days,
        "environment_patterns": DEFAULT_ENV_PATTERNS,
    }
    with open(CONFIG_FILE, "w") as file:
        yaml.dump(config, file)
    console.print(
        f"Configuration file '{CONFIG_FILE}' created successfully.", style="bold green"
    )


@cli.command()
@click.option(
    "--period",
    default=DEFAULT_PERIOD,
    help="Period (in days) to consider databases as unused.",
)
def generate_report(period):
    """Generate a usage report for all projects in the MongoDB Atlas organization."""
    # Load configuration
    if not os.path.exists(CONFIG_FILE):
        console.print(
            f"Configuration file '{CONFIG_FILE}' not found. Run 'mongone init' first.",
            style="bold red",
        )
        return

    with open(CONFIG_FILE, "r") as file:
        config = yaml.safe_load(file)

    atlas_org_id = config.get("atlas_org_id")
    env_patterns = config.get("environment_patterns", DEFAULT_ENV_PATTERNS)

    console.print("[INFO] Fetching projects from MongoDB Atlas...", style="bold blue")
    # Fetch projects from MongoDB Atlas organization
    projects = fetch_projects(atlas_org_id)

    if not projects:
        console.print(
            "No projects found in the organization or an error occurred.",
            style="bold red",
        )
        return

    console.print(
        f"[INFO] Found {len(projects)} projects. Fetching latest invoice ID...",
        style="bold blue",
    )
    latest_invoice_id = get_latest_invoice_id(atlas_org_id)
    if not latest_invoice_id:
        console.print(
            "[ERROR] Unable to retrieve the latest invoice ID.", style="bold red"
        )
        return

    # Fetch the CSV data for the latest invoice
    csv_data = fetch_invoice_csv(atlas_org_id, latest_invoice_id)
    if not csv_data:
        console.print("[ERROR] Unable to retrieve invoice CSV data.", style="bold red")
        return

    console.print(
        f"[INFO] Found {len(projects)} projects. Fetching cluster information...",
        style="bold blue",
    )
    report_data = []
    all_unused_clusters = []
    cutoff_date = datetime.now().replace(tzinfo=None) - timedelta(days=period)

    with ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        futures = [executor.submit(process_project, project, env_patterns, csv_data, cutoff_date) for project in projects]
        for future in futures:
            result = future.result()
            if result:
                project_report, unused_clusters = result
                report_data.append(project_report)
                all_unused_clusters.extend(unused_clusters)

    # Render the HTML report using Jinja2
    console.print("[INFO] Rendering HTML report...", style="bold blue")
    render_html_report(report_data)

    # Display a summary in the console
    table = Table(title="MongoDB Atlas Organization Usage Report")
    table.add_column("Project Name", style="bold cyan")
    table.add_column("Environment", style="bold green")
    table.add_column("Cluster Name", style="bold magenta")
    table.add_column("Last Access Time", style="bold green")
    table.add_column("Status", style="bold yellow")
    table.add_column("Autoscaling Compute", style="bold blue")
    table.add_column("Autoscaling Disk", style="bold blue")
    table.add_column("Cost", style="bold red")

    for project in report_data:
        for cluster in project["clusters"]:
            status = "Unused" if cluster["name"] in all_unused_clusters else "In Use"
            autoscaling_compute = "Enabled" if cluster["autoscaling_compute"] else "Disabled"
            autoscaling_disk = "Enabled" if cluster["autoscaling_disk"] else "Disabled"
            table.add_row(
                project["name"],
                project["environment"],
                cluster["name"],
                cluster["last_access_time"],
                status,
                autoscaling_compute,
                autoscaling_disk,
                f"${cluster['cost']:.2f}",
            )

    console.print(table)


def render_html_report(data):
    """Render the HTML report using Jinja2 template."""
    env = Environment(loader=FileSystemLoader("mongone/templates"))
    template = env.get_template("report.html")
    output_from_parsed_template = template.render(projects=data)

    # Save the report in the 'reports' directory
    output_dir = "reports"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_file_path = os.path.join(
        output_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    )
    with open(output_file_path, "w") as f:
        f.write(output_from_parsed_template)

    console.print(f"Report generated: {output_file_path}", style="bold green")


if __name__ == "__main__":
    cli()
