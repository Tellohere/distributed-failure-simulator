# distributed-failure-simulator
A distributed system failure simulator with cascading failures, recovery, cost modeling, and Monte Carlo risk analysis.

A Python-based simulator that models failures in distributed systems, including
cascading failures, recovery mechanisms, cost impact, and resilience analysis.

## Features
- Dependency-based cascading failures
- Failure injection (manual & random)
- Load-based component failure
- Automatic recovery & MTTR calculation
- Cost modeling per failure
- Monte Carlo risk simulation
- CLI-based visualization
- Streamlit dashboard (experimental)

## Architecture
Network → Databases → Web Servers

## Technologies Used
- Python
- Matplotlib
- Streamlit
- Monte Carlo Simulation

## How to Run

### CLI Simulator
```bash
python3 main.py
