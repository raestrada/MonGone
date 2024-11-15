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

console = Console()


def process_project(project, env_patterns, csv_data, cutoff_date):
    project_name = project["name"]
    environment = detect_environment(project_name, env_patterns)
    clusters = fetch_clusters_data(project["id"])

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
        autoscaling_compute, autoscaling_disk = is_cluster_autoscaling(
            project["id"], cluster_name
        )
        cluster_report = {
            "name": cluster_name,
            "last_access_time": (
                last_access_time.strftime("%Y-%m-%d %H:%M:%S")
                if last_access_time
                else "N/A"
            ),
            "cost": get_cluster_cost(csv_data, project_name, cluster_name),
            "autoscaling_compute": autoscaling_compute,
            "autoscaling_disk": autoscaling_disk,
        }

        if last_access_time and last_access_time.replace(tzinfo=None) >= cutoff_date:
            cluster_unused = False

        if cluster_unused:
            unused_clusters.append(cluster_name)

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
                    total_cost += cluster["cost"]

    generate_plans(
        {
            "clusters_to_activate_autoscaling_computation": {
                env: [
                    cluster["name"]
                    for project in report_data
                    for cluster in project["clusters"]
                    if not cluster["autoscaling_compute"]
                    and project["environment"] == env
                ]
                for env in ["staging", "production", "unknown"]
            },
            "clusters_to_activate_autoscaling_disk": {
                env: [
                    cluster["name"]
                    for project in report_data
                    for cluster in project["clusters"]
                    if not cluster["autoscaling_disk"] and project["environment"] == env
                ]
                for env in ["staging", "production", "unknown"]
            },
            "clusters_to_scale_free_tier": {
                env: [
                    cluster["name"]
                    for project in report_data
                    for cluster in project["clusters"]
                    if cluster["name"] in all_unused_clusters
                    and project["environment"] == env
                ]
                for env in ["staging", "production", "unknown"]
            },
            "clusters_to_delete": {
                env: [
                    cluster["name"]
                    for project in report_data
                    for cluster in project["clusters"]
                    if cluster["name"] in all_unused_clusters
                    and project["environment"] == env
                ]
                for env in ["staging", "production", "unknown"]
            },
        }
    )

    return {
        "report_data": report_data,
        "total_clusters": total_clusters,
        "clusters_without_autoscaling_compute": clusters_without_autoscaling_compute,
        "clusters_without_autoscaling_disk": clusters_without_autoscaling_disk,
        "unused_cluster_count": unused_cluster_count,
        "total_cost": total_cost,
        "all_unused_clusters": all_unused_clusters,
    }
