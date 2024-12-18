import os
import yaml
import sys
from rich.console import Console
from mongone.utils.http import make_request
from mongone.core.config import load_config

console = Console()

# Base URL for MongoDB Atlas API
BASE_URL = (
    "https://cloud.mongodb.com/api/atlas/v2/groups/{groupId}/clusters/{clusterName}"
)


# Proxy function to execute plans based on type and environment
def execute_plan(plan_type, environment, plan_filename):
    if not os.path.exists(plan_filename):
        console.print(
            f"[red]No plan file found for {plan_type} in environment {environment}. Skipping execution.[/]"
        )
        return

    with open(plan_filename, "r") as plan_file:
        plan_data = yaml.safe_load(plan_file)

    # Verify plan metadata matches the provided context
    if (
        plan_data.get("environment", "").lower() != environment.lower()
        or plan_data.get("action", "") != plan_type
    ):
        console.print(
            f"[red]Mismatch in plan metadata. Expected environment: {environment.capitalize()}, action: {plan_type}. Aborting execution.[/]"
        )
        console.print(
            f"[red]Compared with plan metadata: Environment: {plan_data.get('environment')}, Action: {plan_data.get('action')}[/]"
        )
        console.print("[red]Execution aborted due to metadata mismatch.[/]")
        sys.exit(1)

    # Confirm execution details with the user
    console.print(f"[yellow]You are about to execute the following plan:[/]")
    console.print(f"[cyan]Environment: {plan_data.get('environment')}[/]")
    console.print(f"[cyan]Action: {plan_data.get('action')}[/]")
    console.print(
        f"[cyan]Clusters: {', '.join([cluster['cluster_name'] for cluster in plan_data.get('clusters', [])])}[/]"
    )
    confirmation = input("[WARNING] Are you sure you want to proceed? (yes/no): ")
    if confirmation.lower() != "yes":
        console.print("[red]Execution aborted by user.[/]")
        return

    # Call the respective function based on plan type
    if plan_type == "autoscaling_computation":
        enable_autoscaling_computation(plan_data)
    elif plan_type == "autoscaling_disk":
        enable_autoscaling_disk(plan_data)
    elif plan_type == "scale_to_free_tier":
        scale_to_free_tier(plan_data)
    elif plan_type == "delete_clusters":
        delete_clusters(plan_data)
    else:
        console.print(f"[red]Unknown plan type: {plan_type}[/]")


# Function to enable auto-scaling computation for clusters
def enable_autoscaling_computation(plan_data):
    # Load configuration for autoscaling settings
    config = load_config()
    autoscaling_defaults = config.get("autoscaling_defaults", {})

    # Extract default values from configuration or use fallback values
    provider_name = autoscaling_defaults.get("provider_name", "AWS")
    max_instance_size = autoscaling_defaults.get("max_instance_size", "M40")
    min_instance_size = autoscaling_defaults.get("min_instance_size", "M10")
    priority = autoscaling_defaults.get("priority", 7)

    clusters = plan_data.get("clusters", [])
    for cluster in clusters:
        org_id = cluster.get("org_id")
        project_id = cluster.get("project_id")
        cluster_name = cluster.get("cluster_name")

        if not org_id or not project_id or not cluster_name:
            console.print("[red]Missing necessary information to execute plan[/]")
            continue

        # Fetch current cluster details
        url = BASE_URL.format(groupId=project_id, clusterName=cluster_name)

        response = make_request(url, method="GET")

        if response is None:
            console.print(
                f"[red]Failed to fetch cluster details for {cluster_name} in project {project_id}. Skipping...[/]"
            )
            continue

        cluster_details = response.json()
        current_region_name = cluster_details["replicationSpecs"][0]["regionConfigs"][
            0
        ]["regionName"]

        # Use the current region to avoid conflicts
        region_name = current_region_name

        # Payload to enable compute auto-scaling
        payload = {
            "replicationSpecs": [
                {
                    "regionConfigs": [
                        {
                            "providerName": provider_name,
                            "regionName": region_name,
                            "priority": priority,
                            "electableSpecs": {
                                "instanceSize": min_instance_size,
                                "nodeCount": 3,
                                "diskSizeGB": 10,  # Example disk size, adjust as needed
                            },
                            "autoScaling": {
                                "compute": {
                                    "enabled": True,
                                    "maxInstanceSize": max_instance_size,
                                    "minInstanceSize": min_instance_size,
                                    "scaleDownEnabled": True,
                                }
                            },
                        }
                    ]
                }
            ]
        }

        console.print(
            f"[blue]Enabling auto-scaling computation for cluster {cluster_name} in project {project_id}[/]"
        )
        make_request(url, method="PATCH", data=payload, response_format="json")


