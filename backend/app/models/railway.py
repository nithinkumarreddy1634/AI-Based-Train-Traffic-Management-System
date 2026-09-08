from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    DateTime,
    Enum as SQLEnum,
    CheckConstraint,
    Text,
    Boolean,
)
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin
import enum


class StationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    CLOSED = "CLOSED"


class SectionStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    BLOCKED = "BLOCKED"
    MAINTENANCE = "MAINTENANCE"


class TrackDirection(str, enum.Enum):
    UP = "UP"
    DOWN = "DOWN"
    BOTH = "BOTH"


class TrackStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    BLOCKED = "BLOCKED"
    MAINTENANCE = "MAINTENANCE"


class TrainType(str, enum.Enum):
    EXPRESS = "EXPRESS"
    PASSENGER = "PASSENGER"
    LOCAL = "LOCAL"
    FREIGHT = "FREIGHT"


class TrainPriority(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TrainStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    WAITING = "WAITING"
    RUNNING = "RUNNING"
    ARRIVED = "ARRIVED"
    DELAYED = "DELAYED"
    STOPPED = "STOPPED"


class Station(Base, TimestampMixin):
    """Represents a physical railway passenger or junction station."""

    __tablename__ = "stations"

    station_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    station_code = Column(String(10), unique=True, nullable=False, index=True)
    station_name = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False, default=0.0)
    longitude = Column(Float, nullable=False, default=0.0)
    number_of_platforms = Column(Integer, nullable=False, default=2)
    status = Column(String(20), nullable=False, default=StationStatus.ACTIVE.value)

    # Relationships
    sections_started = relationship(
        "RailwaySection",
        foreign_keys="RailwaySection.start_station_id",
        back_populates="start_station",
        cascade="all, delete-orphan",
    )
    sections_ended = relationship(
        "RailwaySection",
        foreign_keys="RailwaySection.end_station_id",
        back_populates="end_station",
        cascade="all, delete-orphan",
    )
    trains_originating = relationship(
        "Train",
        foreign_keys="Train.source_station_id",
        back_populates="source_station",
    )
    trains_terminating = relationship(
        "Train",
        foreign_keys="Train.destination_station_id",
        back_populates="destination_station",
    )
    schedules = relationship("TrainSchedule", back_populates="station")


class RailwaySection(Base, TimestampMixin):
    """Represents a railway section connecting two stations with one or more tracks."""

    __tablename__ = "railway_sections"

    section_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    section_name = Column(String(120), nullable=False)
    start_station_id = Column(Integer, ForeignKey("stations.station_id", ondelete="CASCADE"), nullable=False)
    end_station_id = Column(Integer, ForeignKey("stations.station_id", ondelete="CASCADE"), nullable=False)
    length_km = Column(Float, nullable=False)
    maximum_speed_kmph = Column(Float, nullable=False, default=110.0)
    number_of_tracks = Column(Integer, nullable=False, default=2)
    status = Column(String(20), nullable=False, default=SectionStatus.AVAILABLE.value)

    __table_args__ = (
        CheckConstraint("start_station_id != end_station_id", name="check_different_stations"),
        CheckConstraint("length_km > 0", name="check_positive_length"),
        CheckConstraint("maximum_speed_kmph > 0", name="check_positive_speed"),
    )

    # Relationships
    start_station = relationship("Station", foreign_keys=[start_station_id], back_populates="sections_started")
    end_station = relationship("Station", foreign_keys=[end_station_id], back_populates="sections_ended")
    tracks = relationship("Track", back_populates="section", cascade="all, delete-orphan")
    trains = relationship("Train", back_populates="current_section")


