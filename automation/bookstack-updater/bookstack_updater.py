#!/usr/bin/env python3
"""
BookStack Auto-Updater for Homelab Documentation
Reads audit data and updates BookStack via API
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import yaml
from jinja2 import Environment, FileSystemLoader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BookStackAPI:
    """BookStack API client"""
    
    def __init__(self, url: str, token_id: str, token_secret: str):
        self.base_url = url.rstrip('/')
        self.headers = {
            'Authorization': f'Token {token_id}:{token_secret}',
            'Content-Type': 'application/json'
        }
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make API request"""
        url = f"{self.base_url}/api/{endpoint}"
        resp = requests.request(method, url, headers=self.headers, **kwargs)
        resp.raise_for_status()
        return resp.json() if resp.text else {}
    
    def get_books(self) -> List[Dict]:
        """Get all books"""
        return self._request('GET', 'books')['data']
    
    def create_book(self, name: str, description: str = "") -> Dict:
        """Create a new book"""
        return self._request('POST', 'books', json={
            'name': name,
            'description': description
        })
    
    def get_chapters(self, book_id: int) -> List[Dict]:
        """Get chapters in a book"""
        return self._request('GET', f'books/{book_id}')['contents']
    
    def create_chapter(self, book_id: int, name: str, description: str = "") -> Dict:
        """Create a new chapter"""
        return self._request('POST', 'chapters', json={
            'book_id': book_id,
            'name': name,
            'description': description
        })
    
    def get_pages(self, chapter_id: int = None) -> List[Dict]:
        """Get pages, optionally filtered by chapter"""
        pages = self._request('GET', 'pages')['data']
        if chapter_id:
            pages = [p for p in pages if p.get('chapter_id') == chapter_id]
        return pages
    
    def create_page(self, chapter_id: int, name: str, markdown: str) -> Dict:
        """Create a new page"""
        return self._request('POST', 'pages', json={
            'chapter_id': chapter_id,
            'name': name,
            'markdown': markdown
        })
    
    def update_page(self, page_id: int, name: str, markdown: str) -> Dict:
        """Update an existing page"""
        return self._request('PUT', f'pages/{page_id}', json={
            'name': name,
            'markdown': markdown
        })
    
    def find_or_create_book(self, name: str) -> Dict:
        """Find existing book or create new one"""
        books = self.get_books()
        for book in books:
            if book['name'].lower() == name.lower():
                logger.info(f"Found existing book: {name} (ID: {book['id']})")
                return book
        logger.info(f"Creating new book: {name}")
        return self.create_book(name)
    
    def find_or_create_chapter(self, book_id: int, name: str) -> Dict:
        """Find existing chapter or create new one"""
        chapters = self.get_chapters(book_id)
        for chapter in chapters:
            if chapter.get('type') == 'chapter' and chapter['name'].lower() == name.lower():
                logger.info(f"Found existing chapter: {name} (ID: {chapter['id']})")
                return chapter
        logger.info(f"Creating new chapter: {name}")
        return self.create_chapter(book_id, name)


