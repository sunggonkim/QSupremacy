// HPCA-oriented QArchGauge projection outline.
//
// This file is intentionally an implementation outline, not a compiled
// simulator. It mirrors scripts/hpca_projection_model.py in a C++/cycle-model
// style so an RTL, NoC, or PPA study can replace each hook without changing
// the same-input application record.

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <string>

struct CaseRecord {
  double native_runtime_sec;
  double one_qubit_gates;
  double two_qubit_gates;
  double measurement_ops;
  double circuit_evaluations;
  double measurement_groups_per_eval = 1.0;
  double shot_executions_per_eval = 0.0;
  double magic_state_demand = 0.0;
  double ready_shot_executions = 0.0;
  double independent_circuit_lanes = 0.0;
  double logical_qubits;
  double quality_gap;
};

struct ProjectionConfig {
  double code_distance = 25.0;
  double qec_cycle_sec = 1.0e-6;
  double shots_per_group = 1.0e4;
  double useful_shot_lanes = 1.0e4;
  double critical_path_serialization_fraction = 0.0;
  double twoq_routing_multiplier = 1.0;
  double magic_states_per_oneq_proxy = 0.0;
  double magic_states_per_twoq_proxy = 0.0;
  double magic_state_factory_rate_per_sec = 1.0e30;
  double decoder_floor_sec = 5.0e-6;
  double decoder_bandwidth_bits_per_sec = 4.0e12;
  double host_io_floor_sec = 20.0e-6;
  double host_link_bandwidth_bytes_per_sec = 64.0e9;
  double host_link_buffer_bytes = 16.0e6;
  double host_payload_base_bytes = 256.0;
  double host_payload_bytes_per_measurement = 8.0;
  double host_payload_bytes_per_gate = 0.125;
  double controller_bandwidth_bytes_per_sec = 128.0e9;
  double queue_service_sec = 30.0e-6;
  double queue_utilization = 0.35;
  double queue_arrival_rate_per_sec = 0.0;
  double queue_servers = 1.0;
  double queue_buffer_entries = 4096.0;
  double queue_head_of_line_factor = 1.0;
  double queue_burst_factor = 1.0;
  double queue_percentile = 0.99;
  double controller_llc_bytes = 64.0e6;
  double controller_dram_bytes = 256.0e9;
  double cxl_bandwidth_bytes_per_sec = 64.0e9;
  double noc_bisection_bytes_per_sec = 2.0e12;
  double noc_hop_sec = 2.0e-9;
  double cache_line_bytes = 64.0;
  double cache_miss_sec = 80.0e-9;
  double cxl_access_sec = 350.0e-9;
  double coherence_bytes_per_line = 64.0;
  double coherence_fanout = 1.5;
  double context_switch_sec = 1.0e-6;
  double host_refill_bytes = 256.0e3;
  double physical_error_rate = 0.0;
  double target_logical_error_rate = 1.0e-12;
  double zne_scale_factors = 1.0;
  double pec_gamma = 1.0;
  double mitigation_context_switch_multiplier = 1.0;
  double barren_plateau_slope = 0.0;
  double reference_accelerator_power_w = 400.0;
  double native_tensor_core_peak_flops = 312.0e12;
  double native_hbm_bandwidth_bytes_per_sec = 1.55e12;
  double native_peak_flops = 312.0e12;
  double native_peak_bytes_per_sec = 1.55e12;
  double native_launch_floor_sec = 0.0;
  double fridge_power_w = 25000.0;
  double decoder_power_w = 1500.0;
  double decoder_area_um2_per_syndrome_bit = 0.08;
  double decoder_area_limit_mm2 = 850.0;
  double decoder_power_density_w_per_mm2 = 0.45;
  double control_power_w = 2500.0;
  double host_power_w = 500.0;
  double host_instruction_refill_bytes = 64.0e3;
  double cache_invalidation_bytes_per_eval = 0.0;
  double data_movement_energy_pj_per_byte = 25.0;
};

struct ProjectionResult {
  double gate_sec;
  double base_gate_work_sec;
  double gate_pipeline_sec;
  double factory_sec;
  double shots_per_group;
  double total_shot_executions;
  double ready_shot_executions;
  double effective_shot_lanes;
  double decode_sec;
  double host_io_sec;
  double queue_p99_sec;
  double controller_sec;
  double host_context_sec;
  double core_overlap_lower_bound_sec;
  double core_serialized_upper_bound_sec;
  double core_overlap_penalty_sec;
  double total_sec;
  double queue_utilization_dynamic;
  double decoder_area_mm2;
  double decoder_power_w;
  double data_movement_energy_j;
  double qpu_energy_j;
  double reference_energy_j;
};

