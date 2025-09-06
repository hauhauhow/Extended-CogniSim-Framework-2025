import os
import json
import logging
import time
from openai import OpenAI
from dotenv import load_dotenv
import math

# --- CONFIGURATION ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

RESULTS_DIR = "extended_cognisim_framework_clean_repo/cognisim_v20/results_v8"
ARTIFACTS_DIR = os.path.join(RESULTS_DIR, "artifacts")
ARTICLE_NUM = 24
MAX_SPRINTS = 3

# --- AGENT PERSONAS & PROMPTS ---
PERSONAS = {
    "RegulatoryExtractor": {
        "system": "You are a meticulous Regulatory Analyst. Your sole purpose is to extract every single discrete, numbered requirement from a legal document and return it as a JSON list of strings.",
        "prompt": "Extract all numbered requirements from DORA Article {article_num} and return them as a JSON list of strings.\n\n**DORA Article {article_num} Text:**\n{dora_article_text}"
    },
    "JSON_Parser": {
        "system": "You are a data parsing expert. Your only job is to take a string that may contain messy or broken JSON, find the valid JSON list of objects or strings inside it, and return ONLY that list, perfectly formatted. Do not include any explanatory text or markdown.",
        "prompt": "Find the valid JSON list in the following string and return only the list:\n\n{messy_json_string}"
    },
    "BacklogFormatter": {
        "system": "You are a Product Owner. Your task is to convert a list of raw requirements into a product backlog of user stories. For each and every requirement in the input list, you must create one corresponding user story.",
        "prompt": "Convert the following list of requirements into a JSON array of user story objects. Each user story must have a unique ID, a title, and a description.\n\n**Requirements:**\n{requirements}"
    },
    "Dev_Implementer": {
        "system": "You are a Senior DORA Compliance Officer and Implementation Specialist at a large bank. You are a world-class expert in translating dense legal requirements into actionable, auditable, and technically sound implementation plans.",
        "prompt": "\n        For the given user story, you must generate a complete and actionable implementation plan.\n        Your plan MUST include the following sections, filled with specific, actionable detail relevant to a large bank in 2025:\n\n        **IMPLEMENTATION REQUIREMENTS:**\n        - Specific execution procedures and tools\n        - Testing frequencies and schedules\n        - Resource allocation and role definitions\n        - Measurable KPIs and success criteria\n        - Documentation and audit trail processes\n\n        **QUALITY STANDARDS:**\n        - Immediately actionable guidance (no placeholder text)\n        - Industry-standard tools and vendors\n        - Concrete timelines and responsibilities\n        - Risk-based prioritization frameworks\n        - Compliance mapping to specific article sections\n\n        **CRITICAL INSTRUCTION FOR ITERATIVE IMPROVEMENT:**\n        You MUST incorporate the following feedback, which was provided by the Product Owner on the previous sprint's work, to ensure that this new implementation plan is of higher quality and avoids the same mistakes.\n\n        **Previous Sprint's Feedback:**\n        {feedback}\n\n        **User Story:**\n        {user_story}\n        "
    },
    "Dev_Synthesizer": {
        "system": "You are a senior technical writer. Your job is to synthesize pre-written, high-quality documents into a single, cohesive plan.",
        "prompt": "Synthesize these high-quality, pre-written draft sections into a single, cohesive `final_test_plan_sprint_{sprint_num}.md`. Do not add new content; your only job is to merge and format.\n\n**Drafts:**\n{drafts}"
    },
    "PO_Reviewer": {
        "system": "You are the Product Owner in a Sprint Review. Your task is to provide specific, actionable feedback on the team's work.",
        "prompt": "Review the following Test Plan. Provide your feedback as a markdown document.\n\n**Test Plan:**\n{sprint_plan}"
    },
    "Final_Synthesizer": {
        "system": "You are a senior technical writer responsible for creating the final cumulative compliance document.",
        "prompt": "Synthesize the following sprint plans into a single, cohesive `Final_Cumulative_Test_Plan.md`.\n\n{sprint_plans}"
    }
}

# --- CORE FUNCTIONS (VERIFIED) ---
def interact_with_llm(persona: str, is_json_output: bool = False, **kwargs) -> str:
    logger = logging.getLogger(persona)
    logger.info(f"Interacting with LLM as persona: {persona}...")
    
    system_content = PERSONAS[persona]["system"]
    prompt = PERSONAS[persona]["prompt"].format(**kwargs)
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    try:
        response_format = {"type": "json_object"} if is_json_output else {"type": "text"}
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt},
            ],
            model="gpt-4-1106-preview",
            temperature=0.2,
        )
        response_content = chat_completion.choices[0].message.content
        logger.info("Successfully received response from LLM.")
        return response_content
    except Exception as e:
        logger.getLogger(persona).error(f"An unexpected API error occurred: {e}")
        return '{}' if is_json_output else ''

