"""
Functions for establishing and maintaining connection to Odoo.
"""
import xmlrpc.client

def test_connection(url, db_name, username, password):
    """
    Test connection to Odoo server and authenticate.
    
    Args:
        url (str): The Odoo server URL
        db_name (str): The database name
        username (str): The username for authentication
        password (str): The password for authentication
        
    Returns:
        int or None: User ID if authentication successful, None otherwise
    """
    print(f"Connecting to Odoo at {url}...")
    try:
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        version_info = common.version()
        print(f"Connected to Odoo server version: {version_info['server_version']}")
        print(f"Authenticating as {username}...")
        uid = common.authenticate(db_name, username, password, {})
        
        if uid:
            print(f"Authentication successful! User ID: {uid}")
            return uid
        else:
            print("Authentication failed. Please check your credentials.")
            return None
    except Exception as e:
        print(f"Connection error: {str(e)}")
        return None

def get_model_connection(url):
    """
    Get a connection to the object endpoint for model operations.
    
    Args:
        url (str): The Odoo server URL
        
    Returns:
        ServerProxy: An XML-RPC proxy for model operations
    """
    return xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')