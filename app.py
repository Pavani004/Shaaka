import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import razorpay
from geopy.geocoders import Nominatim

# Function to get latitude and longitude
def get_coordinates(address):
    geolocator = Nominatim(user_agent="farmer_market")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    return None, None

razorpay_client = razorpay.Client(auth=("YOUR_RAZORPAY_KEY", "YOUR_RAZORPAY_SECRET"))

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)

# MySQL Database Setup
db_config = {
    'host': 'localhost',
    'user': 'root',  # Change this to your MySQL username
    'password': '',  # Change this to your MySQL password
    'database': 'farmer_market'
}

# Setup Login Manager
login_manager = LoginManager()
login_manager.init_app(app)

# MySQL connection function
def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',  # Your MySQL user
        password='KARTHIK@2004',  # Your MySQL password
        database='farmer_market'  # Your database name
    )
    return conn

# User class for Flask-Login

class Customer(UserMixin):
    def __init__(self, id, name, phone, email, password, profile_pic=None, latitude=None, longitude=None):
        self.id = id
        self.name = name
        self.phone = phone
        self.email = email
        self.password = password
        self.profile_pic = profile_pic
        self.latitude = latitude
        self.longitude = longitude

    def get_id(self):
        return str(self.id)


# User Loader for Flask-Login
from flask_login import UserMixin

# Define User class
class User(UserMixin):
    def __init__(self, id, name, phone, password, profile_pic=None, latitude=None, longitude=None):
        self.id = id
        self.name = name
        self.phone = phone
        self.password = password
        self.profile_pic = profile_pic  # Add profile_pic
        self.latitude = latitude  # Add latitude
        self.longitude = longitude  # Add longitude

    def get_id(self):
        return str(self.id)

# User Loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM farmers WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return User(id=user['id'], name=user['name'], phone=user['phone'], password=user['password'], profile_pic=user['profile_pic'])
    return None


# Route to Home Page
@app.route('/')
def home():
    return render_template('index.html')

# Route to Farmer Registration Page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        address = request.form['address']
        aadhar = request.form['aadhar']
        password = request.form['password']
        profile_pic = request.files['profile_pic']

        # Get latitude and longitude from address
        latitude, longitude = get_coordinates(address)

        # Hash the password before saving
        hashed_password = generate_password_hash(password)

        if profile_pic:
            filename = secure_filename(profile_pic.filename)
            profile_pic.save(os.path.join('static/uploads', filename))
        else:
            filename = 'default.jpg'  # Default image if not provided

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO farmers (name, phone, address, aadhar, password, profile_pic, latitude, longitude) 
                          VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''', 
                       (name, phone, address, aadhar, hashed_password, filename, latitude, longitude))
        conn.commit()
        conn.close()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Route to Farmer Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM farmers WHERE phone = %s", (phone,))
        user = cursor.fetchone()
        conn.close()

        if user:
            stored_password = user['password']  # Accessing password by column name
            if check_password_hash(stored_password, password):  # Verify the hashed password
                user_obj = User(id=user['id'], name=user['name'], phone=user['phone'], password=user['password'])
                login_user(user_obj)
                return redirect(url_for('farmer_dashboard'))
            else:
                flash('Invalid password. Please try again.', 'danger')
        else:
            flash('No account found with that phone number.', 'danger')

    return render_template('login.html')

@app.route('/proceed_to_payment/<int:total_amount>', methods=['GET', 'POST'])
def proceed_to_payment(total_amount):
    if 'customer_id' not in session:
        flash('Please login to proceed with payment.', 'warning')
        return redirect(url_for('customer_login'))

    # Razorpay Order Creation
    payment_order = razorpay_client.order.create({
        "amount": total_amount * 100,  # Razorpay works with paise
        "currency": "INR",
        "payment_capture": "1"
    })

    return render_template('payment.html', payment_order=payment_order, total_amount=total_amount)

@app.route('/customer_register', methods=['GET', 'POST'])
def customer_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        password = request.form['password']

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO customers (name, email, phone, address, password) 
                          VALUES (%s, %s, %s, %s, %s)''', 
                       (name, email, phone, address, hashed_password))
        conn.commit()
        conn.close()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('customer_login'))

    return render_template('customer_register.html')


