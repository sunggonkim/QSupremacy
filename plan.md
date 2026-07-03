# Quantum Supremacy Modeling and Analysis Plan

## 1. 목표

양자컴퓨터가 실제 응용에서 HPC 대비 어느 정도 빨라져야 "quantum supremacy/양자 이득"으로 볼 수 있는지 모델링하고 분석한다.

비교 대상은 다음 두 축이다. 핵심은 시뮬레이터끼리 비교하는 것이 아니라, 같은 응용 문제를 서로 다른 계산 패러다임으로 푸는 end-to-end 비교이다.

- `Quantum application path`: ML/HPC 응용을 quantum circuit 기반 알고리즘으로 변환한 뒤, 그 회로 실행을 cuQuantum 등으로 시뮬레이션하고 실제 양자 하드웨어 실행 모델로 외삽한다.
- `Native application path`: 같은 ML/HPC 문제를 양자회로로 변환하지 않고 CPU/GPU 기반 HPC에서 직접 푸는 고전 알고리즘 및 AI/HPC 애플리케이션.

따라서 `NumPy state-vector simulator vs cuQuantum state-vector simulator`는 연구 비교 대상이 아니다. 이는 cuQuantum 환경 확인용 smoke test로만 사용한다. 실제 비교는 예를 들어 `PyTorch/JAX ML 모델` vs `quantum feature map/QNN/VQC 회로를 cuQuantum으로 실행한 모델`처럼 application-level로 구성한다.

최종 산출물은 문제 크기, 회로 깊이, 큐비트 수, 게이트 fidelity, 샷 수, 통신 비용, GPU/노드 수에 따라 "양자 하드웨어가 얼마나 빨라져야 native HPC를 이기는지"를 보여주는 모델과 실험 결과이다.

## 2. 핵심 연구 질문

1. 같은 ML/HPC 문제를 `양자회로 기반 응용`과 `native ML/HPC 응용`으로 풀 때 전체 실행 시간, 에너지, 비용의 break-even point는 어디인가?
2. cuQuantum 기반 시뮬레이션 성능을 기준으로 실제 양자 하드웨어가 필요한 logical gate rate, circuit execution rate, error rate, parallel shot throughput은 어느 수준인가?
3. 양자 이득을 주장할 수 있는 구간은 알고리즘 복잡도 차이 때문인가, 하드웨어 처리율 때문인가, 또는 데이터 입출력/전처리 오버헤드가 사라지는 조건 때문인가?
4. 기존 연구인 ScaleQsim, AURORA-Q, SWIFTN의 시뮬레이션/자원 최적화 결과를 이용해 더 현실적인 양자 이득 예측 모델을 만들 수 있는가?

## 3. 기존 연구와 연결점

랩의 기존 논문을 다음 역할로 재사용한다.

- `ScaleQsim`: 대규모 양자회로 시뮬레이션의 HPC 확장성 기준선. 여러 노드/GPU에서 큐비트 수와 회로 깊이에 따른 시뮬레이션 비용 모델의 기반으로 사용.
- `SWIFTN`: 텐서 최적화를 통한 양자회로 시뮬레이션 가속. 회로 구조별 tensor contraction 비용과 최적화 효과를 quantum path의 classical simulation baseline에 반영.
- `AURORA-Q`: HPC 환경에서 양자 시뮬레이션 자원 최적화. 노드 배치, 비동기 실행, 자원 스케줄링, 큐 대기 시간까지 포함한 end-to-end 비용 모델에 반영.
- 기존 HPC I/O 및 성능 예측 논문들: native HPC 애플리케이션의 로그 기반 성능 예측, 시스템 잡음, I/O 병목, 스케줄링 효과를 모델링할 때 활용.

## 4. 비교 프레임워크

### 4.1 전체 실행 시간 정의

각 접근의 end-to-end time을 분해한다. 이때 quantum path의 cuQuantum 시간은 "양자회로로 바꾼 응용을 현재 고전 HPC에서 실행했을 때의 비용"이며, native path는 "같은 문제를 양자 변환 없이 직접 푸는 비용"이다.

```text
T_native_app =
  T_input
+ T_preprocess
+ T_native_training_or_solver
+ T_native_inference_or_evaluation
+ T_communication
+ T_io
+ T_postprocess
+ T_queue

T_quantum_app_on_cuquantum =
  T_input
+ T_encoding
+ T_quantum_model_construction
+ T_circuit_compile
+ T_cuquantum_circuit_simulation
+ T_measurement
+ T_quantum_loss_or_observable_eval
+ T_classical_postprocess
+ T_queue

T_projected_quantum_hardware =
  T_input
+ T_encoding
+ T_quantum_model_construction
+ T_circuit_compile
+ T_quantum_hardware_execute
+ T_measurement
+ T_error_mitigation_or_correction
+ T_classical_postprocess
+ T_queue
```

quantum supremacy threshold 조건은 기본적으로 다음과 같이 둔다.

```text
T_projected_quantum_hardware < T_native_app
```

확장 지표도 함께 본다.

```text
Speedup ratio = T_native_app / T_projected_quantum_hardware
Cost ratio = Cost_native_app / Cost_projected_quantum_hardware
Energy ratio = Energy_native_app / Energy_projected_quantum_hardware
```

### 4.2 양자 하드웨어 요구 성능 역산

문제별로 native ML/HPC 응용의 time-to-quality를 먼저 측정하고, 같은 문제를 quantum circuit model로 변환했을 때 필요한 gate count, depth, shot count, training/evaluation 반복 수를 산출한다.

```text
T_quantum_execute =
  N_shots * (D_1q * t_1q + D_2q * t_2q + D_meas * t_meas)
  / parallel_shot_factor
```