class Track(Base, TimestampMixin):
    """Represents a discrete track within a railway section."""

    __tablename__ = "tracks"

    track_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    section_id = Column(Integer, ForeignKey("railway_sections.section_id", ondelete="CASCADE"), nullable=False)
    track_number = Column(Integer, nullable=False, default=1)
    direction = Column(String(10), nullable=False, default=TrackDirection.BOTH.value)
    maximum_speed = Column(Float, nullable=False, default=100.0)
    status = Column(String(20), nullable=False, default=TrackStatus.AVAILABLE.value)
    occupied_by_train = Column(Integer, ForeignKey("trains.train_id", ondelete="SET NULL"), nullable=True)

    __table_args__ = (
        CheckConstraint("maximum_speed > 0", name="check_track_positive_speed"),
    )

    # Relationships
    section = relationship("RailwaySection", back_populates="tracks")
    train = relationship("Train", foreign_keys=[occupied_by_train], back_populates="occupied_tracks")


class Train(Base, TimestampMixin):
    """Represents a train operating on the railway corridor."""

    __tablename__ = "trains"

    train_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    train_number = Column(String(20), unique=True, nullable=False, index=True)
    train_name = Column(String(100), nullable=False)
    train_type = Column(String(20), nullable=False, default=TrainType.EXPRESS.value)
    priority = Column(String(10), nullable=False, default=TrainPriority.MEDIUM.value)

    source_station_id = Column(Integer, ForeignKey("stations.station_id"), nullable=False)
    destination_station_id = Column(Integer, ForeignKey("stations.station_id"), nullable=False)
    current_station_id = Column(Integer, ForeignKey("stations.station_id"), nullable=True)
    current_section_id = Column(Integer, ForeignKey("railway_sections.section_id"), nullable=True)

    current_position_km = Column(Float, nullable=False, default=0.0)
    speed_kmph = Column(Float, nullable=False, default=0.0)
    direction = Column(String(10), nullable=False, default="UP")
    status = Column(String(20), nullable=False, default=TrainStatus.SCHEDULED.value)

    scheduled_departure = Column(String(30), nullable=False)
    scheduled_arrival = Column(String(30), nullable=False)
    actual_departure = Column(String(30), nullable=True)
    actual_arrival = Column(String(30), nullable=True)
    current_delay_minutes = Column(Float, nullable=False, default=0.0)

    __table_args__ = (
        CheckConstraint("source_station_id != destination_station_id", name="check_train_stations"),
        CheckConstraint("speed_kmph >= 0", name="check_train_positive_speed"),
        CheckConstraint("current_delay_minutes >= 0", name="check_positive_delay"),
    )

    # Relationships
    source_station = relationship("Station", foreign_keys=[source_station_id], back_populates="trains_originating")
    destination_station = relationship("Station", foreign_keys=[destination_station_id], back_populates="trains_terminating")
    current_station = relationship("Station", foreign_keys=[current_station_id])
    current_section = relationship("RailwaySection", foreign_keys=[current_section_id], back_populates="trains")
    occupied_tracks = relationship("Track", foreign_keys="Track.occupied_by_train", back_populates="train")
    schedules = relationship("TrainSchedule", back_populates="train", cascade="all, delete-orphan")
    delay_predictions = relationship("DelayPrediction", back_populates="train", cascade="all, delete-orphan")


class TrainSchedule(Base, TimestampMixin):
    """Represents timetable stops along a train route."""

    __tablename__ = "train_schedules"

    schedule_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    train_id = Column(Integer, ForeignKey("trains.train_id", ondelete="CASCADE"), nullable=False)
    station_id = Column(Integer, ForeignKey("stations.station_id", ondelete="CASCADE"), nullable=False)
    stop_sequence = Column(Integer, nullable=False, default=1)
    scheduled_arrival = Column(String(30), nullable=True)
    scheduled_departure = Column(String(30), nullable=True)
    platform_number = Column(Integer, nullable=False, default=1)

    # Relationships
    train = relationship("Train", back_populates="schedules")
    station = relationship("Station", back_populates="schedules")


