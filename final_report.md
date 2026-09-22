# Literature Review: How can XAI techniques improve trust in automated student answer evaluation?

*Generated from 8 papers, 153 extracted claims, and 6 cross-paper comparisons (0 conflict(s) detected).*

---

Based on the provided literature, explainable artificial intelligence (XAI) techniques play an important role in enhancing transparency, stakeholder trust, and pedagogical value in automated student answer evaluation and automated essay scoring (AES) systems. 

### Enhancing Transparency and Trust Through XAI

XAI techniques such as LIME and SHAP are integrated across model families to provide pedagogically transparent explanations, highlighting which parts of an input text most influenced a model's output (Qureshi et al., 2026, p. 0; Kumawat et al., 2025, p. 3). Similarly, XAI frameworks—including feature importance visualizations, decision trees, and explanation interfaces—are utilized to improve stakeholder transparency and trust (Habagat et al., 2026, p. 0). 

Furthermore, deeper neural network architectures improve the reliability and trustworthiness of explanations. As the depth of a neural network increases, the precision and recall of its corresponding explanation model also improve (Kumar et al., 2020, p. 18). Conversely, the explanation model of a 2-layer predictive model is statistically significantly less trustworthy than that of a 4-layer model (Kumar et al., 2020, p. 11).

### The Nuanced Impact of Explanations on Students

Despite the technical integration of explainability tools, the direct psychological impact of explanations on students presents a complex picture. When testing the specific effects of automated essay scoring explanations—namely full-text global explanations and accuracy statements—research found that neither type of explanation had a direct effect on student trust or motivation compared to receiving no explanations at all (Conijn et al., 2023, p. 0). Instead, a student's subjective trust was significantly predicted by their baseline propensity to trust (Conijn et al., 2023, p. 8), while general trust and motivation were primarily influenced by the grade provided by the system, especially the difference between the student's self-estimated grade and the system grade (Conijn et al., 2023, p. 0). Nevertheless, simple accuracy statements can lead to higher interest in an assignment compared to providing no explanation (Conijn et al., 2023, p. 8).

### Pedagogical Value and Formative Feedback

Beyond holistic scoring, XAI and deep learning approaches offer direct pedagogical value by generating rubric-level feedback. By leveraging SHAP to analyze linguistic indices, AES systems can provide actionable guidance to students (Kumar et al., 2020, p. 0, p. 1). For example, feedback models can estimate that if a student employs diverse verbs in every sentence, their rubric score could improve from a baseline to a higher value, supporting iterative writing improvements and measurable score gains upon resubmission (Kumar et al., 2020, p. 20). 

### Broader Governance and Equity Considerations

Relying solely on high predictive accuracy or technical explainability is insufficient for achieving fairness and trust in automated educational assessments (Habagat et al., 2026, p. 0, p. 8). Automated scoring results remain subject to historical training data biases related to socioeconomic status, ethnicity, cultural background, and language variations (Habagat et al., 2026, p. 0, p. 8). Consequently, the literature highlights that fair AI-assisted assessment requires a combination of transparency via XAI, accountability and ethical governance, and Human-in-the-Loop (HITL) professional oversight frameworks where educators retain decision-making authority (Habagat et al., 2026, p. 0, p. 4, p. 10).

---

## Contradictions Found

- **AGREE**: All claims consistently describe the use and purpose of explainable AI tools like LIME and SHAP for interpreting model decisions and providing transparency.
- **AGREE**: The claims discuss different aspects of automated essay scoring systems—such as their impact on student trust and motivation, their high accuracy compared to humans, and the holistic versus rubric-level approaches in modeling—without presenting mutually exclusive contradictions.
- **UNCLEAR**: The claims discuss different aspects of automated essay scoring explanations—types of explanations and student trust in one, versus network depth and explanation model performance in the other—making direct comparison of agreement or conflict inconclusive without further context.
- **AGREE**: The claims describe different aspects of human rater scoring in essay grading studies (inter-rater reliability vs. scoring scale and method), which are complementary rather than contradictory.
- **AGREE**: The claims discuss different practical aspects of SHAP values—accuracy, algorithmic efficiency in TreeSHAP, and computational overhead—without making contradictory statements.
- **AGREE**: Both claims discuss the use of Explainable Artificial Intelligence (XAI) techniques to provide transparency, with the first focusing on general transparency and trust-building, and the second providing specific examples of XAI methods used to achieve spatial and pixel-level transparency.

## References

- **Towards Trustworthy Automated Essay Scoring: Explainable Transformers and Efficient Fine-Tuning Strategies** — Abdul Rehman Qureshi, Zakria, Muhammad Asif, Muhammad Saddam Khokhar, Safdar Hussain Mangnejo (2026) — https://www.semanticscholar.org/paper/a0313e75e462294769f2783cd78dd0ea5919130e
- **The Effects of Explanations in Automated Essay Scoring Systems on Student Trust and Motivation** — R. Conijn, Patricia K. Kahr, C. Snijders (2023) — https://www.semanticscholar.org/paper/ab9e85db19d5ef0df6295ef33fc44b3a71d78a52
- **Explainable Automated Essay Scoring: Deep Learning Really Has Pedagogical Value** — Vivekanandan S. Kumar, David Boulanger (2020) — https://www.semanticscholar.org/paper/00f754891bd6958896591f7d89cc7805b3e8210a
- **A Model-Agnostic Framework for Transparent, Fair, and Reproducible Automated Essay Scoring** — Ahsan Javed, Research Questions (2026) — https://www.semanticscholar.org/paper/d0e3c442aaafe0089676a0450b4ad4336381237b
- **The Role of Explainable AI (XAI) In Enhancing Transparency and Trust in NLP-Powered Educational Systems** — Priya Kumawat, Pradeep Singh Shaktawat (2025) — https://www.semanticscholar.org/paper/f0e0717d9eab644e17ac1d34e0de9ee8f0f22a44
- **Beyond the Score: A Systematic Literature Review of Explainable Artificial Intelligence Frameworks for Promoting Equity in Automated Educational Assessment** — Marites D. Habagat, L. Reazol (2026) — https://www.semanticscholar.org/paper/84aee0f07ea26ebcce0cb3e51a7f1006805414a1
- **Method of dynamic trust assessment in Zero Trust Architecture based on explainable artificial intelligence** — Andriy Palamarchuk (2026) — https://www.semanticscholar.org/paper/56e48725d6992387276bf4636c3577fd20e447a8
- **Trustworthy deep learning for malaria diagnosis using explainable artificial intelligence** — R. Parveen, Baozhi Qui, Wei Song, N. Al-Kahtani, M. M. Jamjoom, S. M. Mostafa, Nadia Sultan, Joddat Fatima (2025) — https://www.semanticscholar.org/paper/05aae448e22849d56418fefb06ca810836e27a69

---
*All claims above are grounded in the listed source papers with page-level citations, produced by an agentic pipeline: Search → Filter (human-approved) → Read → Contradiction-check → Write.*
