# Multi-Objective AI Traffic Optimization Engine

**Project**: Maximizing Section Throughput Using AI-Powered Precise Train Traffic Control  
**Module**: `optimization/`  

---

## 1. Problem Statement & Mathematical Formulation

Railway traffic control is a complex combinatorial scheduling problem with continuous kinematic parameters. Dispatchers must decide:
1. **Precedence Sequencing**: Which train is granted priority through shared corridor sections?
2. **Track Assignment**: Which track or loop line should be allocated for cruising vs overtakes?
3. **Speed Advisories**: What speed targets should be recommended to avoid yellow/red restrictive signals?

### 1.1. Decision Variables
- $x_{i, k} \in \{0, 1\}$: Binary variable indicating whether train $i$ precedes train $j$ on section $k$.
- $t_{i, k}^{\text{arr}}, t_{i, k}^{\text{dep}}$: Continuous arrival and departure times for train $i$ at section $k$.
- $v_{i, k}$: Recommended speed advisory for train $i$ on section $k$.
- $trk_{i, k} \in \{1, \dots, T_k\}$: Assigned track index within multi-track corridor section $k$.

### 1.2. Objective Function
$$\max \quad Z = w_1 \cdot S_{\text{throughput}} - w_2 \cdot S_{\text{delay}} - w_3 \cdot S_{\text{wait}} - w_4 \cdot S_{\text{congestion}} + w_5 \cdot S_{\text{priority}}$$

Where:
- $S_{\text{throughput}} = \frac{N_{\text{completed}}}{\text{Evaluation Window}}$ (Trains Per Hour)
- $S_{\text{delay}} = \sum_{i=1}^N \max(0, t_{i, \text{dest}}^{\text{arr}} - t_{i, \text{dest}}^{\text{sched}})$ (Total Delay in Minutes)
- $S_{\text{wait}} = \sum_{i=1}^N \text{TimeSpentInHalt}(i)$ (Signal Queueing Time)
- $S_{\text{congestion}} = \sum_{k=1}^K \text{UtilizationRatio}(k)^2$ (Penalizes bottleneck saturation)
- $S_{\text{priority}} = \sum_{i=1}^N \text{PriorityWeight}(i) \cdot \text{OnTimeStatus}(i)$

Standard configured weights:
$$w_1 = 0.35, \quad w_2 = 0.25, \quad w_3 = 0.15, \quad w_4 = 0.15, \quad w_5 = 0.10$$

---

## 2. Hard Constraints

Any candidate dispatch sequence must satisfy the following physical constraints:

1. **Minimum Headway Constraint**:
   $$t_{j, k}^{\text{arr}} - t_{i, k}^{\text{dep}} \ge \Delta t_{\text{headway}} \quad \forall (i, j) \text{ on same track}$$
2. **Speed Restriction Constraint**:
   $$0 \le v_{i, k} \le \min\left(v_{\max, i}, v_{\text{limit}, k}\right)$$
3. **Single-Track / Opposing Movement Interlock**:
   $$x_{i, k} + x_{j, k} = 1 \implies \text{No simultaneous opposing movements on single track}$$
4. **Platform Capacity**:
   $$\sum_{i \in \text{Station } S} \mathbb{I}(train_i \text{ at platform}) \le \text{Platforms}_S$$

---

## 3. Candidate Generation Algorithm

The optimizer computes and evaluates 4 distinct candidate dispatch strategies:

```text
Incoming Corridor Traffic Telemetry
               ↓
    Generate 4 Candidates
               ↓
┌──────────────────────────────────────────────┐
│ Candidate 1: AI Multi-Objective Optimal      │
│ Candidate 2: Strict Priority Sequence        │
│ Candidate 3: First-Come-First-Served (FCFS)  │
│ Candidate 4: Conservative Holding Dispatch   │
└──────────────────────────────────────────────┘
               ↓
    Score Each Strategy via Z
               ↓
    Phase 8 Safety Validation
               ↓
    Top Approved Plan to Controller
```

- **Candidate 1 (AI Multi-Objective)**: Dynamically adjusts speeds and re-orders trains using predicted delays to maximize section throughput.
- **Candidate 2 (Strict Priority)**: High priority Express trains always clear first; lower-priority trains wait on loop lines.
- **Candidate 3 (FCFS Heuristic)**: Traditional FIFO queueing based on arrival order at section boundary.
- **Candidate 4 (Conservative Holding)**: Holds trailing trains at previous stations to maximize safety separation buffers.

---

## 4. Safety Fail-Safe Integration

Before an optimization plan is output to the user or submitted to the simulation engine:
1. The prospective schedule is passed to `SafetyValidator.validate()`.
2. If any of the 9 formal safety rules is violated, the candidate is **disqualified**.
3. If all candidates fail safety checks, the system enters **Fail-Safe Mode**: trains maintain current block speeds or execute service braking to stop at the next signal.