# Function to enable auto-scaling disk for clusters
def enable_autoscaling_disk(plan_data):
    # Load configuration for autoscaling settings
    config = load_config()
    autoscaling_defaults = config.get("autoscaling_defaults", {})

    # Extract default values from configuration or use fallback values
    provider_name = autoscaling_defaults.get("provider_name", "AWS")
    max_instance_size = autoscaling_defaults.get("max_instance_size", "M40")
    min_instance_size = autoscaling_defaults.get("min_instance_size", "M10")

    clusters = plan_data.get("clusters", [])
    for cluster in clusters:
        org_id = cluster.get("org_id")
        project_id = cluster.get("project_id")
        cluster_name = cluster.get("cluster_name")

        if not org_id or not project_id or not cluster_name:
            console.print("[red]Missing necessary information to execute plan[/]")
            continue

        # Fetch current cluster details
        url = BASE_URL.format(groupId=project_id, clusterName=cluster_name)

        response = make_request(url, method="GET")

        if response is None:
            console.print(
                f"[red]Failed to fetch cluster details for {cluster_name} in project {project_id}. Skipping...[/]"
            )
            continue

        cluster_details = response.json()
        current_region_name = cluster_details["replicationSpecs"][0]["regionConfigs"][
            0
        ]["regionName"]

        # Use the current region to avoid conflicts
        region_name = current_region_name

        # Payload to enable disk auto-scaling
        payload = {
            "replicaSetScalingStrategy": "SEQUENTIAL",
            "replicationSpecs": [
                {
                    "regionConfigs": [
                        {
                            "providerName": provider_name,
                            "regionName": region_name,
                            "priority": 7,  # Adding required priority attribute
                            "autoScaling": {
                                "compute": {
                                    "enabled": True,
                                    "maxInstanceSize": max_instance_size,
                                    "minInstanceSize": min_instance_size,
                                    "scaleDownEnabled": True,
                                },
                                "diskGB": {"enabled": True},
                            },
                            "electableSpecs": {
                                "instanceSize": min_instance_size,
                                "nodeCount": 3,
                                "diskSizeGB": 10,  # Example disk size, adjust as needed
                            },
                        }
                    ],
                    "zoneName": "string",
                }
            ],
        }

        console.print(
            f"[blue]Enabling auto-scaling disk for cluster {cluster_name} in project {project_id}[/]"
        )
        make_request(url, method="PATCH", data=payload, response_format="json")


def scale_to_free_tier(plan_data):
    # Load configuration for autoscaling settings
    clusters = plan_data.get("clusters", [])
    for cluster in clusters:
        org_id = cluster.get("org_id")
        project_id = cluster.get("project_id")
        cluster_name = cluster.get("cluster_name")

        if not org_id or not project_id or not cluster_name:
            console.print("[red]Missing necessary information to execute plan[/]")
            continue

        url = BASE_URL.format(groupId=project_id, clusterName=cluster_name)

        # Payload to scale to free tier and disable autoscaling
        payload = {
            "replicaSetScalingStrategy": "SEQUENTIAL",
            "replicationSpecs": [
                {
                    "regionConfigs": [
                        {
                            "electableSpecs": {
                                "diskSizeGB": 5,  # Set appropriate disk size for free tier (M0)
                                "instanceSize": "M0",  # Set instance size to free tier
                                "nodeCount": 1,
                            },
                            "providerName": "AWS",
                            "regionName": "US_EAST_1",  # Example region, adjust as needed
                            "autoScaling": {
                                "compute": {
                                    "enabled": False,
                                    "maxInstanceSize": "M0",
                                    "minInstanceSize": "M0",
                                    "scaleDownEnabled": False,
                                },
                                "diskGB": {"enabled": False},
                            },
                        }
                    ],
                    "zoneName": "string",  # Replace with actual zone name if necessary
                }
            ],
            "redactClientLogData": True,
        }

        console.print(
            f"[blue]Scaling cluster {cluster_name} to free tier in project {project_id}[/]"
        )
        make_request(url, data=payload, method="PATCH", response_format="json")


# Function to delete clusters
def delete_clusters(plan_data):
    clusters = plan_data.get("clusters", [])
    for cluster in clusters:
        org_id = cluster.get("org_id")
        project_id = cluster.get("project_id")
        cluster_name = cluster.get("cluster_name")

        if not org_id or not project_id or not cluster_name:
            console.print("[red]Missing necessary information to execute plan[/]")
            continue

        url = BASE_URL.format(groupId=project_id, clusterName=cluster_name)

        console.print(
            f"[blue]Deleting cluster {cluster_name} in project {project_id}[/]"
        )
        make_request(url, method="DELETE")
