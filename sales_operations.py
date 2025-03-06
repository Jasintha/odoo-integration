"""
Functions for managing sales operations in Odoo.
"""
import datetime
from connection import get_model_connection

def check_sales_module_available(uid, config):
    """
    Check if the sales module is available in the Odoo instance.
    
    Args:
        uid (int): User ID for authentication
        config (dict): Configuration dictionary with Odoo connection parameters
        
    Returns:
        bool: True if sales module is available, False otherwise
    """
    if not uid:
        return False
    
    try:
        models = get_model_connection(config['url'])
        
        # Try to access the sale.order model
        try:
            models.execute_kw(
                config['db_name'], uid, config['password'],
                'sale.order', 'search',
                [[]], {'limit': 1}
            )
            return True
        except Exception:
            # Try alternative models that might exist
            try:
                models.execute_kw(
                    config['db_name'], uid, config['password'],
                    'pos.order', 'search',
                    [[]], {'limit': 1}
                )
                print("Note: Traditional Sales module is not available, but Point of Sale module is available.")
                return False
            except Exception:
                print("Note: Sales module is not available in this Odoo instance.")
                print("This is common in free/trial accounts where not all apps are installed.")
                print("You can still use the inventory management features.")
                return False
    except Exception as e:
        print(f"Error checking sales module: {str(e)}")
        return False

def create_customer(uid, config):
    """
    Create a sample customer if needed or return an existing one.
    
    Args:
        uid (int): User ID for authentication
        config (dict): Configuration dictionary with Odoo connection parameters
        
    Returns:
        int or None: Customer ID if successful, None otherwise
    """
    if not uid:
        return None
    
    if not check_sales_module_available(uid, config):
        print("Cannot create customer because sales module is not available.")
        return None
    
    try:
        models = get_model_connection(config['url'])
        
        # Try with customer_rank first (newer Odoo versions)
        try:
            # Check if we have any customers
            customers = models.execute_kw(
                config['db_name'], uid, config['password'],
                'res.partner', 'search_read',
                [[('customer_rank', '>', 0)]],
                {'fields': ['id', 'name', 'email'], 'limit': 5}
            )
            
            if customers:
                print("\nExisting customers:")
                for cust in customers:
                    print(f"  - ID: {cust['id']}, Name: {cust['name']}")
                return customers[0]['id']
            
            # Create a new customer if none exist
            customer_vals = {
                'name': 'Sample Customer',
                'email': 'sample@example.com',
                'phone': '+9412345678',
                'customer_rank': 1
            }
            
            customer_id = models.execute_kw(
                config['db_name'], uid, config['password'],
                'res.partner', 'create',
                [customer_vals]
            )
            
            print(f"\nCreated new customer with ID: {customer_id}")
            return customer_id
            
        except Exception as e:
            print(f"Error with customer_rank field: {str(e)}")
            
            # Try with customer field (older Odoo versions)
            customers = models.execute_kw(
                config['db_name'], uid, config['password'],
                'res.partner', 'search_read',
                [[('customer', '=', True)]],
                {'fields': ['id', 'name', 'email'], 'limit': 5}
            )
            
            if customers:
                print("\nExisting customers (using legacy API):")
                for cust in customers:
                    print(f"  - ID: {cust['id']}, Name: {cust['name']}")
                return customers[0]['id']
            
            # Create a new customer if none exist
            customer_vals = {
                'name': 'Sample Customer',
                'email': 'sample@example.com',
                'phone': '+9412345678',
                'customer': True
            }
            
            customer_id = models.execute_kw(
                config['db_name'], uid, config['password'],
                'res.partner', 'create',
                [customer_vals]
            )
            
            print(f"\nCreated new customer with ID: {customer_id} (using legacy API)")
            return customer_id
            
    except Exception as e:
        print(f"Error in create_customer: {str(e)}")
        return None

