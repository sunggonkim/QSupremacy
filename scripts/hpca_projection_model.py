#!/usr/bin/env python3
"""HPCA-oriented projection utilities for QArchGauge artifacts.

The functions in this file are intentionally lightweight. They are not a
cycle-accurate simulator, but they keep the architectural terms explicit:
roofline-native lower bounds, payload-dependent host movement, queue-tail
latency, decoder bandwidth, controller-memory/NoC pressure, noise-feedback
diagnostics, and energy-to-solution hooks.
"""

import math


DEFAULT_PROJECTION_CONFIG = {
    "distance": 25.0,
    "cycle_sec": 1.0e-6,
    "oneq_cycles_per_distance": 1.0,
    "twoq_cycles_per_distance": 4.0,
    "measurement_cycles_per_distance": 1.0,
    "shots_per_group": 1.0e4,
    "shot_lanes": 1.0e4,
    "critical_path_serialization_fraction": 0.0,
    "twoq_routing_multiplier": 1.0,
    "magic_states_per_oneq_proxy": 0.0,
    "magic_states_per_twoq_proxy": 0.0,
    "magic_state_factory_rate_per_sec": 1.0e30,
    "decoder_sec_per_eval": 5.0e-6,
    "decoder_bandwidth_bits_per_sec": 4.0e12,
    "host_io_floor_sec_per_eval": 20.0e-6,
    "host_link_bandwidth_bytes_per_sec": 64.0e9,
    "host_link_buffer_bytes": 16.0e6,
    "host_payload_base_bytes": 256.0,
    "host_payload_bytes_per_measurement": 8.0,
    "host_payload_bytes_per_gate": 0.125,
    "queue_service_sec_per_eval": 30.0e-6,
    "queue_utilization": 0.35,
    "queue_arrival_rate_per_sec": 0.0,
    "queue_servers": 1.0,
    "queue_buffer_entries": 4096.0,
    "queue_head_of_line_factor": 1.0,
    "queue_burst_factor": 1.0,
    "queue_tail_percentile": 0.99,
    "enable_queue_model": True,
    "control_memory_bandwidth_bytes_per_sec": 128.0e9,
    "controller_state_bytes_per_physical_qubit": 0.25,
    "logical_to_physical_factor": 2.0,
    "controller_llc_bytes": 64.0e6,
    "controller_dram_bytes": 256.0e9,
    "controller_cxl_bandwidth_bytes_per_sec": 64.0e9,
    "controller_cache_miss_sec": 80.0e-9,
    "controller_cxl_access_sec": 350.0e-9,
    "controller_noc_bisection_bytes_per_sec": 2.0e12,
    "controller_noc_hop_sec": 2.0e-9,
    "controller_noc_mesh_dim": 32.0,
    "enable_controller_scaling": True,
    "coherence_bytes_per_touched_line": 64.0,
    "coherence_directory_fanout": 1.5,
    "cache_line_bytes": 64.0,
    "physical_error_rate": 0.0,
    "target_logical_error_rate": 1.0e-12,
    "zne_scale_factors": 1.0,
    "pec_gamma": 1.0,
    "mitigation_context_switch_multiplier": 1.0,
    "barren_plateau_slope": 0.0,
    "host_context_switch_sec": 1.0e-6,
    "enable_host_context": True,
    "host_l1_l2_refill_bytes": 256.0e3,
    "host_instruction_refill_bytes": 64.0e3,
    "host_cache_invalidation_bytes_per_eval": 0.0,
    "data_movement_energy_pj_per_byte": 25.0,
    "reference_accelerator_power_w": 400.0,
    "native_tensor_core_peak_flops": 312.0e12,
    "native_hbm_bandwidth_bytes_per_sec": 1.55e12,
    "native_peak_flops": 312.0e12,
    "native_peak_bytes_per_sec": 1.55e12,
    "native_launch_floor_sec": 0.0,
    "qpu_fridge_power_w": 25000.0,
    "decoder_power_w": 1500.0,
    "decoder_area_um2_per_syndrome_bit": 0.08,
    "decoder_area_limit_mm2": 850.0,
    "decoder_power_density_w_per_mm2": 0.45,
    "control_power_w": 2500.0,
    "host_power_w": 500.0,
}