여기서 quantum supremacy threshold 조건을 만족하는 `t_1q`, `t_2q`, `parallel_shot_factor`, logical error rate의 범위를 역산한다.

```text
Required quantum speed =
  Current_or_assumed_quantum_time / Target_quantum_time

Target_quantum_time =
  T_native_app - non_quantum_hardware_overheads
```

## 5. 벤치마크 후보

### 5.1 Application-level ML 벤치마크

목적: 같은 ML 문제를 native ML과 quantum circuit ML로 각각 풀고, 정확도/품질을 맞춘 상태에서 time-to-solution을 비교한다.

1차 후보는 classification으로 둔다. 이유는 dataset, accuracy, train/eval split, loss curve를 명확히 정의할 수 있고 QNN/quantum kernel 양쪽으로 확장하기 쉽기 때문이다.

Native ML path:

- Logistic regression
- MLP
- SVM/RBF kernel
- 작은 CNN 또는 Transformer-lite는 2차 확장으로 둔다.

Quantum circuit ML path:

- Quantum feature map + linear classifier
- Quantum kernel method
- Variational quantum classifier 또는 QNN
- QAOA-like classifier/optimizer는 2차 후보로 둔다.

공정 비교 조건:

- 같은 dataset split 사용
- 같은 target accuracy 또는 target loss 도달 시간 비교
- preprocessing과 feature dimension reduction 비용 포함
- quantum path는 data encoding, circuit execution, measurement/shot, gradient/optimizer loop를 모두 포함
- native path는 training/inference/optimizer 시간을 모두 포함

### 5.2 양자회로 시뮬레이션 microbenchmark

목적: cuQuantum/ScaleQsim/SWIFTN이 고전 HPC에서 양자회로를 어디까지 밀어붙일 수 있는지 확인한다. 단, 이 결과는 최종 양자 이득 비교가 아니라 quantum application path의 하위 비용 모델을 보정하기 위한 microbenchmark이다.

후보 회로:

- Random quantum circuit
- QFT
- QAOA
- VQE ansatz
- Hamiltonian simulation
- Quantum kernel / quantum feature map
- Quantum neural network circuit

측정 항목:

- 큐비트 수
- 회로 depth
- 1-qubit/2-qubit gate 수
- entanglement 구조
- tensor network treewidth 또는 contraction cost
- GPU 수/노드 수에 따른 runtime, memory, communication

### 5.3 양자 AI 애플리케이션 확장

목적: 양자회로로 된 AI가 native GPU AI를 이기려면 어느 정도 하드웨어 성능이 필요한지 분석한다.

후보:

- Quantum neural network vs classical MLP/CNN/Transformer-lite
- Quantum kernel method vs classical SVM/kernel approximation
- VQE/QAOA-inspired optimizer vs classical optimizer
- Quantum generative model vs classical generative baseline

주의점:

- 데이터 encoding 비용이 큰 경우 양자 이득이 사라질 수 있으므로 `T_encoding`을 반드시 분리 측정한다.
- 정확도/품질이 다른 모델끼리는 단순 runtime 비교를 하지 않고, 같은 target accuracy 또는 같은 objective value 도달 시간으로 비교한다.

### 5.4 Native HPC 애플리케이션 확장

목적: 양자 접근과 같은 문제를 고전적으로 가장 잘 푸는 baseline을 만든다.

후보:

- Dense/sparse linear algebra
- Optimization
- Graph problem
- Molecular simulation 또는 Hamiltonian 관련 문제
- ML training/inference
- Monte Carlo / sampling

측정 항목:

- CPU/GPU runtime
- strong/weak scaling
- memory bandwidth 사용량
- communication overhead
- I/O overhead
- energy 및 node-hour cost

## 6. 실험 단계

### Phase 0. 범위 고정

- 사용할 HPC 시스템 확정: GPU 종류, 노드 수, interconnect, scheduler, storage.
- 사용할 양자 시뮬레이터 확정: cuQuantum, ScaleQsim, SWIFTN, Qiskit Aer 등.
- native HPC baseline 라이브러리 확정: CUDA/cuBLAS/cuSPARSE, PyTorch/JAX, MPI/OpenMP 등.
- 비교할 ML/HPC 응용 문제 2-3개를 먼저 선정한다.
- 첫 문제는 작은 binary/multiclass classification으로 시작한다.

### Phase 1. Microbenchmark

- quantum circuit ML에 필요한 단일 gate, fused gate, tensor contraction, state-vector update 비용 측정.
- 큐비트 수와 depth에 따른 cuQuantum runtime/memory 측정.
- GPU 수 증가에 따른 통신 비용과 scaling efficiency 측정.
- native HPC에서 matrix multiply, sparse operation, optimizer step, inference step 등 기본 kernel 비용 측정.

산출물:

- `T_gate_sim(q, g, gpu, node)` 모델
- `T_tensor(circuit_structure, gpu, node)` 모델
- native HPC kernel별 roofline-style baseline

### Phase 2. Application Benchmark

- 같은 ML/HPC 문제를 quantum circuit application path와 native application path로 각각 구현한다.
- quantum path는 `data load -> preprocessing -> feature encoding -> circuit construction -> cuQuantum simulation -> measurement/observable -> loss/gradient -> optimizer -> evaluation`을 분리 계측한다.
- native path는 `data load -> preprocessing -> native training/solver -> native inference/evaluation -> output`을 분리 계측한다.
- target accuracy/objective를 맞춘 뒤 time-to-quality로 비교한다.

산출물:

- 문제별 end-to-end runtime table
- 정확도 대비 runtime curve
- GPU/노드 수별 scaling curve
- encoding/shot/training iteration overhead breakdown

