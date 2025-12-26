import matplotlib.pyplot as plt
import random

# ================= GLOBAL VERBOSE FLAG =================
VERBOSE = True  # Auto-disabled during Monte Carlo


# ================= COMPONENT =================
class Component:
    def __init__(self, name, max_load, cost_per_step, recovery_time=2):
        self.name = name
        self.max_load = max_load
        self.cost_per_step = cost_per_step

        self.load = 0
        self.status = "UP"
        self.dependencies = []

        # Recovery
        self.down_since = None
        self.recovery_time = recovery_time
        self.recovery_history = []

        # Load balancer state
        self.degraded = False


# ================= SYSTEM SETUP =================
network = Component("Network", 80, 5000, recovery_time=3)

databases = [
    Component("Database-1", 100, 20000, recovery_time=2),
    Component("Database-2", 100, 20000, recovery_time=2),
]

servers = [
    Component("WebServer-1", 120, 15000, recovery_time=1),
    Component("WebServer-2", 120, 15000, recovery_time=1),
]

for db in databases:
    db.dependencies.append(network)

for srv in servers:
    srv.dependencies.extend(databases)


# ================= GLOBAL TRACKING =================
failure_timeline = []
current_time = 0
system_down_time = None
total_failure_cost = 0


# ================= CORE LOGIC =================
def inject_failure(component):
    global current_time
    component.status = "DOWN"
    component.down_since = current_time
    failure_timeline.append((current_time, component.name, "Injected failure"))

    if VERBOSE:
        print(f"{component.name} has FAILED")


def update_component(component):
    if component.status == "DOWN":
        return

    for dep in component.dependencies:
        if dep.status == "DOWN":
            component.load += 50
            if VERBOSE:
                print(f"{component.name} affected because {dep.name} is DOWN")

    if component.load > component.max_load:
        component.status = "DOWN"
        component.down_since = current_time
        failure_timeline.append(
            (current_time, component.name, "Overload due to dependency failure")
        )
        if VERBOSE:
            print(f"{component.name} FAILED due to overload")


# ================= LOAD BALANCER =================
def distribute_traffic(total_traffic=120):
    active_servers = [s for s in servers if s.status == "UP"]

    if not active_servers:
        if VERBOSE:
            print("🚨 Load Balancer: NO ACTIVE SERVERS")
        return

    traffic_per_server = total_traffic // len(active_servers)

    for srv in active_servers:
        srv.load += traffic_per_server

        if VERBOSE:
            print(f"⚖️ Load Balancer → {srv.name} gets {traffic_per_server} load")

        if 0.8 * srv.max_load < srv.load <= srv.max_load:
            srv.degraded = True
            if VERBOSE:
                print(f"⚠️ {srv.name} is DEGRADED")

        if srv.load > srv.max_load:
            srv.status = "DOWN"
            srv.down_since = current_time
            failure_timeline.append(
                (current_time, srv.name, "Traffic overload")
            )
            if VERBOSE:
                print(f"💥 {srv.name} FAILED due to traffic overload")


# ================= RECOVERY =================
def recover_components():
    for comp in [network] + databases + servers:
        if comp.status == "DOWN" and comp.down_since is not None:
            if current_time - comp.down_since >= comp.recovery_time:
                duration = current_time - comp.down_since
                comp.status = "UP"
                comp.load = 0
                comp.degraded = False
                comp.down_since = None
                comp.recovery_history.append(duration)

                if VERBOSE:
                    print(f"🔁 {comp.name} RECOVERED after {duration} steps")


# ================= SYSTEM CHECKS =================
def system_down():
    return (
        all(db.status == "DOWN" for db in databases)
        or all(srv.status == "DOWN" for srv in servers)
    )


# ================= DISPLAY =================
def print_status():
    if not VERBOSE:
        return

    print("\n--- SYSTEM STATUS ---")
    print(f"Network: {network.status}")

    for db in databases:
        print(f"{db.name}: {db.status}")

    for srv in servers:
        state = "DEGRADED" if srv.degraded else srv.status
        print(f"{srv.name}: {state}")


def print_architecture():
    if not VERBOSE:
        return

    print("\n🧩 SYSTEM ARCHITECTURE")
    print(f"[ Network {'❌' if network.status=='DOWN' else '✅'} ]")
    print("        ↓")

    for db in databases:
        print(f"[ {db.name} {'❌' if db.status=='DOWN' else '✅'} ]")

    print("        ↓")

    for srv in servers:
        icon = "❌" if srv.status == "DOWN" else "⚠️" if srv.degraded else "✅"
        print(f"[ {srv.name} {icon} ]")