def merge_config(overrides=None):
    config = dict(DEFAULT_PROJECTION_CONFIG)
    if overrides:
        config.update(overrides)
    return config


def as_float(row, key, default=0.0):
    value = row.get(key, default)
    if value in ("", None):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def estimate_logical_qubits(row):
    """Infer a conservative logical-qubit count from available record fields."""
    candidates = [
        as_float(row, "sim_qubits"),
        as_float(row, "opt_nodes"),
        as_float(row, "ml_features"),
        as_float(row, "ml_classes"),
    ]
    explicit = max(candidates)
    if explicit > 0.0:
        return max(1.0, explicit)
    twoq = max(1.0, as_float(row, "two_qubit_gates"))
    oneq = max(1.0, as_float(row, "one_qubit_gates"))
    return max(2.0, math.log2(oneq + twoq))


def estimate_physical_qubits(row, config):
    logical = estimate_logical_qubits(row)
    distance = max(1.0, config["distance"])
    return logical * config["logical_to_physical_factor"] * distance * distance


def roofline_time_sec(flops, bytes_moved, peak_flops, peak_bytes_per_sec, launch_floor_sec=0.0):
    """Return a strict roofline lower-bound time for a native accelerator kernel.

    For A100-style stress gates, `peak_flops` is the Tensor Core peak and
    `peak_bytes_per_sec` is the HBM bandwidth limit. The result is a lower
    bound; it does not model occupancy, divergence, or kernel launch overhead
    beyond the explicit launch floor.
    """
    compute = flops / max(peak_flops, 1.0)
    memory = bytes_moved / max(peak_bytes_per_sec, 1.0)
    return launch_floor_sec + max(compute, memory)


def native_deadline_sec(row, config):
    """Return the native deadline used by projection and energy accounting.

    Measured records use the observed native runtime. Deployment-scale proxy
    records can add `native_roofline_flops` and `native_roofline_bytes` to price
    an idealized accelerator baseline at the configured compute/HBM limits. The
    smaller of measured and roofline time is used so a stronger native proxy
    never makes the quantum target easier.
    """
    measured = max(1.0e-12, as_float(row, "native_runtime_sec", 0.0))
    flops = as_float(row, "native_roofline_flops", 0.0)
    bytes_moved = as_float(row, "native_roofline_bytes", 0.0)
    if flops <= 0.0 and bytes_moved <= 0.0:
        return measured
    roof = roofline_time_sec(
        flops,
        bytes_moved,
        config.get("native_tensor_core_peak_flops", config["native_peak_flops"]),
        config.get("native_hbm_bandwidth_bytes_per_sec", config["native_peak_bytes_per_sec"]),
        config["native_launch_floor_sec"],
    )
    return min(measured, max(1.0e-12, roof))


def host_payload_bytes_per_eval(row, config):
    evals = max(1.0, as_float(row, "circuit_evaluations", 1.0))
    gates = as_float(row, "one_qubit_gates") + as_float(row, "two_qubit_gates")
    meas = as_float(row, "measurement_ops")
    physical = estimate_physical_qubits(row, config)
    controller_bytes = (
        physical * config["controller_state_bytes_per_physical_qubit"]
    )
    return (
        config["host_payload_base_bytes"]
        + config["host_payload_bytes_per_measurement"] * meas / evals
        + config["host_payload_bytes_per_gate"] * gates / evals
        + controller_bytes
    )


def controller_working_set_bytes(row, config):
    physical = estimate_physical_qubits(row, config)
    return physical * config["controller_state_bytes_per_physical_qubit"]


