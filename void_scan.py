#!/usr/bin/env python3
"""
███████╗██╗   ██╗███████╗██████╗     ███████╗ ██████╗███████╗ █████╗ ███╗   ██╗
██╔════╝██║   ██║██╔════╝██╔══██╗    ██╔════╝██╔════╝██╔════╝██╔══██╗████╗  ██║
███████╗██║   ██║█████╗  ██████╔╝    ███████╗██║     █████╗  ███████║██╔██╗ ██║
╚════██║██║   ██║██╔══╝  ██╔══██╗    ╚════██║██║     ██╔══╝  ██╔══██║██║╚██╗██║
███████║╚██████╔╝███████╗██║  ██║    ███████║╚██████╗███████╗██║  ██║██║ ╚████║
╚══════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝    ╚══════╝ ╚═════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝

ABSOLUTE ZERO - VOIDSCAN 
Author: Meuorie
Description: The ultimate system integrity auditor. Forensics, rootkit, and anomaly detection.
"""

import os, sys, time, hashlib, platform, subprocess, threading, socket, struct, datetime, re, pwd, grp
from pathlib import Path
import psutil
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.live import Live
from rich.layout import Layout
from rich import box

console = Console()

# ============================== CONFIGURATION ==============================

# Known good hashes for critical system binaries (Ubuntu 22.04 x86_64)
# These are educational examples. In a real deployment, a full set should be used.
KNOWN_GOOD_HASHES = {
    "/bin/ls": "f6a7b1f7a9a5c0e7f4b5c1e7cf5f2e7a0",
    "/bin/ps": "b0a1e2f3c4d5e6a7b8c9d0e1f2a3b4c5",
    "/usr/bin/ss": "1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6",
    "/usr/bin/find": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
    "/usr/bin/top": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
    "/usr/sbin/cron": "f6a7b1f7a9a5c0e7f4b5c1e7cf5f2e7a0"
}

# Signatures (substrings) commonly found in malware
MALWARE_STRINGS = [
    b"/etc/vulnerable",
    b"backdoor",
    b"reverse_shell",
    b"c2_server",
    b"mining",
    b"pool.minexmr.com",
    b"stratum+tcp",
    b"powershell -enc",
    b"eval(base64_decode",
    b"system("
]

SUSPICIOUS_PORTS = {4444, 5555, 6667, 1337, 31337, 8080, 8888, 9999, 12345, 54321}

# ============================== CORE ENGINE ==============================

