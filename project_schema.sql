-- MicroStore AI Consolidated SQL Schema
-- Note: This is a generic SQL representation of all models across Microservices.
-- Table names match exactly the Django Model names without app prefixes.

-- ==========================================
-- USER SERVICE (MySQL)
-- ==========================================
CREATE TABLE MembershipLevel (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    min_points INT DEFAULT 0,
    discount_percentage INT DEFAULT 0
);

CREATE TABLE User (
    id INT AUTO_INCREMENT PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login DATETIME NULL,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    username VARCHAR(150) UNIQUE NOT NULL,
    first_name VARCHAR(150) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL,
    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    date_joined DATETIME NOT NULL,
    role VARCHAR(10) DEFAULT 'CUSTOMER',
    phone_number VARCHAR(20) NULL
);

CREATE TABLE LoyaltyWallet (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usable_points INT DEFAULT 0,
    accumulated_points INT DEFAULT 0,
    current_level_id INT NULL,
    user_id INT UNIQUE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE CASCADE,
    FOREIGN KEY (current_level_id) REFERENCES MembershipLevel(id) ON DELETE SET NULL
);

CREATE TABLE PointTransaction (
    id INT AUTO_INCREMENT PRIMARY KEY,
    amount INT NOT NULL,
    transaction_type VARCHAR(10) NOT NULL,
    description VARCHAR(255) DEFAULT '',
    created_at DATETIME NOT NULL,
    wallet_id INT NOT NULL,
    FOREIGN KEY (wallet_id) REFERENCES LoyaltyWallet(id) ON DELETE CASCADE
);

CREATE TABLE Address (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    recipient_name VARCHAR(255) NULL,
    recipient_phone VARCHAR(20) NULL,
    street VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) DEFAULT 'Vietnam',
    postal_code VARCHAR(20) DEFAULT '',
    is_default BOOLEAN DEFAULT FALSE,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE CASCADE
);

-- ==========================================
-- PRODUCT SERVICE (PostgreSQL)
-- ==========================================
CREATE TABLE Category (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT NULL
);

CREATE TABLE Product (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock INT DEFAULT 0,
    image_url VARCHAR(500) NULL,
    attributes JSONB DEFAULT '{}',
    category_id INT NULL,
    FOREIGN KEY (category_id) REFERENCES Category(id) ON DELETE CASCADE
);

CREATE TABLE Book (
    id SERIAL PRIMARY KEY,
    author VARCHAR(255) NOT NULL,
    publisher VARCHAR(255) NOT NULL,
    isbn VARCHAR(20) NOT NULL,
    product_id INT UNIQUE NOT NULL,
    FOREIGN KEY (product_id) REFERENCES Product(id) ON DELETE CASCADE
);

CREATE TABLE Electronics (
    id SERIAL PRIMARY KEY,
    brand VARCHAR(100) NOT NULL,
    warranty INT NOT NULL,
    product_id INT UNIQUE NOT NULL,
    FOREIGN KEY (product_id) REFERENCES Product(id) ON DELETE CASCADE
);

CREATE TABLE Fashion (
    id SERIAL PRIMARY KEY,
    size VARCHAR(10) NOT NULL,
    color VARCHAR(50) NOT NULL,
    product_id INT UNIQUE NOT NULL,
    FOREIGN KEY (product_id) REFERENCES Product(id) ON DELETE CASCADE
);

CREATE TABLE Cosmetics (
    id SERIAL PRIMARY KEY,
    brand VARCHAR(100) NOT NULL,
    skin_type VARCHAR(50) NOT NULL,
    is_organic BOOLEAN DEFAULT FALSE,
    expiration_date DATE NULL,
    product_id INT UNIQUE NOT NULL,
    FOREIGN KEY (product_id) REFERENCES Product(id) ON DELETE CASCADE
);

CREATE TABLE Toys (
    id SERIAL PRIMARY KEY,
    age_group VARCHAR(50) NOT NULL,
    material VARCHAR(100) NOT NULL,
    requires_batteries BOOLEAN DEFAULT FALSE,
    product_id INT UNIQUE NOT NULL,
    FOREIGN KEY (product_id) REFERENCES Product(id) ON DELETE CASCADE
);

CREATE TABLE Furniture (
    id SERIAL PRIMARY KEY,
    material VARCHAR(100) NOT NULL,
    dimensions VARCHAR(100) NOT NULL,
    weight_capacity FLOAT NULL,
    product_id INT UNIQUE NOT NULL,
    FOREIGN KEY (product_id) REFERENCES Product(id) ON DELETE CASCADE
);

CREATE TABLE Food (
    id SERIAL PRIMARY KEY,
    expiration_date DATE NOT NULL,
    weight VARCHAR(50) NOT NULL,
    is_vegetarian BOOLEAN DEFAULT FALSE,
    calories INT NULL,
    product_id INT UNIQUE NOT NULL,
    FOREIGN KEY (product_id) REFERENCES Product(id) ON DELETE CASCADE
);

