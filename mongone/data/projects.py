from rich.console import Console
from mongone.utils.http import make_request

console = Console()


def fetch_projects(org_id):
    """Fetch project information from MongoDB Atlas organization."""
    url = f"https://cloud.mongodb.com/api/atlas/v2/groups?itemsPerPage=500"
    response = make_request(url)
    if response:
        console.print(
            f"[INFO] Successfully fetched {len(response.json().get('results', []))} projects.",
            style="bold green",
        )
        return response.json().get("results", [])
    return []
