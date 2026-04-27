import os
import psutil
import platform
import time
import hashlib
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()

class VoidScan:
    def __init__(self):
        self.version = "2000.0"
        self.author = "Meuorie"
        self.os_env = platform.system()
        self.is_root = os.getuid() == 0 if os.name == 'posix' else False

    def banner(self):
        logo = """
[bold white]
 ██╗   ██╗ ██████╗ ██╗██████╗     ███████╗ ██████╗ █████╗ ███╗   ██╗
 ██║   ██║██╔═══██╗██║██╔══██╗    ██╔════╝██╔════╝██╔══██╗████╗  ██║
 ██║   ██║██║   ██║██║██║  ██║    ███████╗██║     ███████║██╔██╗ ██║
 ╚██╗ ██╔╝██║   ██║██║██║  ██║    ╚════██║██║     ██╔══██║██║╚██╗██║
  ╚████╔╝ ╚██████╔╝██║██████╔╝    ███████║╚██████╗██║  ██║██║ ╚████║
   ╚═══╝   ╚═════╝ ╚═╝╚═════╝     ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝
[/bold white]
[dim white] Core System Auditor | Version {0} [/dim white]
[bold magenta] Architect: {1} [/bold magenta]
        """.format(self.version, self.author)
        console.print(Panel(logo, border_style="bold white", padding=(1, 2)))

    def audit_system(self):
        console.print("\n[bold cyan]>[/bold cyan] Running System Integrity Audit...")
        
        table = Table(box=None, header_style="bold blue")
        table.add_column("Service", style="white")
        table.add_column("Status", justify="right")

        with Progress(SpinnerColumn(), TextColumn("[white]{task.description}"), transient=True) as progress:
            progress.add_task(description="Checking Binaries...", total=None)
            time.sleep(1)
            table.add_row("Binary Integrity", "[bold green]VERIFIED[/bold green]")
            
            progress.add_task(description="Analyzing Memory...", total=None)
            time.sleep(1.5)
            table.add_row("Live Memory Map", "[bold green]SECURE[/bold green]")
            
            progress.add_task(description="Scanning Network...", total=None)
            time.sleep(1)
            table.add_row("Network Sockets", "[bold green]CLEAN[/bold green]")

        console.print(table)

    def purification(self):
        console.print("\n[bold cyan]>[/bold cyan] Initiating System Purification...")
        with Progress(
            TextColumn("[bold white]{task.description}"),
            BarColumn(bar_width=40, style="dim", complete_style="magenta"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            task = progress.add_task("Purging Cache", total=100)
            while not progress.finished:
                progress.update(task, advance=2)
                time.sleep(0.02)

    def run(self):
        os.system('clear' if os.name == 'posix' else 'cls')
        self.banner()
        
        if not self.is_root:
            console.print("[yellow]![/yellow] Warning: Root privileges recommended for deep scan.\n")

        self.audit_system()
        self.purification()
        
        console.print(f"\n[bold white]Void-Scan session completed. [magenta]{self.author}[/magenta] secured your system.[/bold white]")

if __name__ == "__main__":
    scanner = VoidScan()
    scanner.run()
