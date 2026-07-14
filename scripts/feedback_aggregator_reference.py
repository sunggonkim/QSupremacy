#!/usr/bin/env python3
"""Event-driven correctness model for the epoch-tagged feedback aggregator."""

from collections import deque
import json
import os
import random


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT = os.path.join(
    ROOT, "data/processed/perlmutter/feedback_aggregator_reference_audit.json"
)


class Update:
    __slots__ = ("epoch", "group", "value", "expected", "predecessor")

    def __init__(self, epoch, group, value, expected, predecessor=None):
        self.epoch = epoch
        self.group = group
        self.value = value
        self.expected = expected
        self.predecessor = predecessor


class FeedbackAggregator:
    """One-update-per-bank model with explicit completion and acknowledgement."""

    def __init__(self, banks, entries_per_bank):
        self.bank_count = banks
        self.entries_per_bank = entries_per_bank
        self.queues = [deque() for _ in range(banks)]
        self.entries = [dict() for _ in range(banks)]
        self.acknowledged = set()
        self.emitted = []
        self.accepted = 0
        self.processed = 0
        self.cycles = 0

    def bank_for(self, epoch, group):
        # Stable integer mix; correctness does not depend on collision quality.
        return ((epoch * 0x9E3779B1) ^ group) % self.bank_count

    def submit(self, update):
        bank = self.bank_for(update.epoch, update.group)
        key = (update.epoch, update.group)
        entries = self.entries[bank]
        if key not in entries:
            if len(entries) >= self.entries_per_bank:
                return False
            entries[key] = {
                "count": 0,
                "accepted": 0,
                "sum": 0.0,
                "expected": update.expected,
                "predecessor": update.predecessor,
                "complete": False,
            }
        state = entries[key]
        if (
            state["complete"]
            or state["expected"] != update.expected
            or state["accepted"] >= state["expected"]
        ):
            return False
        self.queues[bank].append(update)
        state["accepted"] += 1
        self.accepted += 1
        return True

    def _ready(self, update):
        return update.predecessor is None or update.predecessor in self.acknowledged

    def step(self):
        self.cycles += 1
        for bank, queue in enumerate(self.queues):
            if not queue:
                continue
            selected = None
            for _ in range(len(queue)):
                candidate = queue.popleft()
                if self._ready(candidate):
                    selected = candidate
                    break
                queue.append(candidate)
            if selected is None:
                continue
            key = (selected.epoch, selected.group)
            state = self.entries[bank][key]
            assert not state["complete"]
            state["count"] += 1
            state["sum"] += selected.value
            self.processed += 1
            assert state["count"] <= state["expected"]
            if state["count"] == state["expected"]:
                state["complete"] = True
                self.emitted.append(
                    {
                        "epoch": selected.epoch,
                        "group": selected.group,
                        "count": state["count"],
                        "sum": state["sum"],
                        "cycle": self.cycles,
                    }
                )

    def acknowledge(self, epoch, group):
        key = (epoch, group)
        bank = self.bank_for(epoch, group)
        state = self.entries[bank].get(key)
        if state is None or not state["complete"]:
            return False
        self.acknowledged.add(key)
        del self.entries[bank][key]
        return True

    def pending(self):
        return sum(len(queue) for queue in self.queues)


def drain(model, limit=1000):
    for _ in range(limit):
        if model.pending() == 0:
            return
        model.step()
    raise AssertionError("finite ready trace did not drain")


def analytical_host_rounds(independent, dependent, batch):
    return dependent + (independent + batch - 1) // batch


def scheduled_host_rounds(independent, dependent, batch):
    """Reference batching schedule, intentionally separate from the formula."""
    rounds = dependent
    remaining = independent
    while remaining:
        remaining -= min(batch, remaining)
        rounds += 1
    return rounds


def total_from_round_cost(fixed, per_round, independent, dependent, batch):
    return fixed + analytical_host_rounds(independent, dependent, batch) * per_round


def total_from_application_host_cost(fixed, host_total, evaluations, independent, dependent, batch):
    rounds = analytical_host_rounds(independent, dependent, batch)
    return fixed + (rounds / evaluations) * host_total