### Phase 3. Quantum Hardware Projection

- 회로별 gate count, depth, shot count, required fidelity를 산출한다.
- 실제 또는 가정한 하드웨어 파라미터를 입력한다.
  - physical/logical qubit 수
  - 1Q/2Q gate time
  - measurement time
  - coherence time
  - gate fidelity
  - logical error rate
  - parallel shot throughput
- `T_projected_quantum_hardware < T_native_app`가 되는 hardware requirement를 역산한다.

산출물:

- required gate speed curve
- required logical qubit count
- required fidelity/error correction overhead
- problem size별 break-even heatmap

### Phase 4. Sensitivity Analysis

- 데이터 encoding 비용을 0%, 10%, 50%, 100%로 변화.
- shot 수를 accuracy requirement에 따라 변화.
- error mitigation/correction overhead를 1x, 10x, 100x, 1000x로 변화.
- native HPC 성능 향상률을 보수적/중간/공격적 시나리오로 변화.
- queue time 포함/제외 두 버전 모두 분석.

산출물:

- 어떤 요인이 양자 이득을 가장 크게 제한하는지에 대한 ranking
- optimistic / realistic / pessimistic scenario

## 7. 성능 모델 구조

### 7.1 입력 파라미터

```yaml
problem:
  name:
  size:
  task_type:
  dataset:
  train_samples:
  test_samples:
  feature_dim:
  target_accuracy:
  target_loss:

native_model:
  model_type:
  parameters:
  optimizer:
  batch_size:
  epochs_or_iterations:
  training_time:
  inference_time:
  achieved_accuracy:

quantum_circuit:
  model_type:
  encoding:
  qubits:
  depth:
  one_qubit_gates:
  two_qubit_gates:
  measurements:
  shots:
  trainable_parameters:
  optimizer_iterations:
  encoding_cost:
  compile_cost:
  achieved_accuracy:

quantum_hardware:
  logical_qubits:
  one_qubit_gate_time:
  two_qubit_gate_time:
  measurement_time:
  logical_error_rate:
  parallel_shots:
  error_correction_overhead:

hpc:
  site: nersc
  system: perlmutter
  nodes:
  gpus_per_node:
  gpu_type:
  gpu_memory:
  constraint:
  qos:
  account:
  interconnect:
  memory_per_gpu:
  peak_flops:
  measured_efficiency:
  walltime:
  queue_time:
  charged_node_hours:
```

### 7.2 출력

```yaml
result:
  native_app_time:
  quantum_app_on_cuquantum_time:
  projected_quantum_time:
  required_quantum_speedup:
  required_gate_time:
  required_parallel_shots:
  required_error_rate:
  native_accuracy:
  quantum_accuracy:
  cost_ratio:
  energy_ratio:
```

## 8. Perlmutter 실행 계획

현재 작업 위치가 Perlmutter의 `$PSCRATCH` 계열이라고 가정하고, 실험은 login node가 아니라 Slurm allocation 안에서만 수행한다.

### 8.1 Perlmutter 기준선

공식 NERSC 문서 기준으로 실험 계획에 반영할 항목:

- Job scheduler는 Slurm이다.
- GPU 노드를 요청할 때는 `-C gpu` 또는 `--constraint=gpu`가 필요하다.
- GPU 노드에서 실제 GPU를 쓰려면 `--gpus`, `--gpus-per-node`, `--gpus-per-task` 중 하나를 명시해야 한다.
- 80 GB GPU memory 노드가 필요한 실험은 `-C "gpu&hbm80g"`로 분리한다.
- 1개 또는 2개 GPU만 쓰는 짧은 실험은 `shared` QOS 후보로 둔다.
- 일반 scaling 실험은 `regular` QOS를 기본으로 둔다.
- CUDA는 `cudatoolkit` module을 기준으로 사용하고, 특정 CUDA/cuQuantum 버전이 필요하면 container/Shifter 또는 conda 환경을 사용한다.
- 비용 모델은 node-hour 기반으로 계산한다. QOS, 사용 노드 수, 실제 walltime, charge factor를 기록한다.

### 8.2 Perlmutter 실험 시나리오

#### Scenario A. 단일 GPU sanity check

목적:

- cuQuantum 설치/실행 확인.
- 작은 회로에서 계측 포맷과 결과 저장 경로 확인.

설정:

- nodes: 1
- tasks: 1
- GPUs: 1
- QOS: `shared` 또는 `debug`
- workload: 20-30 qubit state-vector circuit

#### Scenario B. 단일 노드 4 GPU scaling

목적:

- Perlmutter GPU node 내부의 4 GPU scaling 측정.
- MPI rank/GPU binding 전략 확인.

설정:

- nodes: 1
- tasks per node: 4
- GPUs per node: 4
- CPU cores per task: 32
- QOS: `regular`
- workload: 28-34 qubit state-vector, QAOA, QFT, random circuit

#### Scenario C. 다중 노드 weak/strong scaling

목적:

- ScaleQsim/SWIFTN/AURORA-Q와 연결 가능한 대규모 scaling 결과 확보.
- network communication overhead를 quantum simulation cost model에 반영.

설정:

- nodes: 2, 4, 8, 16, 32
- tasks per node: 4
- GPUs per node: 4
- QOS: `regular`
- workload: GPU memory 한계에 맞춘 state-vector 및 tensor-network circuit

#### Scenario D. Native HPC baseline

목적:

- 양자회로 ML 접근과 같은 ML 문제를 native GPU/HPC 방식으로 푸는 시간 측정.

설정:

- classification 비교 시:
  - native path: logistic regression, MLP, SVM 중 하나
  - quantum path: quantum feature map + linear head, quantum kernel, QNN/VQC 중 하나
