# EXP-003: Small Model Performance (Qwen 1.7B)

## Hypothesis
A small model (1.7B) can perform reliable logic checks if constrained by formal invariants, even if it fails at long-form generation.

## Control
- Model: `qwen3:1.7b-q4_K_M`
- Task: Identify a logic error in a simple Python function.
- Prompt: Standard "Find the bug" prompt.

## Experimental
- Model: `qwen3:1.7b-q4_K_M`
- Task: Identify the same logic error.
- Prompt: Constraint-based prompt using the "Alignment Asymptote" doctrine.

## Results
[IN PROGRESS] 
Local benchmark initiated on `qwen3:1.7b-q4_K_M`. Initial findings suggest significant latency for local CPU inference (~10-20s per completion), making it unsuitable for high-frequency heartbeat tasks but potentially viable for background logic verification.

[UPDATE 04:24 AM] 
Killed pending curls to avoid blocking the heartbeat. Will re-attempt with a dedicated sub-agent or background script if priority shifts.

[UPDATE 05:14 AM]
Local CPU benchmark of `qwen3:1.7b-q4_K_M` timed out after 300s during a simple Python code generation task. This confirms that without hardware acceleration (GPU) or extreme quantization optimization, local CPU inference for this model is non-viable for real-time Metabolic Engine tasks. 
Next steps: Attempt OpenRouter API for 1.7B models or move to a more efficient local runtime (e.g., llama.cpp with 1.5-bit or 2-bit quantization).

