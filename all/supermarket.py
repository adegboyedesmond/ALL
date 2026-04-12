#!/usr/bin/env python3
"""
Supermarket Management System - Tkinter GUI Version
Professional Point of Sale and Inventory Management
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
import json
import os
import hashlib
import datetime
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# ==================== DATA MODELS ====================

class UserRole(Enum):
    CUSTOMER = "customer"
    CASHIER = "cashier"
    MANAGER = "manager"
    ADMIN = "admin"

class PaymentMethod(Enum):
    CASH = "Cash"
    CARD = "Credit/Debit Card"
    MOBILE = "Mobile Payment"
    VOUCHER = "Gift Voucher"

@dataclass
class Product:
    id: str
    name: str
    category: str
    price: float
    stock: int
    barcode: str
    expiry_date: Optional[str] = None
    discount_percent: float = 0.0
    tax_rate: float = 0.08
    
    @property
    def final_price(self) -> float:
        return self.price * (1 - self.discount_percent / 100)
    
    @property
    def is_low_stock(self) -> bool:
        return self.stock < 10

@dataclass
class CartItem:
    product: Product
    quantity: int
    
    @property
    def subtotal(self) -> float:
        return self.product.final_price * self.quantity
    
    @property
    def tax_amount(self) -> float:
        return self.subtotal * self.product.tax_rate

@dataclass
class User:
    username: str
    password_hash: str
    role: UserRole
    full_name: str
    email: str
    phone: str
    created_at: str
    is_active: bool = True

@dataclass
class Transaction:
    id: str
    items: List[Dict]
    subtotal: float
    tax_total: float
    discount_total: float
    total: float
    payment_method: str
    cashier: str
    timestamp: str
    customer_phone: Optional[str] = None

# ==================== DATABASE MANAGER ====================

class Database:
    def __init__(self, data_dir: str = "supermarket_data"):
        self.data_dir = data_dir
        self.ensure_directories()
        self.data = {
            'products': {},
            'users': {},
            'transactions': [],
            'categories': ['Produce', 'Dairy', 'Meat', 'Bakery', 'Beverages', 
                          'Frozen', 'Pantry', 'Household', 'Personal Care', 'Electronics']
        }
        self.load_all()
    
    def ensure_directories(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def get_file_path(self, name: str) -> str:
        return os.path.join(self.data_dir, f"{name}.json")
    
    def load_all(self):
        for key in ['products', 'users', 'transactions', 'categories']:
            path = self.get_file_path(key)
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        data = json.load(f)
                        if key == 'products':
                            self.data[key] = {k: Product(**v) for k, v in data.items()}
                        elif key == 'users':
                            users = {}
                            for k, v in data.items():
                                v['role'] = UserRole(v['role'])
                                users[k] = User(**v)
                            self.data[key] = users
                        else:
                            self.data[key] = data
                except Exception as e:
                    print(f"Warning: Could not load {key}: {e}")
    
    def save_all(self):
        for key, value in self.data.items():
            path = self.get_file_path(key)
            with open(path, 'w') as f:
                if key == 'products':
                    json.dump({k: asdict(v) for k, v in value.items()}, f, indent=2)
                elif key == 'users':
                    users_dict = {}
                    for k, v in value.items():
                        user_dict = asdict(v)
                        user_dict['role'] = v.role.value
                        users_dict[k] = user_dict
                    json.dump(users_dict, f, indent=2)
                else:
                    json.dump(value, f, indent=2)
    
    def get_product(self, product_id: str) -> Optional[Product]:
        return self.data['products'].get(product_id)
    
    def add_product(self, product: Product):
        self.data['products'][product.id] = product
        self.save_all()
    
    def update_product(self, product: Product):
        self.data['products'][product.id] = product
        self.save_all()
    
    def delete_product(self, product_id: str):
        if product_id in self.data['products']:
            del self.data['products'][product_id]
            self.save_all()
    
    def get_user(self, username: str) -> Optional[User]:
        return self.data['users'].get(username)
    
    def add_user(self, user: User):
        self.data['users'][user.username] = user
        self.save_all()
    
    def add_transaction(self, transaction: Transaction):
        self.data['transactions'].append(asdict(transaction))
        self.save_all()
    
    def get_transactions(self, limit: int = 100) -> List[Dict]:
        return self.data['transactions'][-limit:]

# ==================== AUTHENTICATION SERVICE ====================

class AuthService:
    def __init__(self, db: Database):
        self.db = db
        self.current_user: Optional[User] = None
        self.ensure_default_admin()
    
    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    def ensure_default_admin(self):
        if not self.db.data['users']:
            admin = User(
                username="admin",
                password_hash=self.hash_password("admin123"),
                role=UserRole.ADMIN,
                full_name="System Administrator",
                email="admin@supermarket.com",
                phone="0000000000",
                created_at=datetime.datetime.now().isoformat()
            )
            self.db.add_user(admin)
    
    def login(self, username: str, password: str) -> bool:
        user = self.db.get_user(username)
        if user and user.password_hash == self.hash_password(password) and user.is_active:
            self.current_user = user
            return True
        return False
    
    def logout(self):
        self.current_user = None
    
    def register_user(self, username: str, password: str, role: UserRole, 
                     full_name: str, email: str, phone: str) -> bool:
        if self.db.get_user(username):
            return False
        
        user = User(
            username=username,
            password_hash=self.hash_password(password),
            role=role,
            full_name=full_name,
            email=email,
            phone=phone,
            created_at=datetime.datetime.now().isoformat()
        )
        self.db.add_user(user)
        return True
    
    def has_permission(self, min_role: UserRole) -> bool:
        if not self.current_user:
            return False
        hierarchy = [UserRole.CUSTOMER, UserRole.CASHIER, UserRole.MANAGER, UserRole.ADMIN]
        return hierarchy.index(self.current_user.role) >= hierarchy.index(min_role)

# ==================== INVENTORY MANAGER ====================

class InventoryManager:
    def __init__(self, db: Database):
        self.db = db
    
    def generate_product_id(self) -> str:
        return f"PRD{random.randint(10000, 99999)}"
    
    def generate_barcode(self) -> str:
        return f"8{random.randint(100000000000, 999999999999)}"
    
    def add_product(self, name: str, category: str, price: float, stock: int,
                   expiry_date: Optional[str] = None, discount: float = 0) -> Product:
        product = Product(
            id=self.generate_product_id(),
            name=name,
            category=category,
            price=price,
            stock=stock,
            barcode=self.generate_barcode(),
            expiry_date=expiry_date,
            discount_percent=discount
        )
        self.db.add_product(product)
        return product
    
    def update_stock(self, product_id: str, quantity: int) -> bool:
        product = self.db.get_product(product_id)
        if product:
            product.stock += quantity
            self.db.update_product(product)
            return True
        return False
    
    def set_discount(self, product_id: str, discount_percent: float) -> bool:
        product = self.db.get_product(product_id)
        if product:
            product.discount_percent = discount_percent
            self.db.update_product(product)
            return True
        return False
    
    def search_products(self, query: str) -> List[Product]:
        query = query.lower()
        results = []
        for product in self.db.data['products'].values():
            if (query in product.name.lower() or 
                query in product.barcode or 
                query in product.id.lower() or
                query in product.category.lower()):
                results.append(product)
        return results
    
    def get_low_stock_items(self) -> List[Product]:
        return [p for p in self.db.data['products'].values() if p.is_low_stock]
    
    def get_products_by_category(self, category: str) -> List[Product]:
        return [p for p in self.db.data['products'].values() if p.category == category]
    
    def get_all_categories(self) -> List[str]:
        return self.db.data['categories']

# ==================== SHOPPING CART ====================

class ShoppingCart:
    def __init__(self):
        self.items: Dict[str, CartItem] = {}
    
    def add_item(self, product: Product, quantity: int) -> Tuple[bool, str]:
        if product.stock < quantity:
            return False, f"Insufficient stock. Available: {product.stock}"
        
        if product.id in self.items:
            new_qty = self.items[product.id].quantity + quantity
            if product.stock < new_qty:
                return False, f"Insufficient stock. Available: {product.stock}"
            self.items[product.id].quantity = new_qty
        else:
            self.items[product.id] = CartItem(product, quantity)
        
        return True, "Item added successfully"
    
    def remove_item(self, product_id: str) -> bool:
        if product_id in self.items:
            del self.items[product_id]
            return True
        return False
    
    def update_quantity(self, product_id: str, quantity: int) -> Tuple[bool, str]:
        if product_id not in self.items:
            return False, "Item not in cart"
        
        product = self.items[product_id].product
        if quantity <= 0:
            del self.items[product_id]
            return True, "Item removed"
        
        if product.stock < quantity:
            return False, f"Insufficient stock. Available: {product.stock}"
        
        self.items[product_id].quantity = quantity
        return True, "Quantity updated"
    
    def clear(self):
        self.items.clear()
    
    @property
    def subtotal(self) -> float:
        return sum(item.subtotal for item in self.items.values())
    
    @property
    def tax_total(self) -> float:
        return sum(item.tax_amount for item in self.items.values())
    
    @property
    def total(self) -> float:
        return self.subtotal + self.tax_total
    
    def get_items(self) -> List[CartItem]:
        return list(self.items.values())
    
    def is_empty(self) -> bool:
        return len(self.items) == 0

# ==================== CHECKOUT SERVICE ====================

class CheckoutService:
    def __init__(self, db: Database, inventory: InventoryManager):
        self.db = db
        self.inventory = inventory
    
    def process_payment(self, cart: ShoppingCart, payment_method: PaymentMethod,
                       cashier: str, customer_phone: Optional[str] = None) -> Tuple[bool, str, Optional[Transaction]]:
        if cart.is_empty():
            return False, "Cart is empty", None
        
        for item in cart.get_items():
            current_product = self.db.get_product(item.product.id)
            if not current_product or current_product.stock < item.quantity:
                return False, f"Insufficient stock for {item.product.name}", None
        
        transaction_id = f"TXN{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
        
        items_data = []
        for item in cart.get_items():
            items_data.append({
                'product_id': item.product.id,
                'name': item.product.name,
                'quantity': item.quantity,
                'unit_price': item.product.final_price,
                'subtotal': item.subtotal,
                'tax': item.tax_amount
            })
            self.inventory.update_stock(item.product.id, -item.quantity)
        
        transaction = Transaction(
            id=transaction_id,
            items=items_data,
            subtotal=cart.subtotal,
            tax_total=cart.tax_total,
            discount_total=sum(item.product.price * item.product.discount_percent / 100 * item.quantity 
                             for item in cart.get_items()),
            total=cart.total,
            payment_method=payment_method.value,
            cashier=cashier,
            timestamp=datetime.datetime.now().isoformat(),
            customer_phone=customer_phone
        )
        
        self.db.add_transaction(transaction)
        return True, transaction_id, transaction
    
    def generate_receipt(self, transaction: Transaction, width: int = 50) -> str:
        lines = []
        lines.append("=" * width)
        lines.append("SUPERMARKET PLUS".center(width))
        lines.append("123 Main Street, City, Country".center(width))
        lines.append("Tel: (555) 123-4567".center(width))
        lines.append("=" * width)
        lines.append(f"Receipt #: {transaction.id}")
        lines.append(f"Date: {transaction.timestamp[:19]}")
        lines.append(f"Cashier: {transaction.cashier}")
        if transaction.customer_phone:
            lines.append(f"Customer: {transaction.customer_phone}")
        lines.append("-" * width)
        lines.append(f"{'Item':<20} {'Qty':>6} {'Price':>10} {'Total':>12}")
        lines.append("-" * width)
        
        for item in transaction.items:
            name = item['name'][:18]
            lines.append(f"{name:<20} {item['quantity']:>6} ${item['unit_price']:>9.2f} ${item['subtotal']:>11.2f}")
        
        lines.append("-" * width)
        lines.append(f"{'Subtotal:':<38} ${transaction.subtotal:>10.2f}")
        lines.append(f"{'Tax:':<38} ${transaction.tax_total:>10.2f}")
        if transaction.discount_total > 0:
            lines.append(f"{'Discount:':<38} -${transaction.discount_total:>10.2f}")
        lines.append("=" * width)
        lines.append(f"{'TOTAL:':<38} ${transaction.total:>10.2f}")
        lines.append("=" * width)
        lines.append(f"Payment: {transaction.payment_method}")
        lines.append("")
        lines.append("Thank you for shopping with us!".center(width))
        lines.append("Returns accepted within 30 days with receipt".center(width))
        lines.append("=" * width)
        
        return "\n".join(lines)

# ==================== TKINTER GUI APPLICATION ====================

class SupermarketApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Supermarket Plus - Management System")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize backend
        self.db = Database()
        self.auth = AuthService(self.db)
        self.inventory = InventoryManager(self.db)
        self.cart = ShoppingCart()
        self.checkout = CheckoutService(self.db, self.inventory)
        
        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
        
        # Show login screen
        self.show_login_screen()
    
    def configure_styles(self):
        self.style.configure('Title.TLabel', font=('Helvetica', 24, 'bold'), foreground='#2c3e50')
        self.style.configure('Header.TLabel', font=('Helvetica', 16, 'bold'), foreground='#34495e')
        self.style.configure('Normal.TLabel', font=('Helvetica', 11), foreground='#2c3e50')
        self.style.configure('Success.TLabel', font=('Helvetica', 11), foreground='#27ae60')
        self.style.configure('Warning.TLabel', font=('Helvetica', 11), foreground='#e74c3c')
        
        self.style.configure('Action.TButton', font=('Helvetica', 11, 'bold'), padding=10)
        self.style.configure('Menu.TButton', font=('Helvetica', 12), padding=15)
        
        self.style.configure('Card.TFrame', background='white', relief='raised')
        self.style.configure('Sidebar.TFrame', background='#2c3e50')
    
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()
    
    # ==================== LOGIN SCREEN ====================
    
    def show_login_screen(self):
        self.clear_window()
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="50")
        main_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Logo/Title
        ttk.Label(main_frame, text="🛒 SUPERMARKET PLUS", style='Title.TLabel').pack(pady=(0, 10))
        ttk.Label(main_frame, text="Management System", style='Header.TLabel').pack(pady=(0, 30))
        
        # Login card
        login_card = ttk.Frame(main_frame, padding="30", relief='solid', borderwidth=2)
        login_card.pack(fill='both', expand=True)
        
        ttk.Label(login_card, text="Login", style='Header.TLabel').pack(pady=(0, 20))
        
        # Username
        ttk.Label(login_card, text="Username:", style='Normal.TLabel').pack(anchor='w', pady=(10, 5))
        self.username_var = tk.StringVar()
        ttk.Entry(login_card, textvariable=self.username_var, font=('Helvetica', 11), width=30).pack(fill='x', pady=(0, 10))
        
        # Password
        ttk.Label(login_card, text="Password:", style='Normal.TLabel').pack(anchor='w', pady=(10, 5))
        self.password_var = tk.StringVar()
        ttk.Entry(login_card, textvariable=self.password_var, show="•", font=('Helvetica', 11), width=30).pack(fill='x', pady=(0, 20))
        
        # Buttons
        btn_frame = ttk.Frame(login_card)
        btn_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(btn_frame, text="Login", command=self.login, style='Action.TButton').pack(side='left', padx=(0, 10))
        ttk.Button(btn_frame, text="Exit", command=self.root.quit).pack(side='right')
        
        # Default credentials info
        info_label = ttk.Label(main_frame, text="Default: admin / admin123", style='Normal.TLabel', foreground='#7f8c8d')
        info_label.pack(pady=(20, 0))
    
    def login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        
        if self.auth.login(username, password):
            messagebox.showinfo("Success", f"Welcome, {self.auth.current_user.full_name}!")
            self.show_main_dashboard()
        else:
            messagebox.showerror("Error", "Invalid credentials or account inactive!")
    
    # ==================== MAIN DASHBOARD ====================
    
    def show_main_dashboard(self):
        self.clear_window()
        
        # Configure grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        # Sidebar
        sidebar = ttk.Frame(self.root, width=250, style='Sidebar.TFrame')
        sidebar.grid(row=0, column=0, sticky='nsew')
        sidebar.grid_propagate(False)
        
        # User info in sidebar
        ttk.Label(sidebar, text=f"👤 {self.auth.current_user.full_name}", 
                 font=('Helvetica', 12, 'bold'), background='#2c3e50', foreground='white').pack(pady=(20, 5), padx=20, anchor='w')
        ttk.Label(sidebar, text=f"Role: {self.auth.current_user.role.value.title()}", 
                 font=('Helvetica', 10), background='#2c3e50', foreground='#bdc3c7').pack(pady=(0, 30), padx=20, anchor='w')
        
        # Menu buttons
        menu_items = [
            ("🛒 Point of Sale", self.show_pos),
            ("📦 Inventory", self.show_inventory),
            ("📊 Reports", self.show_reports),
            ("👥 Users", self.show_users),
            ("⚙️ Settings", self.show_settings),
        ]
        
        # Filter menu based on permissions
        if not self.auth.has_permission(UserRole.MANAGER):
            menu_items = [item for item in menu_items if item[1] != self.show_inventory and item[1] != self.show_reports]
        if not self.auth.has_permission(UserRole.ADMIN):
            menu_items = [item for item in menu_items if item[1] != self.show_users]
        
        for text, command in menu_items:
            btn = tk.Button(sidebar, text=text, font=('Helvetica', 11), 
                          bg='#34495e', fg='white', activebackground='#2c3e50',
                          bd=0, padx=20, pady=12, anchor='w', cursor='hand2',
                          command=command)
            btn.pack(fill='x', pady=2)
        
        # Logout button at bottom
        ttk.Frame(sidebar).pack(expand=True)  # Spacer
        tk.Button(sidebar, text="🚪 Logout", font=('Helvetica', 11, 'bold'),
                 bg='#e74c3c', fg='white', activebackground='#c0392b',
                 bd=0, padx=20, pady=12, command=self.logout).pack(fill='x', pady=(10, 20), padx=10)
        
        # Main content area
        self.content_frame = ttk.Frame(self.root, padding="20")
        self.content_frame.grid(row=0, column=1, sticky='nsew')
        
        # Show default view
        self.show_pos()
    
    def logout(self):
        self.auth.logout()
        self.show_login_screen()
    
    # ==================== POS SYSTEM ====================
    
    def show_pos(self):
        self.clear_content()
        
        # Header
        header = ttk.Frame(self.content_frame)
        header.pack(fill='x', pady=(0, 20))
        ttk.Label(header, text="Point of Sale", style='Title.TLabel').pack(side='left')
        
        # Cart summary
        cart_frame = ttk.LabelFrame(header, text="Cart Summary", padding="10")
        cart_frame.pack(side='right')
        self.cart_total_var = tk.StringVar(value="Total: $0.00")
        ttk.Label(cart_frame, textvariable=self.cart_total_var, font=('Helvetica', 14, 'bold')).pack()
        
        # Main POS layout
        paned = ttk.PanedWindow(self.content_frame, orient='horizontal')
        paned.pack(fill='both', expand=True)
        
        # Left: Product search and selection
        left_frame = ttk.LabelFrame(paned, text="Products", padding="10")
        paned.add(left_frame, weight=2)
        
        # Search
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill='x', pady=(0, 10))
        ttk.Label(search_frame, text="Search:").pack(side='left', padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, font=('Helvetica', 11))
        search_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        ttk.Button(search_frame, text="Search", command=self.search_products).pack(side='right')
        search_entry.bind('<Return>', lambda e: self.search_products())
        
        # Product list
        columns = ('ID', 'Name', 'Category', 'Price', 'Stock', 'Status')
        self.product_tree = ttk.Treeview(left_frame, columns=columns, show='headings', height=15)
        for col in columns:
            self.product_tree.heading(col, text=col)
            self.product_tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(left_frame, orient='vertical', command=self.product_tree.yview)
        self.product_tree.configure(yscrollcommand=scrollbar.set)
        
        self.product_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Add to cart button
        ttk.Button(left_frame, text="Add to Cart", command=self.add_to_cart, style='Action.TButton').pack(fill='x', pady=(10, 0))
        
        # Right: Cart
        right_frame = ttk.LabelFrame(paned, text="Shopping Cart", padding="10")
        paned.add(right_frame, weight=1)
        
        # Cart items
        cart_columns = ('Name', 'Qty', 'Price', 'Total')
        self.cart_tree = ttk.Treeview(right_frame, columns=cart_columns, show='headings', height=10)
        for col in cart_columns:
            self.cart_tree.heading(col, text=col)
            self.cart_tree.column(col, width=80)
        
        cart_scroll = ttk.Scrollbar(right_frame, orient='vertical', command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=cart_scroll.set)
        
        self.cart_tree.pack(side='left', fill='both', expand=True)
        cart_scroll.pack(side='right', fill='y')
        
        # Cart buttons
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill='x', pady=(10, 5))
        ttk.Button(btn_frame, text="Update Qty", command=self.update_cart_qty).pack(side='left', padx=(0, 5))
        ttk.Button(btn_frame, text="Remove", command=self.remove_from_cart).pack(side='left', padx=(0, 5))
        ttk.Button(btn_frame, text="Clear", command=self.clear_cart).pack(side='right')
        
        # Checkout button
        ttk.Button(right_frame, text="💳 CHECKOUT", command=self.checkout_dialog, 
                  style='Action.TButton').pack(fill='x', pady=(10, 0))
        
        # Load initial products
        self.refresh_product_list()
        self.refresh_cart()
    
    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def refresh_product_list(self, products=None):
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        
        if products is None:
            products = list(self.db.data['products'].values())
        
        for p in products:
            status = "LOW STOCK" if p.is_low_stock else "OK"
            self.product_tree.insert('', 'end', values=(
                p.id, p.name, p.category, f"${p.final_price:.2f}", p.stock, status
            ))
    
    def search_products(self):
        query = self.search_var.get().strip()
        if query:
            results = self.inventory.search_products(query)
            self.refresh_product_list(results)
        else:
            self.refresh_product_list()
    
    def add_to_cart(self):
        selected = self.product_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a product!")
            return
        
        item = self.product_tree.item(selected[0])
        product_id = item['values'][0]
        product = self.db.get_product(product_id)
        
        if not product:
            return
        
        # Ask for quantity
        qty = simpledialog.askinteger("Quantity", f"Enter quantity for {product.name}:", 
                                     minvalue=1, maxvalue=product.stock)
        if qty:
            success, msg = self.cart.add_item(product, qty)
            if success:
                self.refresh_cart()
            else:
                messagebox.showerror("Error", msg)
    
    def refresh_cart(self):
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        
        for item in self.cart.get_items():
            total = item.subtotal + item.tax_amount
            self.cart_tree.insert('', 'end', values=(
                item.product.name, item.quantity, 
                f"${item.product.final_price:.2f}", f"${total:.2f}"
            ))
        
        self.cart_total_var.set(f"Total: ${self.cart.total:.2f}")
    
    def update_cart_qty(self):
        selected = self.cart_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a cart item!")
            return
        
        item = self.cart_tree.item(selected[0])
        product_name = item['values'][0]
        
        # Find product in cart
        for cart_item in self.cart.get_items():
            if cart_item.product.name == product_name:
                new_qty = simpledialog.askinteger("Update Quantity", "Enter new quantity:", 
                                                 minvalue=0, maxvalue=cart_item.product.stock)
                if new_qty is not None:
                    success, msg = self.cart.update_quantity(cart_item.product.id, new_qty)
                    self.refresh_cart()
                    if not success:
                        messagebox.showerror("Error", msg)
                break
    
    def remove_from_cart(self):
        selected = self.cart_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a cart item!")
            return
        
        item = self.cart_tree.item(selected[0])
        product_name = item['values'][0]
        
        for cart_item in self.cart.get_items():
            if cart_item.product.name == product_name:
                self.cart.remove_item(cart_item.product.id)
                self.refresh_cart()
                break
    
    def clear_cart(self):
        if messagebox.askyesno("Confirm", "Clear entire cart?"):
            self.cart.clear()
            self.refresh_cart()
    
    def checkout_dialog(self):
        if self.cart.is_empty():
            messagebox.showwarning("Warning", "Cart is empty!")
            return
        
        # Checkout window
        checkout_win = tk.Toplevel(self.root)
        checkout_win.title("Checkout")
        checkout_win.geometry("400x500")
        checkout_win.transient(self.root)
        checkout_win.grab_set()
        
        ttk.Label(checkout_win, text="Checkout", style='Title.TLabel').pack(pady=20)
        
        # Cart summary
        summary_frame = ttk.LabelFrame(checkout_win, text="Order Summary", padding="10")
        summary_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(summary_frame, text=f"Subtotal: ${self.cart.subtotal:.2f}").pack(anchor='w')
        ttk.Label(summary_frame, text=f"Tax: ${self.cart.tax_total:.2f}").pack(anchor='w')
        ttk.Label(summary_frame, text=f"Total: ${self.cart.total:.2f}", font=('Helvetica', 12, 'bold')).pack(anchor='w', pady=(10, 0))
        
        # Payment method
        ttk.Label(checkout_win, text="Payment Method:").pack(anchor='w', padx=20, pady=(20, 5))
        self.payment_var = tk.StringVar(value=PaymentMethod.CASH.value)
        for method in PaymentMethod:
            ttk.Radiobutton(checkout_win, text=method.value, variable=self.payment_var, 
                          value=method.value).pack(anchor='w', padx=40)
        
        # Customer phone
        ttk.Label(checkout_win, text="Customer Phone (optional):").pack(anchor='w', padx=20, pady=(20, 5))
        self.customer_phone_var = tk.StringVar()
        ttk.Entry(checkout_win, textvariable=self.customer_phone_var).pack(fill='x', padx=20)
        
        # Buttons
        btn_frame = ttk.Frame(checkout_win)
        btn_frame.pack(fill='x', padx=20, pady=30)
        
        ttk.Button(btn_frame, text="Process Payment", command=lambda: self.process_checkout(checkout_win)).pack(side='left', padx=(0, 10))
        ttk.Button(btn_frame, text="Cancel", command=checkout_win.destroy).pack(side='right')
    
    def process_checkout(self, window):
        payment_method = PaymentMethod(self.payment_var.get())
        customer_phone = self.customer_phone_var.get().strip() or None
        
        success, msg, transaction = self.checkout.process_payment(
            self.cart, payment_method, 
            self.auth.current_user.username,
            customer_phone
        )
        
        if success and transaction:
            window.destroy()
            self.show_receipt(transaction)
            self.cart.clear()
            self.refresh_cart()
        else:
            messagebox.showerror("Error", msg)
    
    def show_receipt(self, transaction):
        receipt_win = tk.Toplevel(self.root)
        receipt_win.title("Receipt")
        receipt_win.geometry("400x600")
        
        # Receipt text
        text_widget = scrolledtext.ScrolledText(receipt_win, font=('Courier', 10), wrap=tk.WORD)
        text_widget.pack(fill='both', expand=True, padx=10, pady=10)
        
        receipt_text = self.checkout.generate_receipt(transaction)
        text_widget.insert('1.0', receipt_text)
        text_widget.config(state='disabled')
        
        ttk.Button(receipt_win, text="Print Receipt", command=lambda: messagebox.showinfo("Print", "Receipt sent to printer!")).pack(pady=10)
        ttk.Button(receipt_win, text="Close", command=receipt_win.destroy).pack(pady=(0, 10))
    
    # ==================== INVENTORY ====================
    
    def show_inventory(self):
        self.clear_content()
        
        # Header
        header = ttk.Frame(self.content_frame)
        header.pack(fill='x', pady=(0, 20))
        ttk.Label(header, text="Inventory Management", style='Title.TLabel').pack(side='left')
        ttk.Button(header, text="+ Add Product", command=self.add_product_dialog).pack(side='right')
        
        # Search
        search_frame = ttk.Frame(self.content_frame)
        search_frame.pack(fill='x', pady=(0, 10))
        ttk.Label(search_frame, text="Search:").pack(side='left', padx=(0, 5))
        self.inv_search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.inv_search_var).pack(side='left', fill='x', expand=True, padx=(0, 5))
        ttk.Button(search_frame, text="Search", command=self.search_inventory).pack(side='left', padx=(0, 5))
        ttk.Button(search_frame, text="Show All", command=self.refresh_inventory).pack(side='left')
        
        # Product table
        columns = ('ID', 'Name', 'Category', 'Price', 'Stock', 'Discount', 'Status')
        self.inv_tree = ttk.Treeview(self.content_frame, columns=columns, show='headings')
        for col in columns:
            self.inv_tree.heading(col, text=col)
            self.inv_tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(self.content_frame, orient='vertical', command=self.inv_tree.yview)
        self.inv_tree.configure(yscrollcommand=scrollbar.set)
        
        self.inv_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Context menu
        self.inv_tree.bind('<Double-1>', self.edit_product_dialog)
        
        # Action buttons
        btn_frame = ttk.Frame(self.content_frame)
        btn_frame.pack(fill='x', pady=10)
        ttk.Button(btn_frame, text="Edit", command=lambda: self.edit_product_dialog(None)).pack(side='left', padx=(0, 5))
        ttk.Button(btn_frame, text="Delete", command=self.delete_product).pack(side='left', padx=(0, 5))
        ttk.Button(btn_frame, text="Update Stock", command=self.update_stock_dialog).pack(side='left', padx=(0, 5))
        ttk.Button(btn_frame, text="Set Discount", command=self.set_discount_dialog).pack(side='left')
        ttk.Button(btn_frame, text="Low Stock Alert", command=self.show_low_stock).pack(side='right')
        
        self.refresh_inventory()
    
    def refresh_inventory(self):
        for item in self.inv_tree.get_children():
            self.inv_tree.delete(item)
        
        for p in self.db.data['products'].values():
            status = "LOW STOCK" if p.is_low_stock else "OK"
            self.inv_tree.insert('', 'end', values=(
                p.id, p.name, p.category, f"${p.price:.2f}", 
                p.stock, f"{p.discount_percent}%", status
            ))
    
    def search_inventory(self):
        query = self.inv_search_var.get().strip()
        if query:
            results = self.inventory.search_products(query)
            for item in self.inv_tree.get_children():
                self.inv_tree.delete(item)
            for p in results:
                status = "LOW STOCK" if p.is_low_stock else "OK"
                self.inv_tree.insert('', 'end', values=(
                    p.id, p.name, p.category, f"${p.price:.2f}", 
                    p.stock, f"{p.discount_percent}%", status
                ))
    
    def add_product_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Product")
        dialog.geometry("400x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Add New Product", style='Header.TLabel').pack(pady=20)
        
        # Form fields
        form_frame = ttk.Frame(dialog, padding="20")
        form_frame.pack(fill='both', expand=True)
        
        fields = [
            ("Name:", "name", tk.StringVar()),
            ("Category:", "category", tk.StringVar()),
            ("Price ($):", "price", tk.StringVar()),
            ("Stock:", "stock", tk.StringVar()),
            ("Expiry Date (YYYY-MM-DD):", "expiry", tk.StringVar()),
            ("Discount (%):", "discount", tk.StringVar(value="0")),
        ]
        
        self.add_product_vars = {}
        for label, key, var in fields:
            ttk.Label(form_frame, text=label).pack(anchor='w', pady=(10, 0))
            ttk.Entry(form_frame, textvariable=var).pack(fill='x', pady=(0, 5))
            self.add_product_vars[key] = var
        
        # Category dropdown
        ttk.Label(form_frame, text="Or select category:").pack(anchor='w', pady=(10, 0))
        self.category_combo = ttk.Combobox(form_frame, values=self.inventory.get_all_categories())
        self.category_combo.pack(fill='x', pady=(0, 5))
        self.category_combo.bind('<<ComboboxSelected>>', 
                                lambda e: self.add_product_vars['category'].set(self.category_combo.get()))
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill='x', padx=20, pady=20)
        ttk.Button(btn_frame, text="Save", command=lambda: self.save_new_product(dialog)).pack(side='left', padx=(0, 10))
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side='right')
    
    def save_new_product(self, dialog):
        try:
            name = self.add_product_vars['name'].get().strip()
            category = self.add_product_vars['category'].get().strip()
            price = float(self.add_product_vars['price'].get())
            stock = int(self.add_product_vars['stock'].get())
            expiry = self.add_product_vars['expiry'].get().strip() or None
            discount = float(self.add_product_vars['discount'].get() or 0)
            
            if not name or not category:
                messagebox.showerror("Error", "Name and category are required!")
                return
            
            product = self.inventory.add_product(name, category, price, stock, expiry, discount)
            messagebox.showinfo("Success", f"Product added! ID: {product.id}")
            dialog.destroy()
            self.refresh_inventory()
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")
    
    def edit_product_dialog(self, event):
        selected = self.inv_tree.selection()
        if not selected and event:
            return
        if not selected:
            messagebox.showwarning("Warning", "Please select a product!")
            return
        
        item = self.inv_tree.item(selected[0])
        product_id = item['values'][0]
        product = self.db.get_product(product_id)
        
        if not product:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit Product - {product.name}")
        dialog.geometry("400x400")
        
        ttk.Label(dialog, text="Edit Product", style='Header.TLabel').pack(pady=20)
        
        form_frame = ttk.Frame(dialog, padding="20")
        form_frame.pack(fill='both', expand=True)
        
        ttk.Label(form_frame, text="Name:").pack(anchor='w')
        name_var = tk.StringVar(value=product.name)
        ttk.Entry(form_frame, textvariable=name_var).pack(fill='x', pady=(0, 10))
        
        ttk.Label(form_frame, text="Category:").pack(anchor='w')
        cat_var = tk.StringVar(value=product.category)
        cat_combo = ttk.Combobox(form_frame, values=self.inventory.get_all_categories(), textvariable=cat_var)
        cat_combo.pack(fill='x', pady=(0, 10))
        
        ttk.Label(form_frame, text="Price ($):").pack(anchor='w')
        price_var = tk.StringVar(value=str(product.price))
        ttk.Entry(form_frame, textvariable=price_var).pack(fill='x', pady=(0, 10))
        
        ttk.Label(form_frame, text="Stock:").pack(anchor='w')
        stock_var = tk.StringVar(value=str(product.stock))
        ttk.Entry(form_frame, textvariable=stock_var).pack(fill='x', pady=(0, 10))
        
        def save_changes():
            try:
                product.name = name_var.get()
                product.category = cat_var.get()
                product.price = float(price_var.get())
                product.stock = int(stock_var.get())
                self.db.update_product(product)
                messagebox.showinfo("Success", "Product updated!")
                dialog.destroy()
                self.refresh_inventory()
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid input: {e}")
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill='x', padx=20, pady=20)
        ttk.Button(btn_frame, text="Save", command=save_changes).pack(side='left', padx=(0, 10))
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side='right')
    
    def delete_product(self):
        selected = self.inv_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a product!")
            return
        
        item = self.inv_tree.item(selected[0])
        product_id = item['values'][0]
        product_name = item['values'][1]
        
        if messagebox.askyesno("Confirm", f"Delete {product_name}?"):
            self.db.delete_product(product_id)
            self.refresh_inventory()
    
    def update_stock_dialog(self):
        selected = self.inv_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a product!")
            return
        
        item = self.inv_tree.item(selected[0])
        product_id = item['values'][0]
        product = self.db.get_product(product_id)
        
        new_stock = simpledialog.askinteger("Update Stock", 
                                           f"Current stock: {product.stock}\nEnter quantity to add (+) or remove (-):",
                                           minvalue=-product.stock)
        if new_stock is not None:
            if self.inventory.update_stock(product_id, new_stock):
                messagebox.showinfo("Success", f"Stock updated! New stock: {product.stock + new_stock}")
                self.refresh_inventory()
    
    def set_discount_dialog(self):
        selected = self.inv_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a product!")
            return
        
        item = self.inv_tree.item(selected[0])
        product_id = item['values'][0]
        product = self.db.get_product(product_id)
        
        discount = simpledialog.askfloat("Set Discount", 
                                        f"Current discount: {product.discount_percent}%\nEnter new discount percentage (0-100):",
                                        minvalue=0, maxvalue=100)
        if discount is not None:
            if self.inventory.set_discount(product_id, discount):
                new_price = product.price * (1 - discount/100)
                messagebox.showinfo("Success", f"Discount set! New price: ${new_price:.2f}")
                self.refresh_inventory()
    
    def show_low_stock(self):
        low_stock = self.inventory.get_low_stock_items()
        if not low_stock:
            messagebox.showinfo("Low Stock", "No low stock items! All inventory levels are healthy.")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Low Stock Alert")
        dialog.geometry("500x400")
        
        ttk.Label(dialog, text=f"⚠ {len(low_stock)} items below threshold (10 units)", 
                 style='Warning.TLabel').pack(pady=10)
        
        tree = ttk.Treeview(dialog, columns=('ID', 'Name', 'Stock'), show='headings')
        tree.heading('ID', text='ID')
        tree.heading('Name', text='Name')
        tree.heading('Stock', text='Current Stock')
        tree.column('ID', width=100)
        tree.column('Name', width=300)
        tree.column('Stock', width=100)
        
        for p in low_stock:
            tree.insert('', 'end', values=(p.id, p.name, p.stock))
        
        tree.pack(fill='both', expand=True, padx=10, pady=10)
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    # ==================== REPORTS ====================
    
    def show_reports(self):
        self.clear_content()
        
        header = ttk.Frame(self.content_frame)
        header.pack(fill='x', pady=(0, 20))
        ttk.Label(header, text="Reports & Analytics", style='Title.TLabel').pack(side='left')
        
        # Report buttons
        btn_frame = ttk.Frame(self.content_frame)
        btn_frame.pack(fill='x', pady=10)
        
        ttk.Button(btn_frame, text="📊 Daily Sales", command=self.show_daily_sales).pack(side='left', padx=(0, 10))
        ttk.Button(btn_frame, text="📦 Inventory Valuation", command=self.show_inventory_report).pack(side='left', padx=(0, 10))
        ttk.Button(btn_frame, text="🏆 Top Products", command=self.show_top_products).pack(side='left', padx=(0, 10))
        ttk.Button(btn_frame, text="📝 Transaction History", command=self.show_transaction_history).pack(side='left')
        
        # Report display area
        self.report_frame = ttk.LabelFrame(self.content_frame, text="Report", padding="20")
        self.report_frame.pack(fill='both', expand=True, pady=20)
        
        self.report_text = scrolledtext.ScrolledText(self.report_frame, font=('Courier', 10), wrap=tk.WORD)
        self.report_text.pack(fill='both', expand=True)
        self.report_text.config(state='disabled')
    
    def show_daily_sales(self):
        from datetime import datetime
        date = datetime.now().strftime("%Y-%m-%d")
        
        # Simple daily sales calculation
        transactions = self.db.get_transactions(1000)
        daily_txns = [t for t in transactions if t['timestamp'].startswith(date)]
        
        total_sales = sum(t['total'] for t in daily_txns)
        total_items = sum(sum(i['quantity'] for i in t['items']) for t in daily_txns)
        
        self.report_text.config(state='normal')
        self.report_text.delete('1.0', tk.END)
        self.report_text.insert('1.0', f"""