- optimizer 비교 시:
  - native path: GPU/CPU classical optimizer
  - quantum path: QAOA/VQE-style circuit simulated by cuQuantum
- 공통 조건:
  - 같은 train/test split
  - 같은 target accuracy/loss
  - preprocessing 포함
  - quantum data encoding 비용 포함
  - training iteration 수와 shots 수 기록

### 8.3 Slurm script template

#### 단일 GPU 테스트

```bash
#!/bin/bash
#SBATCH -A <account>
#SBATCH -C gpu
#SBATCH -q shared
#SBATCH -t 00:30:00
#SBATCH -n 1
#SBATCH -c 32
#SBATCH --gpus-per-task=1
#SBATCH -J qadv-1gpu

module load cudatoolkit

export SLURM_CPU_BIND="cores"
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK}

srun python benchmarks/quantum/run_cuquantum.py \
  --config configs/workloads/qaoa_small.yaml \
  --output data/raw/perlmutter/qaoa_small_1gpu.json
```

#### 1 node 4 GPU 테스트

```bash
#!/bin/bash
#SBATCH -A <account>
#SBATCH -C gpu
#SBATCH -q regular
#SBATCH -t 01:00:00
#SBATCH -N 1
#SBATCH --ntasks-per-node=4
#SBATCH -c 32
#SBATCH --gpus-per-task=1
#SBATCH -J qadv-1node

module load cudatoolkit

export SLURM_CPU_BIND="cores"
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK}

srun python benchmarks/quantum/run_cuquantum_mpi.py \
  --config configs/workloads/qaoa_medium.yaml \
  --output data/raw/perlmutter/qaoa_medium_1node4gpu.json
```

#### 다중 노드 4 GPU/node 테스트

```bash
#!/bin/bash
#SBATCH -A <account>
#SBATCH -C gpu
#SBATCH -q regular
#SBATCH -t 02:00:00
#SBATCH -N 4
#SBATCH --ntasks-per-node=4
#SBATCH -c 32
#SBATCH --gpus-per-task=1
#SBATCH -J qadv-multinode

module load cudatoolkit

export SLURM_CPU_BIND="cores"
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK}

srun python benchmarks/quantum/run_cuquantum_mpi.py \
  --config configs/workloads/qaoa_large.yaml \
  --output data/raw/perlmutter/qaoa_large_4node16gpu.json
```

### 8.4 Perlmutter 계측 항목

각 실행은 다음 metadata를 반드시 저장한다.

```yaml
nersc:
  system: perlmutter
  job_id:
  account:
  qos:
  constraint:
  nodes:
  ntasks:
  ntasks_per_node:
  cpus_per_task:
  gpus_per_task:
  gpus_per_node:
  walltime_requested:
  walltime_elapsed:
  queue_wait_time:
  submit_time:
  start_time:
  end_time:
  node_list:

software:
  cuda_version:
  cuquantum_version:
  python_version:
  mpi_version:
  git_commit:

measurement:
  total_runtime:
  setup_time:
  circuit_build_time:
  simulation_time:
  measurement_time:
  postprocess_time:
  max_gpu_memory:
  gpu_utilization:
  cpu_utilization:
```

### 8.5 Perlmutter 비용 모델

Perlmutter에서 양자 이득은 runtime만 보지 않고 allocation cost까지 함께 계산한다.

```text
NodeHour = nodes * walltime_elapsed_hours
ChargedNodeHour = NodeHour * qos_charge_factor * system_charge_factor
CostSpeedup = ChargedNodeHour_native / ChargedNodeHour_quantum
```

실험 결과에는 최소한 다음 4개 시간을 모두 분리한다.

- `T_run`: 실제 실행 시간
- `T_queue`: Slurm 대기 시간
- `T_allocation`: 요청 walltime과 실제 walltime 차이
- `T_end_to_end`: submit부터 output 생성까지의 총 시간

논문 본문에서는 `T_run` 중심으로 알고리즘/하드웨어 이득을 보이고, appendix 또는 sensitivity section에서 `T_queue`와 charged node-hour를 포함한 운영 관점의 이득을 보인다.

### 8.6 첫 Perlmutter 마일스톤

1. `module avail cudatoolkit`, `python -c "import cuquantum"`로 환경 확인.
2. 로그인 노드 smoke suite를 통과시킨다.
3. 첫 본실험 workload는 하나만 고르지 않고 아래 세 트랙을 모두 구성한다.
   - sklearn digits native ML baseline
   - quantum kernel classifier
   - QNN/VQC classifier
4. 세 트랙은 같은 train/test split, 같은 preprocessing, 같은 target accuracy/loss 기준으로 실행한다.
5. 결과 JSON을 `data/raw/perlmutter/`에 저장.
6. `sacct` 결과를 파싱해 queue time, elapsed time, node-hour를 합친다.
7. 첫 break-even plot을 만든다.

### 8.7 로그인 노드 smoke test 상태

로그인 노드에서는 성능 측정이 아니라 환경 확인과 아주 작은 correctness test만 수행한다.

현재 확인 결과:

- host: `login39`
- default `python`: Python 2.7.18
- `python3`: Python 3.6.15
- loaded CUDA module: `cudatoolkit/12.9`
- visible GPU: NVIDIA A100 80GB PCIe
- `python3` NumPy: 사용 가능
- system `python3` CuPy/cuQuantum: 현재 import 불가
- conda base Python 3.12.12: NumPy/CuPy/cuQuantum 기본 미설치
- existing cuQuantum env: `/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python`
- existing cuQuantum version: `26.01.0`
- existing CuPy version: `13.6.0`
- cuStateVec binding path: `cuquantum.bindings.custatevec`

