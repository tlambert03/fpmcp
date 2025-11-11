import pytest
from fastmcp.client import Client
from fastmcp.client.transports import FastMCPTransport
from fpmcp.server import mcp


@pytest.fixture
async def main_mcp_client():
    async with Client(transport=mcp) as mcp_client:
        yield mcp_client


async def test_list_tools(main_mcp_client: Client[FastMCPTransport]):
    list_tools = await main_mcp_client.list_tools()
    assert len(list_tools) >= 3
    tool_names = [tool.name for tool in list_tools]
    assert "get_article_tables" in tool_names
    assert "get_article_text" in tool_names
    assert "get_article_info" in tool_names


async def test_get_article_tables(main_mcp_client: Client[FastMCPTransport]):
    """Test that we can fetch tables from an article."""
    result = await main_mcp_client.call_tool(
        "get_article_tables", {"article_id": "10.1038/s41592-023-02085-6"}
    )
    tables = result.content[0].text
    assert isinstance(tables, str)
    assert len(tables) > 0
    # Should contain table data
    assert "StayGold" in tables or "staygold" in tables.lower()


async def test_quantum_yield_of_staygold(main_mcp_client: Client[FastMCPTransport]):
    """Test finding the quantum yield of StayGold (should be 0.93).

    This test simulates the query:
    "What is the quantum yield of staygold in 10.1038/s41592-023-02085-6"

    The correct answer is 0.93 (found in Table 1 of the paper).
    """
    # Get tables from the article
    result = await main_mcp_client.call_tool(
        "get_article_tables", {"article_id": "10.1038/s41592-023-02085-6"}
    )
    tables_str = result.content[0].text

    # Parse tables - should be multiple tables separated by markdown
    assert "StayGold" in tables_str or "staygold" in tables_str.lower()

    # Find the quantum yield value for StayGold
    # The table has a row for StayGold with QY (quantum yield) value of 0.93
    # Let's search for lines containing "StayGold" and look for the QY value

    lines = tables_str.split("\n")
    staygold_lines = [
        line for line in lines if "stay" in line.lower() and "gold" in line.lower()
    ]

    # Should find at least one line with StayGold
    assert len(staygold_lines) > 0

    # Look for 0.93 in the StayGold rows
    # The format should have the protein name and then columns with values
    found_qy = False
    for line in staygold_lines:
        # Look for 0.93 in this line (the quantum yield)
        if "0.93" in line:
            found_qy = True
            break

    assert found_qy, f"Could not find QY=0.93 for StayGold in: {staygold_lines}"


async def test_absorption_maximum_of_megfp(main_mcp_client: Client[FastMCPTransport]):
    """Test finding the absorption maximum of mEGFP (should be 488).

    This test simulates the query:
    "What is the absorption maximum of mEGFP in 10.1038/s41592-023-02085-6"

    The correct answer is 488 nm (found in Table 1 of the paper).
    """
    # Get tables from the article
    result = await main_mcp_client.call_tool(
        "get_article_tables", {"article_id": "10.1038/s41592-023-02085-6"}
    )
    tables_str = result.content[0].text

    # Find the absorption maximum value for mEGFP
    lines = tables_str.split("\n")
    megfp_lines = [line for line in lines if "mEGFP" in line or "megfp" in line.lower()]

    # Should find at least one line with mEGFP
    assert len(megfp_lines) > 0, "Could not find mEGFP in tables"

    # Look for 488 in the mEGFP rows (absorption maximum)
    found_abs_max = False
    for line in megfp_lines:
        if "488" in line:
            found_abs_max = True
            break

    assert found_abs_max, (
        f"Could not find absorption maximum=488 for mEGFP in: {megfp_lines}"
    )


async def test_get_article_info(main_mcp_client: Client[FastMCPTransport]):
    """Test getting article metadata."""
    result = await main_mcp_client.call_tool(
        "get_article_info", {"article_id": "10.1038/s41592-023-02085-6"}
    )
    info_str = result.content[0].text
    assert "source" in info_str.lower()
    assert "doi" in info_str.lower()
    # Should contain the DOI we requested
    assert "10.1038/s41592-023-02085-6" in info_str