class AuditDataParser:
    """Parse homelab audit results"""
    
    def __init__(self, results_dir: str):
        self.results_dir = Path(results_dir).expanduser()
    
    def _read_json(self, filename: str) -> Optional[Dict]:
        """Read JSON file"""
        filepath = self.results_dir / filename
        if filepath.exists():
            with open(filepath) as f:
                return json.load(f)
        return None
    
    def _read_text(self, filename: str) -> Optional[str]:
        """Read text file"""
        filepath = self.results_dir / filename
        if filepath.exists():
            return filepath.read_text()
        return None
    
    def get_proxmox_nodes(self) -> List[Dict]:
        """Get Proxmox node data"""
        data = self._read_json('proxmox-nodes.json')
        if not data:
            return []
        
        nodes = []
        for node in data:
            nodes.append({
                'name': node.get('node', 'unknown'),
                'ip': node.get('ip', 'N/A'),
                'status': node.get('status', 'unknown'),
                'cpu_usage': round(node.get('cpu', 0) * 100, 1),
                'mem_used': self._format_bytes(node.get('mem', 0)),
                'mem_total': self._format_bytes(node.get('maxmem', 0)),
                'disk_used': self._format_bytes(node.get('disk', 0)),
                'disk_total': self._format_bytes(node.get('maxdisk', 0)),
                'uptime': self._format_uptime(node.get('uptime', 0)),
                'cpu_cores': node.get('maxcpu', 'N/A'),
                'storage_pools': []
            })
        return nodes
    
    def get_vms(self) -> List[Dict]:
        """Get VM inventory"""
        data = self._read_json('proxmox-vms.json')
        if not data:
            return []
        
        vms = []
        for vm in data:
            vms.append({
                'name': vm.get('name', 'unknown'),
                'vmid': vm.get('vmid', 'N/A'),
                'status': vm.get('status', 'unknown'),
                'ip': vm.get('ip', ''),
                'cpu': vm.get('cpus', 1),
                'memory': self._format_bytes(vm.get('maxmem', 0)),
                'node': vm.get('node', 'unknown'),
                'purpose': vm.get('description', '')
            })
        return sorted(vms, key=lambda x: x['name'])
    
    def get_vms_by_node(self, vms: List[Dict]) -> Dict[str, List[Dict]]:
        """Group VMs by Proxmox node"""
        by_node = {}
        for vm in vms:
            node = vm.get('node', 'unknown')
            if node not in by_node:
                by_node[node] = []
            by_node[node].append(vm)
        return by_node
    
    def get_k3s_nodes(self) -> List[Dict]:
        """Get K3s node data"""
        text = self._read_text('k3s-nodes.txt')
        if not text:
            return []
        
        nodes = []
        for line in text.strip().split('\n')[1:]:  # Skip header
            parts = line.split()
            if len(parts) >= 5:
                nodes.append({
                    'name': parts[0],
                    'status': parts[1],
                    'role': parts[2] if parts[2] != '<none>' else 'worker',
                    'version': parts[4] if len(parts) > 4 else 'N/A',
                    'ip': parts[5] if len(parts) > 5 else 'N/A'
                })
        return nodes
    
    def get_k3s_namespaces(self) -> List[Dict]:
        """Get K3s namespaces"""
        text = self._read_text('k3s-namespaces.txt')
        if not text:
            return []
        
        namespaces = []
        for line in text.strip().split('\n')[1:]:
            parts = line.split()
            if len(parts) >= 2:
                namespaces.append({
                    'name': parts[0],
                    'status': parts[1]
                })
        return namespaces
    
    def get_k3s_deployments(self) -> List[Dict]:
        """Get K3s deployments"""
        text = self._read_text('k3s-deployments.txt')
        if not text:
            return []
        
        deployments = []
        for line in text.strip().split('\n')[1:]:
            parts = line.split()
            if len(parts) >= 4:
                deployments.append({
                    'namespace': parts[0],
                    'name': parts[1],
                    'ready': parts[2],
                    'image': parts[3] if len(parts) > 3 else 'N/A'
                })
        return deployments
    
    def get_k3s_services(self) -> List[Dict]:
        """Get K3s services"""
        text = self._read_text('k3s-services.txt')
        if not text:
            return []
        
        services = []
        for line in text.strip().split('\n')[1:]:
            parts = line.split()
            if len(parts) >= 5:
                services.append({
                    'namespace': parts[0],
                    'name': parts[1],
                    'type': parts[2],
                    'cluster_ip': parts[3],
                    'external_ip': parts[4] if parts[4] != '<none>' else '',
                    'ports': parts[5] if len(parts) > 5 else ''
                })
        return services
    
    def get_k3s_ingresses(self) -> List[Dict]:
        """Get K3s ingresses"""
        text = self._read_text('k3s-ingresses.txt')
        if not text:
            return []
        
        ingresses = []
        for line in text.strip().split('\n')[1:]:
            parts = line.split()
            if len(parts) >= 4:
                ingresses.append({
                    'namespace': parts[0],
                    'name': parts[1],
                    'host': parts[3] if len(parts) > 3 else 'N/A',
                    'address': parts[4] if len(parts) > 4 else ''
                })
        return ingresses
    
    @staticmethod
    def _format_bytes(bytes_val: int) -> str:
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024:
                return f"{bytes_val:.1f}{unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f}PB"
    
    @staticmethod
    def _format_uptime(seconds: int) -> str:
        """Format uptime seconds to human readable"""
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d {hours}h"


