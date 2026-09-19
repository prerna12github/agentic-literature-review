# Literature Review: quantum gate error reduction fidelity optimization

*Generated from 9 papers, 163 extracted claims, and 9 cross-paper comparisons (2 conflict(s) detected).*

---

### Quantum Gate Error Reduction and Fidelity Optimization

Optimizing quantum gate fidelity and reducing gate errors involve multiple strategies across various hardware platforms and theoretical frameworks. Approaches range from advanced control pulse optimization and machine learning compilation to physical and environmental noise analysis.

#### Control Frameworks and Pulse Optimization
To simultaneously optimize the speed and fidelity of quantum computation against stochastic control errors and leakage, reinforcement learning (RL) frameworks have been proposed (Niu et al., 2018, p. 0). In superconducting-qubit architectures, deterministic and reversible coherent leakage is caused by direct couplings between the qubit subspace and higher-energy subspaces, while incoherent leakage stems from non-adiabatic transitions or photon loss (Niu et al., 2018, p. 1). Universal control cost function optimization (UFO) techniques combined with continuous-variable policy-gradient agents achieve up to two orders of magnitude reduction in average infidelity and standard deviation compared to stochastic gradient descent (SGD) baselines (Niu et al., 2018, p. 1, 4, 6). 

Similarly, pulse-level calibrations can generate high-fidelity control pulses for continuous parameter sets of quantum gates (Chadwick et al., 2023, p. 0). Pre-calibrating a continuous pulse landscape and re-optimizing specific operations (such as CNOT and $\sqrt{\text{SWAP}}$) allows linear interpolation to yield high-fidelity pulses for intermediate operations, significantly improving calibration efficiency and pulse infidelities (Chadwick et al., 2023, p. 0, 1). 

In neutral-atom platforms, fast single-pulse gates based on optimal control, atomic dark states to minimize scattering, and improved Rydberg excitation and cooling achieve 99.5% fidelity for two-qubit controlled phase (CZ) gates on up to 60 atoms in parallel, surpassing error-correcting thresholds (Evered et al., 2023, p. 0).

#### Qubit Allocation and Circuit Compilation
Circuit-level error reduction can also be achieved through intelligent compilation and qubit allocation. By combining reinforcement learning with a graph neural network (GNN)-based Q-network (GNAQC), mapping decisions analyze the backend graph's connections and error rates to provide more reliable layouts, resulting in an approximate 12.7% relative increase in final output fidelity compared to pre-existing methods (Lecompte et al., 2023, p. 1, 2).

#### Fidelity Analysis and Theoretical Limits
Understanding the limits of fidelity requires examining noise models and open quantum systems. The Average Gate Infidelity (AGI) under Markovian noise can be evaluated through perturbative expansions in terms of environmental coupling coefficients (Hartmann et al., 2024, p. 1). For single qudits under pure dephasing, AGI transitions from a linear regime to a nonlinear regime that saturates at a stable plateau in the strong-noise regime, bounded between $1 - \frac{2}{d+1}$ and $1 - \frac{1}{d+1}$ for dimension $d$ (Hartmann et al., 2024, p. 7, 8, 17). 

#### Addressing Experimental and Architectural Discrepancies
When evaluating high-fidelity entangled states and gate error sources across literature, several architectural differences and specific contexts must be noted:

* **Bell State and Entangled Gate Fidelities:** Quantitative values for Bell state and entangling gate fidelities differ depending on the platform. Evered et al. (2023, p. 1–2) report raw Bell-state fidelities of 98.0(2)% and CZ gate fidelities of 99.52(4)% to 99.54(2)% in neutral-atom systems, whereas Steinacker et al. (2024, p. 1, 4) report uncorrected Bell state fidelities between 96.47% and 97.17% in gate-defined quantum dots. These differences arise because the claims evaluate different quantum computing architectures using distinct experimental setups and physical qubits.
* **Primary Error Sources:** The dominant source of error varies by gate type and deployment. Joas et al. (2024, p. 8) analyze local electron spin gates in diamond quantum registers and find that 90% of observed errors are coherent and correctable, with unpolarized spins and misaligned fields contributing significantly. Conversely, Gupta et al. (2025, p. 1) identify Bell pair infidelity from noisy quantum links as the primary source of error for remote gates in distributed quantum computing. These differing conclusions occur because the claims refer to entirely different types of gates and systems (local spin gates versus remote distributed gates) that inherently possess distinct primary error mechanisms.

---

## Contradictions Found

