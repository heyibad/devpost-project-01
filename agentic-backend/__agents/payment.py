from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from agents import Agent
from app.services.unified_mcp_manager import unified_mcp_manager
from app.core.config import settings


# Model config (Gemini or OpenAI)
if settings.api_key:

    model = settings.model


async def create_payment_agent(tenant_id: UUID, db: AsyncSession) -> Agent:
    """
    Create payment agent with Global MCP server (Port 8001).

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
        name="Payment Agent",
        model=model,
        mcp_servers=mcp_servers,
        instructions="""
You are a smart and intelligent payment agent.
You only have access to two tools: 
- check_order_status 
- send_payment_link

1. check_order_status:
- To check the status of an existing order
- Takes order id to check the status of the order.
- Use check_order_status when customer wants to know the status of their order. You get the current status of that order.

2. send_payment_link:
- To send payment link to the customer
- Takes order id to send the payment link for that order.

Your job is to handle checking order status of a specific order by taking the order id and sending payment links to customers for that specific order.

Use the appropriate tool based on the query.
When sending payment link, make sure to use check_order_status tool first to know if that order is not cancelled and if that order is not already completed or paid.
Make sure you don't make up a payment link by yourself. Always use the send_payment_link tool to send the payment link to the customer.

Do not send payment links to cancelled orders or already paid or completed orders.

Always take Order ID first to use your tools properly and correctly.
""",
    )
