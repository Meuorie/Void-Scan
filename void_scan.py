#!/usr/bin/env python3
"""
██╗   ██╗ ██████╗ ██╗██████╗     ███████╗ ██████╗ █████╗ ███╗   ██╗
██║   ██║██╔═══██╗██║██╔══██╗    ██╔════╝██╔════╝██╔══██╗████╗  ██║
██║   ██║██║   ██║██║██║  ██║    ███████╗██║     ███████║██╔██╗ ██║
╚██╗ ██╔╝██║   ██║██║██║  ██║    ╚════██║██║     ██╔══██║██║╚██╗██║
 ╚████╔╝ ╚██████╔╝██║██████╔╝    ███████║╚██████╗██║  ██║██║ ╚████║
  ╚═══╝   ╚═════╝ ╚═╝╚═════╝     ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝

VOID SCAN ULTRA – The Unseen Auditor
Author: Meuorie
"""

import os, sys, time, hashlib, platform, subprocess, socket, struct, datetime, math, stat as stat_module
from collections import Counter
from pathlib import Path
import psutil
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.layout import Layout
from rich import box

console = Console()

# ============================== ANIME PIXEL ART ==============================
ANIME_CAT = r"""
[bold magenta]
       ／l、   ﾞ､
     （ﾟ､ ｡ ７  ﾞ､
      l、 ~ヽ  ﾞ､
      じしf_,)ノ  ﾞ､
[/bold magenta]
"""

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
    b"powershell -enc", b"eval(base64_decode", b"system(",
    b"LD_PRELOAD", b"ptrace_scope", b"kthreadd"
]

SUSPICIOUS_PORTS = {4444, 5555, 6667, 1337, 31337, 8080, 8888, 9999, 12345, 54321}