double RooflineNativeTime(double flops, double bytes, double peak_flops,
                          double hbm_bytes_per_sec, double launch_floor_sec) {
  // For A100 stress gates, peak_flops is the Tensor Core peak and
  // hbm_bytes_per_sec is the HBM bandwidth roof. Occupancy/divergence can
  // only make a realized native kernel slower than this lower bound.
  const double compute = flops / std::max(peak_flops, 1.0);
  const double memory = bytes / std::max(hbm_bytes_per_sec, 1.0);
  return launch_floor_sec + std::max(compute, memory);
}

double NativeDeadlineSec(const CaseRecord& rec, const ProjectionConfig& cfg,
                         double proxy_flops = 0.0, double proxy_bytes = 0.0) {
  const double measured = std::max(1.0e-12, rec.native_runtime_sec);
  if (proxy_flops <= 0.0 && proxy_bytes <= 0.0) return measured;
  const double roof = RooflineNativeTime(proxy_flops, proxy_bytes,
                                         cfg.native_tensor_core_peak_flops,
                                         cfg.native_hbm_bandwidth_bytes_per_sec,
                                         cfg.native_launch_floor_sec);
  return std::min(measured, std::max(1.0e-12, roof));
}

double PhysicalQubits(const CaseRecord& rec, const ProjectionConfig& cfg) {
  return std::max(1.0, rec.logical_qubits) * 2.0 * cfg.code_distance *
         cfg.code_distance;
}

double EffectiveShotLanes(const CaseRecord& rec, const ProjectionConfig& cfg) {
  const double shots_per_circuit = rec.shot_executions_per_eval > 0.0
      ? rec.shot_executions_per_eval
      : std::max(1.0, rec.measurement_groups_per_eval) *
            std::max(1.0, cfg.shots_per_group);
  double ready = rec.ready_shot_executions;
  if (ready <= 0.0 && rec.independent_circuit_lanes > 0.0) {
    ready = std::min(std::max(1.0, rec.circuit_evaluations),
                     rec.independent_circuit_lanes) * shots_per_circuit;
  }
  if (ready <= 0.0) {
    // Aggregate-only records use all demand as ready and remain optimistic.
    ready = std::max(1.0, rec.circuit_evaluations) * shots_per_circuit;
  }
  return std::min(std::max(1.0, cfg.useful_shot_lanes), std::max(1.0, ready));
}

double DynamicQueueUtilization(const CaseRecord& rec, const ProjectionConfig& cfg) {
  const double service = std::max(1.0e-12, cfg.queue_service_sec);
  const double servers = std::max(1.0, cfg.queue_servers);
  double arrival = cfg.queue_arrival_rate_per_sec;
  if (arrival <= 0.0) {
    arrival = cfg.queue_burst_factor * std::max(1.0, rec.circuit_evaluations) /
              std::max(service * EffectiveShotLanes(rec, cfg), service);
  }
  const double rho_from_arrival = arrival * service / servers;
  return std::clamp(std::max(cfg.queue_utilization, rho_from_arrival), 0.0, 0.985);
}

double QueueTailSec(const CaseRecord& rec, const ProjectionConfig& cfg, double payload) {
  const double service = std::max(1.0e-12, cfg.queue_service_sec);
  const double rho = DynamicQueueUtilization(rec, cfg);
  const double p = std::clamp(cfg.queue_percentile, 0.5, 0.9999);
  const double wait_tail = service * (-std::log(1.0 - p)) * rho /
                           std::max(1.0e-9, 1.0 - rho);
  const double hol = cfg.queue_head_of_line_factor * service * rho /
                     std::max(1.0e-9, 1.0 - rho);
  const double excess_entries =
      std::max(0.0, rec.circuit_evaluations - cfg.queue_buffer_entries);
  const double queue_overflow = excess_entries * service / std::max(1.0, cfg.queue_servers);
  const double burst_bytes =
      std::max(0.0, rec.circuit_evaluations * payload - cfg.host_link_buffer_bytes);
  const double payload_overflow = burst_bytes / cfg.host_link_bandwidth_bytes_per_sec;
  return service + wait_tail + hol + queue_overflow +
         payload_overflow / std::max(1.0, rec.circuit_evaluations);
}

