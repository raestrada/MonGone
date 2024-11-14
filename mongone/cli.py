import os
import click
import yaml
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from jinja2 import Environment, FileSystemLoader
import requests
from requests.auth import HTTPDigestAuth
import dateutil.parser

console = Console()

CONFIG_FILE = "mongone.yaml"
DEFAULT_PERIOD = 30  # days

@click.group()
def cli():
    """MonGone CLI - Optimize MongoDB Atlas usage and generate reports."""
    pass

@cli.command()
@click.option('--atlas_org_id', required=True, help='MongoDB Atlas Organization ID')
@click.option('--report_period_days', default=DEFAULT_PERIOD, help='Default report period in days')
def init(atlas_org_id, report_period_days):
    """Initialize the mongone configuration file."""
    config = {
        "atlas_org_id": atlas_org_id,
        "report_period_days": report_period_days
    }
    with open(CONFIG_FILE, "w") as file:
        yaml.dump(config, file)
    console.print(f"Configuration file '{CONFIG_FILE}' created successfully.", style="bold green")

@cli.command()
@click.option('--period', default=DEFAULT_PERIOD, help='Period (in days) to consider databases as unused.')
def generate_report(period):
    """Generate a usage report for all projects in the MongoDB Atlas organization."""
    # Load configuration
    if not os.path.exists(CONFIG_FILE):
        console.print(f"Configuration file '{CONFIG_FILE}' not found. Run 'mongone init' first.", style="bold red")
        return
    
    with open(CONFIG_FILE, "r") as file:
        config = yaml.safe_load(file)
    
    atlas_org_id = config.get("atlas_org_id")

    console.print("[INFO] Fetching projects from MongoDB Atlas...", style="bold blue")
    # Fetch projects from MongoDB Atlas organization
    projects = fetch_projects(atlas_org_id)

    if not projects:
        console.print("No projects found in the organization or an error occurred.", style="bold red")
        return

    console.print(f"[INFO] Found {len(projects)} projects. Fetching cluster information...", style="bold blue")
    report_data = []
    unused_clusters = []
    cutoff_date = datetime.now().replace(tzinfo=None) - timedelta(days=period)

    for project in projects:
        project_name = project["name"]
        console.print(f"[INFO] Fetching clusters for project: {project_name}", style="bold blue")
        clusters = fetch_clusters(project["id"])

        if not clusters:
            console.print(f"[WARNING] No clusters found for project: {project_name}", style="bold yellow")
            continue

        project_report = {
            "name": project_name,
            "clusters": []
        }

        for cluster in clusters:
            cluster_name = cluster["name"]
            console.print(f"[INFO] Fetching last access time for cluster: {cluster_name}", style="bold blue")
            last_access_time = fetch_cluster_last_access(project["id"], cluster_name)
            cluster_unused = True
            cluster_report = {
                "name": cluster_name,
                "last_access_time": last_access_time.strftime("%Y-%m-%d %H:%M:%S") if last_access_time else "N/A",
                "databases": []
            }

            if last_access_time and last_access_time.replace(tzinfo=None) >= cutoff_date:
                cluster_unused = False
            
            if cluster_unused:
                unused_clusters.append(cluster_name)
            
            project_report["clusters"].append(cluster_report)

        report_data.append(project_report)

        break

    # Render the HTML report using Jinja2
    console.print("[INFO] Rendering HTML report...", style="bold blue")
    render_html_report(report_data)

    # Display a summary in the console
    table = Table(title="MongoDB Atlas Organization Usage Report")
    table.add_column("Project Name", style="bold cyan")
    table.add_column("Cluster Name", style="bold magenta")
    table.add_column("Last Access Time", style="bold green")
    table.add_column("Status", style="bold yellow")

    for project in report_data:
        for cluster in project["clusters"]:
            status = "Unused" if cluster["name"] in unused_clusters else "In Use"
            table.add_row(project["name"], cluster["name"], cluster["last_access_time"], status)
    
    console.print(table)


def make_request(url, params=None, data=None):
    """Make an authenticated request to the MongoDB Atlas API."""
    public_key = os.getenv("ATLAS_PUBLIC_KEY")
    private_key = os.getenv("ATLAS_PRIVATE_KEY")

    if not public_key or not private_key:
        console.print("Atlas public or private key not found. Please set the ATLAS_PUBLIC_KEY and ATLAS_PRIVATE_KEY environment variables.", style="bold red")
        return None

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/vnd.atlas.2024-08-05+json"
    }
    console.print(f"[DEBUG] Sending request to URL: {url}", style="bold blue")
    response = requests.get(url, auth=HTTPDigestAuth(public_key, private_key), headers=headers, params=params, data=data)

    if response.status_code != 200:
        console.print(f"[ERROR] Failed to fetch data from URL: {url}", style="bold red")
        console.print(f"[ERROR] Status Code: {response.status_code}, Response: {response.text}", style="bold red")
        exit(1)

    console.print(f"[INFO] Successfully fetched data from URL: {url}", style="bold green")
    return response.json()

def fetch_projects(org_id):
    """Fetch project information from MongoDB Atlas organization."""
    url = f"https://cloud.mongodb.com/api/atlas/v2/groups"
    response = make_request(url)
    if response:
        console.print(f"[INFO] Successfully fetched {len(response.get('results', []))} projects.", style="bold green")
        return response.get("results", [])
    return []

def fetch_clusters(project_id):
    """Fetch cluster information from MongoDB Atlas project."""
    url = f"https://cloud.mongodb.com/api/atlas/v2/groups/{project_id}/clusters"
    response = make_request(url)
    if response:
        console.print(f"[INFO] Successfully fetched {len(response.get('results', []))} clusters for project ID: {project_id}.", style="bold green")
        return response.get("results", [])
    return []

def fetch_cluster_last_access(project_id, cluster_name):
    """Fetch the last access time for a specific cluster from MongoDB Atlas."""
    url = f"https://cloud.mongodb.com/api/atlas/v2/groups/{project_id}/dbAccessHistory/clusters/{cluster_name}"
    response = make_request(url)
    if response and "accessLogs" in response and response["accessLogs"]:
        # Sort by timestamp to find the most recent access
        access_logs = sorted(response["accessLogs"], key=lambda x: x.get("timestamp", ""), reverse=True)
        console.print(f"[DEBUG] Timestamp received: {access_logs[0]['timestamp']}", style="bold blue")
        try:
            # Attempt to parse the timestamp
            return dateutil.parser.parse(access_logs[0]["timestamp"])
        except (ValueError, TypeError):
            console.print(f"[ERROR] Unable to parse timestamp: {access_logs[0]['timestamp']}", style="bold red")
            return None
    console.print(f"[WARNING] No access logs found for cluster: {cluster_name}", style="bold yellow")
    return None

def render_html_report(data):
    """Render the HTML report using Jinja2 template."""
    env = Environment(loader=FileSystemLoader('mongone/templates'))
    template = env.get_template('report.html')
    output_from_parsed_template = template.render(projects=data)

    # Save the report in the 'reports' directory
    output_dir = "reports"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_file_path = os.path.join(output_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
    with open(output_file_path, "w") as f:
        f.write(output_from_parsed_template)

    console.print(f"Report generated: {output_file_path}", style="bold green")

if __name__ == "__main__":
    cli()
