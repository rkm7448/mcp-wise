"""
Wise API resources for the FastMCP server.
"""

from typing import List, Optional, Dict, Any

from fastmcp import Context
from fastmcp.prompts.prompt import PromptMessage, TextContent
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_context

from wise_mcp.app import mcp
from ..api.wise_client_helper import init_wise_client


@mcp.tool()
def list_recipients(profile_type: str = "personal", currency: Optional[str] = None) -> List:
    """
    Returns all recipients from the Wise API for the given profile type of current user. If a
    user has multiple profiles of that type, it will return recipients from the first profile.

    Args:
        profile_type: The type of profile to list recipients for. one of [personal, business]
        currency: Optional. Filter recipients by currency code (e.g., 'EUR', 'USD')

    Returns:
        List of formatted strings with recipient information
    
    Raises:
        Exception: If the API request fails or profile ID is not available.
    """

    ctx = init_wise_client(profile_type)
    
    return ctx.wise_api_client.list_recipients(ctx.profile.profile_id, currency)


@mcp.tool()
async def get_recipient_requirements(source_currency: Optional[str] = None,
                                     target_currency: Optional[str] = None,
                                     source_amount: Optional[float] = None,
                                     profile_type: str = "personal",
                                     account_details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Fetches recipient requirements for creating a new recipient. If account details are provided,
    validates the account details against the requirements.

    Args:
        source_currency: Optional. The source currency code (e.g., 'USD')
        target_currency: Optional. The target currency code (e.g., 'EUR')
        source_amount: Optional. The amount in the source currency (e.g., 100.0)
        profile_type: The type of profile to use. One of [personal, business]. Default: "personal"
        account_details: Optional. The recipient account details to validate against requirements.
                If not provided, returns the initial account requirements.
    
    Returns:
        Dictionary containing fields that need to be filled in for the recipient account creation.
    
    Raises:
        Exception: If the API request fails
    """

    ctx = init_wise_client(profile_type)

    context = get_context()

    if source_currency is None:
        source_currency_elicit = await context.elicit("Enter source currency", response_type=str)
        if source_currency_elicit.action == "accept":
            source_currency = source_currency_elicit.data
        else:
            raise ToolError("Source currency is required.")

    quote = ctx.wise_api_client.create_quote(
        profile_id=ctx.profile.profile_id,
        source_currency=source_currency,
        target_currency=target_currency,
        source_amount=source_amount
    )
    
    quote_id = quote.get("id")
    
    return ctx.wise_api_client.get_account_requirements(quote_id, account_details)


@mcp.tool()
def create_recipient(
    recipient_fullname: str,
    currency: str,
    recipient_type: str,
    profile_type: str = "personal",
    account_details: Dict[str, Any] = None
) -> str | dict[str, Any]:
    """
    Creates a new recipient with the provided account details.

    Args:
        recipient_fullname: The name of the account holder. Required.
        currency: The currency code for the recipient account. Required.
        recipient_type: The type of recipient account. Required.
        profile_type: The type of profile to use. One of [personal, business]. Default: "personal"
        account_details: Additional recipient account details compliant with Wise API requirements.
               If provided, it will be updated with the required fields.
    
    Returns:
        The created recipient details
    
    Raises:
        Exception: If the API request fails or if required fields are missing
    """

    ctx = init_wise_client(profile_type)

    if account_details is None:
        return "Use 'get_recipient_requirements()' to fetch required fields before creating a recipient."

    return ctx.wise_api_client.create_recipient(
        profile_id=ctx.profile.profile_id,
        recipient_fullname=recipient_fullname,
        currency=currency,
        recipient_type=recipient_type,
        account_details=account_details
    )
