from mcp.server.fastmcp import FastMCP
import requests
import httpx
API_BASE = "http://192.168.100.5:8080"  # FastAPI đang chạy ở đây

# Create an MCP server
mcp = FastMCP(name="MCP_server")

# Add MCP tools (gọi qua FastAPI endpoints)
@mcp.tool()
def create_user(email: str, name: str):
    """Create new user"""
    resp = requests.post(f"{API_BASE}/users/", json={"email": email, "name": name})
    return resp.json()


@mcp.tool()
def get_user_by_email(email: str):
    """Get user by email"""
    resp = requests.get(f"{API_BASE}/users/{email}")
    return resp.json()


@mcp.tool()
def get_all_users():
    """Retrieve all users"""
    resp = requests.get(f"{API_BASE}/users/")
    return resp.json()


@mcp.tool()
def send_message(sender_id: str, recipients: list[str], subject: str, content: str):
    """Send a message to one or more recipients"""
    resp = requests.post(f"{API_BASE}/messages/", json={
        "sender_id": sender_id,
        "recipients": recipients,
        "subject": subject,
        "content": content
    })
    return resp.json()


@mcp.tool()
def get_all_sent_message(sender_id: str):
    """View all messages sent by a user"""
    resp = requests.get(f"{API_BASE}/messages/sent/{sender_id}")
    return resp.json()


@mcp.tool()
def view_inbox(user_id: str):
    """View inbox messages of a user"""
    resp = requests.get(f"{API_BASE}/messages/inbox/{user_id}")
    return resp.json()


@mcp.tool()
def get_unread_message(recipient_id: str):
    """View unread messages for a recipient"""
    resp = requests.get(f"{API_BASE}/messages/unread/{recipient_id}")
    return resp.json()


@mcp.tool()
def get_message_with_recipients(message_id: str):
    """View a message with all its recipients"""
    resp = requests.get(f"{API_BASE}/messages/{message_id}/recipients")
    return resp.json()


@mcp.tool()
def mark_as_read(message_id: str, recipient_id: str):
    """Mark a message as read for a recipient"""
    resp = requests.post(f"{API_BASE}/messages/{message_id}/read", json={"recipient_id": recipient_id})
    return resp.json()


# Run the MCP server
if __name__ == "__main__":
    mcp.run(transport='stdio')