class DelayPrediction(Base, TimestampMixin):
    """Stores ML-generated arrival delay predictions for trains."""

    __tablename__ = "delay_predictions"

    prediction_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    train_id = Column(Integer, ForeignKey("trains.train_id", ondelete="CASCADE"), nullable=False)
    predicted_delay_minutes = Column(Float, nullable=False, default=0.0)
    expected_additional_delay = Column(Float, nullable=False, default=0.0)
    current_delay_minutes = Column(Float, nullable=False, default=0.0)
    prediction_timestamp = Column(String(40), nullable=False)
    model_version = Column(String(50), nullable=False, default="1.0.0")
    features_snapshot = Column(Text, nullable=True)

    # Relationships
    train = relationship("Train", back_populates="delay_predictions")


class OptimizationRun(Base, TimestampMixin):
    """Stores AI traffic optimization runs, recommended sequences, and metrics."""

    __tablename__ = "optimization_runs"

    optimization_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(String(40), nullable=False)
    target_section_id = Column(Integer, nullable=True)
    target_section_name = Column(String(100), nullable=False, default="Monitored Section")
    status = Column(String(50), nullable=False, default="OPTIMIZED")
    train_count = Column(Integer, nullable=False, default=0)
    expected_throughput = Column(Float, nullable=False, default=0.0)
    expected_total_delay = Column(Float, nullable=False, default=0.0)
    expected_waiting_time = Column(Float, nullable=False, default=0.0)
    optimization_score = Column(Float, nullable=False, default=0.0)
    recommended_sequence_json = Column(Text, nullable=False, default="[]")
    train_recommendations_json = Column(Text, nullable=False, default="[]")
    before_metrics_json = Column(Text, nullable=True)
    after_metrics_json = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    applied = Column(Boolean, nullable=False, default=False)


class SafetyAuditLog(Base, TimestampMixin):
    """Stores formal safety validation audit records for all AI recommendations."""

    __tablename__ = "safety_audit_logs"

    audit_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(String(40), nullable=False)
    recommendation_id = Column(Integer, nullable=True)
    status = Column(String(50), nullable=False, default="APPROVED")  # 'APPROVED', 'REJECTED'
    safety_score_status = Column(String(50), nullable=False, default="SAFE")  # 'SAFE', 'WARNING', 'UNSAFE'
    rules_checked_json = Column(Text, nullable=False, default="[]")
    violations_json = Column(Text, nullable=False, default="[]")
    warnings_json = Column(Text, nullable=False, default="[]")
    violations_count = Column(Integer, nullable=False, default=0)
    warnings_count = Column(Integer, nullable=False, default=0)
    candidate_summary_json = Column(Text, nullable=True)
    final_decision = Column(Text, nullable=True)
    applied_to_simulation = Column(Boolean, nullable=False, default=False)
    summary_notes = Column(Text, nullable=True)


class Experiment(Base, TimestampMixin):
    """Stores benchmark experiment definitions and scenario configurations."""

    __tablename__ = "experiments"

    experiment_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    scenario_name = Column(String(100), nullable=False)
    traffic_density = Column(String(50), nullable=False, default="medium")
    num_trains = Column(Integer, nullable=False, default=10)
    delay_profile = Column(String(100), nullable=False, default="moderate")
    simulation_duration = Column(Float, nullable=False, default=3600.0)
    runs_count = Column(Integer, nullable=False, default=1)
    status = Column(String(50), nullable=False, default="COMPLETED")  # 'PENDING', 'RUNNING', 'COMPLETED', 'FAILED'
    timestamp = Column(String(40), nullable=False)

    results = relationship("ExperimentResult", back_populates="experiment", cascade="all, delete-orphan")
    comparisons = relationship("ComparisonResult", back_populates="experiment", cascade="all, delete-orphan")


