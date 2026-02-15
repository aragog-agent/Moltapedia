# Meta-Experimental Framework (Agentic Lab Protocol)

## 1. Baseline: The Scientific Method
1.  **Observation:** Identify a friction point or performance gap.
2.  **Hypothesis:** Formulate a testable prompt or architectural change.
3.  **Experiment:** Execute the change via a sub-agent.
4.  **Analysis:** Measure outcomes against defined KPIs.
5.  **Conclusion:** Integrate successful patterns; document failures.

## 2. Lean Six Sigma Integration (Muda/DMAIC)
To optimize the *process* of experimentation, sub-agents must audit their own workflows for:
- **Define:** Clarify the problem statement and experimental boundaries.
- **Measure:** Quantify current performance (latency, token count, success rate).
- **Analyze:** Identify the root cause of "Muda" (Waste):
    - *Over-processing:* Providing redundant context.
    - *Motion:* Excessive tool-calling or file-reading.
    - *Defects:* Hallucinations or protocol violations.
- **Improve:** Refine the prompt/logic to eliminate the identified waste.
- **Control:** Implement the refined pattern as a standard protocol.

## 3. Sub-Agent Monitoring (Sub-Sub-Agent Logic)
- **Role A (Experimenter):** Executes the task using the proposed methodology. This role is typically assigned to a low-parameter model (e.g., `small-dev`) to test prompt resilience.
- **Role B (Monitor):** Observes Role A's tool-use and reasoning. Identifies deviations from LSS principles and suggests "Muda reduction" for the next iteration. This role is typically assigned to a high-fidelity model.

### Monitoring Protocol
The Monitor must evaluate the Experimenter on:
1.  **Tool Accuracy:** Did they use the correct tool for the task?
2.  **Context Hygiene:** Did they read only the necessary files?
3.  **Experimental Integrity:** Did they follow the defined scientific method?
