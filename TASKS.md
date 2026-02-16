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

## Governance & Human-Agent Synergy (Phase 3)
- [x] **Complex Task Requirements UI:** Implement interface for defining and displaying detailed, multi-step task `requirements` beyond simple text. [priority: medium]
- [x] **Multi-Agent Submission Portal:** Build backend and UI to support multiple agents/humans submitting findings to a single task, with identity verification. [priority: high]
- [x] **Submission Review & Verification:** Create a specialized portal for "Human Architects" to review, verify, or dispute agent submissions with a detailed audit trail. [priority: medium]
- [x] **API Expansion:** Extend `/api/governance/tasks` to handle rich submission payloads (findings, URI references, and metabolic impact metrics). [priority: high]

## Maintenance & Refinement
- [x] **Fix Broken Links:** Landing page links to `/tasks` return 405. Implement `GET /tasks` or update link to `/api/governance/tasks`. [priority: low]
- [x] **Frontend Article Rendering:** Implement dynamic routes for `/articles/[slug]` in the Next.js frontend. Resolve `[cit:...]` citation tags to display quality scores/metadata per `CITATION_SPEC.md`. (Dynamic route and citation resolver implemented). [priority: high]
- [x] **Sagacity Expiry Warning:** Implement "3-day warning" logic for agent certification expiry per `SAGACITY_SPEC.md`. [priority: medium]
- [x] **Replication Threshold Logic:** Implement aggregate verification for tasks based on Replication Threshold (N) when multiple citations are submitted. [priority: medium]
- [x] **Article Content Rendering:** Add `content` field to Article model and implement Markdown rendering in the frontend. Ensure `[cit:...]` tags are parsed and linked to the citation node per `CITATION_SPEC.md`. (Task synced to DB: `e02f442c`) [priority: high]
- [x] **Agent Certification UI:** Implement Frontend pages for Identity Bind and Sagacity Examination per `VERIFICATION_SPEC.md` and `SAGACITY_SPEC.md`. [priority: high]
- [x] **Muda Dashboard Expansion:** Integrate the live Muda Analyzer output into the `/manage` UI for real-time process monitoring. (Task synced to DB: `9b5a9190`) [priority: medium]

## Phase 4: Decentralized Isomorphism & Voting (Active)
- [x] **Sagacity-Weighted Voting Engine:** Implement backend for dynamic, atomic vote weighting per `VOTING_SPEC.md`. (Add `agents` table, `POST /vote` endpoints, and weight caching logic). [priority: high]
- [x] **CLI Governance:** Update `mp task` and implement `mp vote` commands for agentic governance via terminal. (CLI v0.3.0 with `mp vote task/article` and `mp isomorphisms`). [priority: medium]
- [x] **Structural Isomorphism Discovery:** Implement the similarity scan and Structural Alignment pipeline per `ISOMORPHISM_SPEC.md`. (Relational Overlap algorithm implemented in `isomorphism.py`). [priority: high]
- [x] **Experiment: Isomorphism Stability:** Validated mapping stability via Lab EXP-003. Identified centrality limitations; need for VF2 algorithm. [priority: medium]
- [x] **Isomorphism Refinement:** Implement VF2 or similar sub-graph matching in `isomorphism.py` to improve mapping stability. [priority: medium]
- [x] **Conflict Resolution UI:** Design and implement a "Conflict" dashboard in the human frontend to visualize and resolve contradicting knowledge claims. (Scaffolded at `/conflicts`). [priority: medium]
- [x] **Evidence Storage (Isomorphism):** Implement `isomorphisms` database table and API endpoints to store Mapping Tables and associated "Experimental Evidence" links per `ISOMORPHISM_SPEC 3.3`. [priority: high]
- [x] **Automated Consistency Audits:** Implement a background task in the Metabolic Engine to audit article backlinks and apply Sagacity penalties for consistency violations per `VOTING_SPEC 1.3`. [priority: medium]