실행한 smoke test:

```bash
python3 benchmarks/smoke/simple_quantum_smoke.py \
  --qubits 10 \
  --depth 4 \
  --output data/raw/perlmutter/login_smoke_10q_d4.json

python3 benchmarks/smoke/simple_quantum_smoke.py \
  --qubits 12 \
  --depth 4 \
  --output data/raw/perlmutter/login_smoke_12q_d4.json

module load cudatoolkit/12.9

/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python \
  benchmarks/smoke/simple_quantum_smoke.py \
  --qubits 10 \
  --depth 4 \
  --output data/raw/perlmutter/login_smoke_10q_d4_custatevec.json

/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python \
  benchmarks/smoke/simple_quantum_smoke.py \
  --qubits 12 \
  --depth 4 \
  --output data/raw/perlmutter/login_smoke_12q_d4_custatevec.json
```

결과:

- 10 qubit, depth 4 NumPy state-vector: 정상 실행, 약 0.056초
- 12 qubit, depth 4 NumPy state-vector: 정상 실행, 약 0.233초
- 기존 cuQuantum env 사용 시 10 qubit, depth 4 NumPy state-vector: 약 0.031초
- 기존 cuQuantum env 사용 시 10 qubit, depth 4 cuStateVec state-vector: 약 0.008초
- 기존 cuQuantum env 사용 시 12 qubit, depth 4 NumPy state-vector: 약 0.112초
- 기존 cuQuantum env 사용 시 12 qubit, depth 4 cuStateVec state-vector: 약 0.004초
- cuStateVec checksum/norm은 NumPy baseline과 일치
- 매우 작은 회로에서는 CUDA/cuQuantum import 및 context initialization 비용이 커서 `total_runtime_sec`와 kernel loop time을 분리해서 해석해야 한다.

다음 단계는 Slurm GPU job에서 application-level workload를 실행하는 것이다. Login node smoke test는 correctness 및 환경 확인용으로만 사용하고, 연구 비교에는 사용하지 않는다.

### 8.8 Application-level smoke test

로그인 노드에서 실제 연구 비교축에 맞춘 초소형 smoke test도 수행한다.

비교:

- `native ML path`: synthetic classification dataset -> NumPy logistic regression
- `quantum circuit ML path`: 같은 dataset -> RY angle-encoded quantum feature map -> cuStateVec simulation -> X/Z expectation quantum features -> NumPy logistic head

실행:

```bash
module load cudatoolkit/12.9

/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python \
  benchmarks/smoke/ml_vs_quantum_circuit_smoke.py \
  --samples 64 \
  --features 2 \
  --depth 1 \
  --steps 400 \
  --output data/raw/perlmutter/login_smoke_ml_vs_qc_64s_2f_d1.json

/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python \
  benchmarks/smoke/ml_vs_quantum_circuit_smoke.py \
  --samples 64 \
  --features 4 \
  --depth 1 \
  --steps 400 \
  --output data/raw/perlmutter/login_smoke_ml_vs_qc_64s_4f_d1.json
```

결과:

- 2-feature task:
  - native ML: test accuracy 0.9375, runtime 약 0.0067초
  - quantum circuit ML: test accuracy 0.9375, total runtime 약 3.01초
  - quantum feature extraction kernel-loop time: train 약 0.042초, test 약 0.0037초
- 4-feature task:
  - native ML: test accuracy 0.8750, runtime 약 0.0069초
  - quantum circuit ML: test accuracy 0.8125, total runtime 약 3.07초
  - quantum feature extraction kernel-loop time: train 약 0.062초, test 약 0.0094초

해석:

- 이 결과는 `NumPy simulator vs cuQuantum` 비교가 아니라, 같은 toy ML 문제를 native ML과 quantum circuit ML로 각각 푼 application-level smoke test이다.
- 로그인 노드 실행이라 quantum circuit ML의 `total_runtime`에는 CUDA/cuQuantum import, context initialization, Python per-sample dispatch overhead가 크게 포함된다.
- 논문용 비교에서는 Slurm GPU job 안에서 batch 처리, 더 큰 sample size, 더 큰 feature/qubit 수, shot/error model을 포함해야 한다.
- 그래도 이 smoke test는 end-to-end logging schema와 비교 프레임워크가 동작함을 확인한다.

### 8.8.1 Login smoke suite gate

GPU allocation을 쓰기 전에 반드시 로그인 노드 smoke suite를 먼저 통과시킨다.

목적:

- cuQuantum/CuPy/custatevec import 확인
- 작은 state-vector correctness 확인
- application-level `native ML vs quantum circuit ML` pipeline 확인
- JSON output schema 확인
- accuracy/runtime 필드 validation 확인

실행:

```bash
scripts/run_login_smoke.sh
```

생성 파일:

```text
data/raw/perlmutter/login_suite/statevector_10q_d4.json
data/raw/perlmutter/login_suite/statevector_12q_d4.json
data/raw/perlmutter/login_suite/ml_vs_qc_64s_2f_d1.json
data/raw/perlmutter/login_suite/ml_vs_qc_64s_4f_d1.json
```

Validation 기준:

- state-vector norm이 1.0 근처인지 확인
- cuStateVec status가 `ok`인지 확인
- native ML test accuracy가 0.8 이상인지 확인
- quantum circuit ML test accuracy가 0.75 이상인지 확인
- native/quantum runtime field가 존재하고 양수인지 확인

최근 통과 결과:

```text
PASS: login smoke outputs validated

ml_vs_qc_64s_2f_d1.json:
  native acc 0.9375, runtime 0.0077s
  quantum acc 0.9375, total 3.01s

ml_vs_qc_64s_4f_d1.json:
  native acc 0.8750, runtime 0.0057s
  quantum acc 0.8125, total 3.05s

statevector_10q_d4.json:
  numpy norm 1.0, custatevec norm 1.0

statevector_12q_d4.json:
  numpy norm 1.0, custatevec norm 1.0
```

Allocation rule:

- 이 smoke suite가 실패하면 GPU Slurm job을 제출하지 않는다.
- full GPU node job은 4 GPU 병렬 사용 코드가 준비된 뒤에만 제출한다.
- 1 GPU shared job도 최소 10분 이상 채울 sweep이 준비된 뒤에만 제출한다.

### 8.9 Perlmutter GPU job submission

로그인 노드 smoke test 다음 단계로 Perlmutter Slurm GPU job을 제출한다.

작성한 job script:

- full GPU node: `jobs/perlmutter/ml_vs_qc_1gpu_node.sbatch`
- shared 1 GPU: `jobs/perlmutter/ml_vs_qc_1gpu_shared.sbatch`

제출 상태:

- full GPU node job: `55412740`
  - account: `m1248_g`
  - QOS: `gpu_debug`
  - partition: `gpu_ss11`
  - resources: 1 node, 32 CPUs, 4 GPUs
  - final state: `COMPLETED`
  - elapsed: 00:00:46
  - node: `nid001365`
  - visible GPUs: 4 x NVIDIA A100-SXM4-40GB
- shared 1 GPU job: `55412749`
  - account: `m1248_g`
  - QOS: `gpu_shared`
  - partition: `shared_gpu_ss11`
  - resources: 1 node allocation with 1 GPU, 32 CPUs
  - final state: `COMPLETED`
  - elapsed: 00:00:29
  - node: `nid001309`
  - visible GPUs: 1 x NVIDIA A100-SXM4-40GB

확인 명령:

```bash
squeue -j 55412740,55412749 \
  -o '%.18i %.14P %.20j %.8u %.2t %.10M %.10l %.6D %R'

scontrol show job 55412740
scontrol show job 55412749
```

결과 위치:

```text
logs/qadv-ml-qc-55412740.out
logs/qadv-ml-qc-55412740.err
data/raw/perlmutter/gpu_node/

logs/qadv-ml-qc-1g-55412749.out
logs/qadv-ml-qc-1g-55412749.err
data/raw/perlmutter/gpu_shared/
```

주의:

- full GPU node job은 4 GPUs/node를 요청하지만 현재 smoke script는 GPU 0 하나만 사용한다. 이 job은 compute node execution sanity check로 해석한다.
- multi-GPU parallel quantum feature extraction은 다음 단계에서 sample batch를 GPU별로 분할하는 방식으로 확장한다.

GPU job 결과 요약:

```text
full node job 55412740:
  128 samples, 4 features:
    native acc 0.9375, native runtime 0.0048s
    quantum-circuit acc 0.9375, total 19.16s
    cuStateVec train/test loop 0.164s / 0.0048s
  256 samples, 4 features:
    native acc 0.9531, native runtime 0.0051s
    quantum-circuit acc 0.8906, total 8.33s
    cuStateVec train/test loop 0.077s / 0.0090s
  128 samples, 8 features:
    native acc 0.9375, native runtime 0.0045s
    quantum-circuit acc 0.8750, total 8.20s
    cuStateVec train/test loop 0.167s / 0.0386s

shared 1-GPU job 55412749:
  128 samples, 4 features:
    native acc 0.9375, native runtime 0.0048s
    quantum-circuit acc 0.9375, total 9.64s
    cuStateVec train/test loop 0.101s / 0.0050s
  256 samples, 4 features:
    native acc 0.9531, native runtime 0.0074s
    quantum-circuit acc 0.8906, total 6.26s
    cuStateVec train/test loop 0.065s / 0.0097s
  128 samples, 8 features:
    native acc 0.9375, native runtime 0.0044s
    quantum-circuit acc 0.8750, total 7.49s
    cuStateVec train/test loop 0.170s / 0.0637s
```

해석:

- Slurm compute node에서 native ML path와 quantum circuit ML path 모두 정상 실행됐다.
- `logs/*.err`는 0 bytes로 오류가 없다.
- 현재 quantum path의 `total_runtime`은 실제 circuit loop time보다 훨씬 크다. 원인은 각 workload마다 Python process 안에서 cuQuantum/CuPy import, CUDA context initialization, train/test feature extractor 생성, sample-by-sample dispatch overhead가 포함되기 때문이다.
- 다음 실험에서는 하나의 cuStateVec handle/context를 재사용하고, sample batch 처리 또는 GPU별 sample partitioning을 적용해야 한다.
- full node job은 4 GPUs를 할당받았지만 현재 코드는 GPU 0만 사용한다. 다음 단계에서 4 GPU 병렬 feature extraction을 구현해야 full-node 비교가 의미를 가진다.

## 9. 구현 계획

레포 구조는 다음처럼 시작한다.

```text
.
├── plan.md
├── benchmarks/
│   ├── quantum/
│   └── native/
├── configs/
│   ├── systems/
│   ├── circuits/
│   └── workloads/
├── jobs/
│   └── perlmutter/
├── paper/
│   ├── main.tex
│   ├── references.bib
│   └── README.md
├── data/
│   ├── raw/
│   └── processed/
├── models/
│   ├── runtime_model.py
│   ├── hardware_projection.py
│   └── sensitivity.py
├── scripts/
│   ├── run_quantum_bench.sh
│   ├── run_native_bench.sh
│   ├── collect_sacct.py
│   └── analyze.py
└── results/
    ├── tables/
    └── figures/
```