DAILY SALES REPORT
Date: {date}
{'='*50}

Transactions: {len(daily_txns)}
Total Sales: ${total_sales:.2f}
Items Sold: {total_items}
Average Transaction: ${total_sales/len(daily_txns) if daily_txns else 0:.2f}
""")
        self.report_text.config(state='disabled')
    
    def show_inventory_report(self):
        products = list(self.db.data['products'].values())
        total_value = sum(p.price * p.stock for p in products)
        low_stock = len([p for p in products if p.is_low_stock])
        out_of_stock = len([p for p in products if p.stock == 0])
        
        self.report_text.config(state='normal')
        self.report_text.delete('1.0', tk.END)
        self.report_text.insert('1.0', f"""
INVENTORY VALUATION REPORT
{'='*50}

Total Products: {len(products)}
Total Inventory Value: ${total_value:.2f}
Low Stock Items: {low_stock}
Out of Stock: {out_of_stock}

Category Breakdown:
{'-'*50}
""")
        
        category_values = {}
        for p in products:
            if p.category not in category_values:
                category_values[p.category] = 0
            category_values[p.category] += p.price * p.stock
        
        for cat, value in sorted(category_values.items(), key=lambda x: x[1], reverse=True):
            self.report_text.insert(tk.END, f"{cat}: ${value:.2f}\n")
        
        self.report_text.config(state='disabled')
    
    def show_top_products(self):
        transactions = self.db.get_transactions(1000)
        product_sales = {}
        
        for t in transactions:
            for item in t['items']:
                pid = item['product_id']
                if pid not in product_sales:
                    product_sales[pid] = {'name': item['name'], 'quantity': 0, 'revenue': 0}
                product_sales[pid]['quantity'] += item['quantity']
                product_sales[pid]['revenue'] += item['subtotal']
        
        sorted_products = sorted(product_sales.values(), key=lambda x: x['quantity'], reverse=True)[:10]
        
        self.report_text.config(state='normal')
        self.report_text.delete('1.0', tk.END)
        self.report_text.insert('1.0', f"""
