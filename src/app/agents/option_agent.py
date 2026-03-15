from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from importlib.resources import files

from src.app.agents.tools.option_tools import (
    option_max_pain_value,
    stock_option_liquidity,
    get_options_descriptive,
    option_chain_top_oi,
    option_chain_filtered,
    option_chain_raw,
)
from src.app.config.config import DATA_ANALYSIS_MODEL

model = init_chat_model(DATA_ANALYSIS_MODEL)

options_analysis_agent = create_agent(
    model,
    tools=[
        get_options_descriptive,
        option_max_pain_value,
        stock_option_liquidity,
        option_chain_top_oi,
        option_chain_filtered,
        option_chain_raw,
    ],
    system_prompt=(
        files("src.app.agents.prompts")
        .joinpath("options_analysis_agent_prompt.txt")
        .read_text(encoding="utf-8")
    ),
)


if __name__ == "__main__":
    query = "Make analysis of unity stock, ticker U. " \
    "I am now in position with 200 stocks with avr price 24.5. Current price is 19." \
    "How should i manage position: just hold, sell call, sell stocks and sell 2 put or another option?"

    query = "Analyze how options drives USAR prices. " \
    "i currentrly own 200 shares with average price 18. should i sell stock and sell put, or sell short-term call?" \
    " . or wait near 20 and then sell call? or what should i do?"

    query = "Analyze CF. Near IV is higher than IV in few month. Construct most profitable calendar spread for budget under 2k$ considering price will drop."

    for step in options_analysis_agent.stream(
        {"messages": [{"role": "user", "content": query}]}
    ):
        for update in step.values():
            for message in update.get("messages", []):
                message.pretty_print()