우선순위:

1. `configs/`에 시스템, 회로, workload 스키마 작성.
2. `jobs/perlmutter/`에 1 GPU, 1 node 4 GPU, multi-node Slurm template 작성.
3. 첫 ML dataset과 target accuracy 정의.
4. native ML baseline 1개 작성.
5. quantum circuit ML baseline 1개 작성.
6. quantum circuit 실행 backend를 cuQuantum으로 연결.
7. 계측 결과를 CSV/JSON으로 저장.
8. `sacct` 기반 queue/walltime/node-hour 수집 스크립트 작성.
9. `models/runtime_model.py`에서 break-even 계산.
10. heatmap과 curve를 자동 생성.

## 10. 논문 스토리라인 초안

제목 후보:

- Modeling Quantum Supremacy Thresholds over Native HPC
- When Does Quantum Win? A Cross-Stack Supremacy Model for Quantum Applications and Native HPC
- Quantifying Quantum Supremacy Requirements through HPC-based Quantum Simulation and Native Baselines

핵심 주장:

- 단순히 양자 알고리즘의 asymptotic speedup만으로는 quantum supremacy를 판단할 수 없다.
- 데이터 encoding, shot count, error correction, queue/resource overhead를 포함하면 break-even point가 크게 이동한다.
- 기존 HPC 기반 양자 시뮬레이션 성능을 이용하면, 미래 양자 하드웨어가 달성해야 할 구체적인 gate speed/fidelity/parallelism 요구사항을 역산할 수 있다.
- ScaleQsim/SWIFTN/AURORA-Q의 결과를 연결하면 양자 시뮬레이션 baseline과 자원 최적화 모델을 포함한 end-to-end quantum supremacy modeling framework를 만들 수 있다.

## 11. 첫 번째 마일스톤

2주 안에 다음을 완성한다.

- dataset 선정: `sklearn digits`를 1차 본실험 dataset으로 사용하고, feature dimension을 PCA로 4, 8, 12, 16개까지 조절한다.
- native path baseline: logistic regression, MLP, optional SVM/RBF training/inference runtime 측정.
- quantum kernel baseline: 같은 PCA feature를 quantum feature map으로 encoding하고, cuQuantum으로 kernel matrix를 구성한 뒤 classifier runtime/accuracy 측정.
- QNN/VQC baseline: 같은 PCA feature를 parameterized quantum circuit에 넣고, cuQuantum 기반 evaluation/training runtime과 accuracy 측정.
- 최소 성능 모델: `T_quantum_app_on_cuquantum`, `T_native_app`, `T_projected_quantum_hardware`, `required_quantum_speedup` 계산.
- 첫 그림 3개:
  - PCA feature/sample size별 native ML vs quantum kernel vs QNN/VQC runtime
  - 같은 target accuracy 도달 시간 비교
  - shot count, circuit depth, hardware gate time에 따른 break-even curve

## 12. 체크리스트

- [ ] 대상 HPC 시스템 정보 수집
- [x] Perlmutter account/QOS/constraint 확인
- [x] `jobs/perlmutter/` Slurm template 작성
- [x] cuQuantum 실행 환경 확인
- [ ] ScaleQsim/SWIFTN/AURORA-Q 코드와 재사용 가능한 계측 방식 확인
- [x] `sklearn digits` dataset loader 작성
- [x] PCA feature dimension sweep 작성
- [ ] target accuracy/loss policy 선정
- [x] native ML baseline 작성: logistic regression, MLP, optional SVM/RBF
- [x] quantum kernel classifier 작성
- [x] QNN/VQC classifier 작성
- [x] quantum feature encoding 코드 작성
- [x] quantum circuit 생성 코드 작성
- [x] cuQuantum backend 연결
- [x] runtime logging 포맷 정의
- [x] `sacct` metadata 수집
- [x] charged node-hour 계산
- [x] break-even 모델 구현
- [ ] sensitivity analysis 구현
- [ ] 결과 figure template 작성

## 13. 참고 문서

- ATC 2026 Call for Papers: https://sigops.org/s/conferences/atc/2026/cfp.html
- USENIX conference paper templates: https://www.usenix.org/conferences/author-resources/paper-templates
- NERSC Perlmutter running jobs: https://docs.nersc.gov/systems/perlmutter/running-jobs/
- NERSC jobs and Slurm basics: https://docs.nersc.gov/jobs/
- NERSC QOS and charges: https://docs.nersc.gov/jobs/policy/
- NERSC CUDA on Perlmutter: https://docs.nersc.gov/development/programming-models/cuda/
- Existing lab publications: https://hpcbigdata.seoultech.ac.kr/publications

## 14. Paper Target

`paper/` contains an ATC-style quantum supremacy modeling and analysis manuscript scaffold.

Current status:

- `paper/main.tex`: paper draft with abstract, problem definition, methodology, workload plan, projection model, evaluation placeholders, and discussion.
- `paper/references.bib`: initial references and TODO entries for ScaleQsim, SWIFTN, and AURORA-Q.
- `paper/README.md`: paper-specific status, build instructions, and submission readiness checklist.
- `paper/Makefile`: local LaTeX build target.

Important date note:

- ATC 2026 CFP lists June 10, 2026 as the submission deadline.
- Current work date is July 3, 2026, so ATC 2026 submission has already passed.
- Treat the current paper as ATC-style or next-cycle target unless the target venue changes.

Submission readiness gate:

- Do not submit until all three first workloads are implemented and evaluated:
  - `sklearn digits` native ML baselines
  - quantum kernel classifier
  - QNN/VQC classifier
