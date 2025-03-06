#!/usr/bin/env python3
import xmlrpc.client
import json
from pprint import pprint

# Connection parameters
url = 'https://ncinga.odoo.com'
db_name = 'ncinga'
username = 'jasinthad@gmail.com'
password = 'WY!hM4_!*_,Ve)j'  # You should change this password after using this script

def test_connection():
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

def inspect_existing_products(uid):
    if not uid:
        return
    
    try:
        print("\n--- INSPECTING EXISTING PRODUCTS ---")
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        
        # Get all products
        products = models.execute_kw(
            db_name, uid, password,
            'product.product', 'search_read',
            [[]],
            {'fields': ['id', 'name', 'default_code', 'type', 'categ_id', 'list_price', 'standard_price']}
        )
        
        if not products:
            print("No products found in the system.")
            return
        
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
            
            # Get additional detailed information about the product
            product_template = models.execute_kw(
                db_name, uid, password,
                'product.template', 'search_read',
                [[('id', '=', product['id'])]],
                {'fields': []}
            )
            
            if product_template:
                print("\nProduct Template Full Data:")
                pprint(product_template[0])
                
    except Exception as e:
        print(f"Error inspecting products: {str(e)}")

def inspect_product_fields(uid):
    if not uid:
        return
    
    try:
        print("\n--- INSPECTING PRODUCT FIELDS ---")
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        
        # Get fields for product.product model
        product_fields = models.execute_kw(
            db_name, uid, password,
            'product.product', 'fields_get',
            [], {'attributes': ['string', 'help', 'type']}
        )
        
        print("\nProduct Fields:")
        for field_name, field_data in sorted(product_fields.items()):
            if field_name in ['name', 'type', 'categ_id', 'default_code', 'list_price', 'standard_price']:
                print(f"\n{field_name}:")
                print(f"  Label: {field_data.get('string', 'N/A')}")
                print(f"  Type: {field_data.get('type', 'N/A')}")
                print(f"  Help: {field_data.get('help', 'N/A')}")
        
        # Specifically check the 'type' field for valid options
        type_field = models.execute_kw(
            db_name, uid, password,
            'ir.model.fields', 'search_read',
            [[('model', '=', 'product.template'), ('name', '=', 'type')]],
            {'fields': ['selection', 'ttype']}
        )
        
        if type_field:
            print("\nProduct Type Field Options:")
            if 'selection' in type_field[0] and type_field[0]['selection']:
                for option in type_field[0]['selection']:
                    print(f"  - {option[0]}: {option[1]}")
            else:
                print("  Could not retrieve selection options")
        
    except Exception as e:
        print(f"Error inspecting product fields: {str(e)}")

def create_sample_product(uid):
    if not uid:
        return
    
    try:
        print("\n--- ATTEMPTING TO CREATE A PRODUCT WITH MINIMAL FIELDS ---")
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        
        # Get product categories
        categories = models.execute_kw(
            db_name, uid, password,
            'product.category', 'search_read',
            [[]],
            {'fields': ['id', 'name']}
        )
        
        if not categories:
            print("No product categories found.")
            return
        
        print("Available categories:")
        for cat in categories:
            print(f"  - ID: {cat['id']}, Name: {cat['name']}")
        
        category_id = categories[0]['id']  # Use first category
        
        # Create minimal product
        product_vals = {
            'name': 'Test Product (API)',
            'categ_id': category_id,
            # Don't set type or other fields to see what defaults are used
        }
        
        print("\nAttempting to create product with values:")
        print(json.dumps(product_vals, indent=2))
        
        try:
            product_id = models.execute_kw(
                db_name, uid, password,
                'product.product', 'create',
                [product_vals]
            )
            
            print(f"\nSuccess! Created product with ID: {product_id}")
            
            # Get the created product to see what fields were automatically set
            created_product = models.execute_kw(
                db_name, uid, password,
                'product.product', 'read',
                [product_id],
                {'fields': ['id', 'name', 'type', 'categ_id', 'default_code', 'list_price', 'standard_price']}
            )
            
            print("\nCreated product details:")
            pprint(created_product[0])
            
        except Exception as e:
            print(f"\nFailed to create product: {str(e)}")
        
    except Exception as e:
        print(f"Error in create_sample_product: {str(e)}")

def main1():
    uid = test_connection()
    
    if not uid:
        print("Authentication failed. Cannot proceed.")
        return
    
    while True:
        print("\n" + "=" * 60)
        print("ODOO PRODUCT INSPECTOR")
        print("=" * 60)
        print("1. Inspect existing products")
        print("2. Inspect product fields and valid values")
        print("3. Attempt to create a minimal test product")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-3): ")
        
        if choice == '1':
            inspect_existing_products(uid)
        elif choice == '2':
            inspect_product_fields(uid)
        elif choice == '3':
            create_sample_product(uid)
        elif choice == '0':
            print("\nExiting. Thank you!")
            break
        else:
            print("\nInvalid choice. Please try again.")

 