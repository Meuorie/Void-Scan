#!/usr/bin/env python3
"""
██╗   ██╗ ██████╗ ██╗██████╗     ███████╗ ██████╗ █████╗ ███╗   ██╗
██║   ██║██╔═══██╗██║██╔══██╗    ██╔════╝██╔════╝██╔══██╗████╗  ██║
██║   ██║██║   ██║██║██║  ██║    ███████╗██║     ███████║██╔██╗ ██║
╚██╗ ██╔╝██║   ██║██║██║  ██║    ╚════██║██║     ██╔══██║██║╚██╗██║
 ╚████╔╝ ╚██████╔╝██║██████╔╝    ███████║╚██████╗██║  ██║██║ ╚████║
  ╚═══╝   ╚═════╝ ╚═╝╚═════╝     ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝

VOID SCAN ULTRA – THE SILENT ENGINE
Author: Meuorie | Version: 2000.0 (ULTIMATE-SHARP)
"""

import os, sys, time, hashlib, platform, subprocess, socket, datetime, math, stat as stat_module
from collections import Counter
from pathlib import Path
import psutil
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich import box

console = Console()

ANIME_CAT = r"""
[bold magenta]
       /|、   ▓
     (｡､ ｡ 7  ▓
      | ~ヽ   ▓
      じしf_,)ノ ▓
[/bold magenta]
"""

MALWARE_STRINGS = [
    b"/etc/vulnerable", b"backdoor", b"reverse_shell", b"c2_server",
    b"mining", b"pool.minexmr.com", b"stratum+tcp",
    b"powershell -enc", b"eval(base64_decode", b"system(",
    b"LD_PRELOAD", b"ptrace_scope", b"kthreadd"
]

SUSPICIOUS_PORTS = {4444, 5555, 6667, 1337, 31337, 8080, 8888, 9999, 12345}