class VoidScan:
    def __init__(self):
        self.version = "2000.0 (Elite-Ultra)"
        self.author = "Meuorie"
        self.os_env = platform.system()
        self.is_root = os.getuid() == 0 if hasattr(os, "getuid") else False
        self.start_time = datetime.datetime.now()
        self.scan_results = {
            "system": {}, "processes": [], "network": [],
            "autostart": [], "files": [], "rootkits": [],
            "memory": [], "behavior": [], "threats": 0,
            "anomaly_score": 0, "kernel_alerts": []
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
[dim white] VOID SCAN ULTRA | Version {self.version} [/dim white]
[bold magenta] Architect: {self.author} [/bold magenta]
{ANIME_CAT}
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

    def _calculate_entropy(self, data):
        if not data: return 0.0
        entropy = 0.0
        _, counts = 0, Counter(data)
        for count in counts.values():
            prob = count / len(data)
            if prob: entropy -= prob * math.log2(prob)
        return entropy

    def _is_safe_file(self, filepath):
        """تجنب الملفات الخاصة مثل sockets, pipes, devices"""
        try:
            mode = os.lstat(filepath).st_mode
            return stat_module.S_ISREG(mode)  # فقط الملفات العادية
        except:
            return False

    def scan_kernel_integrity(self):
        if self.os_env == 'Linux':
            try:
                with open("/proc/sys/kernel/tainted", "r") as f:
                    if f.read().strip() != "0":
                        self.scan_results["kernel_alerts"].append("Kernel is TAINTED (Possible unauthorized module or hardware error)")
            except: pass
            if "LD_PRELOAD" in os.environ:
                self.scan_results["rootkits"].append(f"LD_PRELOAD detected: {os.environ['LD_PRELOAD']} (Potential User-mode Rootkit)")

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
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'username']):
            try:
                p_info = proc.info
                exe = p_info['exe']
                if p_info['username'] == 'root' and exe and '/home/' in exe:
                    entry = {"PID": p_info['pid'], "Name": p_info['name'], "Path": exe, "Reason": "Root process running from /home (High Risk)"}
                    suspicious.append(entry); self.suspicious_procs.append(entry)
                if exe:
                    exe_path = Path(exe).resolve()
                    if any(part.lower() in ['temp', 'tmp', 'cache'] for part in exe_path.parts):
                        entry = {"PID": p_info['pid'], "Name": p_info['name'], "Path": str(exe_path), "Reason": "Runs from temporary directory"}
                        suspicious.append(entry); self.suspicious_procs.append(entry)
                else:
                    entry = {"PID": p_info['pid'], "Name": p_info['name'] or "Unknown", "Path": "N/A", "Reason": "No executable on disk (memory only)"}
                    suspicious.append(entry); self.suspicious_procs.append(entry)
                cmdline = " ".join(p_info['cmdline'] or [])
                for sig in MALWARE_STRINGS:
                    if sig.decode('utf-8', errors='ignore').lower() in cmdline.lower():
                        entry = {"PID": p_info['pid'], "Name": p_info['name'], "Path": str(exe_path) if exe else "N/A", "Reason": f"Malicious pattern: {sig.decode('utf-8', errors='ignore')}"}
                        suspicious.append(entry); self.suspicious_procs.append(entry)
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied): continue
        self.scan_results["processes"] = suspicious

    def scan_hidden_processes(self):
        ps_pids = {p.pid for p in psutil.process_iter()}
        proc_pids = set()
        for entry in os.listdir('/proc'):
            if entry.isdigit(): proc_pids.add(int(entry))
        for pid in proc_pids - ps_pids:
            try:
                with open(f"/proc/{pid}/comm") as f: name = f.read().strip()
            except: name = "unknown"
            self.scan_results["processes"].append({"PID": pid, "Name": name, "Path": f"/proc/{pid}", "Reason": "Hidden process (Invisible to standard APIs)"})

    def scan_rootkits(self):
        try:
            lsmod = subprocess.check_output("lsmod", shell=True, text=True)
            procs_modules = subprocess.check_output("cat /proc/modules", shell=True, text=True)
            if lsmod.count('\n') != procs_modules.count('\n'):
                self.scan_results["rootkits"].append("Kernel module mismatch detected (lsmod vs /proc/modules)")
        except: pass
        for f in ["/proc/.hidden", "/proc/.backdoor", "/proc/.rootkit", "/tmp/.X11-unix/.ssh"]:
            if os.path.exists(f):
                self.scan_results["rootkits"].append(f"Critical Rootkit marker found: {f}")

    def scan_memory(self):
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                maps_file = f"/proc/{proc.info['pid']}/maps"
                with open(maps_file, 'r') as f:
                    for line in f:
                        if 'rwxp' in line and '[stack]' not in line:
                            self.scan_results["memory"].append(f"PID {proc.info['pid']} ({proc.info['name']}): RWX memory segment (Potential Shellcode)")
                            break
            except: continue

    def scan_network(self):
        suspicious = []
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == 'ESTABLISHED' and conn.raddr:
                lport, rport = conn.laddr.port, conn.raddr.port
                if rport in SUSPICIOUS_PORTS:
                    suspicious.append({"Local": f"{conn.laddr.ip}:{lport}", "Remote": f"{conn.raddr.ip}:{rport}", "PID": conn.pid, "Reason": f"Connection to suspicious port {rport}"})
        for iface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_PACKET:
                    try:
                        with open(f"/sys/class/net/{iface}/flags") as f:
                            flags = int(f.read().strip(), 16)
                            if flags & 0x100:
                                suspicious.append({"Local": iface, "Remote": "N/A", "PID": 0, "Reason": "Network Promiscuous Mode (Sniffing)"})
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
                "/etc/crontab", "/var/spool/cron/crontabs/",
                "/etc/systemd/system/"
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
                            if not self._is_safe_file(full): continue
                            with open(full, 'rb') as fh:
                                content = fh.read()
                                for sig in MALWARE_STRINGS:
                                    if sig in content:
                                        suspicious_entries.append(f"Autorun file {full} contains: {sig.decode('utf-8', errors='ignore')}")
                                        break
                        except: pass
            elif os.path.isfile(base): entries.append(base)
        self.scan_results["autostart"] = entries
        self.scan_results["processes"].extend([{"PID": 0, "Name": "AutoStart", "Path": e, "Reason": "Suspicious persistence entry"} for e in suspicious_entries])

    def deep_file_scan(self, scan_dirs=None):
        if scan_dirs is None:
            if self.os_env == 'Linux':
                scan_dirs = ['/bin', '/sbin', '/usr/bin', '/usr/sbin', '/etc', '/tmp', '/dev/shm', '/var/tmp']
            elif self.os_env == 'Windows':
                scan_dirs = ['C:\\Windows\\System32', 'C:\\Windows\\SysWOW64', 'C:\\Users\\Public']
        with Progress(SpinnerColumn(), TextColumn("[bold white]Deep File Audit..."), BarColumn(), TaskProgressColumn(), transient=True) as progress:
            task = progress.add_task("Auditing", total=len(scan_dirs))
            for directory in scan_dirs:
                if not os.path.exists(directory):
                    progress.advance(task); continue
                for root, dirs, files in os.walk(directory):
                    for f in files:
                        filepath = os.path.join(root, f)
                        try:
                            # ❗️ تجنب الملفات الخاصة
                            if not self._is_safe_file(filepath): continue
                            stat = os.stat(filepath)
                            if self.os_env == 'Linux' and (stat.st_mode & 0o4000):
                                if directory in ['/tmp', '/var/tmp', '/dev/shm']:
                                    self.scan_results["files"].append({"Path": filepath, "Hash": "", "Reason": "SUID bit set in world-writable directory (Dangerous)"})
                            if filepath in KNOWN_GOOD_HASHES:
                                file_hash = self._calculate_hash(filepath)
                                if file_hash and file_hash != KNOWN_GOOD_HASHES[filepath]:
                                    self.scan_results["files"].append({"Path": filepath, "Hash": file_hash, "Reason": "Binary modified (Integrity Failure)"})
                            if (time.time() - stat.st_mtime) < 86400:
                                with open(filepath, 'rb') as fh:
                                    content = fh.read(4096)
                                    for sig in MALWARE_STRINGS:
                                        if sig in content:
                                            self.scan_results["files"].append({"Path": filepath, "Hash": "", "Reason": f"Matched pattern: {sig.decode('utf-8', errors='ignore')}"})
                                            break
                        except (PermissionError, FileNotFoundError, OSError): pass
                progress.advance(task)

    def entropy_scan(self):
        scan_dirs = ['/tmp', '/dev/shm', '/var/tmp'] if self.os_env == 'Linux' else ['C:\\Users\\Public']
        for directory in scan_dirs:
            if os.path.exists(directory):
                for root, _, files in os.walk(directory):
                    for f in files:
                        path = os.path.join(root, f)
                        try:
                            if not self._is_safe_file(path): continue
                            if os.path.getsize(path) > 1024 * 1024 * 10: continue
                            with open(path, 'rb') as fh: data = fh.read(8192)
                            entropy = self._calculate_entropy(data)
                            if entropy > 7.7:
                                self.scan_results["files"].append({"Path": path, "Hash": "", "Reason": f"High entropy ({entropy:.2f}) - Encrypted/Packed payload?"})
                        except: pass

    def behavioral_scan(self):
        for proc_entry in self.suspicious_procs[:30]:
            try:
                p = psutil.Process(proc_entry['PID'])
                for f in p.open_files():
                    if any(x in f.path for x in ['event', 'kbd', 'input']):
                        self.scan_results["behavior"].append({**proc_entry, "Behavior": f"Sniffing input device: {f.path}"})
                if p.cpu_percent(interval=0.1) > 80:
                    self.scan_results["behavior"].append({**proc_entry, "Behavior": "Extreme CPU usage (Potential Crypto-miner)"})
                if len(p.connections()) > 50:
                    self.scan_results["behavior"].append({**proc_entry, "Behavior": "Massive network socket pooling (C2/DDoS activity)"})
            except: pass

    def generate_report(self):
        threat_count = (len(self.scan_results["processes"]) + len(self.scan_results["network"]) +
                        len(self.scan_results["files"]) + len(self.scan_results["rootkits"]) +
                        len(self.scan_results["memory"]) + len(self.scan_results["behavior"]) +
                        len(self.scan_results["kernel_alerts"]))
        self.scan_results["anomaly_score"] = min(100, threat_count * 3)
        health_score = max(0, 100 - self.scan_results["anomaly_score"])

        console.print("\n[bold cyan]─── VOID SCAN ELITE ULTRA REPORT ───[/bold cyan]\n")
        sys_table = Table(title="System Profile", box=box.HORIZONTALS)
        sys_table.add_column("Property", style="cyan"); sys_table.add_column("Value", style="white")
        for k, v in self.scan_results["system"].items(): sys_table.add_row(k, str(v))
        console.print(sys_table)

        if self.scan_results["kernel_alerts"]:
            for alert in self.scan_results["kernel_alerts"]:
                console.print(Panel(f"[bold blink red]KERNEL CRITICAL: {alert}[/bold blink red]", border_style="red"))

        color = "green" if health_score >= 90 else "yellow" if health_score >= 60 else "red"
        console.print(Panel(f"[bold {color}]SYSTEM TRUST SCORE: {health_score}%[/bold {color}]", border_style=color))

        if threat_count == 0:
            console.print(Panel("[bold green]✓ SYSTEM CLEAN.[/bold green]", border_style="green"))
        else:
            console.print(Panel(f"[bold red]⚠ {threat_count} SECURITY ANOMALIES![/bold red]", border_style="red"))
            def tbl(title, data, cols):
                if not data: return
                t = Table(title=title, box=box.ROUNDED, header_style="bold magenta")
                for c in cols: t.add_column(c)
                for row in data: t.add_row(*[str(row.get(c, '') or '')[:60] for c in cols])
                console.print(t)
            tbl("Processes", self.scan_results["processes"], ["PID","Name","Path","Reason"])
            tbl("Network", self.scan_results["network"], ["Local","Remote","PID","Reason"])
            tbl("Files", self.scan_results["files"], ["Path","Reason"])
            tbl("Behavior", self.scan_results["behavior"], ["PID","Name","Behavior"])
            if self.scan_results["rootkits"]:
                console.print(Panel("[bold red]Rootkit Indicators:[/bold red]\n"+"\n".join(self.scan_results["rootkits"]), title="CRITICAL"))

        console.print(f"\n[dim white]Autostart entries scanned: {len(self.scan_results['autostart'])}[/dim white]")

    def run(self):
        os.system('clear' if os.name == 'posix' else 'cls')
        self.banner()
        if not self.is_root:
            console.print(Panel("[yellow]⚠ Run as root for full kernel & memory scan.[/yellow]", border_style="yellow"))

        while True:
            console.print("[bold cyan]1.[/bold cyan] Full Ultra Scan (Kernel + Memory + Heuristics)")
            console.print("[bold cyan]2.[/bold cyan] Forensic Integrity Scan (Files + Autostart)")
            console.print("[bold cyan]3.[/bold cyan] Quick Triage (Net + Procs)")
            console.print("[bold cyan]4.[/bold cyan] Exit")
            choice = Prompt.ask("[bold yellow]Action[/bold yellow]", choices=["1","2","3","4"])

            self.start_time = datetime.datetime.now()
            self.scan_results = {
                "system": {}, "processes": [], "network": [],
                "autostart": [], "files": [], "rootkits": [],
                "memory": [], "behavior": [], "threats": 0,
                "anomaly_score": 0, "kernel_alerts": []
            }
            self.suspicious_procs = []

            if choice == "1":
                self.system_info()
                self.scan_kernel_integrity()
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
                self.scan_autostart()
                self.deep_file_scan()
                self.entropy_scan()
            elif choice == "3":
                self.scan_processes()
                self.scan_network()
            else:
                console.print(f"[bold magenta]Terminating {self.author}'s VOID SCAN ULTRA...[/bold magenta]")
                break

            self.generate_report()
            elapsed = (datetime.datetime.now() - self.start_time).total_seconds()
            console.print(f"\n[dim]Audit finished in {elapsed:.2f}s. Engine: {self.version}[/dim]")
            input("\n[bold white]Press Enter to return...[/bold white]")

if __name__ == "__main__":
    try:
        VoidScan().run()
    except KeyboardInterrupt:
        console.print("\n[red]Scan aborted.[/red]")
        sys.exit(0)