CREATE TABLE Medicine (
    id SERIAL PRIMARY KEY,
    active_ingredient VARCHAR(255) NOT NULL,
    dosage VARCHAR(100) NOT NULL,
    prescription_required BOOLEAN DEFAULT FALSE,
    product_id INT UNIQUE NOT NULL,
    FOREIGN KEY (product_id) REFERENCES Product(id) ON DELETE CASCADE
);

CREATE TABLE PetSupplies (
    id SERIAL PRIMARY KEY,
    animal_type VARCHAR(50) NOT NULL,
    brand VARCHAR(100) NOT NULL,
    weight_limit FLOAT NULL,
    product_id INT UNIQUE NOT NULL,
    FOREIGN KEY (product_id) REFERENCES Product(id) ON DELETE CASCADE
);

CREATE TABLE AutoParts (
    id SERIAL PRIMARY KEY,
    part_number VARCHAR(100) NOT NULL,
    car_model_compatibility TEXT NOT NULL,
    warranty_years INT DEFAULT 1,
    product_id INT UNIQUE NOT NULL,
    FOREIGN KEY (product_id) REFERENCES Product(id) ON DELETE CASCADE
);

-- ==========================================
-- CART SERVICE (PostgreSQL)
-- ==========================================
CREATE TABLE Cart (
    id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL
);

CREATE TABLE CartItem (
    id SERIAL PRIMARY KEY,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    cart_id INT NOT NULL,
    FOREIGN KEY (cart_id) REFERENCES Cart(id) ON DELETE CASCADE
);

-- ==========================================
-- ORDER SERVICE (PostgreSQL)
-- ==========================================
CREATE TABLE Voucher (
    id SERIAL PRIMARY KEY,
    code VARCHAR(100) UNIQUE NOT NULL,
    discount_amount DECIMAL(10, 2) NOT NULL,
    is_percentage BOOLEAN DEFAULT FALSE,
    min_spend DECIMAL(10, 2) DEFAULT 0,
    min_points_level_id INT NULL,
    point_cost INT DEFAULT 0,
    max_quantity INT DEFAULT 100,
    redeemed_quantity INT DEFAULT 0,
    is_public BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    expiry_date TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "Order" (
    id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL,
    total_amount DECIMAL(12, 2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    membership_discount DECIMAL(12, 2) DEFAULT 0,
    voucher_discount DECIMAL(12, 2) DEFAULT 0,
    voucher_code VARCHAR(100) DEFAULT '',
    points_generated INT DEFAULT 0,
    shipping_address TEXT DEFAULT '',
    shipping_fee DECIMAL(10, 2) DEFAULT 0,
    shipping_method VARCHAR(50) DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE OrderItem (
    id SERIAL PRIMARY KEY,
    product_id INT NOT NULL,
    product_name VARCHAR(255) DEFAULT '',
    item_image_url TEXT DEFAULT '',
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    order_id INT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES "Order"(id) ON DELETE CASCADE
);

CREATE TABLE CustomerVoucher (
    id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    redeemed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    used_at TIMESTAMP NULL,
    order_id INT NULL,
    voucher_id INT NOT NULL,
    FOREIGN KEY (voucher_id) REFERENCES Voucher(id) ON DELETE CASCADE
);

CREATE TABLE OrderStatusLog (
    id SERIAL PRIMARY KEY,
    status VARCHAR(50) NOT NULL,
    notes TEXT DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    order_id INT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES "Order"(id) ON DELETE CASCADE
);

-- ==========================================
-- PAY SERVICE (PostgreSQL)
-- ==========================================
CREATE TABLE Payment (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL,
    customer_id INT NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    method VARCHAR(20) DEFAULT 'COD',
    status VARCHAR(20) DEFAULT 'processing',
    transaction_id VARCHAR(100) UNIQUE NOT NULL,
    note TEXT DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- SHIP SERVICE (PostgreSQL)
-- ==========================================
CREATE TABLE ShippingMethod (
    id_slug VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT DEFAULT '',
    base_fee FLOAT NOT NULL,
    free_threshold FLOAT NULL,
    estimated_days INT DEFAULT 3
);

CREATE TABLE Shipment (
    id SERIAL PRIMARY KEY,
    order_id INT UNIQUE NOT NULL,
    customer_id INT NOT NULL,
    tracking_code VARCHAR(50) UNIQUE NOT NULL,
    shipping_method VARCHAR(50) DEFAULT 'standard',
    address TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'ready_for_pickup',
    estimated_delivery TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- COMMENT-RATE SERVICE (PostgreSQL)
-- ==========================================
CREATE TABLE Review (
    id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL,
    product_id INT NOT NULL,
    rating INT NOT NULL,
    comment TEXT DEFAULT '',
    customer_name VARCHAR(255) DEFAULT 'User',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (customer_id, product_id)
);