def controller_memory_sec_per_eval(row, config):
    working_set = controller_working_set_bytes(row, config)
    cache_lines = working_set / max(config["cache_line_bytes"], 1.0)
    cache_excess = max(0.0, working_set - config["controller_llc_bytes"])
    dram_excess = max(0.0, working_set - config["controller_dram_bytes"])
    miss_time = (
        cache_excess
        / max(config["cache_line_bytes"], 1.0)
        * config["controller_cache_miss_sec"]
    )
    cxl_time = (
        dram_excess / max(config["controller_cxl_bandwidth_bytes_per_sec"], 1.0)
        + (dram_excess / max(config["cache_line_bytes"], 1.0))
        * config["controller_cxl_access_sec"]
    )
    coherence_bytes = (
        cache_lines
        * config["coherence_bytes_per_touched_line"]
        * config["coherence_directory_fanout"]
    )
    coherence_time = coherence_bytes / max(config["control_memory_bandwidth_bytes_per_sec"], 1.0)
    return miss_time + cxl_time + coherence_time


def controller_noc_sec_per_eval(row, config):
    physical = estimate_physical_qubits(row, config)
    mesh_dim = max(1.0, config["controller_noc_mesh_dim"])
    active_tiles = max(1.0, math.sqrt(max(1.0, physical)) / mesh_dim)
    hop_count = max(1.0, 0.5 * math.sqrt(active_tiles) * mesh_dim)
    payload = host_payload_bytes_per_eval(row, config)
    bisection_load = payload * max(1.0, active_tiles) / max(
        config["controller_noc_bisection_bytes_per_sec"], 1.0
    )
    return hop_count * config["controller_noc_hop_sec"] + bisection_load


def controller_scaling_sec_per_eval(row, config):
    if not config.get("enable_controller_scaling", True):
        return 0.0
    return controller_memory_sec_per_eval(row, config) + controller_noc_sec_per_eval(row, config)


def host_io_sec_per_eval(row, config):
    payload = host_payload_bytes_per_eval(row, config)
    burst_bytes = max(0.0, payload - config["host_link_buffer_bytes"])
    overflow_sec = burst_bytes / max(config["host_link_bandwidth_bytes_per_sec"], 1.0)
    return (
        config["host_io_floor_sec_per_eval"]
        + payload / max(config["host_link_bandwidth_bytes_per_sec"], 1.0)
        + payload / max(config["control_memory_bandwidth_bytes_per_sec"], 1.0)
        + overflow_sec
    )


def effective_shot_lanes(row, config):
    """Cap hardware lanes by circuit repetitions ready in the same wave."""
    ready, _ = ready_shot_demand(row, config)
    return min(max(1.0, config.get("shot_lanes", 1.0)), ready)


def ready_shot_demand(row, config):
    """Return dependency-ready repetitions and the evidence used for the cap.

    A compiled dependency trace may attach ``ready_shot_executions`` directly.
    ``independent_circuit_lanes`` is a weaker record-level bound.  Legacy
    aggregate records expose neither, so they use all repetitions as ready and
    are explicitly tagged as optimistic throughput lower bounds.
    """
    evals = max(1.0, as_float(row, "circuit_evaluations", 1.0))
    groups = max(1.0, as_float(row, "measurement_groups_per_eval", 1.0))
    shots = max(1.0, config.get("shots_per_group", 1.0))
    shot_executions = as_float(row, "shot_executions_per_eval", 0.0)
    if shot_executions <= 0.0:
        shot_executions = shots * groups
    explicit_ready = as_float(row, "ready_shot_executions", 0.0)
    if explicit_ready > 0.0:
        return max(1.0, explicit_ready), "compiled_dependency_wave"
    independent_circuits = as_float(row, "independent_circuit_lanes", 0.0)
    if independent_circuits > 0.0:
        ready = min(evals, independent_circuits) * shot_executions
        return max(1.0, ready), "recorded_independent_circuit_bound"
    return max(1.0, shot_executions * evals), "aggregate_total_demand_lower_bound"