class ExperimentResult(Base, TimestampMixin):
    """Stores simulation execution results for each scheduler (Traditional vs AI) per run."""

    __tablename__ = "experiment_results"

    result_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    experiment_id = Column(Integer, ForeignKey("experiments.experiment_id", ondelete="CASCADE"), nullable=False)
    scheduler_type = Column(String(50), nullable=False)  # 'TRADITIONAL' or 'AI'
    run_number = Column(Integer, nullable=False, default=1)
    throughput_tph = Column(Float, nullable=False, default=0.0)
    completed_trains = Column(Integer, nullable=False, default=0)
    avg_delay_minutes = Column(Float, nullable=False, default=0.0)
    max_delay_minutes = Column(Float, nullable=False, default=0.0)
    min_delay_minutes = Column(Float, nullable=False, default=0.0)
    total_delay_minutes = Column(Float, nullable=False, default=0.0)
    median_delay_minutes = Column(Float, nullable=False, default=0.0)
    total_waiting_time = Column(Float, nullable=False, default=0.0)
    avg_waiting_time = Column(Float, nullable=False, default=0.0)
    max_waiting_time = Column(Float, nullable=False, default=0.0)
    section_utilization_pct = Column(Float, nullable=False, default=0.0)
    peak_traffic_density = Column(Float, nullable=False, default=0.0)
    bottleneck_duration_sec = Column(Float, nullable=False, default=0.0)
    total_conflicts = Column(Integer, nullable=False, default=0)
    critical_conflicts = Column(Integer, nullable=False, default=0)
    resolved_conflicts = Column(Integer, nullable=False, default=0)
    safety_violations = Column(Integer, nullable=False, default=0)
    unsafe_plans_applied = Column(Integer, nullable=False, default=0)
    avg_journey_time_min = Column(Float, nullable=False, default=0.0)
    detailed_metrics_json = Column(Text, nullable=True)

    experiment = relationship("Experiment", back_populates="results")


class ComparisonResult(Base, TimestampMixin):
    """Stores head-to-head comparison metrics and differential performance scores."""

    __tablename__ = "comparison_results"

    comparison_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    experiment_id = Column(Integer, ForeignKey("experiments.experiment_id", ondelete="CASCADE"), nullable=False)
    throughput_gain_pct = Column(Float, nullable=False, default=0.0)
    delay_reduction_pct = Column(Float, nullable=False, default=0.0)
    waiting_time_reduction_pct = Column(Float, nullable=False, default=0.0)
    conflict_reduction_pct = Column(Float, nullable=False, default=0.0)
    overall_performance_score = Column(Float, nullable=False, default=0.0)
    safety_compliant = Column(Boolean, nullable=False, default=True)
    summary_text = Column(Text, nullable=True)
    statistical_summary_json = Column(Text, nullable=True)

    experiment = relationship("Experiment", back_populates="comparisons")


class DecisionExplanation(Base, TimestampMixin):
    """Stores full explainability audit logs, feature breakdowns, and controller decisions."""

    __tablename__ = "decision_explanations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    recommendation_id = Column(Integer, nullable=False, index=True)
    simulation_time = Column(String(50), nullable=False, default="00:00:00")
    train_id = Column(Integer, nullable=False, index=True)
    train_number = Column(String(50), nullable=False, default="")
    section_id = Column(Integer, nullable=True, index=True)
    section_name = Column(String(100), nullable=False, default="Monitored Section")
    action = Column(String(50), nullable=False, default="PROCEED")  # 'PRIORITIZE', 'HOLD', 'PROCEED', 'DIVERT_LOOP'
    reason = Column(Text, nullable=False)
    decision_score = Column(Float, nullable=False, default=0.0)
    confidence_level = Column(String(20), nullable=False, default="HIGH")  # 'HIGH', 'MEDIUM', 'LOW'
    confidence_score = Column(Float, nullable=False, default=85.0)
    safety_status = Column(String(50), nullable=False, default="APPROVED")  # 'APPROVED', 'REJECTED'
    expected_throughput_change = Column(Float, nullable=False, default=0.0)
    expected_delay_change = Column(Float, nullable=False, default=0.0)
    factors_json = Column(Text, nullable=False, default="[]")
    score_breakdown_json = Column(Text, nullable=False, default="{}")
    alternatives_json = Column(Text, nullable=False, default="[]")
    safety_checks_json = Column(Text, nullable=False, default="{}")
    controller_status = Column(String(50), nullable=False, default="PENDING")  # 'PENDING', 'APPROVED', 'REJECTED', 'APPLIED'
    controller_rejection_reason = Column(Text, nullable=True)


