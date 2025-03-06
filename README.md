# Odoo Inventory & Sales Management CLI

A command-line interface (CLI) application for managing inventory and sales operations in Odoo through the XML-RPC API.

## Overview

This application provides a comprehensive set of tools for interacting with Odoo's inventory and sales systems, allowing you to:

- Create and inspect products
- Add inventory to warehouse locations
- Process sales orders
- Generate inventory and sales reports

The modular design allows for easy extension and customization to fit specific business needs.

## Features

- **Product Management**
  - Create new products (with focus on liquor products)
  - Inspect existing products
  - View product fields and valid values

- **Inventory Management**
  - View warehouses and stock locations
  - Add product inventory to specific locations
  - Generate detailed inventory reports

- **Sales Operations** (if Sales module is available)
  - Create customers
  - Process sales orders
  - Generate location-wise and consolidated sales reports

- **Automated Workflows**
  - Complete end-to-end processing from product creation to reporting

## System Requirements

- Python 3.6+
- Network access to your Odoo instance
- Valid Odoo user credentials with appropriate permissions

## Installation

1. Clone or download this repository
2. Update the `config.py` file with your Odoo connection details:
   ```python
   ODOO_CONFIG = {
       'url': 'https://your-odoo-instance.com',
       'db_name': 'your_database',
       'username': 'your_username',
       'password': 'your_password'
   }
   ```

## File Structure

- `main.py` - Main script with the CLI interface
- `config.py` - Configuration settings
- `connection.py` - Odoo connection handling
- `product_operations.py` - Product management functions
- `inventory_operations.py` - Inventory management functions
- `sales_operations.py` - Sales operations functions

## Usage

Run the main script to start the application:

```
python main.py
```

You'll be presented with a menu of options:

```
ENHANCED ODOO PRODUCT MANAGER
============================================================
1. Inspect existing products
2. Inspect product fields and valid values
3. Create new liquor product
4. Add liquor product to warehouses
5. Process a sale
6. Generate inventory report
7. Generate sales report
8. Run complete process (steps 3-7)
0. Exit
```

### Creating a New Product

Select option 3 to create a new product. You'll be prompted for:
- Product name
- Product code
- Sales price
- Cost price

### Adding Inventory

Select option 4 to add product inventory to warehouses. You'll need to:
1. Select a product from the list
2. Specify quantity for each warehouse

### Processing a Sale

Select option 5 to create a sales order. If the Sales module is available, you'll:
1. Select a product to sell
2. Choose a customer (or create one)
3. Select a warehouse
4. Specify quantity

### Generating Reports

Options 6 and 7 allow you to generate inventory and sales reports, which show:
- Location-wise inventory levels
- Consolidated inventory totals
- Sales breakdown by location and product

### Automated Workflow

Option 8 runs a complete process that:
1. Creates a new liquor product
2. Adds inventory to all warehouses
3. Processes a sale (if Sales module is available)
4. Generates inventory and sales reports

## Customization

### Adding New Product Types

To add support for different product types, modify the `create_liquor_product` function in `product_operations.py`:

```python
# Modify the product_vals dictionary to include type-specific fields
product_vals = {
    'name': product_name,
    'categ_id': category_id,
    'type': 'product',
    # Add additional fields here
}
```

### Supporting Additional Odoo Versions

The code includes fallbacks for different Odoo versions. If you need to support other versions:

1. Add version detection in the connection module
2. Include version-specific code paths in the operation functions

## Technical Details

### Integration Method

This application uses Odoo's XML-RPC API for integration, rather than the newer REST API. XML-RPC provides direct access to Odoo's object methods through remote procedure calls.

Key XML-RPC endpoints used:
- `/xmlrpc/2/common` - For authentication and server info
- `/xmlrpc/2/object` - For model operations

### Error Handling

The application includes comprehensive error handling to:
- Detect available models and methods
- Try alternative approaches if primary methods fail
- Provide meaningful error messages

## Limitations

- The Sales functionality requires the Sales module to be installed in Odoo
- Some complex operations may require additional permissions
- The application is designed primarily for command-line usage and batch operations
- Free/trial Odoo accounts may have limited module availability

## Security Considerations

- Store your Odoo credentials securely and change them regularly
- Consider using API keys instead of user passwords when available
- Restrict user permissions to only what's necessary for the operations

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.