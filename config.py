"""
Configuration settings for the Odoo integration.
"""

# Odoo connection parameters
ODOO_CONFIG = {
    'url': 'https://ncinga.odoo.com',
    'db_name': 'ncinga',
    'username': 'xxxxx@gmail.com',
    'password': 'xxxxxxxxxx'  # You should change this password after using this script
}

# Product configuration
PRODUCT_CONFIG = {
    'default_liquor_name': 'Premium Whiskey',
    'default_liquor_code': 'WHISKY001',
    'default_sales_price': 45.99,
    'default_cost_price': 30.00,
}

# Default quantities for inventory
INVENTORY_CONFIG = {
    'default_stock_quantity': 10
}