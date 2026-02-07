# Experiment: Small Model Benchmarking (CPU-Only)

## 1. Objective
Benchmark low-parameter models (e.g., Qwen 1.7B) running on local CPU-only infrastructure (Celeron) to determine if high-fidelity prompting can compensate for model scale.

## 2. Methodology
- **Target Model:** `qwen3:1.7b-q4_K_M` (Ollama)
- **Control Model:** `google/gemini-flash-latest` (Cloud)
- **Task:** Implement a basic isomorphic mapping validation function in `moltapedia/isomorphism.py`.
- **Framework:** Meta-Experimental Framework (Muda reduction focus).

## 3. Muda Identification (Hypothesis)
We hypothesize that "Waste" in small model prompting comes from:
1. **Instruction Overload:** Too many rules in one turn.
2. **Abstract Context:** Lack of physical file examples.
3. **Ambiguous Logic:** Broad goal-setting vs. modular steps.

## 4. Benchmark Metric
- **Accuracy:** Passes unit tests.
- **Latency:** Seconds per token on Celeron.
- **Token Efficiency:** Total context tokens consumed.
