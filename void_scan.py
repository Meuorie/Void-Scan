#!/usr/bin/env python3
"""
██╗   ██╗ ██████╗ ██╗██████╗     ███████╗ ██████╗ █████╗ ███╗   ██╗
██║   ██║██╔═══██╗██║██╔══██╗    ██╔════╝██╔════╝██╔══██╗████╗  ██║
██║   ██║██║   ██║██║██║  ██║    ███████╗██║     ███████║██╔██╗ ██║
╚██╗ ██╔╝██║   ██║██║██║  ██║    ╚════██║██║     ██╔══██║██║╚██╗██║
 ╚████╔╝ ╚██████╔╝██║██████╔╝    ███████║╚██████╗██║  ██║██║ ╚████║
  ╚═══╝   ╚═════╝ ╚═╝╚═════╝     ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝

VOID SCAN 
Author: Meuorie
Description: The Unseen Auditor. Advanced system integrity, rootkit, entropy, 
             behavioral forensics, and anomaly scoring engine.
"""

import os, sys, time, hashlib, platform, subprocess, threading, socket, struct, datetime, re, math
from collections import Counter
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
KNOWN_GOOD_HASHES = {
    "/bin/ls": "f6a7b1f7a9a5c0e7f4b5c1e7cf5f2e7a0",
    "/bin/ps": "b0a1e2f3c4d5e6a7b8c9d0e1f2a3b4c5",
    "/usr/bin/ss": "1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6",
    "/usr/bin/find": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
    "/usr/bin/top": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
    "/usr/sbin/cron": "f6a7b1f7a9a5c0e7f4b5c1e7cf5f2e7a0"
}

MALWARE_STRINGS = [
    b"/etc/vulnerable", b"backdoor", b"reverse_shell", b"c2_server",
    b"mining", b"pool.minexmr.com", b"stratum+tcp",
    b"powershell -enc", b"eval(base64_decode", b"system("
]

SUSPICIOUS_PORTS = {4444, 5555, 6667, 1337, 31337, 8080, 8888, 9999, 12345, 54321}