class VoidScan:
    def __init__(self):
        self.version = "2000.0 (ULTIMATE-SHARP)"
        self.author = "Meuorie"
        self.is_root = os.getuid() == 0 if hasattr(os, "getuid") else False
        self.scan_results = {
            "system": {}, "processes": [], "network": [],
            "files": [], "rootkits": [], "memory": [], "behavior": []
        }

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
[bold cyan] ❯❯❯ SILENT ENGINE [/bold cyan] | [bold magenta] {self.author} [/bold magenta] | [dim white] v{self.version} [/dim white]
{ANIME_CAT}
        """
        console.print(Panel(logo, border_style="bright_blue", box=box.SQUARE, padding=(1, 4)))

    def _get_package_manager(self):
        for name, cmd in {"pacman": ["pacman", "-Qkk"], "dpkg": ["dpkg", "--verify"], "rpm": ["rpm", "-V"]}.items():
            if subprocess.run(["which", cmd[0]], capture_output=True).returncode == 0:
                return cmd
        return None

    def _calculate_entropy(self, data):
        if not data: return 0.0
        counts = Counter(data)
        return -sum((count/len(data)) * math.log2(count/len(data)) for count in counts.values())

    def scan_kernel_and_rootkits(self):
        if os.path.exists("/proc/sys/kernel/tainted"):
            with open("/proc/sys/kernel/tainted") as f:
                if f.read().strip() != "0": self.scan_results["rootkits"].append("Kernel is TAINTED")
        
        if "LD_PRELOAD" in os.environ:
            self.scan_results["rootkits"].append(f"LD_PRELOAD Active: {os.environ['LD_PRELOAD']}")

        try:
            lsmod_cnt = len(subprocess.check_output("lsmod", shell=True).splitlines())
            proc_cnt = len(open("/proc/modules").readlines())
            if abs(lsmod_cnt - proc_cnt) > 1:
                self.scan_results["rootkits"].append("STEALTH MODULE DETECTED (lsmod mismatch)")
        except: pass

    def scan_memory_segments(self):
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                with open(f"/proc/{proc.info['pid']}/maps", 'r') as f:
                    for line in f:
                        if 'rwxp' in line and '[stack]' not in line:
                            self.scan_results["memory"].append(f"PID {proc.info['pid']} ({proc.info['name']}): RWX Memory Segment")
                            break
            except: continue

    def deep_forensic_scan(self):
        mgr = self._get_package_manager()
        scan_dirs = ['/bin', '/sbin', '/usr/bin', '/usr/sbin', '/tmp', '/dev/shm']
        
        with Progress(SpinnerColumn(spinner_name="dots12"), TextColumn("[bold white]CORE INTEGRITY SCAN..."), BarColumn(bar_width=40), transient=True) as progress:
            task = progress.add_task("Audit", total=len(scan_dirs))
            for d in scan_dirs:
                if not os.path.exists(d): continue
                
                if mgr and d not in ['/tmp', '/dev/shm']:
                    res = subprocess.run(mgr + [d], capture_output=True, text=True)
                    if "mismatch" in res.stdout.lower() or "altered" in res.stdout.lower():
                        self.scan_results["files"].append({"Path": d, "Reason": "CORE BINARY MODIFIED"})

                for root, _, files in os.walk(d):
                    if '.git' in root: continue
                    for f in files:
                        p = os.path.join(root, f)
                        try:
                            # السطر السحري الوحيد المضاف: تجاهل الملفات الخاصة (sockets, pipes, devices)
                            if not stat_module.S_ISREG(os.lstat(p).st_mode):
                                continue
                            
                            st = os.stat(p)
                            if st.st_mode & 0o4000:
                                self.scan_results["files"].append({"Path": p, "Reason": "SUID BIT SET"})
                            
                            if st.st_size < 5*1024*1024:
                                with open(p, 'rb') as fh:
                                    data = fh.read(4096)
                                    if self._calculate_entropy(data) > 7.85:
                                        self.scan_results["files"].append({"Path": p, "Reason": "HIGH ENTROPY (ENCRYPTED)"})
                                    for sig in MALWARE_STRINGS:
                                        if sig in data:
                                            self.scan_results["files"].append({"Path": p, "Reason": f"MALWARE PATTERN: {sig.decode()}"})
                        except:
                            pass
                progress.advance(task)

    def scan_network_and_procs(self):
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == 'ESTABLISHED' and conn.raddr:
                if conn.raddr.port in SUSPICIOUS_PORTS:
                    self.scan_results["network"].append({"Local": f"{conn.laddr.ip}:{conn.laddr.port}", "Remote": f"{conn.raddr.ip}:{conn.raddr.port}", "Reason": "C2 PORT"})

        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            p = proc.info
            if not p['exe'] and p['name'] and not p['name'].startswith('['):
                self.scan_results["behavior"].append({"PID": p['pid'], "Name": p['name'], "Behavior": "FILELESS EXECUTION"})

    def generate_report(self):
        console.print(f"\n[bold cyan]──── [ {self.author.upper()} AUDIT REPORT ] ────[/bold cyan]\n")
        
        threats = sum(len(v) for k, v in self.scan_results.items() if isinstance(v, list))
        color = "bright_green" if threats == 0 else "bright_red"
        
        score = max(0, 100 - (threats * 10))
        console.print(Panel(f"[bold white]INTEGRITY SCORE:[/bold white] [bold {color}]{score}%[/bold {color}] | [bold white]TOTAL ANOMALIES:[/bold white] [bold {color}]{threats}[/bold {color}]", border_style="white", box=box.ASCII2))

        if threats > 0:
            t = Table(box=box.SIMPLE_HEAVY, header_style="bold cyan", border_style="white", expand=True)
            t.add_column("DOMAIN", style="bold magenta", justify="center")
            t.add_column("IDENTIFIER", style="white")
            t.add_column("SECURITY ALERT", style="bold yellow")
            
            for p in self.scan_results["behavior"]: t.add_row("PROC/BEHAVIOR", str(p['PID']), p['Behavior'])
            for f in self.scan_results["files"]: t.add_row("FILE SYSTEM", f['Path'], f['Reason'])
            for m in self.scan_results["memory"]: t.add_row("MEMORY/RAM", "SEGMENT", m)
            for r in self.scan_results["rootkits"]: t.add_row("KERNEL/LKM", "CORE", r)
            
            console.print(t)
        else:
            console.print(Panel("[bold bright_green]STATUS: SECURE - NO THREATS DETECTED[/bold bright_green]", border_style="bright_green", box=box.DOUBLE))

    def run(self):
        os.system('clear')
        self.banner()
        if not self.is_root:
            console.print(Panel("[bold yellow]PRIVILEGE WARNING: ANALYZING WITHOUT ROOT (RESTRICTED)[/bold yellow]", border_style="yellow", box=box.MINIMAL))
        
        with console.status("[bold white]ENGAGING FORENSIC ENGINE..."):
            self.scan_kernel_and_rootkits()
            self.scan_memory_segments()
            self.scan_network_and_procs()
            self.deep_forensic_scan()
            
        self.generate_report()
        console.print(f"\n[dim white]Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {self.author}[/dim white]")

if __name__ == "__main__":
    try:
        VoidScan().run()
    except KeyboardInterrupt:
        sys.exit(0) 
