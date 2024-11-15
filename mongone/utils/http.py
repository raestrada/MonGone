import os
from rich.console import Console
import requests
from requests.auth import HTTPDigestAuth

console = Console()


def make_request(url, params=None, data=None, response_format="json"):
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
    console.print(f"[DEBUG] Sending request to URL: {url}", style="bold blue")
    response = requests.get(
        url,
        auth=HTTPDigestAuth(public_key, private_key),
        headers=headers,
        params=params,
        data=data,
    )

    if response.status_code != 200:
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