TOP SELLING PRODUCTS
{'='*60}

{'Rank':<6} {'Product':<30} {'Qty':<10} {'Revenue':<12}
{'-'*60}
""")
        
        for i, p in enumerate(sorted_products, 1):
            name = p['name'][:28]
            self.report_text.insert(tk.END, f"{i:<6} {name:<30} {p['quantity']:<10} ${p['revenue']:<11.2f}\n")
        
        self.report_text.config(state='disabled')
    
    def show_transaction_history(self):
        transactions = self.db.get_transactions(50)
        
        self.report_text.config(state='normal')
        self.report_text.delete('1.0', tk.END)
        self.report_text.insert('1.0', f"""
TRANSACTION HISTORY (Last 50)
{'='*80}

{'ID':<20} {'Date':<20} {'Total':<12} {'Payment':<15}
{'-'*80}
""")
        
        for t in reversed(transactions):
            tid = t['id'][:18]
            time = t['timestamp'][:16]
            self.report_text.insert(tk.END, f"{tid:<20} {time:<20} ${t['total']:<11.2f} {t['payment_method']:<15}\n")
        
        self.report_text.config(state='disabled')
    
    # ==================== USER MANAGEMENT ====================
    
    def show_users(self):
        self.clear_content()
        
        header = ttk.Frame(self.content_frame)
        header.pack(fill='x', pady=(0, 20))
        ttk.Label(header, text="User Management", style='Title.TLabel').pack(side='left')
        ttk.Button(header, text="+ Add User", command=self.add_user_dialog).pack(side='right')
        
        # User table
        columns = ('Username', 'Role', 'Full Name', 'Email', 'Status')
        self.user_tree = ttk.Treeview(self.content_frame, columns=columns, show='headings')
        for col in columns:
            self.user_tree.heading(col, text=col)
            self.user_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(self.content_frame, orient='vertical', command=self.user_tree.yview)
        self.user_tree.configure(yscrollcommand=scrollbar.set)
        
        self.user_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Action buttons
        btn_frame = ttk.Frame(self.content_frame)
        btn_frame.pack(fill='x', pady=10)
        ttk.Button(btn_frame, text="Deactivate", command=self.deactivate_user).pack(side='left', padx=(0, 5))
        ttk.Button(btn_frame, text="Reset Password", command=self.reset_password_dialog).pack(side='left')
        
        self.refresh_user_list()
    
    def refresh_user_list(self):
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
        
        for u in self.db.data['users'].values():
            status = "ACTIVE" if u.is_active else "INACTIVE"
            self.user_tree.insert('', 'end', values=(
                u.username, u.role.value, u.full_name, u.email, status
            ))
    
    def add_user_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New User")
        dialog.geometry("400x500")
        
        ttk.Label(dialog, text="Add New User", style='Header.TLabel').pack(pady=20)
        
        form_frame = ttk.Frame(dialog, padding="20")
        form_frame.pack(fill='both', expand=True)
        
        fields = [
            ("Username:", "username", tk.StringVar()),
            ("Password:", "password", tk.StringVar()),
            ("Full Name:", "full_name", tk.StringVar()),
            ("Email:", "email", tk.StringVar()),
            ("Phone:", "phone", tk.StringVar()),
        ]
        
        self.add_user_vars = {}
        for label, key, var in fields:
            ttk.Label(form_frame, text=label).pack(anchor='w', pady=(10, 0))
            show = "•" if key == "password" else None
            ttk.Entry(form_frame, textvariable=var, show=show).pack(fill='x', pady=(0, 5))
            self.add_user_vars[key] = var
        
        ttk.Label(form_frame, text="Role:").pack(anchor='w', pady=(10, 0))
        self.role_var = tk.StringVar(value=UserRole.CASHIER.value)
        role_combo = ttk.Combobox(form_frame, values=[r.value for r in UserRole], textvariable=self.role_var)
        role_combo.pack(fill='x', pady=(0, 5))
        
        def save_user():
            try:
                username = self.add_user_vars['username'].get().strip()
                password = self.add_user_vars['password'].get().strip()
                full_name = self.add_user_vars['full_name'].get().strip()
                email = self.add_user_vars['email'].get().strip()
                phone = self.add_user_vars['phone'].get().strip()
                role = UserRole(self.role_var.get())
                
                if len(password) < 4:
                    messagebox.showerror("Error", "Password too short!")
                    return
                
                if self.auth.register_user(username, password, role, full_name, email, phone):
                    messagebox.showinfo("Success", f"User '{username}' created!")
                    dialog.destroy()
                    self.refresh_user_list()
                else:
                    messagebox.showerror("Error", "Username already exists!")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill='x', padx=20, pady=20)
        ttk.Button(btn_frame, text="Save", command=save_user).pack(side='left', padx=(0, 10))
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side='right')
    
    def deactivate_user(self):
        selected = self.user_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a user!")
            return
        
        item = self.user_tree.item(selected[0])
        username = item['values'][0]
        
        if username == self.auth.current_user.username:
            messagebox.showerror("Error", "Cannot deactivate yourself!")
            return
        
        if messagebox.askyesno("Confirm", f"Deactivate user '{username}'?"):
            user = self.db.get_user(username)
            if user:
                user.is_active = False
                self.db.save_all()
                self.refresh_user_list()
    
    def reset_password_dialog(self):
        selected = self.user_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a user!")
            return
        
        item = self.user_tree.item(selected[0])
        username = item['values'][0]
        
        new_password = simpledialog.askstring("Reset Password", f"Enter new password for {username}:", show='•')
        if new_password:
            if len(new_password) < 4:
                messagebox.showerror("Error", "Password too short!")
                return
            
            user = self.db.get_user(username)
            if user:
                user.password_hash = self.auth.hash_password(new_password)
                self.db.save_all()
                messagebox.showinfo("Success", f"Password reset for '{username}'!")
    
    # ==================== SETTINGS ====================
    
    def show_settings(self):
        self.clear_content()
        
        ttk.Label(self.content_frame, text="System Settings", style='Title.TLabel').pack(pady=20)
        
        settings_frame = ttk.Frame(self.content_frame, padding="20")
        settings_frame.pack(fill='both', expand=True)
        
        ttk.Button(settings_frame, text="💾 Backup Data", command=self.backup_data).pack(fill='x', pady=10)
        ttk.Button(settings_frame, text="📥 Load Sample Data", command=self.load_sample_data).pack(fill='x', pady=10)
        
        # About section
        about_frame = ttk.LabelFrame(settings_frame, text="About", padding="20")
        about_frame.pack(fill='x', pady=20)
        
        about_text = """Supermarket Plus v1.0
