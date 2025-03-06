#!/usr/bin/env python3
import xmlrpc.client
import sys

# Connection parameters
url = 'https://ncinga.odoo.com'
db_name = 'ncinga'
username = 'jasinthad@gmail.com'
password = 'WY!hM4_!*_,Ve)j'  # You should change this password after using this script

# Function to test connection and authentication
def test_connection():
    print(f"Attempting to connect to {url}...")
    try:
        # Connect to the common endpoint
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        
        # Get server version info (doesn't require authentication)
        version_info = common.version()
        print(f"Successfully connected to Odoo server version: {version_info['server_version']}")
        
        # Try to authenticate
        print(f"Attempting to authenticate as {username}...")
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

# Function to check user permissions
def check_permissions(uid):
    if not uid:
        return False
    
    try:
        print("\nChecking user permissions...")
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        
        # Get user details
        user_data = models.execute_kw(
            db_name, uid, password,
            'res.users', 'read',
            [uid, ['name', 'groups_id']]
        )
        
        print(f"Logged in as: {user_data[0]['name']}")
        
        # Check if user has stock manager permissions
        groups = models.execute_kw(
            db_name, uid, password,
            'res.groups', 'search_read',
            [[('category_id.name', '=', 'Inventory'), '|', ('name', 'ilike', 'manager'), ('name', 'ilike', 'admin')]],
            {'fields': ['name']}
        )
        
        stock_manager_ids = [group['id'] for group in groups]
        user_groups = user_data[0]['groups_id']
        
        has_permission = any(group_id in user_groups for group_id in stock_manager_ids)
        
        if has_permission:
            print("User has inventory management permissions.")
        else:
            print("WARNING: User may not have sufficient permissions for warehouse management.")
            print("Available inventory-related groups:")
            for group in groups:
                print(f" - {group['name']} (ID: {group['id']})")
        
        return True
    except Exception as e:
        print(f"Error checking permissions: {str(e)}")
        return False

# Function to verify existing stock locations
def verify_locations(uid):
    if not uid:
        return
    
    try:
        print("\nVerifying existing stock locations...")
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        
        # Get all stock locations
        locations = models.execute_kw(
            db_name, uid, password,
            'stock.location', 'search_read',
            [[('usage', '=', 'internal')]],
            {'fields': ['name', 'complete_name', 'warehouse_id']}
        )
        
        print(f"Found {len(locations)} internal stock locations:")
        for loc in locations:
            warehouse = "None" if not loc.get('warehouse_id') else loc['warehouse_id'][1]
            print(f" - {loc['complete_name']} (Warehouse: {warehouse})")
        
        return locations
    except Exception as e:
        print(f"Error verifying locations: {str(e)}")
        return None

# Function to list warehouses
def list_warehouses(uid):
    if not uid:
        return
    
    try:
        # Connect to the object endpoint
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        
        # Search for warehouses
        warehouse_ids = models.execute_kw(
            db_name, uid, password,
            'stock.warehouse', 'search',
            [[]]  # Empty domain to get all warehouses
        )
        
        if not warehouse_ids:
            print("No warehouses found.")
            return
        
        print(f"Found {len(warehouse_ids)} warehouse(s). Fetching details...")
        
        # Read warehouse data
        warehouses = models.execute_kw(
            db_name, uid, password,
            'stock.warehouse', 'read',
            [warehouse_ids, ['name', 'code', 'partner_id']]
        )
        
        # Display warehouse information
        print("\nWarehouse Information:")
        print("-" * 50)
        for wh in warehouses:
            print(f"ID: {wh['id']}")
            print(f"Name: {wh['name']}")
            print(f"Code: {wh['code']}")
            if wh['partner_id']:
                print(f"Location Partner: {wh['partner_id'][1]}")
            print("-" * 50)
    except Exception as e:
        print(f"Error listing warehouses: {str(e)}")

# Function to create a stock location directly
def create_stock_location(uid, name, parent_location_id=None):
    if not uid:
        return None
    
    try:
        print(f"\nAttempting to create new stock location: {name}...")
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        
        # First try to get the default WH/Stock location if no parent is specified
        if not parent_location_id:
            stock_locations = models.execute_kw(
                db_name, uid, password,
                'stock.location', 'search_read',
                [[('name', '=', 'Stock'), ('usage', '=', 'internal')]],
                {'fields': ['id', 'complete_name'], 'limit': 1}
            )
            
            if stock_locations:
                parent_location_id = stock_locations[0]['id']
                print(f"Using parent location: {stock_locations[0]['complete_name']} (ID: {parent_location_id})")
            else:
                # Fallback to getting any internal location
                internal_locations = models.execute_kw(
                    db_name, uid, password,
                    'stock.location', 'search_read',
                    [[('usage', '=', 'internal')]],
                    {'fields': ['id', 'complete_name'], 'limit': 1}
                )
                
                if internal_locations:
                    parent_location_id = internal_locations[0]['id']
                    print(f"Using parent location: {internal_locations[0]['complete_name']} (ID: {parent_location_id})")
                else:
                    print("No suitable parent location found. Cannot create new location.")
                    return None
        
        # Create the location
        location_vals = {
            'name': name,
            'usage': 'internal',
            'location_id': parent_location_id,
        }
        
        print(f"Creating location with values: {location_vals}")
        
        location_id = models.execute_kw(
            db_name, uid, password,
            'stock.location', 'create',
            [location_vals]
        )
        
        if location_id:
            print(f"Successfully created location with ID: {location_id}")
            
            # Read back the created location details
            location = models.execute_kw(
                db_name, uid, password,
                'stock.location', 'read',
                [location_id, ['name', 'complete_name', 'location_id', 'usage']]
            )
            
            print("\nNew Location Details:")
            print("-" * 50)
            print(f"ID: {location[0]['id']}")
            print(f"Name: {location[0]['name']}")
            print(f"Complete Path: {location[0]['complete_name']}")
            print(f"Parent Location: {location[0]['location_id'][1]}")
            print(f"Usage: {location[0]['usage']}")
            print("-" * 50)
            
            return location_id
        else:
            print("Failed to create location. No ID returned.")
            return None
            
    except Exception as e:
        print(f"Error creating location: {str(e)}")
        if "Access Denied" in str(e) or "access right" in str(e).lower():
            print("\nPermission denied: Your user account doesn't have rights to create stock locations.")
            print("Try using the Odoo web interface instead, or contact your administrator.")
        return None

# Main function to create multiple locations
def create_multiple_locations(uid, location_names):
    print(f"\nAttempting to create {len(location_names)} new locations...")
    
    created_locations = []
    for name in location_names:
        location_id = create_stock_location(uid, name)
        if location_id:
            created_locations.append((name, location_id))
    
    if created_locations:
        print("\nSummary of created locations:")
        for name, loc_id in created_locations:
            print(f" - {name} (ID: {loc_id})")
    else:
        print("\nNo locations were successfully created.")
    
    # Verify all locations after creation attempts
    verify_locations(uid)

# Main execution
def main():
    uid = test_connection()
    
    if not uid:
        print("Authentication failed. Cannot proceed.")
        return
    
    # Check permissions first
    check_permissions(uid)
    
    # Location names to create
    location_names = ["Nugegoda", "Kottawa", "Maharagama"]
    
    # Create the locations
    create_multiple_locations(uid, location_names)

if __name__ == "__main__":
    main()