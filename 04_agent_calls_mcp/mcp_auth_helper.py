def IsMCPAuthenticationError(error_info, auth_patterns=None):
    """
    Check if the error is an MCP authentication error.
    
    Args:
        error_info: Dictionary containing error information with keys:
                   - error_type: The exception type name
                   - error_details: The detailed traceback string
        auth_patterns: List of patterns to check for authentication errors
    
    Returns:
        bool: True if it's an authentication error, False otherwise
    """
    if auth_patterns is None:
        auth_patterns = [
            "Client error '403 Forbidden'",
            "Illegal header value b'Bearer '"
        ]
    
    if error_info.get("error_type") == "MCPClientInitializationError":
        error_details = error_info.get("error_details", "")
        return any(pattern in error_details for pattern in auth_patterns)
    return False