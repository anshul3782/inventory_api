import pymysql
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)

# ✅ Enable CORS for all routes
CORS(app, resources={r"/*": {"origins": "*"}})
# Database connection details
DB_CONFIG = {
    'host': 'db-mysql-nyc3-54076-do-user-19716193-0.k.db.ondigitalocean.com',
    'user': 'doadmin',
    'password': 'AVNS_oAN9S2VKGNizJx9BtBA',
    'database': 'hackforge',
    'port': 25060,
    'ssl': {'ssl': {}},  # SSL mode required
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    """Establish a connection to the MySQL database"""
    return pymysql.connect(**DB_CONFIG)

# View all inventory data
@app.route('/api/inventory', methods=['GET'])
def get_all_inventory():
    """Get all inventory items"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM Inventory")
        inventory_items = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "status": "success",
            "count": len(inventory_items),
            "inventory": inventory_items
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Get a specific field value
@app.route('/api/inventory/<path:product_name>/field/<field_name>', methods=['GET'])
def get_field_value(product_name, field_name):
    """Get a specific field value for a product"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if the field exists in the table
        cursor.execute("SHOW COLUMNS FROM Inventory")
        columns = [column['Field'] for column in cursor.fetchall()]
        
        if field_name not in columns:
            return jsonify({
                "status": "error", 
                "message": f"Field '{field_name}' does not exist. Available fields: {', '.join(columns)}"
            }), 400
        
        # Get the field value
        cursor.execute(f"SELECT {field_name} FROM Inventory WHERE Product = %s", (product_name,))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not result:
            return jsonify({
                "status": "error", 
                "message": f"Product '{product_name}' not found"
            }), 404
        
        return jsonify({
            "status": "success",
            "product": product_name,
            "field": field_name,
            "value": result[field_name]
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Set a specific field value
@app.route('/api/inventory/<path:product_name>/field/<field_name>', methods=['PUT'])
def set_field_value(product_name, field_name):
    """Set a specific field value for a product"""
    try:
        # Get the new value from request body
        data = request.get_json()
        if not data or 'value' not in data:
            return jsonify({
                "status": "error",
                "message": "Request body must contain a 'value' field"
            }), 400
        
        new_value = data['value']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if the field exists in the table
        cursor.execute("SHOW COLUMNS FROM Inventory")
        columns = [column['Field'] for column in cursor.fetchall()]
        
        if field_name not in columns:
            cursor.close()
            conn.close()
            return jsonify({
                "status": "error", 
                "message": f"Field '{field_name}' does not exist. Available fields: {', '.join(columns)}"
            }), 400
        
        # Don't allow updating the primary key
        if field_name == 'Product':
            cursor.close()
            conn.close()
            return jsonify({
                "status": "error",
                "message": "Cannot update the Product field as it is the primary key"
            }), 400
        
        # Check if the product exists
        cursor.execute("SELECT 1 FROM Inventory WHERE Product = %s", (product_name,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                "status": "error",
                "message": f"Product '{product_name}' not found"
            }), 404
        
        # Update the field
        cursor.execute(f"UPDATE Inventory SET {field_name} = %s WHERE Product = %s", 
                     (new_value, product_name))
        conn.commit()
        
        # Get the updated record
        cursor.execute("SELECT * FROM Inventory WHERE Product = %s", (product_name,))
        updated_item = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "status": "success",
            "message": f"Field '{field_name}' updated successfully",
            "updated_item": updated_item
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    """Home route with API documentation"""
    return jsonify({
        "status": "online",
        "message": "Inventory Management API",
        "endpoints": {
            "/api/inventory": "GET - View all inventory data",
            "/api/inventory/<product_name>/field/<field_name>": {
                "GET": "Get a specific field value for a product",
                "PUT": "Set a specific field value for a product"
            }
        }
    })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
