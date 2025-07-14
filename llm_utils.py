from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import re

model_id = "microsoft/phi-3-mini-4k-instruct"

print("Loading LLM...")
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
)


def generate_issue_title(user_input: str) -> str:
    """
    Uses few-shot prompt to generate a concise Jira issue title.
    """

    prompt = (
        "Convert the following user request into a concise and professional Jira issue title.\n"
        "Keep it under 12 words.\n\n"
        "Example 1:\n"
        "User: Create an issue for Grafana log monitoring\n"
        "Issue Title: Grafana log monitoring issue\n\n"
        "Example 2:\n"
        "User: File a task for fixing the broken login form on mobile\n"
        "Issue Title: Fix broken login form on mobile\n\n"
        "Example 3:\n"
        "User: Add a bug ticket to resolve API timeout when fetching user data\n"
        "Issue Title: Resolve API timeout fetching user data\n\n"
        "Example 4:\n"
        "User: Open a task in DEVOPS to upgrade dependencies\n"
        "Issue Title: Upgrade dependencies in DEVOPS\n\n"
        "Example 5:\n"
        "User: Create a Jira issue to improve dashboard responsiveness\n"
        "Issue Title: Improve dashboard responsiveness\n\n"
        f"User: {user_input}\n"
        "Issue Title:"
    )

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=20,
            temperature=0.7,
            top_k=50,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract just the generated title
    if "issue title:" in response.lower():
        response = response.lower().split("issue title:")[-1]
    
    title = response.strip().split("\n")[0]
    title = title.strip().capitalize()

    return title

def get_intent(user_input: str) -> str:
    """
    Uses LLM to classify the user's intent as 'Create Issue', 'Get Issue', or 'unknown'.
    """

    prompt = (
        "You are a Jira assistant. Classify the user's intent.\n"
        "Return exactly one of: Create Issue, Get Issue, or unknown.\n\n"

        "Example 1:\n"
        "User: Create a bug for the login crash\n"
        "Intent: Create Issue\n\n"

        "Example 2:\n"
        "User: Open a ticket to add monitoring to the server\n"
        "Intent: Create Issue\n\n"

        "Example 3:\n"
        "User: File a task for setting up Grafana dashboards\n"
        "Intent: Create Issue\n\n"

        "Example 4:\n"
        "User: Get all issues related to Grafana\n"
        "Intent: Get Issue\n\n"

        "Example 5:\n"
        "User: Fetch status of DEVOPS-102\n"
        "Intent: Get Issue\n\n"

        "Example 6:\n"
        "User: Check the ticket for broken signup\n"
        "Intent: Get Issue\n\n"

        f"User: {user_input}\n"
        "Intent:"
    )

    # Tokenize and generate
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=20,
            do_sample=False,
            temperature=0.0,
            pad_token_id=tokenizer.eos_token_id
        )

    decoded = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
    print(f"[DEBUG] LLM Output:\n{decoded}")

    # Reverse search for the last line that looks like "Intent: ..."
    intent_line = ""
    for line in reversed(decoded.splitlines()):
        if "intent:" in line.lower():
            intent_line = line
            break

    # Extract intent text from line
    if intent_line:
        match = re.search(r"intent:\s*(.*)", intent_line, re.IGNORECASE)
        if match:
            intent = match.group(1).strip().lower()
            if "create" in intent:
                return "Create Issue"
            elif "get" in intent:
                return "Get Issue"

    # Fallback to keyword-based detection
    lower_input = user_input.lower()
    if any(k in lower_input for k in ["get", "fetch", "check", "view", "see", "show"]):
        return "Get Issue"
    elif any(k in lower_input for k in ["create", "file", "open", "add", "submit"]):
        return "Create Issue"

    return "unknown"