# Customer Login Route
@app.route('/customer_login', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM customers WHERE email = %s', (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            user_obj = UserMixin()  # UserMixin creates a user-like object
            user_obj.id = user['id']
            user_obj.name = user['name']
            login_user(user_obj)
            return redirect(url_for('customer_dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')

    return render_template('customer_login.html')

@app.route('/customer_dashboard', methods=['GET'])
@login_required
def customer_dashboard():
    # Assuming the customer has a 'latitude' and 'longitude' stored
    customer_lat = current_user.latitude
    customer_long = current_user.longitude

    # Location filter (from dropdown)
    location_filter = request.args.get('location')
    if location_filter:
        location_filter = int(location_filter)
        query = """
            SELECT *, 
            (6371 * acos(cos(radians(%s)) * cos(radians(f.latitude)) 
            * cos(radians(f.longitude) - radians(%s)) 
            + sin(radians(%s)) * sin(radians(f.latitude)))) AS distance 
            FROM crops c 
            JOIN farmers f ON c.farmer_id = f.id 
            WHERE f.location_id = %s
            ORDER BY distance;
        """
        params = (customer_lat, customer_long, customer_lat, location_filter)
    else:
        query = """
            SELECT *, 
            (6371 * acos(cos(radians(%s)) * cos(radians(f.latitude)) 
            * cos(radians(f.longitude) - radians(%s)) 
            + sin(radians(%s)) * sin(radians(f.latitude)))) AS distance 
            FROM crops c 
            JOIN farmers f ON c.farmer_id = f.id
            ORDER BY distance;
        """
        params = (customer_lat, customer_long, customer_lat)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params)
    crops = cursor.fetchall()

    # Fetch all locations for the dropdown
    cursor.execute("SELECT * FROM locations")
    locations = cursor.fetchall()

    conn.close()
    return render_template('customer_dashboard.html', crops=crops, locations=locations)

# Route to Farmer Dashboard (only for logged-in farmers)
@app.route('/farmer_dashboard')
@login_required
def farmer_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT crops.id, crops.crop_name, crops.quantity, crops.price_per_kg, crops.image, 
               COUNT(DISTINCT orders.customer_id) AS customer_count
        FROM crops 
        LEFT JOIN orders ON crops.id = orders.crop_id
        WHERE crops.farmer_id = %s
        GROUP BY crops.id
    ''', (current_user.id,))
    crops = cursor.fetchall()
    conn.close()

    return render_template('farmer_dashboard.html',farmer=current_user, crops=crops)


# Route to Add Crop (via Upload Form)
@app.route('/add_crop', methods=['GET', 'POST'])
@login_required
def add_crop():
    if request.method == 'POST':
        crop_name = request.form['crop_name']
        quantity = request.form['quantity']
        price_per_kg = request.form['price_per_kg']
        offer = request.form['offer']
        offer_details = request.form['offer_details']
        image = request.files['image']
        filename = secure_filename(image.filename)
        image.save(os.path.join('static/uploads', filename))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO crops (farmer_id, crop_name, quantity, price_per_kg, offer, offer_details, image)
                          VALUES (%s, %s, %s, %s, %s, %s, %s)''', 
                       (current_user.id, crop_name, quantity, price_per_kg, offer, offer_details, filename))
        conn.commit()
        conn.close()

        flash('Crop added successfully!', 'success')
        return redirect(url_for('farmer_dashboard'))

    return render_template('add_crop.html')

