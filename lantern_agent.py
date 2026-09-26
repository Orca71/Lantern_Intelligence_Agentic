import anthropic
from dotenv import load_dotenv
from lantern_tools import list_companies, get_metric, COMPANIES, SQL_FILES

load_dotenv()
client = anthropic.Anthropic()

MAX_STEPS = 8

SYSTEM_PROMPT = (
    "You are Lantern, a financial analyst for small service businesses. "
    "Answer only with figures returned by tools; never estimate or invent numbers. "
    "Fetch only the metrics the question needs. "
    "If the data can't answer the question, say so plainly. "
    "Be concise and end with one priority action when relevant. "
)

TOOL_FUNCTION = {"list_companies": list_companies , "get_metric": get_metric}

tools = [
    {
        "name": "list_companies",
        "description": "List the companies available for analysis.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_metric",
        "description": (
            "Run one financial metric query for one company. Returns rows computed by SQL. "
            "Metric: net_profit_margin, monthly_revenue_trend, days_sales_outstanding, client_concentration, burn_rate_runaway, expense_breakdown, "
            "revenue_per_employee, client_churn_rate."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "company": {"type": "string", "enum": list(COMPANIES)},
                "metric": {"type": "string", "enum": list(SQL_FILES)},
            },
            "required": ["company", "metric"],
        },
    },
]

#Confirming names in tools match with actual names

assert set(TOOL_FUNCTION) == {t["name"] for t in tools}, "tool names don't match"

def call_model(messages):
    return client.messages.create(
        model="claude-sonnet-5",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        tools=tools,
        messages=messages,
    )

def run_agent(question):
    messages = [{"role": "user", "content": question}]

    for step in range(1, MAX_STEPS + 1):
        response = call_model(messages)
        print(f"[step {step}] tokens in: {response.usage.input_tokens},out: {response.usage.output_tokens}")
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            return "\n".join(b.text for b in response.content if b.type == "text")

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                try:
                    result = TOOL_FUNCTION[block.name](**block.input)
                    is_error = False
                except Exception as e:
                    result = f"Error: {e}"
                    is_error = True
                print(f"[step {step}] {block.name}({block.input})")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result),
                    "is_error": is_error,
                })
        messages.append({"role": "user", "content": tool_results})
    return "Stopped: hit the step limit."

if __name__ == "__main__":
    print(run_agent("How is Vorto Consulting Group doing?"))
