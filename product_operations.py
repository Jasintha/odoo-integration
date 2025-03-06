"""
Functions for managing products in Odoo.
"""
import json
from pprint import pprint
from connection import get_model_connection

def get_product_categories(uid, config):
    """
    Get all product categories.
    
    Args:
        uid (int): User ID for authentication
        config (dict): Configuration dictionary with Odoo connection parameters
        
    Returns:
        list: List of product categories or empty list if error
    """
    if not uid:
        return []
    
    try:
        models = get_model_connection(config['url'])
        
        # Get product categories
        categories = models.execute_kw(
            config['db_name'], uid, config['password'],
            'product.category', 'search_read',
            [[]],
            {'fields': ['id', 'name', 'complete_name']}
        )
        
        print("\nAvailable product categories:")
        for cat in categories:
            print(f"  - ID: {cat['id']}, Name: {cat.get('complete_name') or cat['name']}")
        
        return categories
    except Exception as e:
        print(f"Error getting product categories: {str(e)}")
        return []

def get_product_uoms(uid, config):
    """
    Get all product units of measure.
    
    Args:
        uid (int): User ID for authentication
        config (dict): Configuration dictionary with Odoo connection parameters
        
    Returns:
        list: List of units of measure or empty list if error
    """
    if not uid:
        return []
    
    try:
        models = get_model_connection(config['url'])
        
        # Get units of measure - only request id and name fields which should exist in all versions
        uoms = models.execute_kw(
            config['db_name'], uid, config['password'],
            'uom.uom', 'search_read',
            [[]],
            {'fields': ['id', 'name']}
        )
        
        print("\nAvailable units of measure:")
        for uom in uoms:
            print(f"  - ID: {uom['id']}, Name: {uom['name']}")
        
        return uoms
    except Exception as e:
        print(f"Error getting units of measure: {str(e)}")
        
        # Try with older model name
        try:
            models = get_model_connection(config['url'])
            
            # In older Odoo versions, the model might be called 'product.uom'
            uoms = models.execute_kw(
                config['db_name'], uid, config['password'],
                'product.uom', 'search_read',
                [[]],
                {'fields': ['id', 'name']}
            )
            
            print("\nAvailable units of measure (using legacy API):")
            for uom in uoms:
                print(f"  - ID: {uom['id']}, Name: {uom['name']}")
            
            return uoms
        except Exception as e2:
            print(f"Error getting units of measure (legacy API): {str(e2)}")
            # Return a default UOM if we can't get the actual ones
            print("\nUsing default unit of measure (Units)")
            return [{'id': 1, 'name': 'Units'}]

def inspect_existing_products(uid, config):
    """
    Inspect and display details of existing products.
    
    Args:
        uid (int): User ID for authentication
        config (dict): Configuration dictionary with Odoo connection parameters
        
    Returns:
        list: List of products or empty list if error
    """
    if not uid:
        return []
    
    try:
        print("\n--- INSPECTING EXISTING PRODUCTS ---")
        models = get_model_connection(config['url'])
        
        # Get all products
        products = models.execute_kw(
            config['db_name'], uid, config['password'],
            'product.product', 'search_read',
            [[]],
            {'fields': ['id', 'name', 'default_code', 'type', 'categ_id', 'list_price', 'standard_price']}
        )
        
        if not products:
            print("No products found in the system.")
            return []
        
        print(f"Found {len(products)} products:")
        for product in products:
            print("\n" + "-" * 50)
            print(f"ID: {product['id']}")
            print(f"Name: {product['name']}")
            print(f"Internal Reference: {product.get('default_code', 'N/A')}")
            print(f"Type: {product['type']}")
            print(f"Category: {product['categ_id'][1] if product.get('categ_id') else 'N/A'}")
            print(f"Sales Price: {product.get('list_price', 'N/A')}")
            print(f"Cost: {product.get('standard_price', 'N/A')}")
            
        return products
    except Exception as e:
        print(f"Error inspecting products: {str(e)}")
        return []

def inspect_product_fields(uid, config):
    """
    Inspect available product fields and their valid values.
    
    Args:
        uid (int): User ID for authentication
        config (dict): Configuration dictionary with Odoo connection parameters
        
    Returns:
        dict: Dictionary of product fields or empty dict if error
    """
    if not uid:
        return {}
    
    try:
        print("\n--- INSPECTING PRODUCT FIELDS ---")
        models = get_model_connection(config['url'])
        
        # Get fields for product.product model
        product_fields = models.execute_kw(
            config['db_name'], uid, config['password'],
            'product.product', 'fields_get',
            [], {'attributes': ['string', 'help', 'type', 'selection']}
        )
        
        print("\nProduct Fields:")
        important_fields = ['name', 'type', 'categ_id', 'default_code', 'list_price', 'standard_price', 'uom_id', 'purchase_ok', 'sale_ok', 'taxes_id']
        
        for field_name in important_fields:
            if field_name in product_fields:
                field_data = product_fields[field_name]
                print(f"\n{field_name}:")
                print(f"  Label: {field_data.get('string', 'N/A')}")
                print(f"  Type: {field_data.get('type', 'N/A')}")
                print(f"  Help: {field_data.get('help', 'N/A')}")
                
                # Print selection options if available
                if field_data.get('type') == 'selection' and 'selection' in field_data:
                    print("  Options:")
                    for option in field_data['selection']:
                        print(f"    - {option[0]}: {option[1]}")
        
        # Try to get product type field options if not already available
        if 'type' in product_fields and not ('selection' in product_fields['type'] and product_fields['type']['selection']):
            try:
                type_field = models.execute_kw(
                    config['db_name'], uid, config['password'],
                    'ir.model.fields', 'search_read',
                    [[('model', '=', 'product.template'), ('name', '=', 'type')]],
                    {'fields': ['selection', 'ttype']}
                )
                
                if type_field:
                    print("\nProduct Type Field Options:")
                    if 'selection' in type_field[0] and type_field[0]['selection']:
                        for option in type_field[0]['selection']:
                            print(f"  - {option[0]}: {option[1]}")
            except Exception as e:
                print(f"Could not retrieve product type options: {str(e)}")
        
        return product_fields
    except Exception as e:
        print(f"Error inspecting product fields: {str(e)}")
        return {}

