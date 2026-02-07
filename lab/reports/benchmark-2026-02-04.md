# Lab Report: Small Model Benchmark Failure

## Context
Initial attempt to benchmark `small-dev` (`qwen3:1.7b-q4_K_M`) on local Celeron CPU infrastructure.

## Findings
- **Timeout (30s):** A simple "Hello" query failed to return a response within 30 seconds.
- **System Signal (SIGKILL):** Background processes were terminated before completion.
- **Constraint Identification:** The CPU-only substrate is a significant bottleneck for real-time local sub-agency.

## Next Steps
- Increase timeout limits for background benchmark processes to 5-10 minutes.
- Audit "Muda" in the Ollama startup sequence (measure time-to-first-token).