def save_artifact(filename: str, content: str):
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    path = os.path.join(ARTIFACTS_DIR, filename)
    try:
        with open(path, 'w') as f:
            f.write(content)
        logging.info(f"Successfully saved artifact to {path}")
    except Exception as e:
        logging.error(f"Failed to save artifact to {path}: {e}")

# --- MAIN LOGIC ---
def verifiable_ingestion(dora_article_text: str):
    print("\n--- Phase 1: Verifiable Ingestion ---")
    
    requirements_str = interact_with_llm("RegulatoryExtractor", is_json_output=True, dora_article_text=dora_article_text, article_num=ARTICLE_NUM)
    
    try:
        requirements = json.loads(requirements_str)
        if isinstance(requirements, dict):
            requirements = next(iter(requirements.values()))
    except (json.JSONDecodeError, StopIteration):
        print("Initial parsing failed. Attempting self-healing with JSON_Parser...")
        requirements_str = interact_with_llm("JSON_Parser", is_json_output=True, messy_json_string=requirements_str)
        try:
            requirements = json.loads(requirements_str)
            if isinstance(requirements, dict):
                requirements = next(iter(requirements.values()))
        except (json.JSONDecodeError, StopIteration):
            print("CRITICAL ERROR: Failed to parse requirements from LLM after self-healing.")
            return None

    print(f"--- Verification: Programmatically counted {len(requirements)} requirements extracted from the source text. ---")
    
    backlog_str = interact_with_llm("BacklogFormatter", is_json_output=True, requirements=json.dumps(requirements, indent=2))
    try:
        product_backlog = json.loads(backlog_str)
        if isinstance(product_backlog, dict):
            product_backlog = next(iter(product_backlog.values()))
    except (json.JSONDecodeError, StopIteration):
        print("Backlog parsing failed. Attempting self-healing with JSON_Parser...")
        backlog_str = interact_with_llm("JSON_Parser", is_json_output=True, messy_json_string=backlog_str)
        try:
            product_backlog = json.loads(backlog_str)
            if isinstance(product_backlog, dict):
                product_backlog = next(iter(product_backlog.values()))
        except (json.JSONDecodeError, StopIteration):
            print("CRITICAL ERROR: Failed to parse product backlog from LLM after self-healing.")
            return None

    return product_backlog

def main():
    logging.info(f"--- Starting CogniSim v20 for DORA Article {ARTICLE_NUM} ---")
    
    with open(f"extended_cognisim_framework_clean_repo/assets/dora_article_{ARTICLE_NUM}.txt", "r") as f:
        dora_article_text = f.read()

    product_backlog = verifiable_ingestion(dora_article_text)
    
    if not product_backlog:
        print("Aborting simulation due to empty product backlog.")
        return

    print(f"Successfully created a backlog with {len(product_backlog)} user stories.")
    save_artifact("product_backlog.json", json.dumps(product_backlog, indent=2))
    
    sprint_plans = []
    feedback = "No feedback from previous sprint."
    num_stories = len(product_backlog)
    stories_per_sprint = math.ceil(num_stories / MAX_SPRINTS)

    for i in range(MAX_SPRINTS):
        sprint_num = i + 1
        print(f"\n--- Starting Sprint {sprint_num} ---")
        
        start_index = i * stories_per_sprint
        end_index = start_index + stories_per_sprint
        sprint_backlog = product_backlog[start_index:end_index]

        if not sprint_backlog:
            continue

        drafts = []
        for user_story in sprint_backlog:
            draft = interact_with_llm("Dev_Implementer", user_story=json.dumps(user_story, indent=2), feedback=feedback)
            drafts.append(draft)
        
        sprint_plan = interact_with_llm("Dev_Synthesizer", drafts="\n\n---\n\n".join(drafts), sprint_num=sprint_num)
        save_artifact(f"final_test_plan_sprint_{sprint_num}.md", sprint_plan)
        sprint_plans.append(sprint_plan)

        feedback = interact_with_llm("PO_Reviewer", sprint_plan=sprint_plan)
        save_artifact(f"product_owner_feedback_sprint_{sprint_num}.md", feedback)

    print("\n--- Phase 3: Final Synthesis ---")
    final_plan = interact_with_llm("Final_Synthesizer", sprint_plans="\n\n---\n\n".join(sprint_plans))
    save_artifact("Final_Cumulative_Test_Plan.md", final_plan)
    
    print(f"\nSimulation complete. All artifacts saved in {ARTIFACTS_DIR}")

if __name__ == "__main__":
    main()
