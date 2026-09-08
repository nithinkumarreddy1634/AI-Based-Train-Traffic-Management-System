"""
Constraint Programming Scheduler using Google OR-Tools CP-SAT.

Formulates and solves the exact train traffic scheduling problem:
- Non-overlapping track occupancy (Disjunctive Interval scheduling)
- Safety headway enforcement between successive block entries
- Priority-weighted delay and waiting time minimization
- Section makespan minimization (maximizing hourly throughput)
"""
from typing import List, Dict, Any, Tuple, Optional
import time
from ortools.sat.python import cp_model
from optimization.config import OptimizationConfig, DEFAULT_CONFIG


class CPSATScheduler:
    """Solves the section train dispatch scheduling problem via CP-SAT."""

    def __init__(self, config: Optional[OptimizationConfig] = None):
        self.config = config or DEFAULT_CONFIG

    def solve_schedule(
        self,
        trains: List[Dict[str, Any]],
        section_length_km: float,
        is_single_track: bool = False,
        fixed_sequence: Optional[List[int]] = None
    ) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Solve optimal entry and wait times for a group of trains.

        Args:
            trains: List of train state dictionaries.
            section_length_km: Length of the bottleneck section.
            is_single_track: Whether opposing trains must mutually exclude.
            fixed_sequence: Optional fixed order of train_ids (e.g. from candidate generator).

        Returns:
            (status, scheduled_entries, diagnostics)
        """
        if not trains:
            return ("OPTIMIZED", [], {"wall_time": 0.0, "status": "EMPTY"})

        model = cp_model.CpModel()
        horizon = self.config.planning_horizon_seconds

        # Store CP decision variables
        entry_vars: Dict[int, cp_model.IntVar] = {}
        wait_vars: Dict[int, cp_model.IntVar] = {}
        interval_vars: Dict[int, cp_model.IntervalVar] = {}
        exit_vars: Dict[int, cp_model.IntVar] = {}

        # 1. Define Decision Variables for each train
        for t in trains:
            tid = t["train_id"]
            speed_kmph = max(30.0, t.get("current_speed_kmph") or t.get("max_speed_kmph") or 60.0)
            transit_duration_sec = max(30, int((section_length_km / speed_kmph) * 3600))
            ready_time_sec = int(t.get("ready_time_sec", 0))

            # Entry time Si >= ready_time
            s_var = model.NewIntVar(ready_time_sec, horizon, f"entry_{tid}")
            # Waiting / hold duration Wi
            w_var = model.NewIntVar(0, self.config.max_hold_seconds, f"wait_{tid}")
            # Exit time Ei = Si + transit_duration
            e_var = model.NewIntVar(ready_time_sec + transit_duration_sec, horizon + transit_duration_sec, f"exit_{tid}")

            # S_i = ready_time_sec + W_i
            model.Add(s_var == ready_time_sec + w_var)
            model.Add(e_var == s_var + transit_duration_sec)

            # Interval variable representing occupancy of the section [Si, Ei]
            ival = model.NewIntervalVar(s_var, transit_duration_sec, e_var, f"interval_{tid}")

            entry_vars[tid] = s_var
            wait_vars[tid] = w_var
            exit_vars[tid] = e_var
            interval_vars[tid] = ival

            # Attach calculated transit duration
            t["transit_duration_sec"] = transit_duration_sec

        # 2. Add Non-Overlap / Disjunctive Constraints
        if is_single_track:
            # Absolute non-overlap on single-track section
            model.AddNoOverlap(list(interval_vars.values()))

        # 3. Headway Constraints between Entry Times
        min_headway = self.config.min_headway_seconds

        if fixed_sequence:
            # Enforce exact sequence ordering
            for k in range(len(fixed_sequence) - 1):
                t1_id = fixed_sequence[k]
                t2_id = fixed_sequence[k + 1]
                if t1_id in entry_vars and t2_id in entry_vars:
                    model.Add(entry_vars[t2_id] >= entry_vars[t1_id] + min_headway)
        else:
            # Free sequencing: for every pair (i, j), determine precedence
            n = len(trains)
            for i in range(n):
                for j in range(i + 1, n):
                    t1_id = trains[i]["train_id"]
                    t2_id = trains[j]["train_id"]

                    # Boolean: prec_ij = 1 if train i enters before train j
                    prec_ij = model.NewBoolVar(f"prec_{t1_id}_{t2_id}")

                    # If prec_ij == 1 => entry_j >= entry_i + headway
                    model.Add(entry_vars[t2_id] >= entry_vars[t1_id] + min_headway).OnlyEnforceIf(prec_ij)
                    # If prec_ij == 0 => entry_i >= entry_j + headway
                    model.Add(entry_vars[t1_id] >= entry_vars[t2_id] + min_headway).OnlyEnforceIf(prec_ij.Not())

        # 4. Define Objective Function
        # Minimize sum of:
        #   - Priority-weighted waiting time
        #   - Initial delay + waiting delay
        #   - Makespan (last exit time) to compact schedule and maximize throughput
        objective_terms = []

        for t in trains:
            tid = t["train_id"]
            prio = str(t.get("priority", "MEDIUM")).upper()
            prio_weight = int(self.config.priority_multipliers.get(prio, 1.5) * 30)  # scale for integer CP

            # Delay penalty term: hold seconds scaled by priority
            objective_terms.append(wait_vars[tid] * prio_weight)

        # Makespan variable: max of all exit times
        makespan = model.NewIntVar(0, horizon + 7200, "makespan")
        for e_var in exit_vars.values():
            model.Add(makespan >= e_var)

        # Makespan weight to compress total clearance time
        objective_terms.append(makespan * 2)

        model.Minimize(sum(objective_terms))

        # 5. Solve with CP-SAT Solver
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.config.solver_time_limit_seconds
        solver.parameters.num_search_workers = self.config.solver_num_workers

        start_time = time.time()
        cp_status = solver.Solve(model)
        solve_duration = round(time.time() - start_time, 3)

        status_str = "FEASIBLE"
        if cp_status == cp_model.OPTIMAL:
            status_str = "OPTIMIZED"
        elif cp_status == cp_model.FEASIBLE:
            status_str = "FEASIBLE"
        elif cp_status == cp_model.INFEASIBLE:
            return ("NO_FEASIBLE_SOLUTION", [], {
                "wall_time": solve_duration,
                "status": "INFEASIBLE",
                "error": "Operational constraints cannot be satisfied without violating headway or single-track boundaries."
            })
        else:
            status_str = "FEASIBLE"

        # 6. Extract Results
        results = []
        for t in trains:
            tid = t["train_id"]
            entry_sec = solver.Value(entry_vars[tid])
            wait_sec = solver.Value(wait_vars[tid])
            dur_sec = t["transit_duration_sec"]
            exit_sec = solver.Value(exit_vars[tid])

            curr_delay = float(t.get("current_delay_minutes", 0.0))
            pred_add = float(t.get("predicted_additional_delay", 0.0))
            total_pred = curr_delay + pred_add + (wait_sec / 60.0)

            # Determine recommendation action tag
            if wait_sec <= 10:
                action = "PROCEED"
                reason = "Track clear ahead; dispatched at earliest feasible headway slot."
            elif t.get("priority", "").upper() == "HIGH":
                action = "PRIORITIZE"
                reason = "Dispatched with minimal necessary holding buffer to maintain High priority schedule."
            elif wait_sec > 180:
                action = "DIVERT_LOOP"
                reason = f"Held at holding siding/loop for {wait_sec // 60}m to clear bottleneck for higher-throughput traffic."
            else:
                action = "HOLD"
                reason = f"Held for {wait_sec}s to guarantee minimum safe headway buffer ({min_headway}s) behind leading train."

            results.append({
                "train_id": tid,
                "train_number": t.get("train_number", f"T{tid}"),
                "train_name": t.get("train_name", ""),
                "train_type": t.get("train_type", "PASSENGER"),
                "priority": t.get("priority", "MEDIUM"),
                "direction": t.get("direction", "UP"),
                "entry_time_sec": entry_sec,
                "hold_duration_sec": wait_sec,
                "transit_duration_sec": dur_sec,
                "exit_time_sec": exit_sec,
                "action": action,
                "reason": reason,
                "current_delay_minutes": curr_delay,
                "predicted_additional_delay": pred_add,
                "expected_total_delay_minutes": round(total_pred, 1),
                "current_speed_kmph": float(t.get("current_speed_kmph") or t.get("speed_kmph") or 60.0),
                "max_speed_kmph": float(t.get("max_speed_kmph") or 100.0) if t.get("max_speed_kmph") else None,
            })

        # Sort results chronologically by scheduled entry time
        results.sort(key=lambda x: x["entry_time_sec"])

        diagnostics = {
            "wall_time": solve_duration,
            "status": status_str,
            "objective_value": solver.ObjectiveValue(),
            "branches": solver.NumBranches(),
            "conflicts": solver.NumConflicts()
        }

        return (status_str, results, diagnostics)