def overlap_bracket(component_terms, serialization_fraction):
    """Bracket unavailable resource contention between overlap and serialization."""
    terms = {name: max(0.0, float(value)) for name, value in component_terms.items()}
    rho = min(1.0, max(0.0, float(serialization_fraction)))
    dominant = max(terms, key=terms.get)
    lower = terms[dominant]
    upper = sum(terms.values())
    contributions = {
        name: value if name == dominant else rho * value
        for name, value in terms.items()
    }
    return {
        "serialization_fraction": rho,
        "dominant": dominant,
        "lower_bound_sec": lower,
        "upper_bound_sec": upper,
        "overlap_penalty_sec": rho * (upper - lower),
        "total_sec": lower + rho * (upper - lower),
        "contributions": contributions,
    }


def dynamic_queue_utilization(row, config):
    """Estimate offered queue utilization from Little's-Law inputs."""
    service = max(1.0e-12, config["queue_service_sec_per_eval"])
    servers = max(1.0, config.get("queue_servers", 1.0))
    arrival = config.get("queue_arrival_rate_per_sec", 0.0)
    if arrival <= 0.0:
        evals = max(1.0, as_float(row, "circuit_evaluations", 1.0))
        lanes = effective_shot_lanes(row, config)
        arrival = (
            config.get("queue_burst_factor", 1.0)
            * evals
            / max(service * lanes, service)
        )
    rho_from_arrival = arrival * service / servers
    return min(0.985, max(config.get("queue_utilization", 0.0), rho_from_arrival))


def queue_tail_sec_per_eval(row, config):
    """Analytical queue-tail stress with HoL and finite-buffer hooks."""
    if not config.get("enable_queue_model", True):
        return 0.0
    service = max(1.0e-12, config["queue_service_sec_per_eval"])
    rho = dynamic_queue_utilization(row, config)
    pct = min(0.9999, max(0.50, config.get("queue_tail_percentile", 0.50)))
    wait_tail = service * (-math.log(1.0 - pct)) * rho / max(1.0e-9, 1.0 - rho)
    hol = (
        config.get("queue_head_of_line_factor", 1.0)
        * service
        * rho
        / max(1.0e-9, 1.0 - rho)
    )
    evals = max(1.0, as_float(row, "circuit_evaluations", 1.0))
    excess_entries = max(0.0, evals - config.get("queue_buffer_entries", 4096.0))
    queue_overflow = excess_entries * service / max(1.0, config.get("queue_servers", 1.0))
    payload = host_payload_bytes_per_eval(row, config)
    payload_burst = max(0.0, evals * payload - config["host_link_buffer_bytes"])
    payload_overflow = payload_burst / max(config["host_link_bandwidth_bytes_per_sec"], 1.0)
    return service + wait_tail + hol + queue_overflow + payload_overflow / evals


def decoder_area_mm2(row, config):
    physical = estimate_physical_qubits(row, config)
    syndrome_bits = physical * config["distance"]
    return syndrome_bits * config["decoder_area_um2_per_syndrome_bit"] * 1.0e-6


def decoder_sec_per_eval(row, config):
    physical = estimate_physical_qubits(row, config)
    syndrome_bits = physical * config["distance"]
    bandwidth_time = syndrome_bits / max(config["decoder_bandwidth_bits_per_sec"], 1.0)
    area = decoder_area_mm2(row, config)
    area_stretch = max(1.0, area / max(config["decoder_area_limit_mm2"], 1.0e-9))
    thermal_power = area * config["decoder_power_density_w_per_mm2"]
    thermal_stretch = max(1.0, thermal_power / max(config["decoder_power_w"], 1.0e-9))
    return max(config["decoder_sec_per_eval"], bandwidth_time) * max(
        area_stretch, thermal_stretch
    )


