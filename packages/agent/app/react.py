import logging

from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, ToolCallPart, UserPromptPart, TextPart
from pydantic_ai.usage import UsageLimits
from pydantic_ai.exceptions import ModelHTTPError, UsageLimitExceeded
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
    except ModelHTTPError as exc:
        # By the time this runs, /agent/chat has already sent HTTP 200 and started
        # the SSE body — there is no status code left to fail with. Letting the
        # exception escape aborts the response mid-stream, which reaches the browser
        # as a bare "network error" with the real reason only in the agent's log.
        # Returning a sentence keeps the stream well-formed and puts the reason
        # where the person asking can actually read it.
        logger.warning(
            "chat turn for project %s failed: model returned %s",
            deps.project_id, exc.status_code,
        )
        if exc.status_code == 429:
            return (
                "The AI service is out of quota right now, so I could not answer this one. "
                "Free-tier keys reset daily — try again later, or switch to a key with billing enabled."
            )
        if exc.status_code >= 500:
            return (
                "The AI service is temporarily unavailable — it is usually a short spike in demand. "
                "Please try that again in a moment."
            )
        return f"The AI service refused that request ({exc.status_code}). The agent log has the details."
    except Exception:
        # Same reasoning as above: whatever went wrong, the stream still has to end
        # in a readable way rather than a severed connection.
        logger.exception("chat turn for project %s failed unexpectedly", deps.project_id)
        return "Something went wrong while answering that. The agent log has the details."