double DecoderAreaMm2(const CaseRecord& rec, const ProjectionConfig& cfg) {
  const double physical = PhysicalQubits(rec, cfg);
  const double syndrome_bits = physical * cfg.code_distance;
  return syndrome_bits * cfg.decoder_area_um2_per_syndrome_bit * 1.0e-6;
}

double DecoderSecPerEval(const CaseRecord& rec, const ProjectionConfig& cfg) {
  const double physical = PhysicalQubits(rec, cfg);
  const double syndrome_bits = physical * cfg.code_distance;
  const double bandwidth_time =
      syndrome_bits / std::max(1.0, cfg.decoder_bandwidth_bits_per_sec);
  const double area = DecoderAreaMm2(rec, cfg);
  const double area_stretch = std::max(1.0, area / cfg.decoder_area_limit_mm2);
  const double thermal_power = area * cfg.decoder_power_density_w_per_mm2;
  const double thermal_stretch = std::max(1.0, thermal_power / cfg.decoder_power_w);
  return std::max(cfg.decoder_floor_sec, bandwidth_time) *
         std::max(area_stretch, thermal_stretch);
}

double ControllerSecPerEval(const CaseRecord& rec, const ProjectionConfig& cfg) {
  const double physical = PhysicalQubits(rec, cfg);
  const double working_set = physical * 0.25;
  const double cache_lines = working_set / cfg.cache_line_bytes;
  const double llc_excess = std::max(0.0, working_set - cfg.controller_llc_bytes);
  const double dram_excess = std::max(0.0, working_set - cfg.controller_dram_bytes);
  const double llc_miss = (llc_excess / cfg.cache_line_bytes) * cfg.cache_miss_sec;
  const double cxl = dram_excess / cfg.cxl_bandwidth_bytes_per_sec +
                     (dram_excess / cfg.cache_line_bytes) * cfg.cxl_access_sec;
  const double coherence =
      cache_lines * cfg.coherence_bytes_per_line * cfg.coherence_fanout /
      cfg.controller_bandwidth_bytes_per_sec;
  const double active_tiles = std::max(1.0, std::sqrt(physical) / 32.0);
  const double noc = std::sqrt(active_tiles) * 32.0 * cfg.noc_hop_sec +
                     working_set * active_tiles / cfg.noc_bisection_bytes_per_sec;
  return llc_miss + cxl + coherence + noc;
}

double NoiseFeedbackMultiplier(const CaseRecord& rec, const ProjectionConfig& cfg) {
  const double pressure =
      cfg.physical_error_rate > 0.0
          ? std::log10(
                std::max(cfg.physical_error_rate / cfg.target_logical_error_rate, 1.0))
          : 0.0;
  const double plateau = std::exp(cfg.barren_plateau_slope * rec.logical_qubits);
  const double eval_scale = std::max(1.0, std::log10(rec.circuit_evaluations + 10.0));
  return cfg.zne_scale_factors * cfg.pec_gamma *
         cfg.mitigation_context_switch_multiplier * plateau *
         (1.0 + pressure / eval_scale);
}

double DataMovementEnergyJ(double bytes_moved, const ProjectionConfig& cfg) {
  return bytes_moved * cfg.data_movement_energy_pj_per_byte * 1.0e-12;
}