- Do not submit until Perlmutter result sweeps include repeated trials, variance, warmup policy, and charged node-hour accounting.
- Replace the lightweight local LaTeX scaffold with the official target venue template before submission.

## 15. First Digits Shared-GPU Sweep

`sklearn digits` 기반 첫 shared-GPU sweep를 완료했다.

Job:

- job id: `55414571`
- partition: `shared_gpu_ss11`
- QOS: `gpu_shared`
- account: `m1248_g`
- node: `nid001324`
- resources: 1 A100 GPU, 32 CPUs
- state: `COMPLETED`
- elapsed: `00:03:41`
- queue time: 128 seconds
- GPU-hours: 0.0614
- Slurm billing core-hours: 1.9644

실험 구성:

- classes: digits `0` vs `1`
- paths: native logistic/MLP, quantum kernel, QNN/VQC
- sweep: sample count 64/96/128, PCA dimension 4/8/12, feature depth 1/2, seed 11/13
- output JSON files: `data/raw/perlmutter/digits_shared/digits_55414571_*.json`
- processed summary: `data/processed/perlmutter/digits_55414571_summary.json`
- accounting: `data/raw/perlmutter/accounting/sacct_55414571.txt`

요약 결과:

- 18/18 cases completed.
- native best accuracy: 1.0 for all cases.
- quantum kernel test accuracy: 0.875 to 1.0, median 1.0.
- QNN/VQC test accuracy: 0.5833 to 0.9583, median 0.8281.
- quantum kernel required simulation-to-native speedup median: 907.7x.
- QNN/VQC required simulation-to-native speedup median: 25.5x.

해석:

- 본실험 pipeline은 세 트랙 모두 Perlmutter shared GPU에서 동작한다.
- 현재 native baseline은 binary digits에서 너무 강하고 빠르므로, quantum path가 같은 quality를 만족하는지 먼저 걸러야 한다.
- QNN/VQC는 일부 seed/config에서 accuracy가 낮다. optimizer iteration, ansatz, target accuracy policy를 정해야 논문 결과로 쓸 수 있다.
- quantum kernel runtime에는 CUDA/cuQuantum initialization overhead가 크게 포함된다. 다음 sweep에서는 warmup과 repeated trials를 분리해야 한다.

## 16. Expanded Digits Sweep

첫 18-case sweep가 너무 작고 쉬운 `0 vs 1` 중심이었기 때문에 expanded sweep를 추가로 수행했다.

실험 의도:

- 지금 양자 이득을 보이는 것이 목적이 아니다.
- 양자 이득 주장이 얼마나 workload, quality, encoding, circuit depth, shot/iteration, native baseline에 민감한지 HPC 기반 양자 시뮬레이션으로 모델링하는 것이 목적이다.
- 따라서 easy pair와 harder pair를 같이 넣어 threshold 변화를 본다.

실행 방식:

- 전체 160 cases.
- `gpu_shared` 1-GPU chunks로 실행.
- 처음 2 chunks는 먼저 완료됐고, 남은 pending chunks는 취소 후 15분 chunk로 재제출했다.
- `gpu_debug` full-node도 test-only로 확인했지만 예상 시작 시간이 더 늦어 실제 제출하지 않았다.
- full-node를 쓸 경우 4 GPU를 모두 사용하는 fallback script를 작성했다: `jobs/perlmutter/digits_supremacy_expanded_4gpu_debug_remaining.sbatch`.

Job ids:

- completed chunks: `55421321`, `55421323`, `55422136`, `55422137`, `55422138`, `55422139`, `55422141`, `55422142`
- cancelled before allocation: `55421074`, `55421133`, `55421201`, `55421202`, `55421203`, `55421204`, `55421324`, `55421327`, `55421332`, `55421334`, `55421335`, `55421338`

Sweep:

- class pairs: `0,1`, `3,8`, `4,9`, `5,8`
- sample count: 128, 256
- PCA/qubit dimension: 4, 8, 12, 16
- feature depth: 1, 2, 3
- seeds: 11, 13
- paths: native logistic/MLP, quantum kernel, QNN/VQC

Accounting:

- completed jobs: 8
- total GPU-hours: 0.4089
- Slurm billing core-hours: 13.0844
- all stderr files: 0 bytes
- output JSON files: `data/raw/perlmutter/digits_expanded/digits_*.json`
- processed summary: `data/processed/perlmutter/digits_expanded_55421321_55422142_summary.json`
- accounting: `data/raw/perlmutter/accounting/sacct_digits_expanded_55421321_55422142.txt`

Key results:

- result count: 160/160
- quantum kernel accuracy: min 0.5312, median 0.8750, max 1.0
- QNN/VQC accuracy: min 0.4688, median 0.7500, max 0.9531
- quantum kernel required speedup: min 338.6x, median 421.9x, max 1038.7x
- QNN/VQC required speedup: min 21.1x, median 64.9x, max 171.7x

Class-pair sensitivity:

- `0 vs 1`: quantum kernel median accuracy 0.9688, QNN/VQC median accuracy 0.8750
- `3 vs 8`: quantum kernel median accuracy 0.8125, QNN/VQC median accuracy 0.7266
- `4 vs 9`: quantum kernel median accuracy 0.9375, QNN/VQC median accuracy 0.7812
- `5 vs 8`: quantum kernel median accuracy 0.8125, QNN/VQC median accuracy 0.6562

Interpretation:

- Native ML remains extremely strong on this dataset.
- Quantum kernel sometimes reaches high quality, but still needs hundreds of times faster projected execution to match native runtime.
- QNN/VQC has lower required speedup than quantum kernel in many cases, but quality is usually below native.
- This is exactly the modeling target: not "quantum wins today", but "what hardware/quality/runtime threshold would be required for quantum to win?"
