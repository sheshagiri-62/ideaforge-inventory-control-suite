import os

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from src.auth import AuthManager
from src.config import LOW_STOCK_THRESHOLD
from src.product_manager import ProductManager
from src.storage import StorageManager
from src.supplier_manager import SupplierManager


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "development-only-change-me")

    storage = StorageManager()
    product_manager = ProductManager(storage)
    supplier_manager = SupplierManager(storage)
    auth_manager = AuthManager(storage)

    def require_login():
        return bool(session.get("logged_in"))

    def get_dashboard_stats():
        products = product_manager.get_all_products()
        suppliers = supplier_manager.get_all_suppliers()
        low_stock = product_manager.get_low_stock_products(LOW_STOCK_THRESHOLD)
        total_inventory_value = sum(float(item.get("price", 0)) * int(item.get("stock", 0)) for item in products)

        return {
            "products": len(products),
            "suppliers": len(suppliers),
            "low_stock": len(low_stock),
            "inventory_value": round(total_inventory_value, 2),
            "username": session.get("username", "Guest"),
            "role": session.get("role", "guest"),
        }

    @app.route('/')
    def index():
        if session.get("logged_in"):
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if session.get("logged_in"):
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            data = request.get_json(silent=True) or request.form
            username = (data.get('username') or '').strip()
            password = data.get('password') or ''

            if auth_manager.login(username, password):
                session['logged_in'] = True
                session['username'] = auth_manager.get_current_username()
                session['role'] = auth_manager.current_user.get('role', 'user')

                if request.is_json:
                    return jsonify({
                        "success": True,
                        "username": session['username'],
                        "role": session['role'],
                    })

                return redirect(url_for('dashboard'))

            message = 'Invalid username or password.'
            if request.is_json:
                return jsonify({"success": False, "message": message}), 401
            return render_template('login.html', error=message)

        return render_template('login.html')

    @app.route('/dashboard')
    def dashboard():
        if not require_login():
            return redirect(url_for('login'))
        return render_template('dashboard.html', stats=get_dashboard_stats())

    @app.route('/products')
    def products_page():
        if not require_login():
            return redirect(url_for('login'))
        return render_template('products.html', stats=get_dashboard_stats())

    @app.route('/suppliers')
    def suppliers_page():
        if not require_login():
            return redirect(url_for('login'))
        return render_template('suppliers.html', stats=get_dashboard_stats())

    @app.route('/orders')
    def orders_page():
        if not require_login():
            return redirect(url_for('login'))
        return render_template('orders.html', stats=get_dashboard_stats())

    @app.route('/reports')
    def reports_page():
        if not require_login():
            return redirect(url_for('login'))
        return render_template('reports.html', stats=get_dashboard_stats())

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))

    @app.route('/api/stats')
    def stats():
        if not require_login():
            return jsonify({"success": False, "message": "Authentication required."}), 401
        return jsonify(get_dashboard_stats())

    @app.route('/api/products', methods=['GET', 'POST'])
    def products_api():
        if not require_login():
            return jsonify({"success": False, "message": "Authentication required."}), 401

        if request.method == 'GET':
            return jsonify(product_manager.get_all_products())

        data = request.get_json(silent=True) or {}
        sku = (data.get('sku') or '').strip()
        name = (data.get('name') or '').strip()
        price = data.get('price')
        category = (data.get('category') or '').strip()
        stock = data.get('stock')
        description = (data.get('description') or '').strip()

        if not sku or not name or not category:
            return jsonify({"success": False, "message": "SKU, name, and category are required."}), 400

        try:
            price_value = float(price)
            stock_value = int(stock)
        except (TypeError, ValueError):
            return jsonify({"success": False, "message": "Price and stock must be valid numbers."}), 400

        if price_value < 0 or stock_value < 0:
            return jsonify({"success": False, "message": "Price and stock cannot be negative."}), 400

        result = product_manager.add_product_with_confirmation(
            sku=sku,
            name=name,
            price=price_value,
            category=category,
            stock=stock_value,
            description=description,
            user=session.get('username', 'admin'),
        )

        if not result.get('success'):
            return jsonify({"success": False, "message": result.get('message', 'Unable to add product.')}), 400

        return jsonify({"success": True, "message": result.get('message'), "product": result.get('product')}), 201

    @app.route('/api/suppliers', methods=['GET', 'POST'])
    def suppliers_api():
        if not require_login():
            return jsonify({"success": False, "message": "Authentication required."}), 401

        if request.method == 'GET':
            return jsonify(supplier_manager.get_all_suppliers())

        data = request.get_json(silent=True) or {}
        name = (data.get('name') or '').strip()
        if not name:
            return jsonify({"success": False, "message": "Supplier name is required."}), 400

        supplier_id = supplier_manager.add_supplier(
            name=name,
            contact_person=(data.get('contact_person') or '').strip(),
            email=(data.get('email') or '').strip(),
            phone=(data.get('phone') or '').strip(),
            address=(data.get('address') or '').strip(),
            user=session.get('username', 'admin'),
        )

        created = supplier_manager.get_supplier(supplier_id)
        return jsonify({"success": True, "supplier": created}), 201

    @app.route('/api/low-stock')
    def low_stock_api():
        if not require_login():
            return jsonify({"success": False, "message": "Authentication required."}), 401
        return jsonify(product_manager.get_low_stock_products(LOW_STOCK_THRESHOLD))

    @app.route('/api/auth/login', methods=['POST'])
    def login_api():
        if not request.is_json:
            return jsonify({"success": False, "message": "JSON request required."}), 400

        data = request.get_json(silent=True) or {}
        username = (data.get('username') or '').strip()
        password = data.get('password') or ''

        if auth_manager.login(username, password):
            session['logged_in'] = True
            session['username'] = auth_manager.get_current_username()
            session['role'] = auth_manager.current_user.get('role', 'user')
            return jsonify({
                "success": True,
                "username": session['username'],
                "role": session['role'],
            })

        return jsonify({"success": False, "message": "Invalid username or password."}), 401

    @app.route('/api/auth/logout', methods=['POST'])
    def logout_api():
        session.clear()
        return jsonify({"success": True, "message": "Logged out."})

    return app


app = create_app()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
