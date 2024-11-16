import os
import yaml
import datetime
from rich.console import Console

console = Console()

# Define output directories
PLANS_DIR = "./plans"


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
def generate_autoscaling_computation_plan(config, report_data, environment):
    clusters = [
        {
            "org_id": config.get("atlas_org_id"),
            "project_id": project.get("id"),
            "project_name": project.get("name"),
            "cluster_name": cluster["name"],
        }
        for project in report_data.get("report_data", [])
        if project.get("environment") == environment
        for cluster in project.get("clusters", [])
        if not cluster.get("autoscaling_compute")
    ]
    if clusters:
        plan_data = {
            "action": "autoscaling_computation",
            "environment": environment,
            "timestamp": datetime.datetime.now().isoformat(),
            "clusters": clusters,
        }
        write_yaml_file("autoscaling_computation", environment, plan_data)
        return True
    return False


# Generate plans to activate disk autoscaling
def generate_autoscaling_disk_plan(config, report_data, environment):
    clusters = [
        {
            "org_id": config.get("atlas_org_id"),
            "project_id": project.get("id"),
            "project_name": project.get("name"),
            "cluster_name": cluster["name"],
        }
        for project in report_data.get("report_data", [])
        if project.get("environment") == environment
        for cluster in project.get("clusters", [])
        if not cluster.get("autoscaling_disk")
    ]
    if clusters:
        plan_data = {
            "action": "autoscaling_disk",
            "environment": environment,
            "timestamp": datetime.datetime.now().isoformat(),
            "clusters": clusters,
        }
        write_yaml_file("autoscaling_disk", environment, plan_data)
        return True
    return False


# Generate plans to scale to free tier and remove autoscaling
def generate_scale_to_free_tier_plan(config, report_data, environment):
    clusters = [
        {
            "org_id": config.get("atlas_org_id"),
            "project_id": project.get("id"),
            "project_name": project.get("name"),
            "cluster_name": cluster["name"],
        }
        for project in report_data.get("report_data", [])
        if project.get("environment") == environment
        for cluster in project.get("clusters", [])
        if not cluster.get("inuse")
    ]
    if clusters:
        plan_data = {
            "action": "scale_to_free_tier",
            "remove_autoscaling": True,
            "environment": environment,
            "timestamp": datetime.datetime.now().isoformat(),
            "clusters": clusters,
        }
        write_yaml_file("scale_to_free_tier", environment, plan_data)
        return True
    return False


# Generate plans to delete clusters
def generate_delete_clusters_plan(config, report_data, environment):
    clusters = [
        {
            "org_id": config.get("atlas_org_id"),
            "project_id": project.get("id"),
            "project_name": project.get("name"),
            "cluster_name": cluster["name"],
        }
        for project in report_data.get("report_data", [])
        if project.get("environment") == environment
        for cluster in project.get("clusters", [])
        if not cluster.get("inuse")
    ]
    if clusters:
        plan_data = {
            "action": "delete_clusters",
            "environment": environment,
            "timestamp": datetime.datetime.now().isoformat(),
            "clusters": clusters,
        }
        write_yaml_file("delete_clusters", environment, plan_data)
        return True
    return False


# Main function to coordinate plan generation
def generate_plans(config, report_data):
    ensure_directory(PLANS_DIR)

    # Generate different plans for each environment based on report data
    for environment in ["staging", "production", "unknown"]:
        console.print(f"[blue]Generating plans for environment:[/] {environment}")
        plans_generated = False

        plans_generated |= generate_autoscaling_computation_plan(
            config, report_data, environment
        )
        plans_generated |= generate_autoscaling_disk_plan(
            config, report_data, environment
        )
        plans_generated |= generate_scale_to_free_tier_plan(
            config, report_data, environment
        )
        plans_generated |= generate_delete_clusters_plan(
            config, report_data, environment
        )

        # Print message only if no plans were generated for the environment
        if not plans_generated:
            console.print(
                f"[blue]No clusters found for any plans in environment {environment}. Skipping plan generation.[/]"
            )