ProjectionResult ProjectCase(const CaseRecord& rec, const ProjectionConfig& cfg) {
  CaseRecord adjusted = rec;
  const double d = cfg.code_distance;
  const double qec = cfg.qec_cycle_sec;
  const double routing = std::max(1.0, cfg.twoq_routing_multiplier);
  const double gates = adjusted.one_qubit_gates * d * qec +
                       adjusted.two_qubit_gates * routing * 4.0 * d * qec +
                       adjusted.measurement_ops * d * qec;
  const double shots = std::max(1.0, cfg.shots_per_group);
  const double groups = std::max(1.0, adjusted.measurement_groups_per_eval);
  const double shot_executions = adjusted.shot_executions_per_eval > 0.0
      ? adjusted.shot_executions_per_eval
      : groups * shots;
  const double lanes = EffectiveShotLanes(adjusted, cfg);
  const double gate_pipeline_sec = gates * shot_executions / lanes;
  const double magic_states = std::max(
      0.0, adjusted.magic_state_demand +
               adjusted.one_qubit_gates * cfg.magic_states_per_oneq_proxy +
               adjusted.two_qubit_gates * cfg.magic_states_per_twoq_proxy);
  const double factory_sec = magic_states * shot_executions /
      std::max(1.0, cfg.magic_state_factory_rate_per_sec);
  const double gate_sec = std::max(gate_pipeline_sec, factory_sec);
  const double physical = PhysicalQubits(adjusted, cfg);
  const double decode_per_eval = DecoderSecPerEval(adjusted, cfg);
  const double payload = cfg.host_payload_base_bytes +
                         cfg.host_payload_bytes_per_measurement * adjusted.measurement_ops /
                             adjusted.circuit_evaluations +
                         cfg.host_payload_bytes_per_gate *
                             (adjusted.one_qubit_gates + adjusted.two_qubit_gates) /
                             adjusted.circuit_evaluations +
                         physical * 0.25;
  const double host_link_overflow =
      std::max(0.0, payload - cfg.host_link_buffer_bytes) /
      cfg.host_link_bandwidth_bytes_per_sec;
  const double host_per_eval = cfg.host_io_floor_sec +
                               payload / cfg.host_link_bandwidth_bytes_per_sec +
                               payload / cfg.controller_bandwidth_bytes_per_sec +
                               host_link_overflow;
  const double context_per_eval =
      cfg.context_switch_sec +
      (cfg.host_refill_bytes + cfg.host_instruction_refill_bytes +
       cfg.cache_invalidation_bytes_per_eval + payload) /
          cfg.controller_bandwidth_bytes_per_sec;

  ProjectionResult out{};
  out.gate_sec = gate_sec;
  out.base_gate_work_sec = gates;
  out.gate_pipeline_sec = gate_pipeline_sec;
  out.factory_sec = factory_sec;
  out.shots_per_group = shots;
  out.total_shot_executions = adjusted.circuit_evaluations * shot_executions;
  out.ready_shot_executions =
      adjusted.ready_shot_executions > 0.0
          ? adjusted.ready_shot_executions
          : (adjusted.independent_circuit_lanes > 0.0
                 ? std::min(adjusted.circuit_evaluations,
                            adjusted.independent_circuit_lanes) * shot_executions
                 : out.total_shot_executions);
  out.effective_shot_lanes = lanes;
  out.decode_sec = out.total_shot_executions * decode_per_eval / lanes;
  out.host_io_sec = adjusted.circuit_evaluations * host_per_eval;
  out.queue_p99_sec = adjusted.circuit_evaluations * QueueTailSec(adjusted, cfg, payload);
  out.controller_sec = adjusted.circuit_evaluations * ControllerSecPerEval(adjusted, cfg);
  out.host_context_sec = adjusted.circuit_evaluations * context_per_eval;
  out.core_overlap_lower_bound_sec =
      std::max({out.gate_pipeline_sec, out.factory_sec, out.decode_sec});
  out.core_serialized_upper_bound_sec =
      out.gate_pipeline_sec + out.factory_sec + out.decode_sec;
  const double rho =
      std::clamp(cfg.critical_path_serialization_fraction, 0.0, 1.0);
  out.core_overlap_penalty_sec =
      rho * (out.core_serialized_upper_bound_sec -
             out.core_overlap_lower_bound_sec);
  out.total_sec = out.core_overlap_lower_bound_sec +
                  out.core_overlap_penalty_sec + out.host_io_sec +
                  out.queue_p99_sec + out.controller_sec + out.host_context_sec;
  out.queue_utilization_dynamic = DynamicQueueUtilization(adjusted, cfg);
  out.decoder_area_mm2 = DecoderAreaMm2(adjusted, cfg);
  out.decoder_power_w =
      std::max(cfg.decoder_power_w, out.decoder_area_mm2 * cfg.decoder_power_density_w_per_mm2);
  const double qpu_power =
      cfg.fridge_power_w + out.decoder_power_w + cfg.control_power_w + cfg.host_power_w;
  const double moved_bytes = adjusted.circuit_evaluations *
                             (payload + cfg.host_refill_bytes +
                              cfg.host_instruction_refill_bytes +
                              cfg.cache_invalidation_bytes_per_eval);
  out.data_movement_energy_j = DataMovementEnergyJ(moved_bytes, cfg);
  out.qpu_energy_j = qpu_power * out.total_sec + out.data_movement_energy_j;
  out.reference_energy_j =
      cfg.reference_accelerator_power_w * NativeDeadlineSec(rec, cfg);
  return out;
}
