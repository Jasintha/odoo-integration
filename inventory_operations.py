"""
Functions for managing inventory in Odoo.
"""
from connection import get_model_connection

def get_warehouses(uid, config):
    """
    Get all warehouses.
    
    Args:
        uid (int): User ID for authentication
        config (dict): Configuration dictionary with Odoo connection parameters
        
    Returns:
        list: List of warehouses or empty list if error
    """
    if not uid:
        return []
    
    try:
        models = get_model_connection(config['url'])
        
        # Get warehouses
        warehouses = models.execute_kw(
            config['db_name'], uid, config['password'],
            'stock.warehouse', 'search_read',
            [[]],
            {'fields': ['id', 'name', 'code', 'lot_stock_id']}
        )
        
        print("\nAvailable warehouses:")
        for wh in warehouses:
            stock_location = f"{wh['lot_stock_id'][1]} (ID: {wh['lot_stock_id'][0]})" if wh.get('lot_stock_id') else 'N/A'
            print(f"  - ID: {wh['id']}, Name: {wh['name']}, Code: {wh.get('code', 'N/A')}, Stock Location: {stock_location}")
        
        return warehouses
    except Exception as e:
        print(f"Error getting warehouses: {str(e)}")
        return []

def get_stock_locations(uid, config):
    """
    Get all stock locations.
    
    Args:
        uid (int): User ID for authentication
        config (dict): Configuration dictionary with Odoo connection parameters
        
    Returns:
        list: List of stock locations or empty list if error
    """
    if not uid:
        return []
    
    try:
        models = get_model_connection(config['url'])
        
        # Get stock locations
        locations = models.execute_kw(
            config['db_name'], uid, config['password'],
            'stock.location', 'search_read',
            [[]],
            {'fields': ['id', 'name', 'complete_name', 'usage', 'location_id']}
        )
        
        print("\nAvailable stock locations:")
        physical_locations = [loc for loc in locations if loc.get('usage') == 'internal']
        for loc in physical_locations:
            print(f"  - ID: {loc['id']}, Name: {loc.get('complete_name') or loc['name']}, Usage: {loc.get('usage', 'N/A')}")
        
        return locations
    except Exception as e:
        print(f"Error getting stock locations: {str(e)}")
        return []