class VoidScan:
    def __init__(self):
        self.version = "2000.0"
        self.author = "Meuorie"
        self.os_env = platform.system()
        self.is_root = os.getuid() == 0 if hasattr(os, "getuid") else False
        self.start_time = datetime.datetime.now()
        self.scan_results = {
            "system": {},
            "processes": [],
            "network": [],
            "autostart": [],
            "files": [],
            "rootkits": [],
            "memory": [],
            "threats": 0
        }
        self.known_hash_db = KNOWN_GOOD_HASHES  # can be expanded

    def banner(self):
        logo = f"""
[bold white]
 ██╗   ██╗ ██████╗ ██╗██████╗     ███████╗ ██████╗███████╗ █████╗ ███╗   ██╗
 ██║   ██║██╔═══██╗██║██╔══██╗    ██╔════╝██╔════╝██╔════╝██╔══██╗████╗  ██║
 ██║   ██║██║   ██║██║██║  ██║    ███████╗██║     █████╗  ███████║██╔██╗ ██║
 ╚██╗ ██╔╝██║   ██║██║██║  ██║    ╚════██║██║     ██╔══╝  ██╔══██║██║╚██╗██║
  ╚████╔╝ ╚██████╔╝██║██████╔╝    ███████║╚██████╗███████╗██║  ██║██║ ╚████║
   ╚═══╝   ╚═════╝ ╚═╝╚═════╝     ╚══════╝ ╚═════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝
[/bold white]
[dim white] ABSOLUTE ZERO THREAT ELIMINATOR | Version {self.version} [/dim white]
[bold magenta] Architect: {self.author} [/bold magenta]
        """
        console.print(Panel(logo, border_style="bold white", padding=(1, 2)))

    def _calculate_hash(self, filepath, algo='sha256'):
        h = hashlib.new(algo)
        try:
            with open(filepath, 'rb') as f:
                while chunk := f.read(8192):
                    h.update(chunk)
            return h.hexdigest()
        except: return None

    def system_info(self):
        self.scan_results["system"] = {
            "Hostname": platform.node(),
            "OS": f"{platform.system()} {platform.release()}",
            "Architecture": platform.machine(),
            "CPU Cores": psutil.cpu_count(logical=True),
            "Total RAM (GB)": round(psutil.virtual_memory().total / (1024**3), 2),
            "Boot Time": datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        }

    # -----------------------------------------------------------------
    # Advanced Process Scan
    # -----------------------------------------------------------------
    def scan_processes(self):
        suspicious = []
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
            try:
                p_info = proc.info
                exe = p_info['exe']
                # Process from temp directory
                if exe:
                    exe_path = Path(exe).resolve()
                    if any(part.lower() in ['temp', 'tmp', 'cache'] for part in exe_path.parts):
                        suspicious.append({"PID": p_info['pid'], "Name": p_info['name'], "Path": str(exe_path), "Reason": "Runs from temporary directory"})
                else:
                    suspicious.append({"PID": p_info['pid'], "Name": p_info['name'] or "Unknown", "Path": "N/A", "Reason": "No executable on disk (memory only)"})
                # Check for known malicious strings in command line
                cmdline = " ".join(p_info['cmdline'] or [])
                for sig in MALWARE_STRINGS:
                    if sig.decode('utf-8', errors='ignore').lower() in cmdline.lower():
                        suspicious.append({"PID": p_info['pid'], "Name": p_info['name'], "Path": str(exe_path) if exe else "N/A", "Reason": f"Malicious pattern: {sig.decode('utf-8', errors='ignore')}"})
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        self.scan_results["processes"] = suspicious

    # -----------------------------------------------------------------
    # Hidden Process Detection (compare /proc with psutil)
    # -----------------------------------------------------------------
    def scan_hidden_processes(self):
        ps_pids = {p.pid for p in psutil.process_iter()}
        proc_pids = set()
        for entry in os.listdir('/proc'):
            if entry.isdigit():
                proc_pids.add(int(entry))
        hidden = proc_pids - ps_pids
        for pid in hidden:
            try:
                with open(f"/proc/{pid}/comm") as f:
                    name = f.read().strip()
            except: name = "unknown"
            self.scan_results["processes"].append({"PID": pid, "Name": name, "Path": f"/proc/{pid}", "Reason": "Hidden process (not in standard APIs)"})

    # -----------------------------------------------------------------
    # Rootkit detection via module comparison
    # -----------------------------------------------------------------
    def scan_rootkits(self):
        try:
            lsmod = subprocess.check_output("lsmod", shell=True, text=True)
            procs_modules = subprocess.check_output("cat /proc/modules", shell=True, text=True)
            if lsmod != procs_modules:
                self.scan_results["rootkits"].append("Possible hidden kernel modules (lsmod vs /proc/modules mismatch)")
        except: pass
        # Check for prominent rootkit signs in /proc
        suspicious_files = ["/proc/.hidden", "/proc/.backdoor", "/proc/.rootkit"]
        for f in suspicious_files:
            if os.path.exists(f):
                self.scan_results["rootkits"].append(f"Rootkit marker found: {f}")

    # -----------------------------------------------------------------
    # Memory Forensic Checks
    # -----------------------------------------------------------------
    def scan_memory(self):
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                maps_file = f"/proc/{proc.info['pid']}/maps"
                with open(maps_file, 'r') as f:
                    for line in f:
                        if 'anon' in line and 'x' in line.split()[1]:
                            self.scan_results["memory"].append(f"PID {proc.info['pid']} ({proc.info['name']}): Anonymous executable memory (possible injection)")
                            break
            except: continue

    # -----------------------------------------------------------------
    # Network scan (promiscuous mode + suspicious ports)
    # -----------------------------------------------------------------
    def scan_network(self):
        suspicious = []
        # Standard connection check
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == 'ESTABLISHED' and conn.raddr:
                lport, rport = conn.laddr.port, conn.raddr.port
                if lport in SUSPICIOUS_PORTS or rport in SUSPICIOUS_PORTS:
                    suspicious.append({"Local": f"{conn.laddr.ip}:{lport}", "Remote": f"{conn.raddr.ip}:{rport}", "PID": conn.pid, "Reason": f"Suspicious port {rport}"})
        # Promiscuous mode check
        for iface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_PACKET:
                    try:
                        with open(f"/sys/class/net/{iface}/flags") as f:
                            flags = int(f.read().strip(), 16)
                            if flags & 0x100:  # IFF_PROMISC
                                suspicious.append({"Local": iface, "Remote": "N/A", "PID": 0, "Reason": "Promiscuous mode active"})
                    except: pass
        self.scan_results["network"] = suspicious

    # -----------------------------------------------------------------
    # Autostart scanning + checking for suspicious entries
    # -----------------------------------------------------------------
    def scan_autostart(self):
        entries = []
        suspicious_entries = []
        paths = []
        if self.os_env == 'Linux':
            paths = [
                os.path.expanduser("~/.config/autostart/"),
                "/etc/xdg/autostart/",
                "/etc/rc.local",
                "/etc/crontab",
                "/var/spool/cron/crontabs/"
            ]
        elif self.os_env == 'Windows':
            paths = [
                os.path.expanduser("~\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"),
                "C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"
            ]
        for base in paths:
            if os.path.isdir(base):
                for root, dirs, files in os.walk(base):
                    for f in files:
                        full = os.path.join(root, f)
                        entries.append(full)
                        # Check file content for malicious strings
                        try:
                            with open(full, 'rb') as fh:
                                content = fh.read()
                                for sig in MALWARE_STRINGS:
                                    if sig in content:
                                        suspicious_entries.append(f"Autorun file {full} contains: {sig.decode('utf-8', errors='ignore')}")
                                        break
                        except: pass
            elif os.path.isfile(base):
                entries.append(base)
        self.scan_results["autostart"] = entries
        self.scan_results["processes"].extend([{"PID": 0, "Name": "AutoStart", "Path": e, "Reason": "Suspicious content"} for e in suspicious_entries])

    # -----------------------------------------------------------------
    # Deep File Scan (hashes + string search)
    # -----------------------------------------------------------------
    def deep_file_scan(self, scan_dirs=None):
        if scan_dirs is None:
            if self.os_env == 'Linux':
                scan_dirs = ['/bin', '/sbin', '/usr/bin', '/usr/sbin', '/etc', '/tmp', '/dev/shm']
            elif self.os_env == 'Windows':
                scan_dirs = ['C:\\Windows\\System32', 'C:\\Windows\\SysWOW64', 'C:\\Users\\Public']
            else:
                scan_dirs = ['/bin', '/usr/bin', '/tmp']
        with Progress(SpinnerColumn(), TextColumn("[bold white]Deep File Scan..."), BarColumn(), TaskProgressColumn(), transient=True) as progress:
            task = progress.add_task("Scanning", total=len(scan_dirs))
            for directory in scan_dirs:
                if not os.path.exists(directory):
                    progress.advance(task)
                    continue
                for root, dirs, files in os.walk(directory):
                    for f in files:
                        filepath = os.path.join(root, f)
                        try:
                            stat = os.stat(filepath)
                            # Check hash of known binaries
                            if filepath in self.known_hash_db:
                                file_hash = self._calculate_hash(filepath)
                                if file_hash and file_hash != self.known_hash_db[filepath]:
                                    self.scan_results["files"].append({"Path": filepath, "Hash": file_hash, "Reason": "Binary modified (integrity failure)"})
                            # Check recently modified and string scan
                            if (time.time() - stat.st_mtime) < 86400:
                                # String scan
                                with open(filepath, 'rb') as fh:
                                    content = fh.read(4096)  # first 4KB
                                    for sig in MALWARE_STRINGS:
                                        if sig in content:
                                            self.scan_results["files"].append({"Path": filepath, "Hash": "", "Reason": f"Matched pattern: {sig.decode('utf-8', errors='ignore')}"})
                                            break
                        except (PermissionError, FileNotFoundError):
                            pass
                progress.advance(task)

    # -----------------------------------------------------------------
    # Report Generation
    # -----------------------------------------------------------------
    def generate_report(self):
        console.print("\n[bold cyan]SCAN RESULTS[/bold cyan]\n")
        sys_table = Table(title="System Information", box=box.SIMPLE)
        sys_table.add_column("Property", style="cyan")
        sys_table.add_column("Value", style="white")
        for k, v in self.scan_results["system"].items():
            sys_table.add_row(k, str(v))
        console.print(sys_table)

        threat_count = (len(self.scan_results["processes"]) + len(self.scan_results["network"]) +
                        len(self.scan_results["files"]) + len(self.scan_results["rootkits"]) +
                        len(self.scan_results["memory"]))

        if threat_count == 0:
            console.print(Panel("[bold green]SYSTEM IS CLEAN. Absolute Zero threats found.[/bold green]", border_style="green"))
        else:
            console.print(Panel(f"[bold red]{threat_count} potential threats detected![/bold red]", border_style="red"))

            if self.scan_results["processes"]:
                proc_table = Table(title="Suspicious Processes", box=box.MINIMAL)
                proc_table.add_column("PID"); proc_table.add_column("Name"); proc_table.add_column("Path"); proc_table.add_column("Reason")
                for p in self.scan_results["processes"]:
                    proc_table.add_row(str(p['PID']), p['Name'], p['Path'][:40], p['Reason'])
                console.print(proc_table)

            if self.scan_results["network"]:
                net_table = Table(title="Network Anomalies", box=box.MINIMAL)
                net_table.add_column("Local"); net_table.add_column("Remote"); net_table.add_column("PID"); net_table.add_column("Reason")
                for n in self.scan_results["network"]:
                    net_table.add_row(n['Local'], n['Remote'], str(n['PID']), n['Reason'])
                console.print(net_table)

            if self.scan_results["files"]:
                file_table = Table(title="Suspicious Files", box=box.MINIMAL)
                file_table.add_column("Path"); file_table.add_column("Hash"); file_table.add_column("Reason")
                for f in self.scan_results["files"]:
                    file_table.add_row(f['Path'][:50], f['Hash'][:15]+"...", f['Reason'])
                console.print(file_table)

            if self.scan_results["rootkits"]:
                root_table = Table(title="Rootkit Indicators", box=box.MINIMAL)
                root_table.add_column("Detail")
                for r in self.scan_results["rootkits"]:
                    root_table.add_row(r)
                console.print(root_table)

            if self.scan_results["memory"]:
                mem_table = Table(title="Memory Anomalies", box=box.MINIMAL)
                mem_table.add_column("Details")
                for m in self.scan_results["memory"]:
                    mem_table.add_row(m)
                console.print(mem_table)

        console.print(f"\n[bold cyan]Autostart entries scanned:[/bold cyan] {len(self.scan_results['autostart'])}")

    def run(self):
        os.system('clear' if os.name == 'posix' else 'cls')
        self.banner()
        if not self.is_root:
            console.print("[yellow]⚠ Root privileges recommended for deep scan.[/yellow]\n")

        while True:
            console.print("[bold cyan]1.[/bold cyan] God Mode (Full Forensics + Rootkit + Memory)")
            console.print("[bold cyan]2.[/bold cyan] Standard Scan (Processes, Network, Autostart, Files)")
            console.print("[bold cyan]3.[/bold cyan] Quick Scan (Processes + Network)")
            console.print("[bold cyan]4.[/bold cyan] Exit")
            choice = Prompt.ask("[bold yellow]Select scan mode[/bold yellow]", choices=["1","2","3","4"])

            self.start_time = datetime.datetime.now()
            if choice == "1":
                self.system_info()
                self.scan_processes()
                self.scan_hidden_processes()
                self.scan_rootkits()
                self.scan_memory()
                self.scan_network()
                self.scan_autostart()
                self.deep_file_scan()
            elif choice == "2":
                self.system_info()
                self.scan_processes()
                self.scan_network()
                self.scan_autostart()
                self.deep_file_scan()
            elif choice == "3":
                self.scan_processes()
                self.scan_network()
            else:
                console.print("[dim]Shutting down Absolute Zero...[/dim]")
                break

            self.generate_report()
            elapsed = (datetime.datetime.now() - self.start_time).total_seconds()
            console.print(f"\n[dim]Scan completed in {elapsed:.2f} seconds by {self.author}.[/dim]")
            input("\n[dim]Press Enter to continue...[/dim]")

if __name__ == "__main__":
    scanner = VoidScan()
    scanner.run()