def noise_feedback_multiplier(row, config):
    """Return an analytic stress factor; it is not applied to the main path."""
    physical_error = max(0.0, config.get("physical_error_rate", 0.0))
    target = max(1.0e-18, config.get("target_logical_error_rate", 1.0e-12))
    zne = max(1.0, config.get("zne_scale_factors", 1.0))
    pec_gamma = max(1.0, config.get("pec_gamma", 1.0))
    context_mult = max(1.0, config.get("mitigation_context_switch_multiplier", 1.0))
    logical_qubits = estimate_logical_qubits(row)
    evals = max(1.0, as_float(row, "circuit_evaluations", 1.0))
    # The log-ratio term avoids claiming a specific noise channel while making
    # clear that lower logical-error targets and larger systems inflate work.
    error_pressure = math.log10(max(physical_error / target, 1.0)) if physical_error > 0.0 else 0.0
    plateau = math.exp(config.get("barren_plateau_slope", 0.0) * logical_qubits)
    return zne * pec_gamma * context_mult * plateau * (
        1.0 + error_pressure / max(1.0, math.log10(evals + 10.0))
    )


def host_context_sec_per_eval(row, config):
    if not config.get("enable_host_context", True):
        return 0.0
    payload = host_payload_bytes_per_eval(row, config)
    refill = (
        config["host_l1_l2_refill_bytes"]
        + config["host_instruction_refill_bytes"]
        + config["host_cache_invalidation_bytes_per_eval"]
        + payload
    )
    return config["host_context_switch_sec"] + refill / max(
        config["control_memory_bandwidth_bytes_per_sec"], 1.0
    )


def data_movement_energy_j(row, config):
    evals = max(1.0, as_float(row, "circuit_evaluations", 1.0))
    bytes_moved = evals * (
        host_payload_bytes_per_eval(row, config)
        + config["host_l1_l2_refill_bytes"]
        + config["host_instruction_refill_bytes"]
        + config["host_cache_invalidation_bytes_per_eval"]
    )
    return bytes_moved * config["data_movement_energy_pj_per_byte"] * 1.0e-12