class BookStackUpdater:
    """Main updater class"""
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path).expanduser()
        self.config = self._load_config()
        self.dry_run = False
        
        # Initialize components
        if self.config['bookstack']['api_token_id'] and self.config['bookstack']['api_token_secret']:
            self.api = BookStackAPI(
                self.config['bookstack']['url'],
                self.config['bookstack']['api_token_id'],
                self.config['bookstack']['api_token_secret']
            )
        else:
            self.api = None
            logger.warning("BookStack API credentials not configured")
        
        self.parser = AuditDataParser(self.config['audit']['results_dir'])
        
        # Setup Jinja2
        template_dir = self.config_path.parent / 'templates'
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))
    
    def _load_config(self) -> Dict:
        """Load configuration file"""
        with open(self.config_path) as f:
            return yaml.safe_load(f)
    
    def run_audit(self) -> bool:
        """Run the homelab audit script"""
        script = Path(self.config['audit']['script']).expanduser()
        if not script.exists():
            logger.error(f"Audit script not found: {script}")
            return False
        
        logger.info(f"Running audit script: {script}")
        try:
            result = subprocess.run(
                [str(script)],
                capture_output=True,
                text=True,
                timeout=600
            )
            if result.returncode != 0:
                logger.error(f"Audit script failed: {result.stderr}")
                return False
            logger.info("Audit completed successfully")
            return True
        except subprocess.TimeoutExpired:
            logger.error("Audit script timed out")
            return False
        except Exception as e:
            logger.error(f"Error running audit: {e}")
            return False
    
    def render_template(self, template_name: str, context: Dict) -> str:
        """Render a Jinja2 template"""
        template = self.jinja_env.get_template(template_name)
        return template.render(**context)
    
    def build_context(self) -> Dict[str, Any]:
        """Build template context from audit data"""
        vms = self.parser.get_vms()
        
        return {
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'nodes': self.parser.get_proxmox_nodes(),
            'vms': vms,
            'vms_by_node': self.parser.get_vms_by_node(vms),
            'k3s_version': 'v1.33.3+k3s1',
            'k3s_nodes': self.parser.get_k3s_nodes(),
            'namespaces': self.parser.get_k3s_namespaces(),
            'deployments': self.parser.get_k3s_deployments(),
            'services': self.parser.get_k3s_services(),
            'ingresses': self.parser.get_k3s_ingresses(),
        }
    
    def update_docs(self) -> Dict[str, int]:
        """Update BookStack documentation"""
        if not self.api:
            logger.error("API not configured - cannot update docs")
            return {'created': 0, 'updated': 0, 'errors': 1}
        
        stats = {'created': 0, 'updated': 0, 'errors': 0}
        context = self.build_context()
        
        for book_key, book_config in self.config['books'].items():
            try:
                # Find or create book
                book = self.api.find_or_create_book(book_config['name'])
                book_id = book['id']
                
                for chapter_config in book_config.get('chapters', []):
                    # Find or create chapter
                    chapter = self.api.find_or_create_chapter(book_id, chapter_config['name'])
                    chapter_id = chapter['id']
                    
                    for page_config in chapter_config.get('pages', []):
                        template_file = page_config.get('template')
                        if not template_file:
                            continue
                        
                        try:
                            # Render template
                            content = self.render_template(
                                Path(template_file).name,
                                context
                            )
                            
                            # Find existing page or create new
                            pages = self.api.get_pages(chapter_id)
                            existing = next(
                                (p for p in pages if p['name'].lower() == page_config['name'].lower()),
                                None
                            )
                            
                            if self.dry_run:
                                action = "Would update" if existing else "Would create"
                                logger.info(f"{action} page: {page_config['name']}")
                            elif existing:
                                self.api.update_page(existing['id'], page_config['name'], content)
                                logger.info(f"Updated page: {page_config['name']}")
                                stats['updated'] += 1
                            else:
                                self.api.create_page(chapter_id, page_config['name'], content)
                                logger.info(f"Created page: {page_config['name']}")
                                stats['created'] += 1
                                
                        except Exception as e:
                            logger.error(f"Error with page {page_config['name']}: {e}")
                            stats['errors'] += 1
                            
            except Exception as e:
                logger.error(f"Error with book {book_config['name']}: {e}")
                stats['errors'] += 1
        
        return stats
    
    def send_notification(self, stats: Dict[str, int]):
        """Send Discord notification"""
        if not self.config['discord'].get('enabled'):
            return
        
        webhook_url = self.config['discord'].get('webhook_url')
        if not webhook_url:
            logger.warning("Discord webhook URL not configured")
            return
        
        from discord_webhook import DiscordWebhook, DiscordEmbed
        
        webhook = DiscordWebhook(url=webhook_url)
        embed = DiscordEmbed(
            title="📚 BookStack Docs Updated",
            description=f"Homelab documentation has been updated.",
            color=0x00ff00 if stats['errors'] == 0 else 0xff9900
        )
        embed.add_embed_field(name="Pages Created", value=str(stats['created']))
        embed.add_embed_field(name="Pages Updated", value=str(stats['updated']))
        embed.add_embed_field(name="Errors", value=str(stats['errors']))
        embed.add_embed_field(
            name="Link",
            value=f"[View Docs]({self.config['bookstack']['url']})",
            inline=False
        )
        embed.set_timestamp()
        
        webhook.add_embed(embed)
        webhook.execute()
        logger.info("Discord notification sent")


def main():
    parser = argparse.ArgumentParser(description='BookStack Documentation Auto-Updater')
    parser.add_argument('--config', '-c', default='config.yaml', help='Config file path')
    parser.add_argument('--audit', '-a', action='store_true', help='Run audit before update')
    parser.add_argument('--update', '-u', action='store_true', help='Update BookStack docs')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Dry run (no changes)')
    parser.add_argument('--notify', action='store_true', help='Send Discord notification')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Find config file
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = Path(__file__).parent / args.config
    
    updater = BookStackUpdater(str(config_path))
    updater.dry_run = args.dry_run
    
    # Run audit if requested
    if args.audit:
        if not updater.run_audit():
            logger.error("Audit failed")
            sys.exit(1)
    
    # Update docs if requested
    stats = {'created': 0, 'updated': 0, 'errors': 0}
    if args.update:
        stats = updater.update_docs()
        logger.info(f"Update complete: {stats}")
    
    # Send notification if requested
    if args.notify:
        updater.send_notification(stats)
    
    sys.exit(0 if stats['errors'] == 0 else 1)


if __name__ == '__main__':
    main()
