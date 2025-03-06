#!/usr/bin/env python3
"""
Odoo Integration Main Script
This script provides a menu-driven interface to interact with Odoo.
"""
import sys
from config import ODOO_CONFIG
from connection import test_connection
from product_operations import (
    inspect_existing_products,
    inspect_product_fields,
    create_liquor_product
)
from inventory_operations import (
    get_warehouses,
    get_stock_locations,
    add_product_to_warehouse,
    generate_inventory_report
)
from sales_operations import (
    create_customer,
    create_sale_order,
    generate_sales_report
)

def main():
    """Main function to orchestrate the entire process."""
    uid = test_connection(
        ODOO_CONFIG['url'],
        ODOO_CONFIG['db_name'],
        ODOO_CONFIG['username'],
        ODOO_CONFIG['password']
    )
    
    if not uid:
        print("Authentication failed. Cannot proceed.")
        return
    
    while True:
        print("\n" + "=" * 60)
        print("ENHANCED ODOO PRODUCT MANAGER")
        print("=" * 60)
        print("1. Inspect existing products")
        print("2. Inspect product fields and valid values")
        print("3. Create new liquor product")
        print("4. Add liquor product to warehouses")
        print("5. Process a sale")
        print("6. Generate inventory report")
        print("7. Generate sales report")
        print("8. Run complete process (steps 3-7)")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-8): ")
        
        if choice == '1':
            inspect_existing_products(uid, ODOO_CONFIG)
        elif choice == '2':
            inspect_product_fields(uid, ODOO_CONFIG)
        elif choice == '3':
            create_liquor_product(uid, ODOO_CONFIG)
        elif choice == '4':
            handle_add_product_to_warehouses(uid, ODOO_CONFIG)
        elif choice == '5':
            handle_create_sale(uid, ODOO_CONFIG)
        elif choice == '6':
            generate_inventory_report(uid, ODOO_CONFIG)
        elif choice == '7':
            generate_sales_report(uid, ODOO_CONFIG)
        elif choice == '8':
            run_complete_process(uid, ODOO_CONFIG)
        elif choice == '0':
            print("\nExiting. Thank you!")
            break
        else:
            print("\nInvalid choice. Please try again.")

def handle_add_product_to_warehouses(uid, config):
    """Handle the process of adding a product to warehouses."""
    # Get warehouses and locations
    warehouses = get_warehouses(uid, config)
    
    if not warehouses:
        print("No warehouses found")
        return
    
    # Get products
    products = inspect_existing_products(uid, config)
    
    if not products:
        print("No products found")
        return
    
    # Select product
    print("\nSelect a product to add to warehouses:")
    for i, product in enumerate(products):
        print(f"{i+1}. {product['name']} (ID: {product['id']})")
    
    try:
        product_idx = int(input("Enter product number: ")) - 1
        if product_idx < 0 or product_idx >= len(products):
            print("Invalid product selection")
            return
    except ValueError:
        print("Please enter a valid number")
        return
    
    product_id = products[product_idx]['id']
    
    # Add to each warehouse
    for wh in warehouses:
        if wh.get('lot_stock_id'):
            location_id = wh['lot_stock_id'][0]
            try:
                quantity_input = input(f"Enter quantity to add to {wh['name']} (leave empty for 10): ")
                quantity = float(quantity_input) if quantity_input.strip() else 10
                add_product_to_warehouse(uid, config, product_id, location_id, quantity)
            except ValueError:
                print("Please enter a valid number. Using default quantity of 10.")
                add_product_to_warehouse(uid, config, product_id, location_id, 10)

def handle_create_sale(uid, config):
    """Handle the process of creating a sale."""
    # Get products
    products = inspect_existing_products(uid, config)
    
    if not products:
        print("No products found")
        return
    
    # Select product
    print("\nSelect a product to sell:")
    for i, product in enumerate(products):
        print(f"{i+1}. {product['name']} (ID: {product['id']})")
    
    try:
        product_idx = int(input("Enter product number: ")) - 1
        if product_idx < 0 or product_idx >= len(products):
            print("Invalid product selection")
            return
    except ValueError:
        print("Please enter a valid number")
        return
    
    product_id = products[product_idx]['id']
    
    # Get customer
    customer_id = create_customer(uid, config)
    
    if not customer_id:
        print("Could not create or find a customer")
        return
    
    # Get warehouses
    warehouses = get_warehouses(uid, config)
    
    if not warehouses:
        print("No warehouses found")
        return
    
    # Select warehouse
    print("\nSelect a warehouse for the sale:")
    for i, wh in enumerate(warehouses):
        print(f"{i+1}. {wh['name']} (ID: {wh['id']})")
    
    try:
        wh_idx = int(input("Enter warehouse number: ")) - 1
        if wh_idx < 0 or wh_idx >= len(warehouses):
            print("Invalid warehouse selection")
            return
    except ValueError:
        print("Please enter a valid number")
        return
    
    warehouse_id = warehouses[wh_idx]['id']
    
    # Get quantity
    try:
        quantity_input = input("Enter quantity to sell (leave empty for 1): ")
        quantity = float(quantity_input) if quantity_input.strip() else 1
    except ValueError:
        print("Please enter a valid number. Using default quantity of 1.")
        quantity = 1
    
    # Create sale
    create_sale_order(uid, config, product_id, customer_id, warehouse_id, quantity)

def run_complete_process(uid, config):
    """Run the complete process from creating a product to generating reports."""
    print("\n--- RUNNING COMPLETE PROCESS ---")
    
    # Step 3: Create liquor product
    liquor_product = create_liquor_product(uid, config)
    
    if not liquor_product:
        print("Failed to create liquor product. Aborting process.")
        return
    
    product_id = liquor_product['id']
    
    # Step 4: Add to warehouses
    warehouses = get_warehouses(uid, config)
    
    if not warehouses:
        print("No warehouses found. Aborting process.")
        return
    
    # Add product to each warehouse with different quantities
    quantities = [15, 20, 25]  # Different quantities for different warehouses
    
    for i, wh in enumerate(warehouses):
        if wh.get('lot_stock_id'):
            location_id = wh['lot_stock_id'][0]
            # Use modulo to cycle through quantities if we have more warehouses than quantities
            quantity = quantities[i % len(quantities)]
            print(f"Adding {quantity} units to {wh['name']}...")
            add_product_to_warehouse(uid, config, product_id, location_id, quantity)
    
    # Step 5: Create a sale if the sales module is available
    from sales_operations import check_sales_module_available
    sales_available = check_sales_module_available(uid, config)
    
    if sales_available:
        customer_id = create_customer(uid, config)
        
        if customer_id and warehouses:
            warehouse_id = warehouses[0]['id']
            print(f"Creating sale in warehouse: {warehouses[0]['name']}")
            create_sale_order(uid, config, product_id, customer_id, warehouse_id, 5)
    else:
        print("Skipping sales process since sales module is not available.")
    
    # Step 6: Generate inventory report
    print("\nGenerating inventory report...")
    generate_inventory_report(uid, config)
    
    # Step 7: Generate sales report if the sales module is available
    if sales_available:
        print("\nGenerating sales report...")
        generate_sales_report(uid, config)
    
    print("\n--- COMPLETE PROCESS FINISHED ---")  
    print("\n--- COMPLETE PROCESS FINISHED ---")

if __name__ == "__main__":
    main()