def projected_components_sec(row, overrides=None):
    config = merge_config(overrides)
    row = dict(row)
    evals = max(1.0, as_float(row, "circuit_evaluations", 1.0))
    groups = max(1.0, as_float(row, "measurement_groups_per_eval", 1.0))
    oneq = as_float(row, "one_qubit_gates")
    twoq = as_float(row, "two_qubit_gates")
    meas = as_float(row, "measurement_ops")
    distance = config["distance"]
    cycle_sec = config["cycle_sec"]
    shots = max(1.0, config.get("shots_per_group", 1.0))
    routing = max(1.0, config.get("twoq_routing_multiplier", 1.0))
    ready_shots, lane_evidence = ready_shot_demand(row, config)
    shot_lanes = min(max(1.0, config.get("shot_lanes", 1.0)), ready_shots)
    shot_executions_per_eval = as_float(row, "shot_executions_per_eval", 0.0)
    if shot_executions_per_eval <= 0.0:
        shot_executions_per_eval = groups * shots
    total_shot_executions = evals * shot_executions_per_eval
    magic_states = max(
        0.0,
        as_float(row, "magic_state_demand", 0.0)
        + oneq * max(0.0, config.get("magic_states_per_oneq_proxy", 0.0))
        + twoq * max(0.0, config.get("magic_states_per_twoq_proxy", 0.0)),
    )
    factory_sec = (
        magic_states
        * shot_executions_per_eval
        / max(1.0, config.get("magic_state_factory_rate_per_sec", 1.0e30))
    )

    base_gate_work_sec = (
        oneq * config["oneq_cycles_per_distance"] * distance * cycle_sec
        + twoq
        * routing
        * config["twoq_cycles_per_distance"]
        * distance
        * cycle_sec
        + meas
        * config["measurement_cycles_per_distance"]
        * distance
        * cycle_sec
    )
    gate_pipeline_sec = base_gate_work_sec * shot_executions_per_eval / shot_lanes
    decode_sec = total_shot_executions * decoder_sec_per_eval(row, config) / shot_lanes
    host_sec = evals * host_io_sec_per_eval(row, config)
    queue_sec = evals * queue_tail_sec_per_eval(row, config)
    controller_sec = evals * controller_scaling_sec_per_eval(row, config)
    context_sec = evals * host_context_sec_per_eval(row, config)

    core = overlap_bracket(
        {
            "logical": gate_pipeline_sec,
            "factory": factory_sec,
            "decoder": decode_sec,
        },
        config.get("critical_path_serialization_fraction", 0.0),
    )
    critical_logical_sec = core["contributions"]["logical"]
    critical_factory_sec = core["contributions"]["factory"]
    critical_decode_sec = core["contributions"]["decoder"]
    critical_gate_sec = critical_logical_sec + critical_factory_sec
    gate_sec = max(gate_pipeline_sec, factory_sec)
    total_sec = (
        core["total_sec"]
        + host_sec
        + queue_sec
        + controller_sec
        + context_sec
    )
    twoq_gate_sec = (
        twoq
        * routing
        * config["twoq_cycles_per_distance"]
        * distance
        * cycle_sec
        * shot_executions_per_eval
        / shot_lanes
    )

    decoder_area = decoder_area_mm2(row, config)
    decoder_power = max(
        config["decoder_power_w"],
        decoder_area * config["decoder_power_density_w_per_mm2"],
    )
    qpu_power = (
        config["qpu_fridge_power_w"]
        + decoder_power
        + config["control_power_w"]
        + config["host_power_w"]
    )
    native_sec = native_deadline_sec(row, config)
    movement_energy = data_movement_energy_j(row, config)
    return {
        "gate_sec": gate_sec,
        "base_gate_work_sec": base_gate_work_sec,
        "gate_pipeline_sec": gate_pipeline_sec,
        "factory_sec": factory_sec,
        "magic_state_demand": magic_states,
        "twoq_routing_multiplier": routing,
        "shots_per_group": shots,
        "measurement_groups_per_eval": groups,
        "shot_executions_per_eval": shot_executions_per_eval,
        "total_shot_executions": total_shot_executions,
        "ready_shot_executions": ready_shots,
        "shot_lane_evidence": lane_evidence,
        "effective_shot_lanes": shot_lanes,
        "decode_sec": decode_sec,
        "critical_logical_sec": critical_logical_sec,
        "critical_factory_sec": critical_factory_sec,
        "critical_gate_sec": critical_gate_sec,
        "critical_decode_sec": critical_decode_sec,
        "critical_path_dominant": core["dominant"],
        "critical_path_serialization_fraction": core["serialization_fraction"],
        "core_overlap_lower_bound_sec": core["lower_bound_sec"],
        "core_serialized_upper_bound_sec": core["upper_bound_sec"],
        "core_overlap_penalty_sec": core["overlap_penalty_sec"],
        "host_io_sec": host_sec,
        "queue_sec": queue_sec,
        "controller_sec": controller_sec,
        "context_sec": context_sec,
        "total_sec": total_sec,
        "twoq_gate_sec": twoq_gate_sec,
        "host_payload_bytes_per_eval": host_payload_bytes_per_eval(row, config),
        "queue_tail_sec_per_eval": queue_tail_sec_per_eval(row, config),
        "decoder_sec_per_eval": decoder_sec_per_eval(row, config),
        "controller_sec_per_eval": controller_scaling_sec_per_eval(row, config),
        "host_context_sec_per_eval": host_context_sec_per_eval(row, config),
        "unapplied_noise_stress_multiplier": noise_feedback_multiplier(row, config),
        "physical_qubits_est": estimate_physical_qubits(row, config),
        "queue_utilization_dynamic": dynamic_queue_utilization(row, config),
        "decoder_area_mm2": decoder_area,
        "decoder_power_w": decoder_power,
        "data_movement_energy_j": movement_energy,
        "native_deadline_sec": native_sec,
        "qpu_energy_j": qpu_power * total_sec + movement_energy,
        "reference_energy_j": config["reference_accelerator_power_w"] * native_sec,
    }


def projected_time_sec(row, overrides=None):
    return projected_components_sec(row, overrides)["total_sec"]
