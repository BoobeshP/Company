from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
db = SQLAlchemy(app)
class Product(db.Model):
    product_id = db.Column(db.String(50), primary_key=True)
    movements = db.relationship('ProductMovement', backref='product', lazy=True)

class Location(db.Model):
    location_id = db.Column(db.String(50), primary_key=True)
    # Define the one-to-many relationship between Location and ProductMovement for both from_location and to_location
    movements_from = db.relationship('ProductMovement', foreign_keys='ProductMovement.from_location', backref='from_location_obj', lazy=True)
    movements_to = db.relationship('ProductMovement', foreign_keys='ProductMovement.to_location', backref='to_location_obj', lazy=True)

class ProductMovement(db.Model):
    movement_id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    from_location = db.Column(db.String(50), db.ForeignKey('location.location_id'))
    to_location = db.Column(db.String(50), db.ForeignKey('location.location_id'))
    product_id = db.Column(db.String(50), db.ForeignKey('product.product_id'))
    qty = db.Column(db.Integer)
with app.app_context():
    db.create_all()
sample_products = ["New Product 1", "New Product 2", "New Product 3"]
sample_locations = ["New Location 1", "New Location 2", "New Location 3"]
def add_sample_data():
    for product_name in sample_products:
        existing_product = Product.query.filter_by(product_id=product_name).first()
        if not existing_product:
            product = Product(product_id=product_name)
            db.session.add(product)

    for location_name in sample_locations:
        existing_location = Location.query.filter_by(location_id=location_name).first()
        if not existing_location:
            location = Location(location_id=location_name)
            db.session.add(location)

    db.session.commit()
with app.app_context():
    db.create_all()
    add_sample_data()
def get_product_balance():
    balance = []
    locations = Location.query.all()
    for location in locations:
        products = Product.query.all()
        for product in products:
            total_in = sum(pm.qty for pm in ProductMovement.query.filter_by(to_location=location.location_id, product_id=product.product_id).all())
            total_out = sum(pm.qty for pm in ProductMovement.query.filter_by(from_location=location.location_id, product_id=product.product_id).all())
            qty = total_in - total_out
            balance.append({'product': product.product_id, 'warehouse': location.location_id, 'qty': qty})
    return balance
@app.route('/')
def index():
    balance = get_product_balance()
    return render_template('index.html', balance=balance)

@app.route('/products', methods=['GET', 'POST'])
def products():
    if request.method == 'POST':
        product_id = request.form['product_id']
        product = Product(product_id=product_id)
        db.session.add(product)
        db.session.commit()
        return redirect(url_for('products'))

    products = Product.query.all()
    return render_template('products.html', products=products)

@app.route('/locations', methods=['GET', 'POST'])
def locations():
    if request.method == 'POST':
        location_id = request.form['location_id']
        location = Location(location_id=location_id)
        db.session.add(location)
        db.session.commit()
        return redirect(url_for('locations'))

    locations = Location.query.all()
    return render_template('locations.html', locations=locations)

@app.route('/movements', methods=['GET', 'POST'])
def movements():
    if request.method == 'POST':
        timestamp = datetime.utcnow()
        from_location = request.form['from_location']
        to_location = request.form['to_location']
        product_id = request.form['product_id']
        qty = request.form['qty']

        movement = ProductMovement(timestamp=timestamp,from_location=from_location,to_location=to_location,product_id=product_id,qty=qty)
        db.session.add(movement)
        db.session.commit()
        return redirect(url_for('movements'))

    movements = ProductMovement.query.all()
    return render_template('movements.html', movements=movements)

# Add other routes to handle CRUD operations for Product, Location, and ProductMovement
# Use SQLAlchemy queries to interact with the database

if __name__ == '__main__':
    app.run(debug=True)
