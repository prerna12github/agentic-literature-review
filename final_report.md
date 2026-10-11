# Literature Review: How to improve ASAG model to evaluate students's answers ?

*Generated from 7 papers, 75 extracted claims, and 8 cross-paper comparisons (3 conflict(s) detected).*

---

Based on the provided literature, improving Automated Short Answer Grading (ASAG) models involves several approaches, including architectural advancements, feature extraction, data preprocessing, and reasoning-guided fine-tuning. 

### Transition from Feature Engineering to Deep Learning
The field of ASAG has evolved from hand-engineered text features toward feature learning architectures utilizing deep learning (Haller et al., 2022, p. 21). However, ASAG benchmark datasets are often sparse, meaning that complex models developed for general Natural Language Processing (NLP) tasks do not always generalize well (Haller et al., 2022, p. 21). 

### Semantic Similarity and Embeddings
Improving model accuracy frequently relies on capturing the semantic similarity between student answers and reference answers. 
* **Embedding Models:** Various embedding generations have been explored, such as Sentence-BERT (SBERT), Universal Sentence Encoder (USE), and transformer variants like BERT, RoBERTa, DistilBERT, and ALBERT (Jagdishbhai et al., 2025, p. 3). Among these, fine-tuned SBERT models have outperformed standard transformers and USE in capturing contextual relationships and sentence-level similarity (Jagdishbhai et al., 2025, p. 7). 
* **Semantic Networks & Vector Metrics:** Semantic networks utilizing WordNet (as a knowledge-based source) and GloVe (as a corpus-based source) can measure word-to-word similarity using metrics like Wu & Palmer similarity and cosine similarity (Hameed et al., 2023, pp. 4, 7). Extracted features—such as Reference Answer Semantic Weight (RASW), Student Answer Semantic Weight (SASW), word overlapping, and length ratio—can then be fed into Support Vector Machine (SVM) models (Hameed et al., 2023, pp. 0, 9). 
* **Hybrid Architectures:** Combining GloVe embeddings with Long Short-Term Memory (LSTM) networks helps capture both sequential dependencies and semantic/syntactic word relationships (Diyasa et al., 2025, p. 4). 

### Reasoning-Guided Fine-Tuning and Overcoming Length Bias
Standard fine-tuning of large language models for ASAG can lead to catastrophic overfitting, where models show near-perfect training scores but poor test scores (Faza et al., 2025, p. 0). To address this and avoid relying on superficial heuristics (such as answer length bias), a **reasoning-guided fine-tuning approach**—using teacher models to generate analytical rationales—can achieve state-of-the-art performance and greater robustness, even though it requires significantly more inference time (Faza et al., 2025, pp. 0, 10, 25). 

Additionally, transformer or transformer-ensemble approaches can generally benefit from a phase of generating various reference answers to improve performance (Kortemeyer, 2023, p. 3).

### Data Preprocessing Pipelines
Model performance is heavily influenced by data preparation:
* Pre-cleaning student answers before embedding generation results in significantly better similarity estimation and grading performance (Jagdishbhai et al., 2025, p. 8). 
* **Addressing Conflicts in Preprocessing and Datasets:** The literature shows variations in preprocessing steps and dataset scopes. For instance, some studies on Indonesian data utilize specific regional libraries like Sastrawi for stemming and case folding (Diyasa et al., 2025, p. 9), whereas English-focused studies apply lemmatization, stopword removal, and length-bin categorization (Jagdishbhai et al., 2025, p. 3; Hameed et al., 2023, p. 6). These differences stem from the distinct target languages, underlying methods, and datasets used across the respective papers. 

Similarly, papers reference different dataset scales and subsets—such as the full Beetle dataset containing 47 questions with ~366 answers per question (Haller et al., 2022, p. 6), a specific Kaggle download of test data featuring 504 items and 14,186 student answers (Kortemeyer, 2023, p. 3), or separate regional datasets containing 1,140 unique questions with multiple answer variations (Diyasa et al., 2025, p. 8)—reflecting the diverse evaluation boundaries chosen by each set of researchers.

---

## Contradictions Found

