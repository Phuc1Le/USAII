import logging

from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, ToolCallPart, UserPromptPart, TextPart
from pydantic_ai.usage import UsageLimits
from pydantic_ai.exceptions import UsageLimitExceeded
from app import tools
from app.config import GEMINI_MODEL
from app.schemas import ChatMessage, WebSearchResult
from dataclasses import dataclass
from app.schemas import DecisionSearchResult, FocusedStepContext, MilestoneContext
MODEL = f"google:{GEMINI_MODEL}"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@dataclass
class ChatDeps:
    project_id: str

def to_pydantic_history(history: list[ChatMessage]) -> list[ModelMessage]:
    messages: list[ModelMessage] = []
    for m in history:
        if m.role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=m.content)]))
        else:
            messages.append(ModelResponse(parts=[TextPart(content=m.content)]))  
    return messages

def build_agent(system_instruction: str) -> Agent:
    agent = Agent(MODEL, system_prompt=system_instruction)
    
    @agent.tool_plain
    async def web_search(query: str, num_results: int = 5) -> WebSearchResult:
        """Search the web for information not present in the project context or conversation."""
        return await tools.web_search(query, num_results)

    @agent.tool
    async def retrieve_milestones(ctx: RunContext[ChatDeps]) -> list[MilestoneContext]:
        """Get this project's milestones and whether each has been achieved."""
        return await tools.retrieve_milestones(ctx.deps.project_id)

    @agent.tool
    async def query_decisions(ctx: RunContext[ChatDeps], query: str) -> DecisionSearchResult:
        """Search past project decisions semantically related to query."""
        return await tools.query_decisions(ctx.deps.project_id, query)

    @agent.tool
    async def retrieve_step(ctx: RunContext[ChatDeps], step_id: str) -> FocusedStepContext:
        """Get details and tasks for a specific project step by id."""
        return await tools.retrieve_step(step_id)
    return agent

async def run_chat(agent: Agent, prompt: str, deps: ChatDeps, message_history: list[ModelMessage]) -> str:
    try:
        result = await agent.run(
            prompt,
            deps=deps,
            message_history=message_history,
            usage_limits=UsageLimits(tool_calls_limit=6),
        )
        tool_calls = [
            part.tool_name
            for m in result.all_messages()
            for part in m.parts
            if isinstance(part, ToolCallPart)
        ]
        if tool_calls:
            logger.info("chat turn for project %s used tools: %s", deps.project_id, tool_calls)
        else:
            logger.info("chat turn for project %s answered with no tool calls", deps.project_id)
        return result.output
    except UsageLimitExceeded:
        logger.warning("chat turn for project %s hit the tool_calls_limit cap", deps.project_id)
        return "I started looking into this but hit a processing limit before I could finish — could you rephrase or narrow the question?"
