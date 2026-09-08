"""
Standard Railway Safety Rule Definitions.

Provides rule keys, human-readable titles, severities, and descriptions.
"""
from typing import Dict, Any


RULE_EMERGENCY_STATE = "EMERGENCY_STATE"
RULE_SPEED_LIMIT = "SPEED_LIMIT"
RULE_MINIMUM_HEADWAY = "MINIMUM_HEADWAY"
RULE_TRACK_OCCUPANCY = "TRACK_OCCUPANCY"
RULE_SECTION_OCCUPANCY = "SECTION_OCCUPANCY"
RULE_OPPOSITE_DIRECTION = "OPPOSITE_DIRECTION"
RULE_ROUTE_CONNECTIVITY = "ROUTE_CONNECTIVITY"
RULE_JUNCTION_CLEARANCE = "JUNCTION_CLEARANCE"
RULE_STOPPING_DISTANCE = "STOPPING_DISTANCE"


ALL_SAFETY_RULES: Dict[str, Dict[str, Any]] = {
    RULE_EMERGENCY_STATE: {
        "title": "Emergency State Interlock",
        "severity": "CRITICAL",
        "description": "Prohibits dispatching when active track blocks, unexpected train halts, or emergency flags exist.",
    },
    RULE_SPEED_LIMIT: {
        "title": "Speed Limit Compliance",
        "severity": "CRITICAL",
        "description": "Verifies that recommended speeds never exceed train capability, section limits, or track geometry restrictions.",
    },
    RULE_MINIMUM_HEADWAY: {
        "title": "Minimum Headway Separation",
        "severity": "CRITICAL",
        "description": "Ensures consecutive trains maintain at least the minimum safe headway time and stopping distance buffer.",
    },
    RULE_TRACK_OCCUPANCY: {
        "title": "Track Occupancy Exclusivity",
        "severity": "CRITICAL",
        "description": "Prohibits assigning a train to an already occupied, blocked, or maintenance-flagged track.",
    },
    RULE_SECTION_OCCUPANCY: {
        "title": "Section Capacity & Permitted Occupancy",
        "severity": "HIGH",
        "description": "Ensures section concurrent train counts do not exceed physical track capacity.",
    },
    RULE_OPPOSITE_DIRECTION: {
        "title": "Opposite-Direction Single-Track Mutex",
        "severity": "CRITICAL",
        "description": "Strictly forbids simultaneous opposing train movements on bidirectional or single-track sections.",
    },
    RULE_ROUTE_CONNECTIVITY: {
        "title": "Route Connectivity & Line Compatibility",
        "severity": "HIGH",
        "description": "Verifies that the recommended path forms a valid, contiguous graph traversal from origin to destination.",
    },
    RULE_JUNCTION_CLEARANCE: {
        "title": "Junction & Interlocking Clearance",
        "severity": "HIGH",
        "description": "Enforces required time windows between conflicting converging or crossing routes at switch points.",
    },
    RULE_STOPPING_DISTANCE: {
        "title": "Safe Braking Distance Margin",
        "severity": "CRITICAL",
        "description": "Calculates kinematic stopping distance and verifies that trains can safely halt before restricted zones.",
    },
}

RULE_DESCRIPTIONS = ALL_SAFETY_RULES

