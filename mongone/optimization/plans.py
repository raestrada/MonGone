import os
import yaml
import datetime
from rich.console import Console

console = Console()

# Define output directories
PLANS_DIR = "./plans"

# Define plan names
PLAN_NAMES = [
    "autoscaling_computation",
    "autoscaling_disk",
    "scale_to_free_tier",
    "delete_clusters",
]


# Create the directory if it doesn't exist
def ensure_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


# Generate a YAML file
def write_yaml_file(plan_name, environment, data):
    filename = f"{PLANS_DIR}/{environment}/{plan_name}_plan_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.yaml"
    ensure_directory(os.path.dirname(filename))
    with open(filename, "w") as yaml_file:
        yaml.dump(data, yaml_file, default_flow_style=False)
    console.print(f"[green]Plan generated:[/] {filename}")


# Generate plans to activate computation autoscaling
def generate_autoscaling_computation_plan(report_data, environment):
    plan_data = {
        "action": "activate_autoscaling_computation",
        "clusters": [
            {
                "org_id": project["org_id"],
                "project_id": project["project_id"],
                "cluster_name": cluster["name"],
            }
            for project in report_data.get("projects", [])
            for cluster in project.get("clusters", [])
            if not cluster.get("autoscaling_compute")
            and project.get("environment") == environment
        ],
    }
    if plan_data["clusters"]:
        write_yaml_file("autoscaling_computation", environment, plan_data)


# Generate plans to activate disk autoscaling
def generate_autoscaling_disk_plan(report_data, environment):
    plan_data = {
        "action": "activate_autoscaling_disk",
        "clusters": [
            {
                "org_id": project["org_id"],
                "project_id": project["project_id"],
                "cluster_name": cluster["name"],
            }
            for project in report_data.get("projects", [])
            for cluster in project.get("clusters", [])
            if not cluster.get("autoscaling_disk")
            and project.get("environment") == environment
        ],
    }
    if plan_data["clusters"]:
        write_yaml_file("autoscaling_disk", environment, plan_data)


# Generate plans to scale to free tier and remove autoscaling
def generate_scale_to_free_tier_plan(report_data, environment):
    plan_data = {
        "action": "scale_to_free_tier",
        "remove_autoscaling": True,
        "clusters": [
            {
                "org_id": project["org_id"],
                "project_id": project["project_id"],
                "cluster_name": cluster["name"],
            }
            for project in report_data.get("projects", [])
            for cluster in project.get("clusters", [])
            if cluster.get("unused") and project.get("environment") == environment
        ],
    }
    if plan_data["clusters"]:
        write_yaml_file("scale_to_free_tier", environment, plan_data)


# Generate plans to delete clusters
def generate_delete_clusters_plan(report_data, environment):
    plan_data = {
        "action": "delete_clusters",
        "clusters": [
            {
                "org_id": project["org_id"],
                "project_id": project["project_id"],
                "cluster_name": cluster["name"],
            }
            for project in report_data.get("projects", [])
            for cluster in project.get("clusters", [])
            if cluster.get("unused") and project.get("environment") == environment
        ],
    }
    if plan_data["clusters"]:
        write_yaml_file("delete_clusters", environment, plan_data)


# Main function to coordinate plan generation
def generate_plans(report_data):
    ensure_directory(PLANS_DIR)

    # Generate different plans for each environment based on report data
    for environment in ["staging", "production", "unknown"]:
        console.print(f"[blue]Generating plans for environment:[/] {environment}")
        generate_autoscaling_computation_plan(report_data, environment)
        generate_autoscaling_disk_plan(report_data, environment)
        generate_scale_to_free_tier_plan(report_data, environment)
        generate_delete_clusters_plan(report_data, environment)