A Complete Supermarket Management System

Features:
• Point of Sale (POS) with barcode support
• Inventory Management with low stock alerts
• Multi-role User Management
• Sales Reporting & Analytics
• Receipt Generation
• Data Backup & Recovery"""
        
        ttk.Label(about_frame, text=about_text, justify='left').pack()
    
    def backup_data(self):
        import shutil
        backup_dir = f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(backup_dir, exist_ok=True)
        
        for key in ['products', 'users', 'transactions', 'categories']:
            src = self.db.get_file_path(key)
            if os.path.exists(src):
                shutil.copy(src, os.path.join(backup_dir, f"{key}.json"))
        
        messagebox.showinfo("Success", f"Backup created in: {backup_dir}")
    
    def load_sample_data(self):
        if self.db.data['products']:
            if not messagebox.askyesno("Confirm", "This will add sample products. Continue?"):
                return
        
        sample_products = [
            ("Apples", "Produce", 2.99, 150, "2026-12-31"),
            ("Milk 1L", "Dairy", 3.49, 80, "2026-06-15"),
            ("Bread", "Bakery", 2.79, 45, "2026-04-10"),
            ("Chicken Breast", "Meat", 8.99, 60, "2026-04-08"),
            ("Rice 5kg", "Pantry", 12.99, 100, None),
            ("Orange Juice", "Beverages", 4.29, 75, "2026-08-01"),
            ("Toilet Paper", "Household", 6.99, 200, None),
            ("Shampoo", "Personal Care", 5.49, 90, None),
            ("Frozen Pizza", "Frozen", 7.99, 120, "2026-11-01"),
            ("AA Batteries", "Electronics", 4.99, 300, None),
        ]
        
        for name, cat, price, stock, expiry in sample_products:
            self.inventory.add_product(name, cat, price, stock, expiry)
        
        messagebox.showinfo("Success", f"Added {len(sample_products)} sample products!")

# ==================== MAIN ENTRY ====================

if __name__ == "__main__":
    root = tk.Tk()
    app = SupermarketApp(root)
    root.mainloop()