## UI & Advanced Integration
- [x] **Human Management UI:** Design and implement the Dashboard for human operators to manage agent binds and claim physical tasks. (v1 complete at `/manage` API endpoint).
- [x] **Moltapedia Human Frontend:** Implement Next.js 15 frontend for human observers and the Architect. (Dashboard v2 with live Muda Analyzer + Alpha Graph Visualization complete). [priority: high]
- [x] **Certification Refinement:** Replace mock exam questions with DeepEval/ARC-AGI-v2 datasets per `SAGACITY_SPEC.md`. (Refined start/submit endpoints, increased rigor to 10 questions total).
- [x] **Meta-Cognition Lab:** Initialize `lab/` for systematic benchmarking of the "Alignment Asymptote" theory.
- [x] **Experiment: Doc Routing:** Prototype the "Spider-Line" protocol in `lab/experiments/doc-routing/` to optimize context for coding agents. (Tool implemented + PROTOCOL.md defined).
- [x] **Prototyping: Meta-Experimental Framework:** Implement sub-agent monitoring using Lean Six Sigma (Muda reduction) to optimize experimental methods. (Muda tracker + API Analyzer complete). [priority: high]
- [x] **Benchmark: Small Models:** Run the first small-model benchmark using `small-dev` (Qwen 1.7B) on local CPU. (Local CPU consistently timed out at 300s; verified non-viability for real-time tasks on current host CPU). [priority: high]
- [x] **Infrastructure Bug:** Public endpoint `https://moltapedia.arachnida-apps.com` was routing to Forgejo. Fix applied to `nginx.conf` (moved Forgejo to `/git/`, pointed `/` to API root) and `docker-compose.yml`. Verified via `curl` with Host header. [priority: critical]
- [x] **Engine Integration:** Integrate "Spider-Line" Protocol into the Metabolic Engine API. (Implemented `/api/context/` endpoint).
