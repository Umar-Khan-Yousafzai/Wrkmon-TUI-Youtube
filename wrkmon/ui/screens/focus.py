"""Focus mode screen for wrkmon.

Displays a clean terminal output overlay (htop, build log, or test runner).
Press any key or Escape to dismiss.
"""

import random

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static
from textual.binding import Binding


def _fake_htop() -> str:
    cpu_count = random.choice([4, 8, 12, 16])
    mem_total = random.choice([8, 16, 32, 64])
    mem_used = round(random.uniform(mem_total * 0.30, mem_total * 0.75), 1)
    swap_total = mem_total // 2
    swap_used = round(random.uniform(0.1, swap_total * 0.25), 1)
    tasks_total = random.randint(180, 340)
    tasks_running = random.randint(1, 5)
    uptime_h = random.randint(0, 72)
    uptime_m = random.randint(0, 59)
    load_1 = round(random.uniform(0.05, cpu_count * 0.6), 2)
    load_5 = round(random.uniform(0.05, cpu_count * 0.5), 2)
    load_15 = round(random.uniform(0.05, cpu_count * 0.4), 2)

    bars = []
    for i in range(1, cpu_count + 1):
        usage = random.uniform(0.5, 95.0)
        filled = int(usage / 100 * 40)
        bar = "|" * filled + " " * (40 - filled)
        bars.append(f"  {i:>2} [{bar} {usage:5.1f}%]")
    cpu_section = "\n".join(bars)

    mem_filled = int(mem_used / mem_total * 40)
    mem_bar = "|" * mem_filled + " " * (40 - mem_filled)
    swap_filled = int(swap_used / swap_total * 40)
    swap_bar = "|" * swap_filled + " " * (40 - swap_filled)

    header = "  PID USER      PRI  NI  VIRT   RES   SHR S  CPU%  MEM%   TIME+  Command"
    separator = "-" * 90

    users = ["root", "umer", "www-data", "nobody", "systemd+", "postgres", "redis"]
    commands = [
        "/usr/lib/systemd/systemd --switched-root --system",
        "/usr/bin/dbus-daemon --system --address=systemd:",
        "/usr/lib/systemd/systemd-journald",
        "/usr/lib/systemd/systemd-udevd",
        "/usr/sbin/NetworkManager --no-daemon",
        "/usr/bin/python3 /usr/bin/networkd-dispatcher --run-startup",
        "/usr/lib/systemd/systemd-resolved",
        "/usr/lib/systemd/systemd-logind",
        "/usr/sbin/cupsd -l",
        "/usr/bin/pulseaudio --daemonize=no --log-target=journal",
        "/usr/lib/xorg/Xorg -core :0 -seat seat0 -auth /var/run/lightdm",
        "/usr/bin/gnome-shell",
        "/usr/lib/gnome-terminal/gnome-terminal-server",
        "/usr/bin/bash",
        "node /usr/lib/node_modules/pm2/lib/Satan.js",
        "/usr/sbin/sshd -D",
        "/usr/lib/postgresql/14/bin/postgres -D /var/lib/postgresql",
        "/usr/bin/redis-server 127.0.0.1:6379",
        "containerd --config /etc/containerd/config.toml",
        "/usr/bin/dockerd -H fd:// --containerd=/run/containerd",
        "/usr/lib/systemd/systemd-timesyncd",
        "/usr/sbin/cron -f",
        "[kworker/0:1-events]",
        "[kworker/u16:2-flush-259:0]",
        "[rcu_sched]",
        "[ksoftirqd/0]",
    ]

    procs = []
    used_pids: set[int] = set()
    for _ in range(24):
        pid = random.randint(1, 32000)
        while pid in used_pids:
            pid = random.randint(1, 32000)
        used_pids.add(pid)
        user = random.choice(users)
        pri = random.randint(0, 39)
        ni = random.choice([0, 0, 0, 0, -5, -10, 10, 19])
        virt = f"{random.randint(4, 4096)}M"
        res = f"{random.randint(1, 512)}M"
        shr = f"{random.randint(0, 128)}M"
        state = random.choice(["S", "S", "S", "S", "R", "D", "I"])
        cpu = round(random.uniform(0.0, 18.0), 1)
        mem = round(random.uniform(0.0, 8.0), 1)
        minutes = random.randint(0, 120)
        seconds = random.randint(0, 59)
        hundredths = random.randint(0, 99)
        time_str = f"{minutes}:{seconds:02d}.{hundredths:02d}"
        cmd = random.choice(commands)
        procs.append(
            f"  {pid:>5} {user:<9} {pri:>3}  {ni:>2} {virt:>6} {res:>5} {shr:>5} "
            f"{state}  {cpu:5.1f} {mem:5.1f} {time_str:>8}  {cmd}"
        )

    return (
        f"htop - {uptime_h}:{uptime_m:02d}:00 up {uptime_h} hr,"
        f"  load average: {load_1}, {load_5}, {load_15}\n"
        f"Tasks: {tasks_total}, {tasks_running} running\n\n"
        f"{cpu_section}\n"
        f"  Mem [{mem_bar} {mem_used:5.1f}G/{mem_total}G]\n"
        f"  Swp [{swap_bar} {swap_used:5.1f}G/{swap_total}G]\n\n"
        f"{header}\n{separator}\n"
        + "\n".join(procs)
        + "\n\n  F1Help  F2Setup  F3Search  F4Filter  F5Tree  F6SortBy"
        "  F7Nice-  F8Nice+  F9Kill  F10Quit"
    )