- **UNCLEAR**: The claims discuss completely different datasets used in the respective studies (SciEntsBank for English science answers vs. an expanded Indonesian dataset for short answer pairs), so they do not directly contradict or agree on the same facts.
- **CONFLICT**: The claims describe different datasets and subsets used in their experiments. The first claim describes the full Beetle data set (47 questions, ~366 answers per question), the second claim describes a specific downloaded subset from Kaggle (test data including 504 items and 14,186 answers), and the third describes a completely different dataset with 1,140 unique questions and three answer variations.
- **AGREE**: The claims discuss different aspects of automated short answer grading, such as word overlap methods, semantic weights, and feature importance, without contradicting one another.
- **CONFLICT**: The claims describe different text preprocessing pipelines because the papers utilize different underlying methods, datasets, and target languages (e.g., using Sastrawi for Indonesian stemming in one paper versus standard English NLP techniques in others, and varying sequence lengths for padding).
- **AGREE**: The claims discuss the use of various embedding models like SBERT, BERT, RoBERTa, and USE for short answer grading and sentence similarity, with consistent findings regarding SBERT's strong performance. The differences in specific models used (such as multilingual-e5 in the second paper) are due to different languages and datasets (Indonesian vs. general) rather than contradictory findings.
- **AGREE**: The claims discuss the same topic of automatic short answer grading by evaluating semantic similarity between student answers and reference answers, either using vector embeddings or semantic networks, without presenting contradictory conclusions.
- **CONFLICT**: The claims describe different dataset sizes and partitioning strategies (an 80/20 train/test split with 220 total samples versus a 70/15/15 train/validation/test split with 3,152 total samples), indicating they used entirely different datasets for their respective experiments.
- **AGREE**: All claims support the use of automated systems and machine learning/natural language processing for evaluating student answers efficiently and accurately.

## References

- **Survey on Automated Short Answer Grading with Deep Learning: from Word Embeddings to Transformers** — Stefan Haller, Adina Aldea, C. Seifert, N. Strisciuglio (2022) — https://www.semanticscholar.org/paper/3e0b093db102aaf4e491342194d5942211081748
- **Performance of the pre-trained large language model GPT-4 on automated short answer grading** — Gerd Kortemeyer (2023) — https://www.semanticscholar.org/paper/6c16ffcdd208f0dbbbb30bfb518d9214befe6804
- **Deep Learning Techniques for Automatic Short Answer Grading** — Parmar Ashishkumar Jagdishbhai, Nikunj C. Gamit, Jashvantkumar R. Dave (2025) — https://www.semanticscholar.org/paper/d7f107aa8ee507f9424ff204d50a07b8d5e5808e
- **Automatic Short Answer Grading System Based on Semantic Networks and Support Vector Machine** — Naamah Hussien Hameed, Ahmed T. Sadiq (2023) — https://www.semanticscholar.org/paper/40b601c832cfda4bc700ca8b0c6ed42a4bdda818
- **Defying Data Scarcity: High-Performance Indonesian Short Answer Grading via Reasoning-Guided Language Model Fine-Tuning** — M. Faza, P. D. Purnamasari, Anak Agung Putri Ratna (2025) — https://www.semanticscholar.org/paper/81f2cc5b456b58e1a61b84f0ccb3a3634cd94a2c
- **Automated Student Answer Scoring Using GloVe-LSTM and Hybrid Similarity Metrics** — I. G. S. M. Diyasa, M. Idhom, Ahmad Sofian Aris Saputra, Deshinta Arrova Dewi, Tresna Maulana Fahrudin (2025) — https://www.semanticscholar.org/paper/e6b69ca5006a499ff7298432f0d920cb4dea1d98
- **A survey on automates grading of hand written examination answer scripts using machine learning and natural language processing** — Kavitha Soppari, Kosini Abhilaasha, Kommu Akanksha, Panumatinti Navya (2025) — https://www.semanticscholar.org/paper/ae3369a654d165ba7072c4785f25d23fa0685274

---
*All claims above are grounded in the listed source papers with page-level citations, produced by an agentic pipeline: Search → Filter (human-approved) → Read → Contradiction-check → Write.*
