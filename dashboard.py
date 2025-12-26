# dashboard.py
import streamlit as st
import random
import matplotlib.pyplot as plt

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Distributed Failure Simulator",
    layout="wide"
)

# ================= COMPONENT =================
class Component:
    def __init__(self, name, max_load, cost, recovery_time):
        self.name = name
        self.max_load = max_load
        self.cost = cost
        self.recovery_time = recovery_time
        self.status = "UP"
        self.load = 0
        self.dependencies = []
        self.down_since = None
        self.recovery_history = []

# ================= INIT SYSTEM =================
def init_system():
    network = Component("Network", 80, 5000, 3)

    databases = [
        Component("Database-1", 100, 20000, 2),
        Component("Database-2", 100, 20000, 2),
    ]

    servers = [
        Component("WebServer-1", 120, 15000, 1),
        Component("WebServer-2", 120, 15000, 1),
    ]

    for db in databases:
        db.dependencies.append(network)

    for srv in servers:
        srv.dependencies.extend(databases)

    return network, databases, servers

# ================= SESSION STATE =================
if "initialized" not in st.session_state:
    net, dbs, srvs = init_system()
    st.session_state.network = net
    st.session_state.databases = dbs
    st.session_state.servers = srvs
    st.session_state.components = [net] + dbs + srvs
    st.session_state.time = 0
    st.session_state.cost = 0
    st.session_state.initialized = True

# ================= LOGIC =================
def inject_failure(comp):
    if comp.status == "UP":
        comp.status = "DOWN"
        comp.down_since = st.session_state.time

def update_component(comp):
    if comp.status != "UP":
        return
    for dep in comp.dependencies:
        if dep.status == "DOWN":
            comp.load += 50
    if comp.load > comp.max_load:
        comp.status = "DOWN"
        comp.down_since = st.session_state.time

def recover_components():
    for comp in st.session_state.components:
        if comp.status == "DOWN" and comp.down_since is not None:
            if st.session_state.time - comp.down_since >= comp.recovery_time:
                comp.status = "UP"
                comp.load = 0
                comp.recovery_history.append(
                    st.session_state.time - comp.down_since
                )
                comp.down_since = None

def simulate_step():
    st.session_state.time += 1

    for db in st.session_state.databases:
        update_component(db)

    for srv in st.session_state.servers:
        update_component(srv)

    recover_components()

    for comp in st.session_state.components:
        if comp.status == "DOWN":
            st.session_state.cost += comp.cost

def system_down():
    return (
        all(db.status == "DOWN" for db in st.session_state.databases) or
        all(s.status == "DOWN" for s in st.session_state.servers)
    )

def mttr():
    times = []
    for c in st.session_state.components:
        times.extend(c.recovery_history)
    return round(sum(times) / len(times), 2) if times else 0.0

def reset_system():
    net, dbs, srvs = init_system()
    st.session_state.network = net
    st.session_state.databases = dbs
    st.session_state.servers = srvs
    st.session_state.components = [net] + dbs + srvs
    st.session_state.time = 0
    st.session_state.cost = 0

# ================= UI =================
st.title("💥 Distributed System Failure Simulator")

# ---------- Controls ----------
c1, c2, c3 = st.columns(3)

with c1:
    target_name = st.selectbox(
        "Inject Failure",
        [c.name for c in st.session_state.components]
    )

with c2:
    if st.button("🚨 Inject Failure"):
        target = next(
            c for c in st.session_state.components if c.name == target_name
        )
        inject_failure(target)

with c3:
    if st.button("⏱ Next Time Step"):
        simulate_step()

# ---------- Metrics ----------
st.divider()
m1, m2, m3, m4 = st.columns(4)

m1.metric("Time Step", st.session_state.time)
m2.metric("Total Cost (₹)", st.session_state.cost)
m3.metric("System Status", "DOWN" if system_down() else "UP")
m4.metric("MTTR", mttr())

# ---------- Table ----------
st.subheader("📋 Component Status")

table = []
for c in st.session_state.components:
    table.append({
        "Component": c.name,
        "Status": c.status,
        "Load": c.load,
        "Recovery Time": c.recovery_time
    })

st.dataframe(table, use_container_width=True)

# ---------- Architecture ----------
st.subheader("🧩 Architecture View")

components = st.session_state.components

fig, ax = plt.subplots(figsize=(10, 2))

x = [0, 2, 4, 6, 8]
y_nodes = [0] * len(components)
y_arrows = 0.35  # arrows slightly above nodes

# Colors
colors = []
for c in components:
    if c.status == "DOWN":
        colors.append("red")
    else:
        colors.append("green")

# Draw arrows FIRST (behind nodes)
arrow = dict(arrowstyle="->", lw=2, color="white")

# Network → Databases
ax.annotate("", xy=(1.6, y_arrows), xytext=(0.4, y_arrows), arrowprops=arrow)
ax.annotate("", xy=(3.6, y_arrows), xytext=(0.4, y_arrows), arrowprops=arrow)

# Databases → WebServers
ax.annotate("", xy=(5.6, y_arrows), xytext=(2.4, y_arrows), arrowprops=arrow)
ax.annotate("", xy=(5.6, y_arrows), xytext=(4.4, y_arrows), arrowprops=arrow)
ax.annotate("", xy=(7.6, y_arrows), xytext=(2.4, y_arrows), arrowprops=arrow)
ax.annotate("", xy=(7.6, y_arrows), xytext=(4.4, y_arrows), arrowprops=arrow)

# Draw nodes ON TOP
ax.scatter(x, y_nodes, s=2600, c=colors, zorder=3)

# Labels
for i, c in enumerate(components):
    ax.text(
        x[i],
        y_nodes[i] + 0.12,
        c.name,
        ha="center",
        fontsize=11,
        fontweight="bold",
        zorder=4
    )

ax.axis("off")
st.pyplot(fig)

# ---------- Monte Carlo ----------
st.subheader("🎲 Monte Carlo Simulation")

if st.button("Run Monte Carlo (50 runs)"):
    costs = []
    outages = 0

    for _ in range(50):
        reset_system()
        inject_failure(random.choice(st.session_state.components))
        for _ in range(3):
            simulate_step()
        costs.append(st.session_state.cost)
        if system_down():
            outages += 1

    st.success("Monte Carlo Completed")
    st.write(f"Average Cost: ₹{sum(costs)//len(costs)}")
    st.write(f"Worst Cost: ₹{max(costs)}")
    st.write(f"Outage Probability: {(outages/50)*100:.2f}%")

# ---------- Reset ----------
st.divider()
if st.button("🔄 Reset Simulation"):
    reset_system()
    st.experimental_rerun()
