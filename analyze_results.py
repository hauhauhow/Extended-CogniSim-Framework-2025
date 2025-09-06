import os
import json
import re
from datetime import datetime
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from openai import OpenAI
import textwrap

# --- Configuration ---
# Base directory for all results
BASE_RESULTS_DIR = "extended_cognisim_framework_clean_repo/cognisim_v20/results_v8"
# Articles to analyze (assuming both structured and unstructured have results for these)
ARTICLES_TO_ANALYZE = [24, 25]
# Number of trials for each approach
NUM_TRIALS = 5

# OpenAI API Key (replace with your actual key or set as environment variable)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"), base_url="https://api.openai.com/v1")

# --- Helper Functions ---

def get_word_count(content):
    """Calculates the word count of a given content string."""
    return len(content.split())

def get_acceptance_criteria(product_backlog_path):
    """Extracts acceptance criteria (descriptions) from product_backlog.json."""
    try:
        with open(product_backlog_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            criteria = []
            for story in data: # Iterate directly over the list
                criteria.extend([story.get('description', '')])
            return criteria
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print(f"Error: Malformed JSON in {product_backlog_path}")
        return []

def get_requirements_from_dora_article(article_path):
    """Extracts requirements from DORA article text."""
    try:
        with open(article_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Simple regex to find numbered requirements (e.g., "1. Blah blah", "2. Blah blah")
            # This might need refinement based on actual DORA article formatting
            requirements = re.findall(r'^\d+\.\s*(.*)', content, re.MULTILINE)
            return requirements
    except FileNotFoundError:
        print(f"Error: DORA article file not found: {article_path}")
        return []

def evaluate_coverage_with_llm(requirement, test_plan_content):
    """Evaluates how well a requirement is covered in content using an LLM (0, 1, or 2)."""
    prompt = textwrap.dedent(f'''

You are an expert DORA compliance auditor. Your task is to evaluate how well the following DORA requirement is covered in the provided test plan content. Rate the coverage on a scale of 0 to 2: 

0: Not Covered - The requirement is not addressed or is completely irrelevant.
1: Partially Covered - The requirement is mentioned, but the coverage is superficial, inaccurate, or lacks sufficient detail/quality.
2: Fully Covered - The requirement is addressed comprehensively, accurately, and with high quality, demonstrating a clear understanding and actionable implementation.

Requirement: {requirement}

Test Plan Content:
"""{test_plan_content}"""

Provide only the score (0, 1, or 2) as a single digit. Do not add any other text or explanation.
''')
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides numerical scores."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0, # Keep temperature low for consistent scoring
            max_tokens=1 # Expect a single digit response
        )
        score_str = response.choices[0].message.content.strip()
        return int(score_str) if score_str.isdigit() and int(score_str) in [0, 1, 2] else 0
    except Exception as e:
        print(f"LLM evaluation error for requirement '{requirement[:50]}...': {e}")
        return 0 # Default to 0 on error

def get_timestamps_from_log(log_content):
    """Extracts first and last timestamps from simulation log content."""
    time_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
    timestamps = re.findall(time_pattern, log_content)
    if len(timestamps) >= 2:
        # Convert to datetime objects for calculation
        start_time = datetime.strptime(timestamps[0], '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(timestamps[-1], '%Y-%m-%d %H:%M:%S')
        return start_time, end_time
    return None, None

def get_feedback_points(feedback_md_path):
    """Extracts feedback points from a feedback Markdown file."""
    try:
        with open(feedback_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Look for lines starting with -, *, or numbers followed by a dot
            feedback_lines = re.findall(r'^[*-]?\s*(.*)', content, re.MULTILINE)
            # Filter out empty lines and potential headers
            feedback_points = [line.strip() for line in feedback_lines if line.strip() and not line.strip().startswith('#')]
            return feedback_points
    except FileNotFoundError:
        return []

def evaluate_feedback_integration_with_llm(feedback_point, test_plan_content):
    """Evaluates how well a single feedback point is integrated into content using an LLM (0, 1, or 2)."""
    prompt = textwrap.dedent(f'''
You are an expert DORA compliance auditor. Your task is to evaluate how well the following feedback point has been addressed or integrated into the provided test plan content. Rate the integration on a scale of 0 to 2:

0: Not Addressed - The feedback point is not reflected or is completely ignored.
1: Partially Addressed - The feedback point is mentioned, but the integration is superficial, incomplete, or lacks sufficient detail/quality.
2: Fully Addressed - The feedback point is addressed comprehensively, accurately, and with high quality, demonstrating a clear understanding and actionable implementation.

Feedback Point: {feedback_point}

Test Plan Content:
"""{test_plan_content}"""

Provide only the score (0, 1, or 2) as a single digit. Do not add any other text or explanation.
''')
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides numerical scores."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0, # Keep temperature low for consistent scoring
            max_tokens=1 # Expect a single digit response
        )
        score_str = response.choices[0].message.content.strip()
        return int(score_str) if score_str.isdigit() and int(score_str) in [0, 1, 2] else 0
    except Exception as e:
        print(f"LLM evaluation error for feedback point '{feedback_point[:50]}...': {e}")
        return 0 # Default to 0 on error

# --- Main Analysis Functions ---

def analyze_results():
    """Analyzes simulation results for both structured and unstructured approaches."""
    analysis_data = {
        "analysis_timestamp": datetime.now().isoformat(),
        "articles_analyzed": ARTICLES_TO_ANALYZE,
        "structured_results": {},
        "unstructured_results": {},
        "comparative_analysis": {}
    }

    for article_num in ARTICLES_TO_ANALYZE:
        print(f"Analyzing results for Article {article_num}...")
        
        # --- Structured Approach Analysis ---
        structured_article_results = []
        for trial_num in range(1, NUM_TRIALS + 1):
            print(f"  Processing Structured Trial {trial_num}...")
            trial_dir = os.path.join(BASE_RESULTS_DIR, "structured", f"article_{article_num}", f"trial_{trial_num}")
            
            # Paths for structured artifacts
            simulation_log_path = os.path.join(trial_dir, "artifacts", "simulation_output.txt")
            final_test_plan_path = os.path.join(trial_dir, "artifacts", "Final_Cumulative_Test_Plan.md")
            # product_backlog_path = os.path.join(trial_dir, "artifacts", "product_backlog.json") # Removed
            dora_article_path = os.path.join(
     "extended_cognisim_framework_clean_repo/cognisim_v20/assets", f"dora_article_{article_num}.txt")


            # Incremental artifact paths for Compliance Coverage Trend
            sprint_test_plans = []
            for s in range(1, 4): # Assuming 3 sprints for incremental analysis
                sprint_plan_path = os.path.join(trial_dir, "artifacts", f"final_test_plan_sprint_{s}.md")
                if os.path.exists(sprint_plan_path):
                    sprint_test_plans.append(sprint_plan_path)

            if not os.path.exists(final_test_plan_path):
                print(f"  Structured: Missing final_test_plan for Article {article_num}, Trial {trial_num}. Skipping.")
                continue

            log_content = "" # Default empty if log is missing
            if os.path.exists(simulation_log_path):
                with open(simulation_log_path, 'r', encoding='utf-8') as f:
                    log_content = f.read()
            
            with open(final_test_plan_path, 'r', encoding='utf-8') as f:
                final_test_plan_content = f.read()

            # --- Calculate Metrics for Structured Trial ---
            metrics = calculate_structured_metrics(
                log_content,
                final_test_plan_content,
                sprint_test_plans,
                trial_dir,
                dora_article_path # Added
            )
            structured_article_results.append(metrics)
        analysis_data["structured_results"][f"article_{article_num}"] = structured_article_results

        # --- Unstructured Approach Analysis ---
        unstructured_article_results = []
        for trial_num in range(1, NUM_TRIALS + 1):
            print(f"  Processing Unstructured Trial {trial_num}...")
            trial_file_path = os.path.join(BASE_RESULTS_DIR, "unstructured", f"article_{article_num}", f"trial_{trial_num}.md")
            dora_article_path = os.path.join("extended_cognisim_framework_clean_repo/cognisim_v20/assets", f"dora_article_{article_num}.txt") # Path to DORA article text
            
            if not os.path.exists(trial_file_path):
                print(f"  Unstructured: Checking trial_file_path: {trial_file_path}")
                print(f"  Unstructured: Missing file for Article {article_num}, Trial {trial_num}. Skipping.")
                continue
            
            with open(trial_file_path, 'r', encoding='utf-8') as f:
                test_plan_content = f.read()

            # --- Calculate Metrics for Unstructured Trial ---
            metrics = calculate_unstructured_metrics(test_plan_content, dora_article_path) # Pass DORA article path
            unstructured_article_results.append(metrics)
        analysis_data["unstructured_results"][f"article_{article_num}"] = unstructured_article_results

    # --- Perform Comparative Analysis and Generate Summary ---
    perform_comparative_analysis(analysis_data)
    generate_thesis_summary(analysis_data)

    # Save the full analysis data
    with open(os.path.join(BASE_RESULTS_DIR, "thesis_metrics_analysis.json"), 'w', encoding='utf-8') as f:
        json.dump(analysis_data, f, indent=2)
    print(f"Full analysis saved to: {os.path.join(BASE_RESULTS_DIR, 'thesis_metrics_analysis.json')}")

    print("\nAnalysis complete. Check thesis_metrics_analysis.json and generated plots.")

def calculate_structured_metrics(log_content, final_test_plan_content, sprint_test_plans, trial_dir, dora_article_path):
    """Calculates metrics for a single structured trial."""
    metrics = {}

    # Metric 1: Requirement Coverage Rate
    all_criteria = get_requirements_from_dora_article(dora_article_path) # Changed to use DORA article
    total_score = 0
    for i, criterion in enumerate(all_criteria):
        print(f"    - Evaluating structured coverage for requirement {i+1}/{len(all_criteria)}...")
        score = evaluate_coverage_with_llm(criterion, final_test_plan_content)
        total_score += score
    metrics['requirement_coverage_rate'] = (total_score / (len(all_criteria) * 2) * 100) if all_criteria else 0
    metrics['compliance_gap_count_final'] = (len(all_criteria) * 2) - total_score

    

    # Metric 3: Generative Verbosity
    metrics['generative_verbosity'] = get_word_count(final_test_plan_content) # Only final plan for this metric

    # Metric 4: Feedback Integration Rate
    total_possible_feedback_score = 0
    actual_feedback_score = 0
    for i in range(1, len(sprint_test_plans)): # Iterate from sprint 2 to 3
        prev_sprint_num = i
        curr_sprint_plan_path = sprint_test_plans[i] # Current sprint's test plan
        feedback_md_path = os.path.join(trial_dir, "artifacts", f"product_owner_feedback_sprint_{prev_sprint_num}.md")

        feedback_points = get_feedback_points(feedback_md_path)
        if feedback_points and os.path.exists(curr_sprint_plan_path):
            with open(curr_sprint_plan_path, 'r', encoding='utf-8') as f:
                curr_sprint_plan_content = f.read()
            
            for j, point in enumerate(feedback_points):
                print(f"    - Evaluating feedback integration for point {j+1}/{len(feedback_points)}...")
                score = evaluate_feedback_integration_with_llm(point, curr_sprint_plan_content)
                actual_feedback_score += score
                total_possible_feedback_score += 2 # Each point can get a max score of 2
    
    metrics['feedback_integration_rate'] = (actual_feedback_score / total_possible_feedback_score * 100) if total_possible_feedback_score > 0 else 0

    

    # Metric 6: Compliance Coverage Trend (for plotting)
    metrics['compliance_coverage_trend_data'] = []
    for s_idx, sprint_plan_path in enumerate(sprint_test_plans):
        if os.path.exists(sprint_plan_path):
            with open(sprint_plan_path, 'r', encoding='utf-8') as f:
                sprint_plan_content = f.read()
            
            # Calculate compliance coverage for each sprint plan using LLM evaluation
            sprint_total_score = 0
            for i, criterion in enumerate(all_criteria):
                print(f"      - Evaluating coverage trend for sprint {s_idx+1}, requirement {i+1}/{len(all_criteria)}...")
                score = evaluate_coverage_with_llm(criterion, sprint_plan_content)
                sprint_total_score += score
            
            # Calculate coverage rate as a percentage
            coverage_rate = (sprint_total_score / (len(all_criteria) * 2) * 100) if all_criteria else 0
            metrics['compliance_coverage_trend_data'].append(coverage_rate)
        else:
            metrics['compliance_coverage_trend_data'].append(None) # Handle missing sprint plans

    return metrics

def calculate_unstructured_metrics(test_plan_content, dora_article_path):
    """Calculates metrics for a single unstructured trial."""
    metrics = {}

    # Metric 1: Requirement Coverage Rate
    all_requirements = get_requirements_from_dora_article(dora_article_path) # Use new function
    total_score = 0
    for i, requirement in enumerate(all_requirements):
        print(f"    - Evaluating unstructured coverage for requirement {i+1}/{len(all_requirements)}...")
        score = evaluate_coverage_with_llm(requirement, test_plan_content)
        total_score += score
    metrics['requirement_coverage_rate'] = (total_score / (len(all_requirements) * 2) * 100) if all_requirements else 0
    metrics['compliance_gap_count_final'] = (len(all_requirements) * 2) - total_score

    # Metric 3: Generative Verbosity
    metrics['generative_verbosity'] = get_word_count(test_plan_content)

    metrics['feedback_integration_rate'] = None # Not applicable
    metrics['compliance_coverage_trend_data'] = None # Not applicable

    return metrics

def perform_comparative_analysis(analysis_data):
    """Performs statistical comparison for metrics 1-3."""
    comparative_results = {}

    for article_num in ARTICLES_TO_ANALYZE:
        structured_results = analysis_data["structured_results"].get(f"article_{article_num}", [])
        unstructured_results = analysis_data["unstructured_results"].get(f"article_{article_num}", [])

        if not structured_results or not unstructured_results:
            print(f"Skipping comparative analysis for Article {article_num} due to insufficient data.")
            continue

        # Extract data for comparison
        structured_coverage = [m['requirement_coverage_rate'] for m in structured_results if m['requirement_coverage_rate'] is not None]
        unstructured_coverage = [m['requirement_coverage_rate'] for m in unstructured_results if m['requirement_coverage_rate'] is not None]

        

        structured_verbosity = [m['generative_verbosity'] for m in structured_results if m['generative_verbosity'] is not None]
        unstructured_verbosity = [m['generative_verbosity'] for m in unstructured_results if m['generative_verbosity'] is not None]

        article_comparisons = {}

        # Metric 1: Requirement Coverage Rate
        if structured_coverage and unstructured_coverage:
            mean_s = np.mean(structured_coverage)
            std_s = np.std(structured_coverage)
            mean_u = np.mean(unstructured_coverage)
            std_u = np.std(unstructured_coverage)
            
            # Mann-Whitney U Test
            u_stat, p_value = stats.mannwhitneyu(structured_coverage, unstructured_coverage, alternative='two-sided')
            
            # Cohen's d (Effect Size) - pooled standard deviation
            pooled_std = np.sqrt(((len(structured_coverage) - 1) * std_s**2 + (len(unstructured_coverage) - 1) * std_u**2) / (len(structured_coverage) + len(unstructured_coverage) - 2))
            cohens_d = (mean_s - mean_u) / pooled_std if pooled_std != 0 else 0

            article_comparisons['requirement_coverage_rate'] = {
                "structured_mean": round(mean_s, 2),
                "structured_std": round(std_s, 2),
                "unstructured_mean": round(mean_u, 2),
                "unstructured_std": round(std_u, 2),
                "mann_whitney_u_p_value": round(p_value, 4),
                "cohens_d": round(cohens_d, 2),
                "statistical_significance": "Yes" if p_value < 0.05 else "No"
            }
        
        

        # Metric 3: Generative Verbosity
        if structured_verbosity and unstructured_verbosity:
            mean_s = np.mean(structured_verbosity)
            std_s = np.std(structured_verbosity)
            mean_u = np.mean(unstructured_verbosity)
            std_u = np.std(unstructured_verbosity)

            u_stat, p_value = stats.mannwhitneyu(structured_verbosity, unstructured_verbosity, alternative='two-sided')
            pooled_std = np.sqrt(((len(structured_verbosity) - 1) * std_s**2 + (len(unstructured_verbosity) - 1) * std_u**2) / (len(structured_verbosity) + len(unstructured_verbosity) - 2))
            cohens_d = (mean_s - mean_u) / pooled_std if pooled_std != 0 else 0

            article_comparisons['generative_verbosity'] = {
                "structured_mean": round(mean_s, 2),
                "structured_std": round(std_s, 2),
                "unstructured_mean": round(mean_u, 2),
                "unstructured_std": round(std_u, 2),
                "mann_whitney_u_p_value": round(p_value, 4),
                "cohens_d": round(cohens_d, 2),
                "statistical_significance": "Yes" if p_value < 0.05 else "No"
            }

        comparative_results[f"article_{article_num}"] = article_comparisons
    analysis_data["comparative_analysis"] = comparative_results

def plot_compliance_coverage_trend(analysis_data):
    """Generates and saves line graphs for Compliance Coverage Trend."""
    plot_dir = os.path.join(BASE_RESULTS_DIR, "plots")
    os.makedirs(plot_dir, exist_ok=True)

    for article_num in ARTICLES_TO_ANALYZE:
        structured_results = analysis_data["structured_results"].get(f"article_{article_num}", [])
        
        if not structured_results:
            print(f"No structured results for Article {article_num} to plot compliance coverage trend.")
            continue

        plt.figure(figsize=(10, 6))
        sprints = [1, 2, 3] # Assuming 3 sprints for now

        for trial_idx, trial_data in enumerate(structured_results):
            coverage_data = trial_data.get('compliance_coverage_trend_data')
            if coverage_data:
                # Filter out None values if any sprint plan was missing
                valid_sprints = [sprints[i] for i, val in enumerate(coverage_data) if val is not None]
                valid_coverage = [val for val in coverage_data if val is not None]
                if valid_coverage:
                    plt.plot(valid_sprints, valid_coverage, marker='o', linestyle='-', label=f'Trial {trial_idx + 1}')

        plt.title(f'Compliance Coverage Trend Across Sprints for Article {article_num}')
        plt.xlabel('Sprint Number')
        plt.ylabel('Compliance Coverage Rate (%)')
        plt.xticks(sprints)
        plt.ylim(0, 100) # Set Y-axis from 0 to 100 for percentage
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plot_file = os.path.join(plot_dir, f"compliance_coverage_trend_article_{article_num}.png")
        plt.savefig(plot_file)
        plt.close()
        print(f"Generated plot: {plot_file}")

def generate_thesis_summary(analysis_data):
    """Generates a thesis-ready summary report."""
    summary_dir = BASE_RESULTS_DIR
    summary_file_path = os.path.join(summary_dir, "thesis_summary_report.md")

    summary_content = ""
    summary_content += "# Extended CogniSim Framework - DORA Compliance Simulation Analysis\n\n"
    summary_content += "## Executive Summary\n"
    summary_content += f"Analysis conducted on {analysis_data['analysis_timestamp']}\n"
    summary_content += f"Articles analyzed: {', '.join(map(str, analysis_data['articles_analyzed']))}\n\n"
    summary_content += "## Key Findings (Thesis Metrics)\n\n"
    summary_content += "### Comparative Analysis (Structured vs. Unstructured)\n"

    for article_num in ARTICLES_TO_ANALYZE:
        article_comp = analysis_data['comparative_analysis'].get(f"article_{article_num}")
        if article_comp:
            summary_content += f"\n### Article {article_num} Comparative Results\n"
            for metric_name, data in article_comp.items():
                summary_content += f"- **{metric_name.replace('_', ' ').title()}:**\n"
                if 'structured_mean' in data:
                    summary_content += f"  - Structured Mean: {data['structured_mean']}"
                    if 'structured_std' in data: summary_content += f" (Std: {data['structured_std']})\n"
                    summary_content += f"  - Unstructured Mean: {data['unstructured_mean']}"
                    if 'unstructured_std' in data: summary_content += f" (Std: {data['unstructured_std']})\n"
                    summary_content += f"  - Mann-Whitney U p-value: {data['mann_whitney_u_p_value']}\n"
                    summary_content += f"  - Cohen's d: {data['cohens_d']}\n"
                    summary_content += f"  - Statistically Significant Difference: {'Yes' if data['mann_whitney_u_p_value'] < 0.05 else 'No'}\n"
                else:
                    summary_content += f"  - Structured Mean: {data['structured_mean']}"
                    if 'structured_std' in data: summary_content += f" (Std: {data['structured_std']})\n"

    summary_content += "\n### Internal Analysis (Agile Fidelity of Structured Approach)\n"
    for article_num in ARTICLES_TO_ANALYZE:
        structured_results = analysis_data["structured_results"].get(f"article_{article_num}", [])
        if structured_results:
            summary_content += f"\n#### Article {article_num} Internal Metrics\n"
            feedback_rates = [m['feedback_integration_rate'] for m in structured_results if m['feedback_integration_rate'] is not None]
            

            if feedback_rates:
                summary_content += f"- **Average Feedback Integration Rate:** {round(np.mean(feedback_rates), 2)}% (Std: {round(np.std(feedback_rates), 2)})\n"
            
            
            # Compliance Coverage Trend Plot reference
            summary_content += f"- **Compliance Coverage Trend:** See `plots/compliance_coverage_trend_article_{article_num}.png` for visual trend across sprints.\n"

    with open(summary_file_path, 'w', encoding='utf-8') as f:
        f.write(summary_content)
    print(f"Thesis summary saved to: {summary_file_path}")

    # Generate plots after summary
    plot_compliance_coverage_trend(analysis_data)


if __name__ == "__main__":
    analyze_results()
