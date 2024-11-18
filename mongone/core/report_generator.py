from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
from mongone.data.clusters import fetch_cluster_last_access, is_cluster_autoscaling
from mongone.data.invoices import get_cluster_cost
from mongone.data.enviroments import detect_environment
from mongone.optimization.plans import generate_plans
from mongone.utils.helpers import Console
from mongone.core.data_loader import (
    fetch_clusters_data,
    fetch_projects_data,
    fetch_invoice_data,
)
from mongone.cost.prediction import calculate_predicted_costs

console = Console()


def process_project(project, env_patterns, csv_data, cutoff_date):
    project_id = project["id"]
    project_name = project["name"]
    environment = detect_environment(project_name, env_patterns)
    clusters = fetch_clusters_data(project["id"])

    if not clusters:
        return None

    project_report = {
        "id": project_id,
        "name": project_name,
        "environment": environment,
        "clusters": [],
    }

    unused_clusters = []

    for cluster in clusters:
        cluster_name = cluster["name"]
        last_access_time = fetch_cluster_last_access(project["id"], cluster_name)

        cluster_unused = True
        if last_access_time and last_access_time.replace(tzinfo=None) >= cutoff_date:
            cluster_unused = False

        if cluster_unused:
            unused_clusters.append(cluster_name)

        autoscaling_compute, autoscaling_disk = is_cluster_autoscaling(
            project["id"], cluster_name
        )

        cost = get_cluster_cost(csv_data, project_name, cluster_name)

        # Llamar a la función calculate_predicted_costs
        predicted_values = calculate_predicted_costs(cost, 0)

        # Extraer los valores calculados
        predicted_cost = predicted_values["total_predicted_cost"]

        cluster_report = {
            "name": cluster_name,
            "last_access_time": (
                last_access_time.strftime("%Y-%m-%d %H:%M:%S")
                if last_access_time
                else "N/A"
            ),
            "cost": get_cluster_cost(csv_data, project_name, cluster_name),
            "predicted_cost": predicted_cost,
            "autoscaling_compute": autoscaling_compute,
            "autoscaling_disk": autoscaling_disk,
            "inuse": not cluster_unused,
        }

        project_report["clusters"].append(cluster_report)

    return project_report, unused_clusters


def generate_report_logic(config, period):
    """Generate a usage report for all projects in the MongoDB Atlas organization."""
    atlas_org_id = config.get("atlas_org_id")
    env_patterns = config.get("environment_patterns")

    console.print("[INFO] Fetching projects from MongoDB Atlas...", style="bold blue")
    projects = fetch_projects_data(atlas_org_id)

    console.print(
        f"[INFO] Found {len(projects)} projects. Fetching latest invoice ID...",
        style="bold blue",
    )
    csv_data = fetch_invoice_data(atlas_org_id)

    console.print(
        f"[INFO] Found {len(projects)} projects. Fetching cluster information...",
        style="bold blue",
    )
    report_data = []
    all_unused_clusters = []
    cutoff_date = datetime.now().replace(tzinfo=None) - timedelta(days=period)

    total_clusters = 0
    clusters_without_autoscaling_compute = 0
    clusters_without_autoscaling_disk = 0
    unused_cluster_count = 0
    total_cost = 0.0
    estimated_saves = 0.0

    with ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        futures = [
            executor.submit(
                process_project, project, env_patterns, csv_data, cutoff_date
            )
            for project in projects
        ]
        for future in futures:
            result = future.result()
            if result:
                project_report, unused_clusters = result
                report_data.append(project_report)
                all_unused_clusters.extend(unused_clusters)

                for cluster in project_report["clusters"]:
                    total_clusters += 1
                    if not cluster["autoscaling_compute"]:
                        clusters_without_autoscaling_compute += 1
                    if not cluster["autoscaling_disk"]:
                        clusters_without_autoscaling_disk += 1
                    if cluster["name"] in unused_clusters:
                        unused_cluster_count += 1
                        estimated_saves += cluster["cost"]  # Assuming full cost is saved when scaled to free tier
                    total_cost += cluster["cost"]

                    # Estimating potential savings from enabling autoscaling
                    if not cluster["autoscaling_compute"] or not cluster["autoscaling_disk"]:
                        estimated_saves += cluster["cost"] * 0.2  # Assuming autoscaling saves 20% of cost

    # Llamar a la función calculate_predicted_costs
    predicted_values = calculate_predicted_costs(total_cost, estimated_saves)

    # Extraer los valores calculados
    total_predicted_cost = predicted_values["total_predicted_cost"]
    estimated_saves_projected = predicted_values["estimated_saves_projected"]


    return {
        "report_data": report_data,
        "total_clusters": total_clusters,
        "clusters_without_autoscaling_compute": clusters_without_autoscaling_compute,
        "clusters_without_autoscaling_disk": clusters_without_autoscaling_disk,
        "unused_cluster_count": unused_cluster_count,
        "total_cost": total_cost,
        "total_predicted_cost": total_predicted_cost,
        "all_unused_clusters": all_unused_clusters,
        "estimated_saves": estimated_saves,
        "estimated_saves_projected": estimated_saves_projected,
    }