- **AGREE**: The claims discuss different aspects of quantum control—such as optimizing gate fidelity, mitigating leakage errors, and generating control pulses—and represent complementary advancements in quantum computing rather than contradictory findings.
- **AGREE**: The claims discuss improvements in quantum gate synthesis and optimization using different advanced control methods (reinforcement learning and optimal control) on different quantum computing platforms, representing complementary advancements rather than conflicting results.
- **AGREE**: The claims discuss different aspects of average gate infidelity (AGI) and quantum control: one set of claims measures performance improvements of RL-based control over SGD baselines, while the other derives perturbative expansions of AGI. They address different topics within quantum control and do not contradict one another.
- **UNCLEAR**: The claims discuss different aspects of quantum computing and gate optimization—such as optimal gate synthesis via reinforcement learning, pulse space calibration efficiency, and multi-qubit entangling gate design—using disparate methods and contexts, making direct comparison of their findings inconclusive.
- **AGREE**: The claims discuss different aspects of quantum gate fidelities (experimental demonstration, general error-correcting thresholds, and theoretical simulation assumptions), which address different contexts rather than directly contradicting one another.
- **CONFLICT**: The claims are from two different papers evaluating different quantum computing architectures (neutral-atom quantum computers versus gate-defined quantum dots) using different experimental setups and physical qubits, resulting in different quantitative fidelity values for Bell states and entangling gates.
- **AGREE**: Both sets of claims discuss high-fidelity quantum gates achieved experimentally in different physical systems (spatial mode quantum gates and diamond quantum registers), and while their specific fidelity values and contexts differ, they do not contradict each other as they describe separate physical implementations and methods.
- **CONFLICT**: The claims refer to different types of gates and systems (local spin gates in diamond quantum registers versus remote gates in distributed quantum computing) which naturally have different primary error sources.
- **AGREE**: The claims from the first paper consistently describe the performance, benefits, and scalability of the GNAQC method without contradiction, while the claim from the second paper addresses a different topic in quantum computing (distributed quantum computing) and does not contradict the findings about GNAQC.

## References

- **Universal quantum control through deep reinforcement learning** — M. Niu, S. Boixo, V. Smelyanskiy, H. Neven (2018) — https://www.semanticscholar.org/paper/3ada65624811cfc46bc113509f3120100bcf4f52
- **Efficient Control Pulses for Continuous Quantum Gate Families Through Coordinated Re-Optimization** — Jason Chadwick, F. Chong (2023) — https://www.semanticscholar.org/paper/98c011f2d43a9e89b2529dc88e8557f0db69a163
- **Nonlinearity of the Fidelity in Open Qudit Systems: Gate and Noise Dependence in High-dimensional Quantum Computing** — Jean-Gabriel Hartmann, D. Janković, Rémi Pasquier, M. Ruben, P. Hervieux (2024) — https://www.semanticscholar.org/paper/39fd0b4b4be09ff75664e8140624d482a4134486
- **High-fidelity parallel entangling gates on a neutral-atom quantum computer** — S. Evered, D. Bluvstein, M. Kalinowski, S. Ebadi, T. Manovitz, Hengyun Zhou, Sophie Li, A. Geim, Tout T. Wang, N. Maskara, H. Levine, G. Semeghini, M. Greiner, V. Vuletić, M. Lukin (2023) — https://www.semanticscholar.org/paper/531874012fede3c01f44f2d81bfb926c0a25c9aa
- **Ultrahigh-fidelity spatial mode quantum gates in high-dimensional space by diffractive deep neural networks** — Qianke Wang, Jun Liu, Dawei Lyu, Jian Wang (2024) — https://www.semanticscholar.org/paper/3b743298ec22e8d6a69dd7afd4256dcafe1421a0
- **High-Fidelity Electron Spin Gates for Scaling Diamond Quantum Registers** — T. Joas, F. Ferlemann, Roberto Sailer, Philipp J. Vetter, Jingfu Zhang, R. Said, T. Teraji, Shinobu Onoda, T. Calarco, G. Genov, Matthias M. Muller, F. Jelezko (2024) — https://www.semanticscholar.org/paper/26e0df30047c596ad4e9114f0d11e2c3c8492648
- **Machine-Learning-Based Qubit Allocation for Error Reduction in Quantum Circuits** — Travis Lecompte, Fang Qi, Xu Yuan, Nian-feng Tzeng, M. Najafi, Lu Peng (2023) — https://www.semanticscholar.org/paper/bb15ab89d88c4ca337d5d4af19c467d31d811f3e
- **Gate Teleportation vs. Circuit Cutting in Distributed Quantum Computing** — Shobhit Gupta, Nikolay Sheshko, Daniel Dilley, A. Gonzales, M. K. Singh, Zain Saleem (2025) — https://www.semanticscholar.org/paper/ab52e5a9bb47b5ae4ad286d3ad779bd841ebb9b8
- **Bell inequality violation in gate-defined quantum dots** — P. Steinacker, T. Tanttu, Wee-Han Lim, Nard Dumoulin Stuyck, M. Feng, S. Serrano, E. Vahapoglu, R.-Y. Su, J. Y. Huang, Cameron Jones, Kohei M. Itoh, F. Hudson, C. Escott, A. Morello, A. Saraiva, C. Yang, A. Dzurak, A. Laucht (2024) — https://www.semanticscholar.org/paper/f56adec68b99f3ed5eafbcf7c2c21c26ed41aa10

---
*All claims above are grounded in the listed source papers with page-level citations, produced by an agentic pipeline: Search → Filter (human-approved) → Read → Contradiction-check → Write.*
