import os
from dotenv import load_dotenv

from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from langchain_huggingface import HuggingFacePipeline
import torch  # Required when loading model with device_map

from confluence_tools import ConfluenceAPI

load_dotenv()

# --- Initialize Confluence API and tools ---
confluence_api = ConfluenceAPI()

@tool
def create_page(space_key: str, title: str, body: str) -> str:
    """Creates a Confluence page."""
    return confluence_api.create_page(space_key, title, body)

@tool
def list_pages(space_key: str, query: str = None) -> str:
    """Lists pages in a Confluence space (optionally filtered by query)."""
    return confluence_api.list_pages(space_key, query)

tools = [create_page, list_pages]

# --- Load local Phi-3 Mini (HuggingFace) ---
LOCAL_MODEL_PATH = "/content/phi-3-mini-4k-instruct"
tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(
    LOCAL_MODEL_PATH,
    device_map="auto",
    torch_dtype=torch.bfloat16,
    trust_remote_code=True
)
pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=512, return_full_text=False, use_cache=False)
llm = HuggingFacePipeline(pipeline=pipe)

# --- Prompt (ReAct style) ---
template = """
Answer the following questions as best you can. You have access to the following tools:

{tools}

To use a tool, please use:

Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (you can repeat Thought/Action/Action Input/Observation)

When you have a final answer only use:

Thought: I now have the final answer
Final Answer: <your answer>

Begin!

Question: {input}
{agent_scratchpad}
"""
prompt = PromptTemplate.from_template(template)

# --- Agent & Executor ---
agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

# --- Interactive CLI ---
if __name__ == "__main__":
    print("Welcome to the Confluence AI Assistant!")
    print("Example: Create a page 'Q3 Report' in space 'IT' with body 'Quarterly summary...'")
    print("Type 'exit' to quit.")

    while True:
        user_input = input("\nYour request: ")
        if user_input.lower() == "exit":
            break

        try:
            print("\n--- Agent Execution Stream ---")
            for step in agent_executor.stream({"input": user_input}):
                print(step, end="", flush=True)
            print("")  # newline after completion
        except KeyboardInterrupt:
            print("Generation interrupted by user.")