def add_product_to_warehouse(uid, config, product_id, location_id, quantity=10):
    """
    Add product inventory to a specific warehouse location.
    
    Args:
        uid (int): User ID for authentication
        config (dict): Configuration dictionary with Odoo connection parameters
        product_id (int): Product ID to add
        location_id (int): Location ID to add product to
        quantity (float): Quantity to add
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not uid or not product_id or not location_id:
        print("Missing required parameters for adding inventory")
        return False
    
    try:
        print(f"\n--- ADDING PRODUCT (ID: {product_id}) TO LOCATION (ID: {location_id}) ---")
        models = get_model_connection(config['url'])
        
        # Get product info for logging
        product = models.execute_kw(
            config['db_name'], uid, config['password'],
            'product.product', 'read',
            [product_id],
            {'fields': ['name']}
        )
        product_name = product[0]['name'] if product else f"Product ID {product_id}"
        
        # Let's try to determine what inventory methods are available in this version
        print("Checking available inventory adjustment methods...")
        
        # Check for available models
        available_models = []
        potential_models = ['stock.quant', 'stock.inventory', 'stock.move', 'stock.immediate.transfer']
        
        for model in potential_models:
            try:
                result = models.execute_kw(
                    config['db_name'], uid, config['password'],
                    model, 'search',
                    [[]], {'limit': 1}
                )
                available_models.append(model)
                print(f"Model {model} is available")
            except Exception:
                print(f"Model {model} is not available")
        
        # Try using stock.quant without calling action_apply_inventory
        try:
            print("Attempting to update inventory using stock.quant...")
            
            # First, check if there's an existing quant for this product/location
            existing_quants = models.execute_kw(
                config['db_name'], uid, config['password'],
                'stock.quant', 'search_read',
                [[['product_id', '=', product_id], ['location_id', '=', location_id]]],
                {'fields': ['id', 'quantity']}
            )
            
            if existing_quants:
                quant_id = existing_quants[0]['id']
                current_qty = existing_quants[0].get('quantity', 0)
                print(f"Found existing quant ID: {quant_id} with quantity: {current_qty}")
                
                # Update the existing quant with new quantity
                result = models.execute_kw(
                    config['db_name'], uid, config['password'],
                    'stock.quant', 'write',
                    [[quant_id], {'quantity': current_qty + quantity}]
                )
                
                print(f"Successfully updated quant with {quantity} more units, new total: {current_qty + quantity}")
                return True
            else:
                # Create a new quant
                quant_vals = {
                    'product_id': product_id,
                    'location_id': location_id,
                    'quantity': quantity
                }
                
                # Try to add company_id field if it's required
                try:
                    company = models.execute_kw(
                        config['db_name'], uid, config['password'],
                        'res.company', 'search_read',
                        [[]], {'limit': 1, 'fields': ['id']}
                    )
                    if company:
                        quant_vals['company_id'] = company[0]['id']
                except Exception:
                    pass
                
                # Try to add owner_id field if needed
                company_user = models.execute_kw(
                    config['db_name'], uid, config['password'],
                    'res.users', 'read',
                    [uid], {'fields': ['partner_id']}
                )
                
                if company_user and company_user[0].get('partner_id'):
                    quant_vals['owner_id'] = company_user[0]['partner_id'][0]
                
                quant_id = models.execute_kw(
                    config['db_name'], uid, config['password'],
                    'stock.quant', 'create',
                    [quant_vals]
                )
                
                print(f"Successfully created new quant with {quantity} units")
                return True
                
        except Exception as e:
            print(f"Error directly updating stock.quant: {str(e)}")
            
            # Try to use the stock_change_product_qty wizard which is often available
            print("Attempting to use stock.change.product.qty wizard...")
            
            try:
                # Get the wizard fields
                wizard_fields = models.execute_kw(
                    config['db_name'], uid, config['password'],
                    'stock.change.product.qty', 'fields_get',
                    [], {'attributes': ['string', 'required']}
                )
                
                # Prepare wizard values
                wizard_vals = {
                    'product_id': product_id,
                    'new_quantity': quantity,
                }
                
                # Add location_id if it's a valid field
                if 'location_id' in wizard_fields:
                    wizard_vals['location_id'] = location_id
                
                # Create and process the wizard
                wizard_id = models.execute_kw(
                    config['db_name'], uid, config['password'],
                    'stock.change.product.qty', 'create',
                    [wizard_vals]
                )
                
                # Execute the wizard
                result = models.execute_kw(
                    config['db_name'], uid, config['password'],
                    'stock.change.product.qty', 'change_product_qty',
                    [[wizard_id]]
                )
                
                print(f"Successfully updated inventory for {product_name} to {quantity} units")
                return True
                
            except Exception as e2:
                print(f"Error using stock.change.product.qty wizard: {str(e2)}")
                
                # Last resort - try to create an inventory adjustment entry
                try:
                    print("Attempting to find another method...")
                    
                    # Check if we have stock scrap model as a backup option
                    scrap_model_exists = False
                    try:
                        models.execute_kw(
                            config['db_name'], uid, config['password'],
                            'stock.scrap', 'search',
                            [[]], {'limit': 1}
                        )
                        scrap_model_exists = True
                    except Exception:
                        pass
                    
                    if scrap_model_exists:
                        print("Using stock.scrap as a workaround...")
                        # This is a bit of a hack but could work to add inventory in a pinch
                        # We create a "negative scrap" which effectively adds stock
                        scrap_vals = {
                            'product_id': product_id,
                            'scrap_qty': -quantity,  # Negative quantity to add stock
                            'location_id': location_id,
                            'scrap_location_id': location_id  # Same location to just adjust qty
                        }
                        
                        scrap_id = models.execute_kw(
                            config['db_name'], uid, config['password'],
                            'stock.scrap', 'create',
                            [scrap_vals]
                        )
                        
                        # Try to validate the scrap
                        models.execute_kw(
                            config['db_name'], uid, config['password'],
                            'stock.scrap', 'action_validate',
                            [[scrap_id]]
                        )
                        
                        print(f"Successfully added {quantity} units via scrap adjustment")
                        return True
                    else:
                        print("No more methods available to adjust inventory")
                        return False
                    
                except Exception as e3:
                    print(f"All inventory adjustment methods failed: {str(e3)}")
                    print("Could not add product to location. Please check Odoo version or try using the web interface.")
                    return False
        
    except Exception as e:
        print(f"Error in add_product_to_warehouse: {str(e)}")
        return False

def generate_inventory_report(uid, config):
    """
    Generate inventory report for all locations.
    
    Args:
        uid (int): User ID for authentication
        config (dict): Configuration dictionary with Odoo connection parameters
    """
    if not uid:
        return
    
    try:
        print("\n--- GENERATING INVENTORY REPORT ---")
        models = get_model_connection(config['url'])
        
        # Get all warehouse stock locations
        warehouses = get_warehouses(uid, config)
        stock_locations = []
        
        for wh in warehouses:
            if wh.get('lot_stock_id'):
                stock_locations.append({
                    'id': wh['lot_stock_id'][0],
                    'name': wh['lot_stock_id'][1],
                    'warehouse': wh['name']
                })
        
        # Get products with inventory information
        print("\nLocation-wise Inventory Report:")
        print("-" * 80)
        print(f"{'Location':<30} {'Product':<30} {'Quantity':<10}")
        print("-" * 80)
        
        total_inventory = {}
        
        for location in stock_locations:
            # Get quants for this location
            quants = models.execute_kw(
                config['db_name'], uid, config['password'],
                'stock.quant', 'search_read',
                [[['location_id', '=', location['id']], ['quantity', '>', 0]]],
                {'fields': ['product_id', 'quantity']}
            )
            
            if not quants:
                print(f"{location['name']} ({location['warehouse']}):<30 No inventory")
                continue
            
            for quant in quants:
                product = models.execute_kw(
                    config['db_name'], uid, config['password'],
                    'product.product', 'read',
                    [quant['product_id'][0]],
                    {'fields': ['name']}
                )
                
                product_name = product[0]['name'] if product else f"Unknown ({quant['product_id'][0]})"
                quantity = quant['quantity']
                
                print(f"{location['name']:<30} {product_name:<30} {quantity:<10.2f}")
                
                # Add to total inventory
                if product_name not in total_inventory:
                    total_inventory[product_name] = 0
                total_inventory[product_name] += quantity
        
        # Print consolidated report
        print("\nConsolidated Inventory Report:")
        print("-" * 50)
        print(f"{'Product':<30} {'Total Quantity':<10}")
        print("-" * 50)
        
        for product_name, quantity in total_inventory.items():
            print(f"{product_name:<30} {quantity:<10.2f}")
        
    except Exception as e:
        print(f"Error generating inventory report: {str(e)}")