# ================= SIMULATION =================
def simulate(time_steps):
    global current_time, system_down_time, total_failure_cost

    for t in range(1, time_steps + 1):
        current_time = t
        if VERBOSE:
            print(f"\n⏱ TIME STEP {t}")

        for db in databases:
            update_component(db)

        for srv in servers:
            update_component(srv)

        distribute_traffic()

        print_status()
        print_architecture()

        for comp in [network] + databases + servers:
            if comp.status == "DOWN":
                total_failure_cost += comp.cost_per_step

        if system_down() and system_down_time is None:
            system_down_time = current_time

        recover_components()


# ================= METRICS =================
def calculate_resilience_score(total_time):
    score = 100

    if system_down_time is not None:
        score -= (total_time - system_down_time) * 10

    failed_components = set(c for _, c, _ in failure_timeline)
    score -= len(failed_components) * 10
    score -= len(failure_timeline) * 5

    return max(score, 0)


def calculate_mttr():
    times = []
    for comp in [network] + databases + servers:
        times.extend(comp.recovery_history)
    return sum(times) / len(times) if times else 0


def reset_system():
    global failure_timeline, current_time, system_down_time, total_failure_cost

    failure_timeline.clear()
    current_time = 0
    system_down_time = None
    total_failure_cost = 0

    for comp in [network] + databases + servers:
        comp.status = "UP"
        comp.load = 0
        comp.down_since = None
        comp.degraded = False


# ================= GRAPH =================
def draw_graph():
    plt.figure(figsize=(9, 2))

    components = [network] + databases + servers
    x = [0, 2, 4, 6, 8]
    y = [0] * 5

    colors = [
        "red" if c.status == "DOWN"
        else "orange" if c.degraded
        else "green"
        for c in components
    ]

    plt.scatter(x, y, s=2000, c=colors)

    for i, c in enumerate(components):
        plt.text(x[i], y[i] + 0.1, c.name, ha="center")

    plt.title("System Dependency Graph")
    plt.axis("off")
    plt.show()


# ================= MENU =================
def scenario_menu():
    while True:
        print("\n🧪 SELECT FAILURE SCENARIO")
        print("1. Fail Network")
        print("2. Fail Database-1")
        print("3. Fail Database-2")
        print("4. Fail WebServer-1")
        print("5. Fail WebServer-2")

        choice = input("Enter choice (1–5): ").strip()
        mapping = {
            "1": network,
            "2": databases[0],
            "3": databases[1],
            "4": servers[0],
            "5": servers[1],
        }

        if choice in mapping:
            return mapping[choice]

        print("❌ Invalid input.")


# ================= MONTE CARLO =================
def random_failure():
    return random.choice([network] + databases + servers)


def monte_carlo_simulation(runs=50, time_steps=3):
    global VERBOSE
    VERBOSE = False

    results = []

    for _ in range(runs):
        reset_system()
        failed = random_failure()
        inject_failure(failed)
        simulate(time_steps)

        results.append({
            "cost": total_failure_cost,
            "score": calculate_resilience_score(time_steps),
            "failed": failed.name,
            "outage": system_down()
        })

    VERBOSE = True
    return results


def analyze_monte_carlo(results):
    total_runs = len(results)
    avg_cost = sum(r["cost"] for r in results) / total_runs
    worst_cost = max(r["cost"] for r in results)
    avg_score = sum(r["score"] for r in results) / total_runs
    outage_prob = sum(1 for r in results if r["outage"]) / total_runs * 100

    frequency = {}
    for r in results:
        frequency[r["failed"]] = frequency.get(r["failed"], 0) + 1

    print("\n📊 MONTE CARLO ANALYSIS SUMMARY")
    print(f"Total runs               : {total_runs}")
    print(f"Average failure cost     : ₹{int(avg_cost)}")
    print(f"Worst-case cost          : ₹{worst_cost}")
    print(f"Average resilience score : {int(avg_score)}")
    print(f"Outage probability       : {outage_prob:.2f}%")

    print("\n🔥 COMPONENT RISK RANKING")
    for comp, count in sorted(frequency.items(), key=lambda x: x[1], reverse=True):
        print(f"{comp}: {count} runs")


# ================= RUN =================
reset_system()

target = scenario_menu()
inject_failure(target)

simulate(3)

score = calculate_resilience_score(3)
mttr = calculate_mttr()

print(f"\n📊 RESILIENCE SCORE: {score} / 100")
print(f"💰 TOTAL FAILURE COST: ₹{total_failure_cost}")
print(f"⏱️ MEAN TIME TO RECOVERY (MTTR): {mttr:.2f} time steps")

draw_graph()

mc_results = monte_carlo_simulation(runs=50)
analyze_monte_carlo(mc_results)
