from rich.console import Console
import csv
from io import StringIO
from mongone.http import make_request

console = Console()


def get_latest_invoice_id(org_id):
    """Fetch the latest invoice ID for the MongoDB Atlas organization."""
    url = f"https://cloud.mongodb.com/api/atlas/v2/orgs/{org_id}/invoices"
    response = make_request(url)
    if response:
        invoices = response.json().get("results", [])
        if invoices:
            # Sort invoices by end date and get the latest one
            latest_invoice = sorted(invoices, key=lambda x: x["endDate"], reverse=True)[
                0
            ]
            console.print(
                f"[DEBUG] Latest invoice ID: {latest_invoice['id']}", style="bold blue"
            )
            return latest_invoice["id"]
    console.print("[ERROR] No invoices found for the organization.", style="bold red")
    return None


def fetch_invoice_csv(org_id, invoice_id):
    """Fetch the CSV data for a specific invoice."""
    csv_url = f"https://cloud.mongodb.com/api/atlas/v2/orgs/{org_id}/invoices/{invoice_id}/csv"
    csv_response = make_request(csv_url, response_format="csv")
    if not csv_response:
        console.print("[ERROR] Unable to retrieve invoice CSV data.", style="bold red")
        return None
    return csv_response.text


def get_cluster_cost(csv_data, cluster_name):
    """Fetch the total cost for a specific cluster from the provided CSV data."""
    csv_reader = csv.DictReader(StringIO(csv_data))
    total_cost = 0.0
    headers = csv_reader.fieldnames
    console.print(f"[DEBUG] CSV Headers: {headers}", style="bold blue")
    if "Cluster" not in headers:
        console.print(
            f"[ERROR] 'Cluster' column not found in CSV headers: {headers}",
            style="bold red",
        )
        return total_cost
    for row in csv_reader:
        if row.get("Cluster") == cluster_name:
            try:
                total_cost += float(row.get("Amount", 0))
            except ValueError:
                console.print(
                    f"[ERROR] Unable to parse cost amount for cluster: {cluster_name}",
                    style="bold red",
                )
    return total_cost
