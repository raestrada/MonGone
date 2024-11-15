import os
import yaml
from mongone.data.invoices import get_latest_invoice_id, fetch_invoice_csv
from mongone.data.projects import fetch_projects
from mongone.data.clusters import fetch_clusters

FORCE_DATA_FILE = "force-data.yaml"


def load_force_data():
    """Load force data from the force-data.yaml file."""
    if not os.path.exists(FORCE_DATA_FILE):
        raise FileNotFoundError(f"Force data file '{FORCE_DATA_FILE}' not found.")
    with open(FORCE_DATA_FILE, "r") as file:
        return yaml.safe_load(file)


def fetch_projects_data(atlas_org_id):
    """Fetch all projects from MongoDB Atlas using the given organization ID."""
    projects = fetch_projects(atlas_org_id)
    if not projects:
        raise ValueError("No projects found in the organization or an error occurred.")
    return projects


def fetch_invoice_data(atlas_org_id):
    """Fetch the latest invoice data from MongoDB Atlas using the given organization ID."""
    latest_invoice_id = get_latest_invoice_id(atlas_org_id)
    if not latest_invoice_id:
        raise ValueError("Unable to retrieve the latest invoice ID.")
    csv_data = fetch_invoice_csv(atlas_org_id, latest_invoice_id)
    if not csv_data:
        raise ValueError("Unable to retrieve invoice CSV data.")
    return csv_data


def fetch_clusters_data(project_id):
    """Fetch cluster data for a specific project."""
    return fetch_clusters(project_id)