def create_liquor_product(uid, config):
    """
    Create a new liquor product.
    
    Args:
        uid (int): User ID for authentication
        config (dict): Configuration dictionary with Odoo connection parameters
        
    Returns:
        dict or None: Created product information or None if error
    """
    if not uid:
        return None
    
    try:
        print("\n--- CREATING NEW LIQUOR PRODUCT ---")
        models = get_model_connection(config['url'])
        
        # Get product category for alcoholic beverages
        categories = get_product_categories(uid, config)
        
        # Look for a category related to beverages or goods
        category_names = ['Goods', 'Beverages', 'Alcoholic Beverages', 'Liquor']
        category_id = None
        
        for cat in categories:
            name = cat['name']
            if any(cat_name in name for cat_name in category_names):
                category_id = cat['id']
                break
        
        if not category_id and categories:
            category_id = categories[0]['id']  # Default to first category if no match
        
        # Get UOM
        uoms = get_product_uoms(uid, config)
        uom_id = None
        
        for uom in uoms:
            if uom['name'] in ['Units', 'Unit(s)', 'Bottles', 'Bottle(s)']:
                uom_id = uom['id']
                break
        
        if not uom_id and uoms:
            uom_id = uoms[0]['id']  # Default to first UOM if no match
        
        # Prepare product values
        product_name = input("Enter liquor product name (or press Enter for 'Premium Whiskey'): ") or "Premium Whiskey"
        product_code = input("Enter product code (or press Enter for 'WHISKY001'): ") or "WHISKY001"
        
        try:
            sales_price = float(input("Enter sales price (or press Enter for 45.99): ") or 45.99)
            cost_price = float(input("Enter cost price (or press Enter for 30.00): ") or 30.00)
        except ValueError:
            print("Invalid price format. Using default values.")
            sales_price = 45.99
            cost_price = 30.00
        
        # Create basic product values - we'll keep this minimal to improve compatibility
        product_vals = {
            'name': product_name,
            'categ_id': category_id,
            'default_code': product_code,
            'list_price': sales_price,
            'standard_price': cost_price,
        }
        
        # Try to add type field - this may vary between Odoo versions
        try:
            # Check if 'type' is a valid field and get its options
            field_info = models.execute_kw(
                config['db_name'], uid, config['password'],
                'product.product', 'fields_get',
                [['type']], {'attributes': ['type', 'selection']}
            )
            
            if 'type' in field_info and field_info['type'].get('selection'):
                # Find the stockable product option
                for option in field_info['type']['selection']:
                    if option[0] in ['product', 'stockable']:
                        product_vals['type'] = option[0]
                        break
                
                # If no stockable option found, use the first option
                if 'type' not in product_vals and field_info['type']['selection']:
                    product_vals['type'] = field_info['type']['selection'][0][0]
            else:
                # Default to 'product' which is common
                product_vals['type'] = 'product'
        except Exception as e:
            print(f"Warning: Could not determine product type options: {str(e)}")
            # Use default type
            product_vals['type'] = 'product'
        
        # Try to add sale_ok and purchase_ok
        try:
            field_info = models.execute_kw(
                config['db_name'], uid, config['password'],
                'product.product', 'fields_get',
                [['sale_ok', 'purchase_ok']], {'attributes': ['type']}
            )
            
            if 'sale_ok' in field_info:
                product_vals['sale_ok'] = True
            
            if 'purchase_ok' in field_info:
                product_vals['purchase_ok'] = True
        except Exception:
            # These fields may not exist in all versions, so ignore errors
            pass
        
        # Add UOM if available
        if uom_id:
            # Check if uom_id and uom_po_id fields exist
            try:
                field_info = models.execute_kw(
                    config['db_name'], uid, config['password'],
                    'product.product', 'fields_get',
                    [['uom_id', 'uom_po_id']], {'attributes': ['type']}
                )
                
                if 'uom_id' in field_info:
                    product_vals['uom_id'] = uom_id
                
                if 'uom_po_id' in field_info:
                    product_vals['uom_po_id'] = uom_id
            except Exception:
                # These fields may not exist in all versions, so ignore errors
                pass
        
        print("\nAttempting to create liquor product with values:")
        print(json.dumps(product_vals, indent=2))
        
        try:
            product_id = models.execute_kw(
                config['db_name'], uid, config['password'],
                'product.product', 'create',
                [product_vals]
            )
            
            print(f"\nSuccess! Created liquor product with ID: {product_id}")
            
            # Get the created product
            created_product = models.execute_kw(
                config['db_name'], uid, config['password'],
                'product.product', 'read',
                [product_id],
                {'fields': ['id', 'name', 'type', 'categ_id', 'default_code', 'list_price', 'standard_price']}
            )
            
            print("\nCreated product details:")
            pprint(created_product[0])
            
            return created_product[0] if created_product else None
            
        except Exception as e:
            print(f"\nFailed to create product: {str(e)}")
            return None
        
    except Exception as e:
        print(f"Error in create_liquor_product: {str(e)}")
        return None