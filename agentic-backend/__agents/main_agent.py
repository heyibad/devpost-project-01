from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from agents import Agent
from app.core.config import settings

# Import individual agent creators
from .accounts import create_accounts_agent
from .sales import create_sales_agent
from .marketing import create_marketing_agent
from .inventory import create_inventory_agent

# from .analytics import create_analytics_agent  # Commented out - not using for now


# Model config (Gemini or OpenAI)
if settings.api_key:

    model = settings.model


async def create_triage_agent(tenant_id: UUID, db: AsyncSession) -> Agent:
    """
    Create the main triage agent with all specialized agents.

    MCP Server Access:
    - Triage Agent: NO MCP servers (routing only)
    - Accounts Agent: Port 8002 (QuickBooks only, tenant-specific)
    - Sales Agent: Port 8001 (Global services)
    - Marketing Agent: Port 8001 (Global services)
    - Inventory Agent: Port 8001 (Global services)
    - Analytics Agent: DISABLED (commented out)

    Args:
        tenant_id: UUID of the tenant
        db: Database session (AsyncSession)

    Returns:
        Triage agent with handoffs to all specialized agents
    """
    import asyncio
    import time

    print(f"🤖 Creating Triage Agent for tenant {tenant_id}...")
    start_time = time.time()

    # PERFORMANCE: Create all specialized agents in parallel (not sequential!)
    accounts_task = create_accounts_agent(tenant_id, db)  # Port 8002 (QB only)
    sales_task = create_sales_agent(tenant_id, db)  # Port 8001
    marketing_task = create_marketing_agent(tenant_id, db)  # Port 8001
    inventory_task = create_inventory_agent(tenant_id, db)  # Port 8001
    # analytics_task = create_analytics_agent(tenant_id, db)  # Port 8001 

    # Wait for all agents to be created in parallel
    accounts, marketing, inventory = await asyncio.gather(
        accounts_task,
        # sales_task,
        marketing_task,
        inventory_task,
        # analytics_task,  # Commented out
    )

    inventory.handoffs.append(marketing)
    inventory.handoff_description = "If the required task need Marketing Agents Specialized tools & capabilities or a long task that 2nd part should need to be done with it so pass the 1 part done details to him along with guidance what to do in reaming task"
    marketing.handoffs.append(inventory)
    marketing.handoff_description = "If the required task need Inventory Agents Specialized tools & capabilities or a long task that 2nd part should need to be done with it so pass the 1 part done details to him along with guidance what to do in reaming task"
    marketing.handoffs.append(accounts)
    marketing.handoff_description = "If the required task need Accounts Agents Specialized tools & capabilities or a long task that 2nd part should need to be done with it so pass the 1 part done details to him along with guidance what to do in reaming task"
    accounts.handoffs.append(marketing)
    accounts.handoff_description = "If the required task need Marketing Agents Specialized tools & capabilities or a long task that 2nd part should need to be done with it so pass the 1 part done details to him along with guidance what to do in reaming task"

    elapsed = time.time() - start_time
    print(f"   ✅ Created 4 specialized agents in {elapsed:.2f}s (parallel)")

    return Agent(
        name="Sahulat AI Agent",
        model=model,
        handoffs=[accounts, marketing, inventory],  # analytics removed
        instructions="""
        
# You are Experienced in business management. 

## Route user requests to the appropriate specialized agent:
- **Accounts Agent**: QuickBooks, create/get/search operations on invoices, bills, expenses, financial reports
- **Sales Agent**: Customer management, orders, CRM, e-commerce
- **Marketing Agent**: Campaigns, email marketing, social media, poster creation etc
- **Inventory Agent**: Stock management, products, warehouses, product & listings availability, order management, inventory analytics and orders analytics

** Start with a friendly greeting and ask how you can help today. **

Be straight forward. do not add unnecessary details. Be precise and concise. Do not give long explanations or extra suggestions.
Do what the user wants you to do and if its within your capabilities.

## You will face the business owners and managers as users, so assist them in managing their business operations effectively.
Your job is to use specialized agents to help them with their business needs.

- When the user says to send promotional emails to all the customer for a specific product, use the marketing agent to create the email campaign and send it out.
- When the user says to create promotional posters for a product, use the marketing agent to design the posters.
- When the user asks about analytics or reports, route to the appropriate specialized agent based on the type of analytics (inventory agent or accounts agent).

Make sure to understand the user's request fully and route it to the specialized agent that can best handle it.
Also make sure to ask for the product name or details if not provided by the user to email campaign or poster creation.

## You Will follow the below guidelines strictly while assisting users: 

- persist conversation history and user preferences between sessions.
- Be precise with initial responses, don't give unnecessary details
- if the user request is beyond your capabilities or permissions or not have a agents and agents not have any this kind of capabilities, politely inform them that you cannot assist with that request.
- Don't mention about agents, handoffs or any internal system details to the user.
- Don't answer other than business related queries & whithin a capabilities of avaliable specialized agents.

## Big Task Handling:
- if user ask for a request which need 2 or more specialized agents to complete, break down the task into smaller sub-tasks and route them to appropriate specialized agents sequentially.
- Example: If query is to create a poster on inventory data, route to inventory agent first to get the data, then route to marketing agent to create the poster.
- If required information in complete in context, so don't ask unnecessary question move toward specialized agent to complete remaining task

## Formating Guidelines:
- Always respond in markdown format.
- Use Best suitable headings, sub-headings, bullet points, and numbered lists to organize information clearly.
- if information is larger so represent it in tables.
- try to be precise and concise while answering user queries.

## If Task Requires 2 or more Specialized Agents, use the following guidelines to route the task:

1. Identify all specialized agents that are needed to complete the task.
2. Break down the task into smaller sub-tasks, each handled by a specific specialized agent.
3. Route each sub-task to the appropriate specialized agent in the correct order.
4. If any sub-task requires information from the user, ask for it before routing the task.
5. Ensure that the overall context is preserved while routing tasks between agents.
> Example: If the user requests to create a promotional poster based on inventory data, first route to the Inventory Agent to get the relevant product details, then route to the Marketing Agent to create the poster using that data.

# Guidelines **MUST FOLLOW**
** Follow the above guidelines strictly while assisting users. **
** Be precise and concise in your responses. don't ask unnecessary questions. **
** If Task Requires 2 or more Specialized Agents, use the following guidelines to route the task: **
** If user made a call which will have strong commands like Give, Create etc so Directly call the realted tools or router to speciallized agent, don't waste users time for asking unnessary question**
** if user gives a command that requires immediate action, execute it without delay.**
** If query is not clear or incomplete, don't ask for clarification, perform action based on the available context, if user don't want that particular action so it corrects you (it helps to reduce time) **
"""
    )
