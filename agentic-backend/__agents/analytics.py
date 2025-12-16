from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from agents import Agent
from app.services.unified_mcp_manager import unified_mcp_manager
from app.core.config import settings


# Model config (Gemini or OpenAI)
if settings.api_key:

    model = settings.model


async def create_analytics_agent(tenant_id: UUID, db: AsyncSession) -> Agent:
    """
    Create analytics agent with Global MCP server (Port 8001).

    Args:
        tenant_id: UUID of the tenant
        db: Database session (AsyncSession)

    Returns:
        Agent with Global MCP server (port 8001)
    """
    # Get Global MCP from unified manager (Port 8001)
    global_mcp = await unified_mcp_manager.get_global_mcp(tenant_id, db)
    mcp_servers = [global_mcp] if global_mcp else []

    return Agent(
        name="Analytics Agent",
        model=model,
        mcp_servers=mcp_servers,
        instructions="""You are a helpful chatbot specialized in analytics and reporting tasks.
Help users with business performance reports, sales trend analysis, customer behavior insights,
KPI tracking, and data visualization recommendations.""",
    )
