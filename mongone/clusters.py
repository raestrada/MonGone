from rich.console import Console
import dateutil.parser
from mongone.http import make_request

console = Console()


def fetch_clusters(project_id):
    """Fetch cluster information from MongoDB Atlas project."""
    url = f"https://cloud.mongodb.com/api/atlas/v2/groups/{project_id}/clusters"
    response = make_request(url)
    if response:
        console.print(
            f"[INFO] Successfully fetched {len(response.json().get('results', []))} clusters for project ID: {project_id}.",
            style="bold green",
        )
        return response.json().get("results", [])
    return []


def fetch_cluster_last_access(project_id, cluster_name):
    """Fetch the last access time for a specific cluster from MongoDB Atlas."""
    url = f"https://cloud.mongodb.com/api/atlas/v2/groups/{project_id}/dbAccessHistory/clusters/{cluster_name}"
    response = make_request(url)
    if response and "accessLogs" in response.json() and response.json()["accessLogs"]:
        # Sort by timestamp to find the most recent access
        access_logs = sorted(
            response.json()["accessLogs"],
            key=lambda x: x.get("timestamp", ""),
            reverse=True,
        )
        console.print(
            f"[DEBUG] Timestamp received: {access_logs[0]['timestamp']}",
            style="bold blue",
        )
        try:
            # Attempt to parse the timestamp
            return dateutil.parser.parse(access_logs[0]["timestamp"])
        except (ValueError, TypeError):
            console.print(
                f"[ERROR] Unable to parse timestamp: {access_logs[0]['timestamp']}",
                style="bold red",
            )
            return None
    console.print(
        f"[WARNING] No access logs found for cluster: {cluster_name}",
        style="bold yellow",
    )
    return None
