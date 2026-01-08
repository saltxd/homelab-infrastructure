#!/usr/bin/env python3
"""
BookStack Initialization Script
Sets up initial book/chapter structure and creates API token
"""
import requests
import re
import json
import yaml
import os
from pathlib import Path

BOOKSTACK_URL = "http://docs.k3s.nox"
DEFAULT_EMAIL = "admin@admin.com"
DEFAULT_PASSWORD = "password"

class BookStackSession:
    """Session-based BookStack client for initial setup"""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self._token = None

    def _get_csrf_token(self, html: str) -> str:
        """Extract CSRF token from HTML"""
        match = re.search(r'name="_token"\s+value="([^"]+)"', html)
        if match:
            return match.group(1)
        match = re.search(r'<meta name="token" content="([^"]+)"', html)
        if match:
            return match.group(1)
        raise ValueError("Could not find CSRF token")

    def login(self, email: str, password: str) -> bool:
        """Login to BookStack with session cookie"""
        # Get login page for CSRF token
        resp = self.session.get(f"{self.base_url}/login")
        resp.raise_for_status()
        token = self._get_csrf_token(resp.text)

        # Submit login
        resp = self.session.post(
            f"{self.base_url}/login",
            data={
                "_token": token,
                "email": email,
                "password": password
            },
            allow_redirects=False
        )

        # Follow redirect and check if logged in
        if resp.status_code in (302, 303):
            resp = self.session.get(f"{self.base_url}/")
            if "logout" in resp.text.lower() or email in resp.text:
                print(f"Logged in as {email}")
                return True

        print(f"Login failed - status: {resp.status_code}")
        return False

    def _get_page_token(self, url: str) -> str:
        """Get CSRF token from any authenticated page"""
        resp = self.session.get(url)
        resp.raise_for_status()
        return self._get_csrf_token(resp.text)

    def create_api_token(self, name: str = "Automation") -> dict:
        """Create API token through web interface"""
        # Go to API tokens page
        resp = self.session.get(f"{self.base_url}/api-tokens")
        if resp.status_code != 200:
            print("API tokens page not accessible")
            return None

        token = self._get_csrf_token(resp.text)

        # Create token
        resp = self.session.post(
            f"{self.base_url}/api-tokens",
            data={
                "_token": token,
                "name": name,
                "expires_at": ""
            },
            allow_redirects=False
        )

        # Check for token in response
        if resp.status_code in (302, 303):
            # Follow redirect to get the created token
            location = resp.headers.get('Location', '')
            if '/api-tokens/' in location:
                token_resp = self.session.get(location)
                # Parse the token details from the page
                token_id_match = re.search(r'Token ID.*?<code[^>]*>([^<]+)</code>', token_resp.text, re.DOTALL)
                token_secret_match = re.search(r'Token Secret.*?<code[^>]*>([^<]+)</code>', token_resp.text, re.DOTALL)

                if token_id_match and token_secret_match:
                    return {
                        "id": token_id_match.group(1).strip(),
                        "secret": token_secret_match.group(1).strip()
                    }

        print(f"Failed to create API token - status: {resp.status_code}")
        return None

    def create_book(self, name: str, description: str = "") -> dict:
        """Create a book"""
        token = self._get_page_token(f"{self.base_url}/create-book")

        resp = self.session.post(
            f"{self.base_url}/books",
            data={
                "_token": token,
                "name": name,
                "description": description,
                "tags": []
            },
            allow_redirects=False
        )

        if resp.status_code in (302, 303):
            location = resp.headers.get('Location', '')
            slug = location.rstrip('/').split('/')[-1]
            print(f"Created book: {name} (slug: {slug})")
            return {"name": name, "slug": slug}

        print(f"Failed to create book '{name}' - status: {resp.status_code}")
        return None

    def create_chapter(self, book_slug: str, name: str, description: str = "") -> dict:
        """Create a chapter in a book using form submission"""
        # First get the create chapter page
        create_url = f"{self.base_url}/books/{book_slug}/create-chapter"
        resp = self.session.get(create_url)
        if resp.status_code != 200:
            print(f"  Cannot access chapter creation page for {book_slug}")
            return None

        token = self._get_csrf_token(resp.text)

        # Find book ID from the form
        book_id_match = re.search(r'name="book_id"\s+value="(\d+)"', resp.text)
        book_id = book_id_match.group(1) if book_id_match else None

        if not book_id:
            # Try to get book ID from books list
            books_resp = self.session.get(f"{self.base_url}/books/{book_slug}")
            book_id_match = re.search(r'/books/(\d+)', books_resp.text)
            book_id = book_id_match.group(1) if book_id_match else "1"

        # Submit as a form post with proper content type
        resp = self.session.post(
            create_url,
            data={
                "_token": token,
                "name": name,
                "description_html": description,
                "description": description,
                "book_id": book_id
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            allow_redirects=True
        )

        # Check if chapter was created by looking for it in the response
        if name in resp.text and resp.status_code == 200:
            print(f"  Created chapter: {name}")
            return {"name": name, "slug": name.lower().replace(" ", "-")}

        # Also check if we got redirected to the chapter page
        if f"/chapter/" in resp.url:
            slug = resp.url.rstrip('/').split('/')[-1]
            print(f"  Created chapter: {name} (slug: {slug})")
            return {"name": name, "slug": slug}

        print(f"  Failed to create chapter '{name}' - status: {resp.status_code}")
        return None

    def get_books(self) -> list:
        """Get list of existing books"""
        resp = self.session.get(f"{self.base_url}/api/books")
        if resp.status_code == 200:
            return resp.json().get("data", [])
        return []


def main():
    print(f"Connecting to BookStack at {BOOKSTACK_URL}...")

    client = BookStackSession(BOOKSTACK_URL)

    # Login
    if not client.login(DEFAULT_EMAIL, DEFAULT_PASSWORD):
        print("Failed to login to BookStack")
        return 1

    # Check existing books
    print("\nChecking existing content...")

    # Define initial structure
    structure = {
        "Infrastructure": {
            "description": "Core infrastructure documentation",
            "chapters": [
                "Network Topology",
                "Proxmox Nodes",
                "Virtual Machines",
                "DNS & Routing"
            ]
        },
        "K3s Cluster": {
            "description": "Kubernetes cluster documentation",
            "chapters": [
                "Cluster Overview",
                "Deployments",
                "Services & Ingress",
                "Storage"
            ]
        },
        "Runbooks": {
            "description": "Operational runbooks and procedures",
            "chapters": [
                "Incident Response",
                "Backup & Recovery",
                "Maintenance",
                "Troubleshooting"
            ]
        },
        "Services": {
            "description": "Documentation for deployed services",
            "chapters": [
                "Monitoring (Grafana/Prometheus)",
                "Dashboard (Homer/Homarr)",
                "DNS (AdGuard)",
                "GPT-OS"
            ]
        }
    }

    # Create books and chapters
    print("\nCreating book structure...")
    created_books = {}

    for book_name, book_info in structure.items():
        book = client.create_book(book_name, book_info["description"])
        if book:
            created_books[book_name] = book
            for chapter_name in book_info["chapters"]:
                client.create_chapter(book["slug"], chapter_name)

    # Create API token
    print("\nCreating API token for automation...")
    api_token = client.create_api_token("Homelab-Automation")

    if api_token:
        print(f"\nAPI Token Created:")
        print(f"  Token ID: {api_token['id']}")
        print(f"  Token Secret: {api_token['secret']}")

        # Save to config file
        config_path = Path(__file__).parent / "config.yaml"
        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f)

            config['bookstack']['api_token_id'] = api_token['id']
            config['bookstack']['api_token_secret'] = api_token['secret']

            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)

            print(f"\nUpdated {config_path} with API credentials")

    # Save credentials reference
    creds_path = Path.home() / "Forge" / "bookstack-config.yaml"
    creds = {
        "bookstack": {
            "url": BOOKSTACK_URL,
            "admin_email": DEFAULT_EMAIL,
            "admin_password": DEFAULT_PASSWORD,
            "api_token_id": api_token['id'] if api_token else "",
            "api_token_secret": api_token['secret'] if api_token else ""
        }
    }

    with open(creds_path, 'w') as f:
        yaml.dump(creds, f, default_flow_style=False)
    os.chmod(creds_path, 0o600)
    print(f"Saved credentials to {creds_path}")

    print("\n" + "="*50)
    print("BookStack initialization complete!")
    print(f"Access BookStack at: {BOOKSTACK_URL}")
    print(f"Login: {DEFAULT_EMAIL} / {DEFAULT_PASSWORD}")
    print("="*50)

    return 0


if __name__ == "__main__":
    exit(main())