def _fake_npm_build() -> str:
    project = random.choice([
        "dashboard-frontend", "admin-panel", "customer-portal",
        "internal-tools", "analytics-ui", "design-system",
    ])
    node_ver = f"{random.choice([16, 18, 20])}.{random.randint(0, 19)}.{random.randint(0, 9)}"
    webpack_ver = f"5.{random.randint(75, 92)}.{random.randint(0, 3)}"
    total_modules = random.randint(180, 420)

    modules = [
        "src/index.tsx", "src/App.tsx", "src/store/index.ts",
        "src/store/slices/authSlice.ts", "src/components/Header/Header.tsx",
        "src/components/Sidebar/Sidebar.tsx", "src/components/Dashboard/Dashboard.tsx",
        "src/components/Dashboard/Chart.tsx", "src/components/Auth/Login.tsx",
        "src/hooks/useAuth.ts", "src/utils/api.ts", "src/styles/globals.css",
    ]

    lines = [
        f"$ npm run build",
        "",
        f"> {project}@2.{random.randint(0, 9)}.{random.randint(0, 15)} build",
        "> webpack --mode production --config webpack.prod.js",
        "",
        f"[webpack-cli] Compiling...",
        "",
    ]

    for mod in random.sample(modules, min(len(modules), 10)):
        size = random.randint(2, 580)
        lines.append(f"  {mod} {size} KiB [built]")

    lines.append("")

    chunks = [
        ("main", random.randint(120, 380)),
        ("vendor", random.randint(400, 900)),
        ("runtime", random.randint(2, 12)),
    ]

    lines.append("asset                                 size       chunks  name")
    lines.append("-" * 67)
    total_size = 0
    for name, size in chunks:
        hash_str = f"{random.randint(0, 0xFFFFFFFF):08x}"
        total_size += size
        lines.append(f"  {name}.{hash_str}.js{' ' * (30 - len(name))} {size:>5} KiB  [{name}]")

    build_time = round(random.uniform(8.5, 45.0), 2)
    lines.extend([
        "",
        f"webpack {webpack_ver} compiled successfully in {int(build_time * 1000)} ms",
        "",
        f"  {total_modules} modules",
        f"  {len(chunks)} assets",
        f"  {total_size} KiB total",
        "",
        f"Done in {build_time}s.",
    ])

    return "\n".join(lines)


def _fake_pytest() -> str:
    project = random.choice([
        "backend-api", "data-pipeline", "ml-service",
        "auth-service", "notification-service", "core-lib",
    ])
    py_ver = f"3.{random.choice([10, 11, 12])}.{random.randint(0, 8)}"
    pytest_ver = f"7.{random.randint(2, 4)}.{random.randint(0, 3)}"
    mod_name = project.replace("-", "_")

    test_files = [
        "tests/unit/test_auth.py", "tests/unit/test_users.py",
        "tests/unit/test_models.py", "tests/unit/test_validators.py",
        "tests/unit/test_utils.py", "tests/unit/test_cache.py",
        "tests/integration/test_api_endpoints.py",
        "tests/integration/test_database.py",
    ]

    test_names = [
        "test_create_user", "test_login_valid_credentials",
        "test_login_invalid_password", "test_token_refresh",
        "test_user_profile_update", "test_list_pagination",
        "test_search_filter", "test_permission_denied",
        "test_rate_limiting", "test_input_validation",
        "test_cache_invalidation", "test_database_transaction",
    ]

    lines = [
        f"$ python -m pytest tests/ -v --tb=short --cov={mod_name}",
        "",
        "=" * 60 + " test session starts " + "=" * 19,
        f"platform linux -- Python {py_ver}, pytest-{pytest_ver}",
        f"rootdir: /home/umer/projects/{project}",
        "configfile: pyproject.toml",
        f"collected {len(test_names)} items",
        "",
    ]

    passed = 0
    for test_file in random.sample(test_files, min(6, len(test_files))):
        for t in random.sample(test_names, min(3, len(test_names))):
            outcome = random.choices(["PASSED", "SKIPPED"], weights=[90, 10], k=1)[0]
            if outcome == "PASSED":
                passed += 1
            lines.append(f"{test_file}::{t} {outcome}")

    total = passed + (len(lines) - 8 - passed)
    duration = round(random.uniform(4.0, 28.0), 2)
    lines.extend([
        "",
        f"{'=' * 20} {passed} passed in {duration}s {'=' * 20}",
    ])

    return "\n".join(lines)


_GENERATORS = [_fake_htop, _fake_npm_build, _fake_pytest]


class FocusScreen(ModalScreen):
    """Full-screen focus mode overlay with terminal output."""

    DEFAULT_CSS = """
    FocusScreen {
        background: $surface;
        layout: vertical;
    }

    FocusScreen #focus-scroll {
        width: 100%;
        height: 100%;
        background: #0c0c0c;
        color: #cccccc;
        padding: 0 1;
    }

    FocusScreen #focus-output {
        width: 100%;
        color: #cccccc;
        background: #0c0c0c;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss_focus", "Close", show=False),
    ]

    def compose(self) -> ComposeResult:
        generator = random.choice(_GENERATORS)
        with VerticalScroll(id="focus-scroll"):
            yield Static(generator(), id="focus-output")

    def action_dismiss_focus(self) -> None:
        self.dismiss()

    def on_key(self) -> None:
        self.dismiss()