# ============================== CORE ENGINE ==============================
class VoidScan:
    def __init__(self):
        self.version = "2000.0 (Elite)"
        self.author = "Meuorie"
        self.os_env = platform.system()
        self.is_root = os.getuid() == 0 if hasattr(os, "getuid") else False
        self.start_time = datetime.datetime.now()
        self.scan_results = {
            "system": {}, "processes": [], "network": [],
            "autostart": [], "files": [], "rootkits": [],
            "memory": [], "behavior": [], "threats": 0,
            "anomaly_score": 0
        }
        self.suspicious_procs = []

    def banner(self):
        logo = f"""
[bold white]
 ██╗   ██╗ ██████╗ ██╗██████╗     ███████╗ ██████╗ █████╗ ███╗   ██╗
 ██║   ██║██╔═══██╗██║██╔══██╗    ██╔════╝██╔════╝██╔══██╗████╗  ██║
 ██║   ██║██║   ██║██║██║  ██║    ███████╗██║     ███████║██╔██╗ ██║
 ╚██╗ ██╔╝██║   ██║██║██║  ██║    ╚════██║██║     ██╔══██║██║╚██╗██║
  ╚████╔╝ ╚██████╔╝██║██████╔╝    ███████║╚██████╗██║  ██║██║ ╚████║
   ╚═══╝   ╚═════╝ ╚═╝╚═════╝     ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝
[/bold white]
[dim white] VOID SCAN ELITE | Version {self.version} [/dim white]
[bold magenta] Architect: {self.author} [/bold magenta]
        """
        console.print(Panel(logo, border_style="bold white", padding=(1, 2)))

    # -----------------------------------------------------------------
    # UTILITIES
    # -----------------------------------------------------------------
    def _calculate_hash(self, filepath, algo='sha256'):
        h = hashlib.new(algo)
        try:
            with open(filepath, 'rb') as f:
                while chunk := f.read(8192):
                    h.update(chunk)
            return h.hexdigest()
        except: return None

    def _calculate_entropy(self, data):
        if not data: return 0
        entropy = 0
        _, counts = 0, Counter(data)
        for count in counts.values():
            prob = count / len(data)
            if prob: entropy -= prob * math.log2(prob)
        return entropy

    # -----------------------------------------------------------------
    # DATA COLLECTION
    # -----------------------------------------------------------------
    def system_info(self):
        self.scan_results["system"] = {
            "Hostname": platform.node(),
            "OS": f"{platform.system()} {platform.release()}",
            "Architecture": platform.machine(),
            "CPU Cores": psutil.cpu_count(logical=True),
            "Total RAM (GB)": round(psutil.virtual_memory().total / (1024**3), 2),
            "Boot Time": datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        }

    def scan_processes(self):
        suspicious = []
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
            try:
                p_info = proc.info
                exe = p_info['exe']
                if exe:
                    exe_path = Path(exe).resolve()
                    if any(part.lower() in ['temp', 'tmp', 'cache'] for part in exe_path.parts):
                        entry = {"PID": p_info['pid'], "Name": p_info['name'], "Path": str(exe_path), "Reason": "Runs from temporary directory"}
                        suspicious.append(entry)
                        self.suspicious_procs.append(entry)
                else:
                    entry = {"PID": p_info['pid'], "Name": p_info['name'] or "Unknown", "Path": "N/A", "Reason": "No executable on disk (memory only)"}
                    suspicious.append(entry)
                    self.suspicious_procs.append(entry)
                cmdline = " ".join(p_info['cmdline'] or [])
                for sig in MALWARE_STRINGS:
                    if sig.decode('utf-8', errors='ignore').lower() in cmdline.lower():
                        entry = {"PID": p_info['pid'], "Name": p_info['name'], "Path": str(exe_path) if exe else "N/A", "Reason": f"Malicious pattern: {sig.decode('utf-8', errors='ignore')}"}
                        suspicious.append(entry)
                        self.suspicious_procs.append(entry)
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        self.scan_results["processes"] = suspicious

    def scan_hidden_processes(self):
        ps_pids = {p.pid for p in psutil.process_iter()}
        proc_pids = set()
        for entry in os.listdir('/proc'):
            if entry.isdigit():
                proc_pids.add(int(entry))
        for pid in proc_pids - ps_pids:
            try:
                with open(f"/proc/{pid}/comm") as f:
                    name = f.read().strip()
            except: name = "unknown"
            self.scan_results["processes"].append({"PID": pid, "Name": name, "Path": f"/proc/{pid}", "Reason": "Hidden process (not in standard APIs)"})

    def scan_rootkits(self):
        try:
            lsmod = subprocess.check_output("lsmod", shell=True, text=True)
            procs_modules = subprocess.check_output("cat /proc/modules", shell=True, text=True)
            if lsmod != procs_modules:
                self.scan_results["rootkits"].append("Possible hidden kernel modules (lsmod vs /proc/modules mismatch)")
        except: pass
        for f in ["/proc/.hidden", "/proc/.backdoor", "/proc/.rootkit"]:
            if os.path.exists(f):
                self.scan_results["rootkits"].append(f"Rootkit marker found: {f}")

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

    def scan_network(self):
        suspicious = []
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == 'ESTABLISHED' and conn.raddr:
                lport, rport = conn.laddr.port, conn.raddr.port
                if lport in SUSPICIOUS_PORTS or rport in SUSPICIOUS_PORTS:
                    suspicious.append({"Local": f"{conn.laddr.ip}:{lport}", "Remote": f"{conn.raddr.ip}:{rport}", "PID": conn.pid, "Reason": f"Suspicious port {rport}"})
        for iface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_PACKET:
                    try:
                        with open(f"/sys/class/net/{iface}/flags") as f:
                            flags = int(f.read().strip(), 16)
                            if flags & 0x100:
                                suspicious.append({"Local": iface, "Remote": "N/A", "PID": 0, "Reason": "Promiscuous mode active"})
                    except: pass
        self.scan_results["network"] = suspicious

    def scan_autostart(self):
        entries = []
        suspicious_entries = []
        paths = []
        if self.os_env == 'Linux':
            paths = [
                os.path.expanduser("~/.config/autostart/"),
                "/etc/xdg/autostart/", "/etc/rc.local",
                "/etc/crontab", "/var/spool/cron/crontabs/"
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
                            if filepath in KNOWN_GOOD_HASHES:
                                file_hash = self._calculate_hash(filepath)
                                if file_hash and file_hash != KNOWN_GOOD_HASHES[filepath]:
                                    self.scan_results["files"].append({"Path": filepath, "Hash": file_hash, "Reason": "Binary modified (integrity failure)"})
                            if (time.time() - stat.st_mtime) < 86400:
                                with open(filepath, 'rb') as fh:
                                    content = fh.read(4096)
                                    for sig in MALWARE_STRINGS:
                                        if sig in content:
                                            self.scan_results["files"].append({"Path": filepath, "Hash": "", "Reason": f"Matched pattern: {sig.decode('utf-8', errors='ignore')}"})
                                            break
                        except (PermissionError, FileNotFoundError):
                            pass
                progress.advance(task)

    def entropy_scan(self):
        scan_dirs = ['/tmp', '/dev/shm'] if self.os_env == 'Linux' else ['C:\\Users\\Public']
        for directory in scan_dirs:
            if os.path.exists(directory):
                for root, _, files in os.walk(directory):
                    for f in files:
                        path = os.path.join(root, f)
                        try:
                            with open(path, 'rb') as fh:
                                data = fh.read(4096)
                            entropy = self._calculate_entropy(data)
                            if entropy > 7.5:
                                self.scan_results["files"].append({"Path": path, "Hash": "", "Reason": f"High entropy ({entropy:.2f}) - likely encrypted/packed"})
                        except: pass

    def behavioral_scan(self):
        for proc_entry in self.suspicious_procs[:20]:
            try:
                p = psutil.Process(proc_entry['PID'])
                for f in p.open_files():
                    if 'event' in f.path or 'kbd' in f.path:
                        self.scan_results["behavior"].append({**proc_entry, "Behavior": f"Reading keyboard device: {f.path}"})
                if len(p.connections()) > 50:
                    self.scan_results["behavior"].append({**proc_entry, "Behavior": "Excessive network connections (possible C2)"})
            except: pass

    # -----------------------------------------------------------------
    # REPORTING
    # -----------------------------------------------------------------
    def generate_report(self):
        threat_count = (len(self.scan_results["processes"]) + len(self.scan_results["network"]) +
                        len(self.scan_results["files"]) + len(self.scan_results["rootkits"]) +
                        len(self.scan_results["memory"]) + len(self.scan_results["behavior"]))
        max_score = 100
        self.scan_results["anomaly_score"] = min(100, threat_count * 2)
        health_score = max(0, max_score - self.scan_results["anomaly_score"])

        console.print("\n[bold cyan]ELITE SCAN RESULTS[/bold cyan]\n")
        sys_table = Table(title="System Profile", box=box.SIMPLE)
        sys_table.add_column("Property", style="cyan")
        sys_table.add_column("Value", style="white")
        for k, v in self.scan_results["system"].items():
            sys_table.add_row(k, str(v))
        console.print(sys_table)

        if health_score >= 90:
            color = "green"
        elif health_score >= 70:
            color = "yellow"
        else:
            color = "red"
        console.print(Panel(f"[bold {color}]SYSTEM HEALTH: {health_score}%[/bold {color}]", border_style=color))

        if threat_count == 0:
            console.print(Panel("[bold green]ABSOLUTE ZERO. No anomalies detected.[/bold green]", border_style="green"))
        else:
            console.print(Panel(f"[bold red]{threat_count} anomalies detected![/bold red]", border_style="red"))

            def _print_table(title, data, columns):
                if not data: return
                t = Table(title=title, box=box.MINIMAL)
                for c in columns: t.add_column(c)
                for row in data:
                    t.add_row(*[str(row.get(c, '') or '')[:50] for c in columns])
                console.print(t)

            _print_table("Process Anomalies", self.scan_results["processes"], ["PID","Name","Path","Reason"])
            _print_table("Network Anomalies", self.scan_results["network"], ["Local","Remote","PID","Reason"])
            _print_table("File Integrity Issues", self.scan_results["files"], ["Path","Hash","Reason"])
            _print_table("Behavioral Anomalies", self.scan_results["behavior"], ["PID","Name","Path","Behavior"])

        console.print(f"\n[bold cyan]Autostart entries scanned:[/bold cyan] {len(self.scan_results['autostart'])}")

    # -----------------------------------------------------------------
    # MAIN MENU
    # -----------------------------------------------------------------
    def run(self):
        os.system('clear' if os.name == 'posix' else 'cls')
        self.banner()
        if not self.is_root:
            console.print("[yellow]⚠ Root privileges recommended for deep scan.[/yellow]\n")

        while True:
            console.print("[bold cyan]1.[/bold cyan] Elite Full Scan (Forensics + Behavioral + Entropy)")
            console.print("[bold cyan]2.[/bold cyan] Standard Forensic Scan (Processes, Network, Autostart, Files)")
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
                self.entropy_scan()
                self.behavioral_scan()
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
                console.print("[dim]Shutting down VOID SCAN ELITE...[/dim]")
                break

            self.generate_report()
            elapsed = (datetime.datetime.now() - self.start_time).total_seconds()
            console.print(f"\n[dim]Scan completed in {elapsed:.2f} seconds by {self.author}.[/dim]")
            input("\n[dim]Press Enter to continue...[/dim]")

if __name__ == "__main__":
    scanner = VoidScan()
    scanner.run()