def run_audit():
    checks = []

    collision = FeedbackAggregator(banks=1, entries_per_bank=4)
    collision_trace = [
        Update(0, 0, 1.0, 2),
        Update(0, 1, 10.0, 2),
        Update(0, 0, 2.0, 2),
        Update(0, 1, 20.0, 2),
    ]
    checks.append({"name": "collision_trace_accepted", "passed": all(collision.submit(x) for x in collision_trace)})
    drain(collision)
    sums = {(x["epoch"], x["group"]): x["sum"] for x in collision.emitted}
    checks.append({"name": "tag_isolation", "passed": sums == {(0, 0): 3.0, (0, 1): 30.0}})
    checks.append({"name": "collision_no_drop", "passed": collision.accepted == collision.processed == 4})
    checks.append({"name": "one_update_per_bank_cycle", "passed": collision.cycles == 4})

    serial = FeedbackAggregator(banks=2, entries_per_bank=2)
    assert serial.submit(Update(0, 0, 4.0, 1))
    assert serial.submit(Update(1, 0, 9.0, 1, predecessor=(0, 0)))
    serial.step()
    serial.step()
    emitted_before_ack = {(x["epoch"], x["group"]) for x in serial.emitted}
    checks.append({"name": "serial_epoch_waits_for_ack", "passed": emitted_before_ack == {(0, 0)}})
    assert serial.acknowledge(0, 0)
    drain(serial)
    emitted_after_ack = {(x["epoch"], x["group"]) for x in serial.emitted}
    checks.append({"name": "serial_epoch_released_after_ack", "passed": emitted_after_ack == {(0, 0), (1, 0)}})

    pressure = FeedbackAggregator(banks=1, entries_per_bank=1)
    first = pressure.submit(Update(0, 0, 1.0, 1))
    second = pressure.submit(Update(0, 1, 2.0, 1))
    checks.append({"name": "full_bank_backpressure", "passed": first and not second and pressure.accepted == 1})
    drain(pressure)
    checks.append({"name": "accepted_update_not_dropped", "passed": pressure.processed == 1 and len(pressure.emitted) == 1})

    b1 = FeedbackAggregator(banks=1, entries_per_bank=1)
    assert b1.submit(Update(0, 0, 7.0, 1))
    drain(b1)
    checks.append({"name": "b1_identity", "passed": b1.cycles == 1 and b1.emitted[0]["sum"] == 7.0})

    overfill = FeedbackAggregator(banks=1, entries_per_bank=1)
    overfill_results = [
        overfill.submit(Update(0, 0, 1.0, 2)),
        overfill.submit(Update(0, 0, 2.0, 2)),
        overfill.submit(Update(0, 0, 4.0, 2)),
    ]
    drain(overfill)
    checks.append(
        {
            "name": "expected_count_overfill_rejected",
            "passed": overfill_results == [True, True, False]
            and overfill.emitted[0]["sum"] == 3.0,
        }
    )

    mismatch = FeedbackAggregator(banks=1, entries_per_bank=1)
    mismatch_results = [
        mismatch.submit(Update(0, 0, 1.0, 2)),
        mismatch.submit(Update(0, 0, 2.0, 3)),
        mismatch.submit(Update(0, 0, 2.0, 2)),
    ]
    drain(mismatch)
    checks.append(
        {
            "name": "expected_count_mismatch_rejected",
            "passed": mismatch_results == [True, False, True]
            and mismatch.emitted[0]["sum"] == 3.0,
        }
    )

    round_equivalence = True
    for independent in range(65):
        for dependent in range(17):
            for batch in (1, 2, 4, 8, 16, 32, 64):
                round_equivalence = round_equivalence and (
                    analytical_host_rounds(independent, dependent, batch)
                    == scheduled_host_rounds(independent, dependent, batch)
                )
    checks.append(
        {
            "name": "analytical_host_round_equivalence",
            "passed": round_equivalence,
        }
    )

    unit_equivalence = True
    for independent in range(1, 33):
        for dependent in range(0, 9):
            evaluations = independent + dependent
            for batch in (1, 2, 4, 8, 16, 32):
                direct = total_from_round_cost(
                    fixed=7.0,
                    per_round=0.25,
                    independent=independent,
                    dependent=dependent,
                    batch=batch,
                )
                fraction = total_from_application_host_cost(
                    fixed=7.0,
                    host_total=evaluations * 0.25,
                    evaluations=evaluations,
                    independent=independent,
                    dependent=dependent,
                    batch=batch,
                )
                unit_equivalence = unit_equivalence and abs(direct - fraction) < 1.0e-12
    checks.append(
        {
            "name": "host_total_round_fraction_unit_equivalence",
            "passed": unit_equivalence,
        }
    )

    rng = random.Random(20260712)
    randomized = FeedbackAggregator(banks=4, entries_per_bank=16)
    trace = []
    expected_sums = {}
    for group in range(32):
        expected = 1 + rng.randrange(8)
        values = [float(1 + rng.randrange(1000)) for _ in range(expected)]
        expected_sums[(0, group)] = sum(values)
        trace.extend(Update(0, group, value, expected) for value in values)
    rng.shuffle(trace)
    randomized_accept = all(randomized.submit(update) for update in trace)
    drain(randomized, limit=10000)
    observed_sums = {
        (record["epoch"], record["group"]): record["sum"]
        for record in randomized.emitted
    }
    checks.append(
        {
            "name": "randomized_collision_conservation",
            "passed": randomized_accept
            and randomized.accepted == randomized.processed == len(trace)
            and observed_sums == expected_sums,
        }
    )
    checks.append(
        {
            "name": "randomized_bank_throughput_bound",
            "passed": randomized.cycles <= len(trace),
        }
    )

    result = {
        "schema": "qsup.feedback-aggregator-reference-audit.v1",
        "scope": "event-driven correctness and cycle-accounting model; no RTL timing, area, power, or workload-independence claim",
        "checks": checks,
        "passed": all(check["passed"] for check in checks),
    }
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w") as destination:
        json.dump(result, destination, indent=2)
        destination.write("\n")
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    run_audit()