class Scenario(Base, TimestampMixin):
    """Stores metadata and configuration for predefined and custom railway simulation scenarios."""

    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    scenario_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    traffic_density = Column(String(50), nullable=False, default="medium")
    num_trains = Column(Integer, nullable=False, default=12)
    config_json = Column(Text, nullable=False, default="{}")
    is_custom = Column(Boolean, nullable=False, default=False)


class EmergencyEvent(Base, TimestampMixin):
    """Stores simulated emergency incidents, impacted corridor assets, and safe AI mitigation responses."""

    __tablename__ = "emergency_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_type = Column(String(50), nullable=False, index=True)
    affected_section_id = Column(Integer, nullable=True, index=True)
    affected_section_name = Column(String(100), nullable=True)
    affected_train_id = Column(Integer, nullable=True, index=True)
    affected_train_number = Column(String(50), nullable=True)
    severity = Column(String(20), nullable=False, default="HIGH")  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    status = Column(String(20), nullable=False, default="ACTIVE")  # 'ACTIVE', 'RESOLVED'
    impact_summary_json = Column(Text, nullable=True, default="{}")
    ai_recommendation_id = Column(Integer, nullable=True)
    safety_status = Column(String(50), nullable=False, default="PENDING")
    resolution_notes = Column(Text, nullable=True)
    timestamp = Column(String(50), nullable=False)
    resolved_at = Column(String(50), nullable=True)


class ControllerAction(Base, TimestampMixin):
    """Comprehensive audit log for all manual controller overrides and safety validation outcomes."""

    __tablename__ = "controller_actions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    action_type = Column(String(50), nullable=False, index=True)
    train_id = Column(Integer, nullable=True, index=True)
    train_number = Column(String(50), nullable=True)
    section_id = Column(Integer, nullable=True, index=True)
    section_name = Column(String(100), nullable=True)
    previous_state_json = Column(Text, nullable=True)
    requested_state_json = Column(Text, nullable=True)
    safety_status = Column(String(50), nullable=False, default="APPROVED")  # 'APPROVED', 'REJECTED'
    violations_json = Column(Text, nullable=True, default="[]")
    result = Column(String(50), nullable=False, default="APPLIED")  # 'APPLIED', 'REJECTED'
    reason = Column(Text, nullable=True)
    timestamp = Column(String(50), nullable=False)


class SystemEvent(Base, TimestampMixin):
    """Centralized real-time event log for unified event stream and live control timeline."""

    __tablename__ = "system_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_type = Column(String(50), nullable=False, index=True)
    category = Column(String(50), nullable=False, default="OPERATIONAL")  # 'SIMULATION', 'TRAFFIC', 'SAFETY', 'AI', 'EMERGENCY', 'CONTROLLER'
    severity = Column(String(20), nullable=False, default="INFO")  # 'INFO', 'WARNING', 'CRITICAL', 'SUCCESS'
    train_id = Column(Integer, nullable=True, index=True)
    section_id = Column(Integer, nullable=True, index=True)
    message = Column(Text, nullable=False)
    details_json = Column(Text, nullable=True, default="{}")
    timestamp = Column(String(50), nullable=False)


class DemoSession(Base, TimestampMixin):
    """Tracks state and step progression for automated end-to-end demonstration mode."""

    __tablename__ = "demo_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, default="End-to-End Demonstration")
    status = Column(String(50), nullable=False, default="IDLE")  # 'IDLE', 'RUNNING', 'COMPLETED', 'FAILED'
    current_step_index = Column(Integer, nullable=False, default=0)
    total_steps = Column(Integer, nullable=False, default=12)
    steps_progress_json = Column(Text, nullable=False, default="[]")
    created_at_time = Column(String(50), nullable=False)
    updated_at_time = Column(String(50), nullable=False)
