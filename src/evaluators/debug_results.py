"""
Debug script: retrieve evaluation results and verify parsing.

Uses the eval ID and run ID from the last evaluation run to avoid
re-running the evaluation. Tests the same parsing logic as evaluate_agent.py.
"""

import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

load_dotenv()

endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]

project_client = AIProjectClient(
    endpoint=endpoint,
    credential=DefaultAzureCredential(),
)
client = project_client.get_openai_client()

# IDs from the last successful run (from evaluation_results.txt)
EVAL_ID = "eval_5463e42ab9804338990a17ef42e5389f"
RUN_ID  = "evalrun_54d04026cad241bdb731e6a8683aae1a"

# ---- Retrieve the run object ----
run = client.evals.runs.retrieve(run_id=RUN_ID, eval_id=EVAL_ID)
print(f"Status: {run.status}")
print(f"Report URL: {run.report_url}")
print(f"Result counts: {run.result_counts}")
print(f"Per-criteria: {run.per_testing_criteria_results}")

# ---- Retrieve output items and parse scores ----
output_items = list(
    client.evals.runs.output_items.list(run_id=RUN_ID, eval_id=EVAL_ID)
)

errored_items = [item for item in output_items if getattr(item, "status", None) == "error"]
scored_items  = [item for item in output_items if getattr(item, "status", None) != "error"]

scores = {"intent_resolution": [], "relevance": [], "groundedness": []}

for item in scored_items:
    results = getattr(item, "results", None) or []
    for result in results:
        if result.name in scores and hasattr(result, "score") and result.score is not None:
            scores[result.name].append(result.score)

# ---- Display results ----
print(f"\nTotal items: {len(output_items)}, Errored: {len(errored_items)}, Scored: {len(scored_items)}")

metric_labels = {
    "intent_resolution": "Intent Resolution",
    "relevance":         "Relevance        ",
    "groundedness":      "Groundedness     ",
}

print("\nAverage Scores (1-5 scale, threshold: 3)")
for key, label in metric_labels.items():
    values = scores[key]
    if values:
        avg  = sum(values) / len(values)
        rate = sum(1 for v in values if v >= 3) / len(values) * 100
        print(f"  {label}: {avg:.2f} (n={len(values)})")
    else:
        print(f"  {label}: NO SCORES")

print("\nPass Rates (score >= 3)")
for key, label in metric_labels.items():
    values = scores[key]
    if values:
        rate = sum(1 for v in values if v >= 3) / len(values) * 100
        print(f"  {label}: {rate:.1f}%")
