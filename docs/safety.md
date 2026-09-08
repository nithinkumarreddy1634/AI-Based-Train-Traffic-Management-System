# Safety Validation Engine & Fail-Safe Invariants

**Project**: Maximizing Section Throughput Using AI-Powered Precise Train Traffic Control  
**Module**: `safety/` (Phase 8 Integration)  
**Mandatory Invariant**: **Unsafe Plans Applied = 0**  

---

## 1. Safety Architecture Overview

The system incorporates a formal, dedicated **Safety Validation Engine** positioned between the algorithmic decision components (AI Optimizer, Human Dispatcher Overrides, Emergency Mitigation) and the simulation execution environment.

```text
Decision Source (AI / Manual Controller / Emergency Plan)
                         │
                         ▼
        ┌───────────────────────────────────┐
        │   Phase 8 Safety Validation Gate  │
        │   (9 Formal Safety Rule Theorems) │
        └───────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         ▼                               ▼
    [ PASS (100%) ]                 [ FAIL (>0) ]
         │                               │
         ▼                               ▼
Apply Plan to Simulation          BLOCK EXECUTION
(Update speeds & tracks)          Log Safety Violation
                                  Return HTTP 422 Error
```

No API endpoint or internal module can modify train positions, allocate track blocks, or adjust target speeds without passing this safety gate.

---

## 2. The 9 Formal Safety Rules

Every prospective trajectory and dispatch command is audited against 9 mathematical safety rules:

### Rule 1 (`R01`): Maximum Speed Enforcement
- **Theorem**: Train speed $v_i$ must not exceed either the train's maximum mechanical speed $v_{\max, i}$ or the section civil speed limit $v_{\text{track\_limit}}$.
- **Mathematical Form**: $0 \le v_i \le \min\left(v_{\max, i}, v_{\text{track\_limit}}\right)$
- **Intervention**: Any instruction ordering $v_i > v_{\text{limit}}$ or $v_i < 0$ is rejected.

### Rule 2 (`R02`): Spatial Headway Separation
- **Theorem**: The physical distance between consecutive trains $i$ and $j$ on the same track must exceed the minimum statutory safety distance.
- **Mathematical Form**: $d_{i, j} \ge d_{\min\_headway} = 1,500\text{ meters}$

### Rule 3 (`R03`): Minimum Temporal Headway
- **Theorem**: Successive train departures from the same platform or block entry must maintain a minimum time interval.
- **Mathematical Form**: $\Delta t \ge 120\text{ seconds}$

### Rule 4 (`R04`): Safe Braking Distance Margin
- **Theorem**: Available clearance distance ahead of a train must exceed its calculated emergency stopping distance by at least $25\%$.
- **Mathematical Form**: $d_{\text{avail}} \ge 1.25 \cdot \left(\frac{v^2}{2 \cdot b} + v \cdot \tau_{\text{reaction}}\right)$

### Rule 5 (`R05`): Opposing Movement Interlock
- **Theorem**: Two trains traveling in opposite directions cannot be assigned or routed to the same single or bidirectional track block simultaneously.
- **Mathematical Form**: $\text{Direction}(i) \ne \text{Direction}(j) \implies \text{Track}(i) \ne \text{Track}(j)$

### Rule 6 (`R06`): Platform Dwell Time Safety
- **Theorem**: Passenger trains must observe minimum dwell times for safe boarding before signal clearance.
- **Mathematical Form**: $t_{\text{dwell}} \ge t_{\text{dwell, min}} = 60\text{ seconds}$

### Rule 7 (`R07`): Route Reservation Clearance
- **Theorem**: Switches and route interlockings must be verified physically unoccupied and locked before authority to proceed is issued.

### Rule 8 (`R08`): Section Capacity Limit
- **Theorem**: The total number of active trains in a corridor section cannot exceed the total number of physical tracks.
- **Mathematical Form**: $N_{\text{trains, section}} \le N_{\text{tracks, section}}$

### Rule 9 (`R09`): Emergency Braking Buffer
- **Theorem**: A static safety buffer of $500\text{ m}$ must remain clear behind any stopped or degraded train.

---

## 3. Manual Controller Override Safety Interlock

While the system supports **Human-in-the-Loop** operational control (`HOLD_TRAIN`, `RELEASE_TRAIN`, `SPEED_ADVISORY`, `FORCE_ROUTE`), controllers are **not permitted to bypass safety invariants**:

- Submitting a negative speed advisory (e.g. `-20 km/h`) returns **HTTP 422 Unprocessable Entity** with violation detail: *"Braking distance or speed advisory invalid"*.
- Submitting an overspeed advisory (e.g. `200 km/h` on a `110 km/h` track) returns **HTTP 422** with violation detail: *"Target speed exceeds maximum section speed limit"*.
- All manual override attempts (both approved and rejected) are permanently recorded in the `ControllerAction` audit table.

---

## 4. Prototype Safety Boundaries

> [!CAUTION]
> **Prototype Limitation Notice**:
> This software is an academic simulation, algorithmic modeling, and decision-support prototype.
> - It does NOT interface with real-world vital railway interlocking hardware (e.g., Solid State Interlocking, Relays, Track Circuits, Axle Counters).
> - It does NOT interface with locomotive European Train Control System (ETCS) or Automatic Train Protection (ATP) on-board computers.
> - It is NOT certified for operational railway deployment under CENELEC EN 50126, EN 50128, or EN 50129 standards.

