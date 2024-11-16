import os
from rich.console import Console
import requests
from requests.auth import HTTPDigestAuth

console = Console()


def make_request(url, params=None, data=None, method="GET", response_format="json"):
    """Make an authenticated request to the MongoDB Atlas API."""
    public_key = os.getenv("ATLAS_PUBLIC_KEY")
    private_key = os.getenv("ATLAS_PRIVATE_KEY")

    if not public_key or not private_key:
        console.print(
            "Atlas public or private key not found. Please set the ATLAS_PUBLIC_KEY and ATLAS_PRIVATE_KEY environment variables.",
            style="bold red",
        )
        return None

    headers = {
        "Content-Type": "application/json",
        "Accept": (
            "application/vnd.atlas.2024-08-05+json"
            if response_format == "json"
            else "application/vnd.atlas.2024-08-05+csv"
        ),
    }
    
    # Select the appropriate request method
    method = method.upper()
    console.print(f"[DEBUG] Sending {method} request to URL: {url}", style="bold blue")

    if method == "GET":
        response = requests.get(url, auth=HTTPDigestAuth(public_key, private_key), headers=headers, params=params)
    elif method == "POST":
        response = requests.post(url, auth=HTTPDigestAuth(public_key, private_key), headers=headers, params=params, json=data)
    elif method == "PATCH":
        response = requests.patch(url, auth=HTTPDigestAuth(public_key, private_key), headers=headers, params=params, json=data)
    elif method == "PUT":
        response = requests.put(url, auth=HTTPDigestAuth(public_key, private_key), headers=headers, params=params, json=data)
    elif method == "DELETE":
        response = requests.delete(url, auth=HTTPDigestAuth(public_key, private_key), headers=headers, params=params)
    else:
        console.print(f"[red]HTTP method '{method}' is not supported.[/]")
        return None

    # Check for successful request
    if response.status_code not in [200, 201, 202]:
        console.print(f"[ERROR] Failed to fetch data from URL: {url}", style="bold red")
        console.print(
            f"[ERROR] Status Code: {response.status_code}, Response: {response.text}",
            style="bold red",
        )
        exit(1)

    console.print(
        f"[INFO] Successfully fetched data from URL: {url}", style="bold green"
    )
    return response
