ensure your Python version >=3.11 better 3.12

run this command in VS code terminal "pip install -r requirements.txt"

to run the project, run this "python app.py"

Here’s the SQL schema for your project based on the features and requirements we've discussed:

---

### **Farmers Table**
Stores information about farmers, including their profile and location.

```sql
CREATE TABLE farmers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(15) UNIQUE NOT NULL,
    address TEXT,
    aadhar VARCHAR(20),
    password VARCHAR(255) NOT NULL,
    profile_pic VARCHAR(255) DEFAULT 'default.jpg',
    latitude DECIMAL(9,6),        -- Latitude for location
    longitude DECIMAL(9,6),       -- Longitude for location
    location_name VARCHAR(255)   -- Human-readable location name
);
```

---

### **Customers Table**
Stores information about customers, including their location.

```sql
CREATE TABLE customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(15) UNIQUE NOT NULL,
    email VARCHAR(100),
    password VARCHAR(255) NOT NULL,
    profile_pic VARCHAR(255) DEFAULT 'default.jpg',
    latitude DECIMAL(9,6),        -- Latitude for location
    longitude DECIMAL(9,6),       -- Longitude for location
    location_name VARCHAR(255)   -- Human-readable location name
);
```

---

### **Crops Table**
Stores information about the crops uploaded by farmers.

```sql
CREATE TABLE crops (
    id INT AUTO_INCREMENT PRIMARY KEY,
    farmer_id INT NOT NULL,                     -- Reference to the farmer
    crop_name VARCHAR(100) NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,            -- Quantity in Kg
    price_per_kg DECIMAL(10,2) NOT NULL,
    offer VARCHAR(255),                         -- Short offer description
    offer_details TEXT,                         -- Detailed offer description
    image VARCHAR(255) DEFAULT 'default.jpg',   -- Image of the crop
    FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE
);
```

---

### **Cart Table**
Stores items added to the customer's cart.

```sql
CREATE TABLE cart (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,                 -- Reference to the customer
    crop_id INT NOT NULL,                     -- Reference to the crop
    quantity DECIMAL(10,2) NOT NULL,          -- Quantity in Kg
    price DECIMAL(10,2) NOT NULL,             -- Total price for the quantity
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (crop_id) REFERENCES crops(id) ON DELETE CASCADE
);
```

---

### **Orders Table**
Stores information about customer orders.

```sql
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,                -- Reference to the customer
    crop_id INT NOT NULL,                    -- Reference to the crop
    farmer_id INT NOT NULL,                  -- Reference to the farmer
    quantity DECIMAL(10,2) NOT NULL,         -- Quantity ordered in Kg
    total_price DECIMAL(10,2) NOT NULL,      -- Total price of the order
    status ENUM('Pending', 'Completed') DEFAULT 'Pending',  -- Order status
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (crop_id) REFERENCES crops(id) ON DELETE CASCADE,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE
);
```

---

### **Locations Table**
(Optional, for predefined dropdown of locations.)

```sql
CREATE TABLE locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    location_name VARCHAR(255) NOT NULL,  -- Name of the location
    latitude DECIMAL(9,6) NOT NULL,       -- Latitude
    longitude DECIMAL(9,6) NOT NULL       -- Longitude
);
```

---

### **Razorpay Payment Table (Optional)**
Tracks payment details for orders.

```sql
CREATE TABLE payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,                 -- Reference to the order
    razorpay_payment_id VARCHAR(255),      -- Razorpay's payment ID
    payment_status ENUM('Success', 'Failed', 'Pending') DEFAULT 'Pending',
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);
```

---

### **Indexes and Optimization**
1. Add an index on latitude and longitude in both `farmers` and `customers` for faster location-based queries:
   ```sql
   CREATE INDEX lat_lon_idx ON farmers(latitude, longitude);
   CREATE INDEX lat_lon_idx ON customers(latitude, longitude);
   ```

2. Index `crop_name` in the `crops` table for faster searching/filtering:
   ```sql
   CREATE INDEX crop_name_idx ON crops(crop_name);
   ```

---

### Summary of Relationships
- **Farmers and Crops**: A farmer can upload multiple crops.
- **Customers and Cart**: A customer can add multiple items to their cart.
- **Customers and Orders**: A customer can place multiple orders.
- **Farmers and Orders**: Each order references a farmer who owns the crop.
- **Payments and Orders**: Payments are linked to specific orders.

Let me know if you need further assistance!