# Route to Edit/Delete Crop
@app.route('/edit_crop/<int:crop_id>', methods=['GET', 'POST'])
@login_required
def edit_crop(crop_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM crops WHERE id = %s', (crop_id,))
    crop = cursor.fetchone()

    if not crop or crop['farmer_id'] != current_user.id:
        flash('Crop not found or unauthorized access', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        crop_name = request.form['crop_name']
        quantity = request.form['quantity']
        price_per_kg = request.form['price_per_kg']
        offer = request.form['offer']
        offer_details = request.form['offer_details']

        cursor.execute('''UPDATE crops SET crop_name = %s, quantity = %s, price_per_kg = %s, 
                          offer = %s, offer_details = %s WHERE id = %s''', 
                       (crop_name, quantity, price_per_kg, offer, offer_details, crop_id))
        conn.commit()
        conn.close()

        flash('Crop updated successfully!', 'success')
        return redirect(url_for('farmer_dashboard'))

    conn.close()
    return render_template('edit_crop.html', crop=crop)

# Route to Delete Crop
@app.route('/delete_crop/<int:crop_id>', methods=['GET'])

@app.route('/delete_crop/<int:crop_id>', methods=['GET'])
@login_required  # Ensure user is logged in
def delete_crop(crop_id):
    # This part should only be accessible by authenticated users
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM crops WHERE id = %s AND farmer_id = %s', (crop_id, current_user.id))
    conn.commit()
    conn.close()

    flash('Crop deleted successfully!', 'success')
    return redirect(url_for('farmer_dashboard'))


@app.route('/customer_orders')
def customer_orders():
    if 'customer_id' not in session:
        flash('Please login to view your orders.', 'warning')
        return redirect(url_for('customer_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT orders.id AS order_id, crops.crop_name, orders.quantity, orders.total_price, orders.order_status, orders.order_date
        FROM orders 
        JOIN crops ON orders.crop_id = crops.id 
        WHERE orders.customer_id = %s
        ORDER BY orders.order_date DESC
    ''', (session['customer_id'],))
    orders = cursor.fetchall()
    conn.close()

    return render_template('customer_orders.html', orders=orders)

@app.route('/payment_handler', methods=['POST'])
def payment_handler():
    if 'customer_id' not in session:
        flash('Please log in to complete your order.', 'danger')
        return redirect(url_for('customer_login'))

    # Capture payment details from Razorpay
    payment_id = request.form.get('razorpay_payment_id')
    total_amount = request.form.get('total_amount')

    if not payment_id:
        flash('Payment failed. Please try again.', 'danger')
        return redirect(url_for('view_cart'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Retrieve cart items for the customer
    cursor.execute('''
        SELECT cart.crop_id, cart.quantity, cart.price, crops.quantity AS available_stock 
        FROM cart 
        JOIN crops ON cart.crop_id = crops.id 
        WHERE cart.customer_id = %s
    ''', (session['customer_id'],))
    cart_items = cursor.fetchall()

    # Validate stock availability
    for item in cart_items:
        if item['quantity'] > item['available_stock']:
            flash(f"Not enough stock available for {item['crop_name']}.", 'danger')
            return redirect(url_for('view_cart'))

    # Deduct stock and place orders
    for item in cart_items:
        cursor.execute('''
            INSERT INTO orders (customer_id, crop_id, quantity, total_price, payment_id, order_status) 
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (session['customer_id'], item['crop_id'], item['quantity'], item['price'], payment_id, 'Completed'))

        # Update crop stock
        cursor.execute('UPDATE crops SET quantity = quantity - %s WHERE id = %s', (item['quantity'], item['crop_id']))

    # Clear the cart
    cursor.execute('DELETE FROM cart WHERE customer_id = %s', (session['customer_id'],))

    conn.commit()
    conn.close()

    flash('Your order has been successfully placed!', 'success')
    return redirect(url_for('customer_dashboard'))

@app.route('/add_to_cart/<int:crop_id>', methods=['POST'])
def add_to_cart(crop_id):
    if 'customer_id' not in session:
        flash('Please login as a customer to add items to your cart.', 'warning')
        return redirect(url_for('customer_login'))

    quantity = int(request.form['quantity'])
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM crops WHERE id = %s', (crop_id,))
    crop = cursor.fetchone()

    if not crop or quantity > crop['quantity']:
        flash('Not enough stock available or crop not found.', 'danger')
        return redirect(url_for('customer_dashboard'))

    total_price = quantity * crop['price_per_kg']

    # Add item to cart
    cursor.execute('''INSERT INTO cart (customer_id, crop_id, quantity, price) 
                      VALUES (%s, %s, %s, %s)''', 
                    (session['customer_id'], crop_id, quantity, total_price))
    conn.commit()
    conn.close()

    flash(f'Added {quantity} Kg of {crop["crop_name"]} to your cart.', 'success')
    return redirect(url_for('view_cart'))


@app.route('/view_cart')
def view_cart():
    if 'customer_id' not in session:
        flash('Please login to view your cart.', 'warning')
        return redirect(url_for('customer_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT cart.id AS cart_id, crops.crop_name, crops.image, cart.quantity, cart.price 
        FROM cart 
        JOIN crops ON cart.crop_id = crops.id 
        WHERE cart.customer_id = %s
    ''', (session['customer_id'],))
    cart_items = cursor.fetchall()

    # Calculate total amount
    total_amount = sum(item['price'] for item in cart_items)
    conn.close()

    return render_template('view_cart.html', cart_items=cart_items, total_amount=total_amount)

@app.route('/remove_from_cart/<int:cart_id>', methods=['GET'])
def remove_from_cart(cart_id):
    if 'customer_id' not in session:
        flash('Please login to manage your cart.', 'warning')
        return redirect(url_for('customer_login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM cart WHERE id = %s AND customer_id = %s', (cart_id, session['customer_id']))
    conn.commit()
    conn.close()

    flash('Item removed from cart.', 'success')
    return redirect(url_for('view_cart'))



# Route to Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