def transform_force_data_to_expected_structure(raw_data, period=30):
    """
    Transforms the data loaded from 'force-data.yaml' to match the expected structure for the report,
    including calculating metrics like total clusters, clusters without autoscaling, and total cost.
    """
    transformed_data = []
    all_unused_clusters = []
    total_clusters = 0
    clusters_without_autoscaling_compute = 0
    clusters_without_autoscaling_disk = 0
    unused_cluster_count = 0
    total_cost = 0.0

    cutoff_date = datetime.now().replace(tzinfo=None) - timedelta(days=period)

    for project in raw_data.get("projects", []):
        project_report = {
            "id": project.get("id"),
            "name": project.get("name"),
            "environment": project.get("environment", "unknown"),
            "clusters": [],
        }

        for cluster in project.get("clusters", []):
            last_access_time = cluster.get("last_access_time")
            cluster_unused = (
                True if not last_access_time or last_access_time == "N/A" else False
            )
            if last_access_time and last_access_time != "N/A":
                last_access_time = datetime.strptime(
                    last_access_time, "%Y-%m-%dT%H:%M:%S"
                )
                if last_access_time.replace(tzinfo=None) >= cutoff_date:
                    cluster_unused = False

            cluster_report = {
                "name": cluster.get("name"),
                "last_access_time": cluster.get("last_access_time", "N/A"),
                "databases": cluster.get("databases", []),
                "cost": cluster.get("cost", 0),
                "predicted_cost": cluster.get("predicted_cost", 0),
                "autoscaling_compute": cluster.get("autoscaling_compute", False),
                "autoscaling_disk": cluster.get("autoscaling_disk", False),
                "inuse": cluster.get("inuse", True),
            }
            project_report["clusters"].append(cluster_report)

            # Update metrics
            total_clusters += 1
            if not cluster_report["autoscaling_compute"]:
                clusters_without_autoscaling_compute += 1
            if not cluster_report["autoscaling_disk"]:
                clusters_without_autoscaling_disk += 1
            if cluster_unused:
                unused_cluster_count += 1
                all_unused_clusters.append(cluster_report["name"])
            total_cost += cluster_report["cost"]

        transformed_data.append(project_report)

    return {
        "report_data": transformed_data,
        "total_clusters": total_clusters,
        "clusters_without_autoscaling_compute": clusters_without_autoscaling_compute,
        "clusters_without_autoscaling_disk": clusters_without_autoscaling_disk,
        "unused_cluster_count": unused_cluster_count,
        "total_cost": total_cost,
        "total_predicted_cost": total_cost * 1.5,
        "all_unused_clusters": all_unused_clusters,
        "estimated_saves": total_cost/2,
        "estimated_saves_projected": (total_cost/2)*1.3,
    }
