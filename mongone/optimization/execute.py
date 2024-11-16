import os
import yaml
from rich.console import Console
from mongone.utils.http import make_request
from mongone.core.config import load_config

console = Console()

# Base URL for MongoDB Atlas API
BASE_URL = "https://cloud.mongodb.com/api/atlas/v2/groups/{groupId}/clusters/{clusterName}"

# Proxy function to execute plans based on type and environment

def execute_plan(plan_type, environment, plan_filename):
    if not os.path.exists(plan_filename):
        console.print(f"[red]No plan file found for {plan_type} in environment {environment}. Skipping execution.[/]")
        return

    with open(plan_filename, "r") as plan_file:
        plan_data = yaml.safe_load(plan_file)

    # Call the respective function based on plan type
    if plan_type == "autoscaling_computation":
        enable_autoscaling_computation(plan_data)
    else:
        console.print(f"[red]Unknown plan type: {plan_type}[/]")

# Function to enable auto-scaling computation for clusters
def enable_autoscaling_computation(plan_data):
    # Load configuration for autoscaling settings
    config = load_config()
    autoscaling_defaults = config.get("autoscaling_defaults", {})

    # Extract default values from configuration or use fallback values
    provider_name = autoscaling_defaults.get("provider_name", "AWS")
    region_name = autoscaling_defaults.get("region_name", "US_GOV_WEST_1")
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

        url = BASE_URL.format(groupId=project_id, clusterName=cluster_name)

        # Payload to enable compute auto-scaling
        payload = {
            "replicationSpecs": [
                {
                    "regionConfigs": [
                        {
                            "providerName": provider_name,
                            "regionName": region_name,
                            "autoScaling": {
                                "compute": {
                                    "enabled": True,
                                    "maxInstanceSize": max_instance_size,
                                    "minInstanceSize": min_instance_size,
                                    "scaleDownEnabled": True
                                }
                            }
                        }
                    ]
                }
            ]
        }

        console.print(f"[blue]Enabling auto-scaling computation for cluster {cluster_name} in project {project_id}[/]")
        make_request(url, data=payload, response_format="json")
