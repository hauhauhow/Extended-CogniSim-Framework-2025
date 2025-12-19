**# Extended CogniSim Framework for DORA Compliance**

The Extended CogniSim Framework applies multi-agent systems to regulatory compliance in banking, specifically targeting the EU's Digital Operational Resilience Act (DORA). The framework extends the original CogniSim software engineering tool to handle financial regulatory compliance workflows.

The system simulates Agile Scrum teams using AI agents powered by Large Language Models (ChatGPT-3.5 and 4.0) to generate compliance test plans for DORA Articles 24 and 25. Manager Agents (Product Owner, Scrum Master) and Executor Agents (Developers) work through iterative sprints, incorporating feedback and refining deliverables. The architecture operates through five phases: user invocation, regulatory requirement ingestion, sprint development, final synthesis, and post-simulation analysis.

The repository includes all agent configurations, simulation logic written in Python using LangChain, and evaluation metrics for reproducibility.

## Quickstart

### Prerequisites

Ensure you have Python 3.8 or higher installed.

### Installation

1. Clone the repository:
```bash
   git clone https://github.com/hauhauhow/Extended-CogniSim-Framework-2025
   cd Extended-CogniSim-Framework-2025
```

2. Install dependencies:
```bash
   pip install -r requirements.txt
```

3. Set up your OpenAI API key:
```bash
   export OPENAI_API_KEY="YOUR_API_KEY"
```

### Running the Simulation

Execute the simulation for DORA Article 24 or 25:
```bash
python cognisim_v20/main.py
```

When prompted, select the target DORA article (24 or 25) to begin the simulation.

### Analyzing Results

After simulation completion, analyze the generated artifacts:
```bash
python analyze_results.py
```

This generates comparative metrics including requirement coverage rates, feedback integration rates, and compliance coverage trends.