def create_sale_order(uid, config, product_id, customer_id, warehouse_id, quantity=1):
    """
    Create a sales order for a product.
    
    Args:
        uid (int): User ID for authentication
        config (dict): Configuration dictionary with Odoo connection parameters
        product_id (int): Product ID to sell
        customer_id (int): Customer ID for the sale
        warehouse_id (int): Warehouse ID for the sale
        quantity (float): Quantity to sell
        
    Returns:
        int or None: Sales order ID if successful, None otherwise
    """
    if not uid or not product_id or not customer_id:
        print("Missing required parameters for creating sale order")
        return None
    
    if not check_sales_module_available(uid, config):
        print("Cannot create sale order because sales module is not available.")
        print("You may need to activate the Sales app in your Odoo instance.")
        return None
    
    try:
        print(f"\n--- CREATING SALE ORDER FOR PRODUCT (ID: {product_id}) ---")
        models = get_model_connection(config['url'])
        
        # Get product info
        product = models.execute_kw(
            config['db_name'], uid, config['password'],
            'product.product', 'read',
            [product_id],
            {'fields': ['name', 'list_price']}
        )
        
        if not product:
            print(f"Product with ID {product_id} not found")
            return None
        
        product_name = product[0]['name']
        price = product[0]['list_price']
        
        # Create sale order
        print(f"Creating sale order for {quantity} units of '{product_name}' at {price} per unit")
        
        sale_order_vals = {
            'partner_id': customer_id,
            'date_order': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        if warehouse_id:
            sale_order_vals['warehouse_id'] = warehouse_id
        
        # Create the sale order
        order_id = models.execute_kw(
            config['db_name'], uid, config['password'],
            'sale.order', 'create',
            [sale_order_vals]
        )
        
        if not order_id:
            print("Failed to create sale order")
            return None
        
        # Create order line
        order_line_vals = {
            'order_id': order_id,
            'product_id': product_id,
            'product_uom_qty': quantity,
            'price_unit': price
        }
        
        line_id = models.execute_kw(
            config['db_name'], uid, config['password'],
            'sale.order.line', 'create',
            [order_line_vals]
        )
        
        print(f"Sale order created with ID: {order_id}")
        
        # Confirm the sale order
        try:
            result = models.execute_kw(
                config['db_name'], uid, config['password'],
                'sale.order', 'action_confirm',
                [[order_id]]
            )
            
            print("Sale order confirmed")
        except Exception as e:
            print(f"Warning: Could not confirm sale order: {str(e)}")
        
        # Get the details of the created order
        order = models.execute_kw(
            config['db_name'], uid, config['password'],
            'sale.order', 'read',
            [order_id],
            {'fields': ['name', 'state', 'amount_total']}
        )
        
        if order:
            print(f"Order: {order[0]['name']}, State: {order[0]['state']}, Total: {order[0]['amount_total']}")
        
        return order_id
        
    except Exception as e:
        print(f"Error in create_sale_order: {str(e)}")
        return None

def generate_sales_report(uid, config):
    """
    Generate sales report by location.
    
    Args:
        uid (int): User ID for authentication
        config (dict): Configuration dictionary with Odoo connection parameters
    """
    if not uid:
        return
    
    if not check_sales_module_available(uid, config):
        print("Cannot generate sales report because sales module is not available.")
        
        # Try to generate an inventory report instead as a fallback
        try:
            print("\nGenerating inventory report as an alternative...")
            from inventory_operations import generate_inventory_report
            generate_inventory_report(uid, config)
        except Exception as e:
            print(f"Could not generate alternative report: {str(e)}")
        return
    
    try:
        print("\n--- GENERATING SALES REPORT ---")
        models = get_model_connection(config['url'])
        
        # Get warehouses
        warehouses = models.execute_kw(
            config['db_name'], uid, config['password'],
            'stock.warehouse', 'search_read',
            [[]],
            {'fields': ['id', 'name']}
        )
        
        # Create warehouse lookup dictionary
        warehouse_dict = {wh['id']: wh['name'] for wh in warehouses}
        
        # Get confirmed sales orders
        sales = models.execute_kw(
            config['db_name'], uid, config['password'],
            'sale.order', 'search_read',
            [[['state', 'in', ['sale', 'done']]]],
            {'fields': ['name', 'warehouse_id', 'amount_total', 'date_order', 'partner_id']}
        )
        
        if not sales:
            print("No confirmed sales orders found")
            return
        
        # Organize sales by warehouse
        sales_by_warehouse = {}
        
        for sale in sales:
            warehouse_id = sale.get('warehouse_id', (0, 'Unknown'))[0] if isinstance(sale.get('warehouse_id'), tuple) else sale.get('warehouse_id', 0)
            
            if warehouse_id not in sales_by_warehouse:
                sales_by_warehouse[warehouse_id] = []
            
            sales_by_warehouse[warehouse_id].append(sale)
        
        # Print location-wise sales report
        print("\nLocation-wise Sales Report:")
        print("-" * 100)
        print(f"{'Warehouse':<20} {'Order':<15} {'Customer':<25} {'Date':<20} {'Total':<10}")
        print("-" * 100)
        
        total_sales = 0
        
        for wh_id, orders in sales_by_warehouse.items():
            warehouse_name = warehouse_dict.get(wh_id, "Unknown")
            
            for order in orders:
                order_name = order['name']
                customer_name = order['partner_id'][1] if isinstance(order.get('partner_id'), tuple) else "Unknown"
                date_order = order.get('date_order', 'Unknown')
                amount = order.get('amount_total', 0)
                
                print(f"{warehouse_name:<20} {order_name:<15} {customer_name:<25} {date_order:<20} {amount:<10.2f}")
                total_sales += amount
        
        # Print consolidated sales report
        print("\nConsolidated Sales Report:")
        print("-" * 50)
        print(f"Total number of orders: {len(sales)}")
        print(f"Total sales amount: {total_sales:.2f}")
        
        # Get sales breakdown by product
        print("\nSales Breakdown by Product:")
        print("-" * 70)
        print(f"{'Product':<30} {'Quantity':<10} {'Revenue':<15} {'Profit':<15}")
        print("-" * 70)
        
        # Get all order lines
        order_ids = [sale['id'] for sale in sales]
        
        if order_ids:
            try:
                order_lines = models.execute_kw(
                    config['db_name'], uid, config['password'],
                    'sale.order.line', 'search_read',
                    [[['order_id', 'in', order_ids]]],
                    {'fields': ['product_id', 'product_uom_qty', 'price_subtotal', 'margin']}
                )
                
                product_sales = {}
                
                for line in order_lines:
                    product_id = line['product_id'][0] if isinstance(line.get('product_id'), tuple) else line.get('product_id', 0)
                    
                    if product_id not in product_sales:
                        product_sales[product_id] = {
                            'name': line['product_id'][1] if isinstance(line.get('product_id'), tuple) else f"Product {product_id}",
                            'quantity': 0,
                            'revenue': 0,
                            'profit': 0
                        }
                    
                    product_sales[product_id]['quantity'] += line.get('product_uom_qty', 0)
                    product_sales[product_id]['revenue'] += line.get('price_subtotal', 0)
                    product_sales[product_id]['profit'] += line.get('margin', 0)
                
                # Print product breakdown
                for product_id, data in product_sales.items():
                    print(f"{data['name']:<30} {data['quantity']:<10.2f} {data['revenue']:<15.2f} {data['profit']:<15.2f}")
            
            except Exception as e:
                print(f"Could not generate product breakdown: {str(e)}")
        
    except Exception as e:
        print(f"Error generating sales report: {str(e)}")
        # Try to generate an inventory report as a fallback
        try:
            print("\nGenerating inventory report as an alternative...")
            from inventory_operations import generate_inventory_report
            generate_inventory_report(uid, config)
        except Exception as e2:
            print(f"Could not generate alternative report: {str(e2)}")