# Thesis Metrics Analysis Guide

This document explains the quantitative metrics used by the `analyze_results.py` script to evaluate and compare the structured (CogniSim) and unstructured AI approaches for DORA compliance.

---

## 1. Requirement Coverage Rate (%)

- **Purpose:** To measure how comprehensively the final generated test plan addresses the required acceptance criteria (for the structured approach) or the raw DORA article requirements (for the unstructured approach).
- **Calculation:** An LLM (gpt-3.5-turbo) scores each individual requirement on a scale of 0 (not covered), 1 (partially covered), or 2 (fully covered). The final percentage is calculated as:
  `(Total Score / (Total Requirements * 2)) * 100`
- **Interpretation:** A higher percentage is better, indicating a more complete and compliant document that thoroughly addresses all specified requirements.

---

## 2. Feedback Integration Rate (%)

- **Purpose:** (Structured Approach Only) To quantitatively measure the agility of the agent team by evaluating how well it incorporates feedback from one sprint to the next.
- **Calculation:** An LLM scores how well each feedback point from a sprint's review is addressed in the subsequent sprint's test plan (0, 1, or 2). The final percentage is:
  `(Total Feedback Score / (Total Feedback Points * 2)) * 100`
- **Interpretation:** A higher percentage demonstrates a more effective iterative process and a stronger adherence to Agile principles.

---

## 3. Compliance Coverage Trend (%)

- **Purpose:** (Structured Approach Only) To visualize the iterative improvement of the test plan's quality across the three simulated sprints.
- **Calculation:** The "Requirement Coverage Rate (%)" is calculated independently for each sprint's test plan artifact. These percentages are then plotted on a line graph.
- **Interpretation:** An upward-trending line provides powerful visual evidence of learning and iterative improvement, showing the agents are progressively closing compliance gaps over time.

---

## 4. Generative Verbosity (Word Count)

- **Purpose:** To measure the total length of the final generated test plan.
- **Calculation:** A simple word count of the final `.md` artifact.
- **Interpretation:** This is a measure of output size, not necessarily quality. It is used to compare the conciseness of the structured vs. unstructured approaches. A lower word count with a high coverage rate could indicate a more efficient and focused output.

---

## 5. Compliance Gap Count (Final)

- **Purpose:** To provide a simple, absolute number representing how far the final test plan is from a perfect score.
- **Calculation:** `(Total Requirements * 2) - Final LLM Score`.
- **Interpretation:** A lower number is better. This is the inverse of the Coverage Rate and provides a raw count of compliance gaps.

---

## Statistical Analysis

- **Mann-Whitney U Test:** This test is used to determine if the observed differences in the metric scores (e.g., Requirement Coverage Rate) between the structured and unstructured groups are statistically significant. A `p-value` of less than 0.05 suggests the difference is likely not due to random chance.
- **Cohen's d:** This metric measures the *size* of the difference between the two groups. A larger `d` value indicates a more substantial and meaningful difference in performance between the two approaches.
