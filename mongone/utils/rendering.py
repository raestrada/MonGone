import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from rich.table import Table
from mongone.utils.helpers import Console

console = Console()


def render_html_report(data):
    """Render the HTML report using Jinja2 template."""
    template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("report.html")
    output_from_parsed_template = template.render(
        projects=data["report_data"],
        total_clusters=data["total_clusters"],
        percentage_no_autoscaling_compute=(
            data["clusters_without_autoscaling_compute"] / data["total_clusters"]
        )
        * 100,
        percentage_no_autoscaling_disk=(
            data["clusters_without_autoscaling_disk"] / data["total_clusters"]
        )
        * 100,
        percentage_unused_clusters=(
            data["unused_cluster_count"] / data["total_clusters"]
        )
        * 100,
        total_cost=data["total_cost"],
    )

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


def display_summary(data):
    """Display a summary report in the console using rich.Table."""
    report_data = data["report_data"]
    all_unused_clusters = data["all_unused_clusters"]

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
            status = "In Use" if cluster["inuse"]  else "Unused"
            autoscaling_compute = (
                "Enabled" if cluster["autoscaling_compute"] else "Disabled"
            )
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
