from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATABASE = 'library.db'
def get_db():
    return sqlite3.connect(DATABASE)
def initialize_db():
    with get_db() as conn:
        # Create tables if they don't exist
        conn.execute(''' CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY, title TEXT NOT NULL, author TEXT NOT NULL, stock INTEGER NOT NULL  ) ''')
        conn.execute(''' CREATE TABLE IF NOT EXISTS members ( id INTEGER PRIMARY KEY,name TEXT NOT NULL, outstanding_debt REAL NOT NULL) ''')
        conn.execute(''' CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY,book_id INTEGER NOT NULL,member_id INTEGER NOT NULL,issue_date DATE NOT NULL,return_date DATE,rent_fee REAL NOT NULL, FOREIGN KEY (book_id) REFERENCES books (id),FOREIGN KEY (member_id) REFERENCES members (id) )  ''')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'password':
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            return "Invalid username or password.", 401
    return render_template('login.html')
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))
@app.route('/')
def index():
     return redirect(url_for('login'))
@app.route('/dashboard')
def dashboard():
    if 'logged_in' in session:
        return render_template('dashboard.html')
    else:
        return redirect(url_for('login'))  
@app.route('/books')
def view_books():
    with get_db() as conn:
        cursor = conn.execute('SELECT * FROM books')
        books = cursor.fetchall()
    return render_template('view_books.html', books=books)    
@app.route('/books/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        stock = int(request.form['stock'])
        with get_db() as conn:
            conn.execute('INSERT INTO books (title, author, stock) VALUES (?, ?, ?)', (title, author, stock))
        return redirect(url_for('view_books'))
    return render_template('add_book.html')
@app.route('/members')
def view_members():
    with get_db() as conn:
        cursor = conn.execute('SELECT * FROM members')
        members = cursor.fetchall()
    return render_template('view_members.html', members=members)
@app.route('/members/add', methods=['GET', 'POST'])
def add_member():
    if request.method == 'POST':
        name = request.form['name']
        outstanding_debt = float(request.form['outstanding_debt'])
        with get_db() as conn:
            conn.execute('INSERT INTO members (name, outstanding_debt) VALUES (?, ?)', (name, outstanding_debt))
        return redirect(url_for('view_members'))
    return render_template('add_member.html')
@app.route('/members/<int:member_id>', methods=['GET', 'POST'])
def view_member(member_id):
    with get_db() as conn:
        cursor = conn.execute('SELECT * FROM members WHERE id = ?', (member_id,))
        member = cursor.fetchone()
    if not member:
        return "Member not found.", 404
    if request.method == 'POST':
        outstanding_debt = float(request.form['outstanding_debt'])
        with get_db() as conn:
            conn.execute('UPDATE members SET outstanding_debt = ? WHERE id = ?', (outstanding_debt, member_id))
        return redirect(url_for('view_members'))
    return render_template('view_member.html', member=member)
@app.route('/issue_book', methods=['GET', 'POST'])
def issue_book():
    if request.method == 'POST':
        book_id = int(request.form['book_id'])
        member_id = int(request.form['member_id'])
        rent_fee = float(request.form['rent_fee'])
        with get_db() as conn:
            cursor = conn.execute('SELECT stock FROM books WHERE id = ?', (book_id,))
            stock = cursor.fetchone()[0]
            if stock <= 0:
                return "Book is not available in stock.", 400
            conn.execute('UPDATE books SET stock = stock - 1 WHERE id = ?', (book_id,))
            conn.execute('INSERT INTO transactions (book_id, member_id, issue_date, rent_fee) VALUES (?, ?, DATE(), ?)', (book_id, member_id, rent_fee))
        return redirect(url_for('view_transactions'))
    with get_db() as conn:
        cursor_books = conn.execute('SELECT * FROM books')
        books = cursor_books.fetchall()
        cursor_members = conn.execute('SELECT * FROM members')
        members = cursor_members.fetchall()
    return render_template('issue_book.html', books=books, members=members)
@app.route('/return_book', methods=['GET', 'POST'])
def return_book():
    if request.method == 'POST':
        transaction_id = int(request.form['transaction_id'])
        return_date = request.form['return_date']
        rent_fee = float(request.form['rent_fee'])
        with get_db() as conn:
            cursor = conn.execute('SELECT book_id, member_id FROM transactions WHERE id = ?', (transaction_id,))
            transaction = cursor.fetchone()
            if not transaction:
                return "Transaction not found.", 404
            conn.execute('UPDATE books SET stock = stock + 1 WHERE id = ?', (transaction[0],))
            conn.execute('UPDATE transactions SET return_date = ?, rent_fee = ? WHERE id = ?', (return_date, rent_fee, transaction_id))
            cursor_member = conn.execute('SELECT SUM(rent_fee) FROM transactions WHERE member_id = ?', (transaction[1],))
            total_rent_fee = cursor_member.fetchone()[0]
            if total_rent_fee > 500:
                conn.execute('UPDATE members SET outstanding_debt = ? WHERE id = ?', (total_rent_fee - 500, transaction[1]))
        return redirect(url_for('view_transactions'))
    with get_db() as conn:
        cursor = conn.execute('SELECT * FROM transactions WHERE return_date IS NULL')
        transactions = cursor.fetchall()
    return render_template('return_book.html', transactions=transactions)
@app.route('/transactions')
def view_transactions():
    with get_db() as conn:
        cursor = conn.execute('SELECT transactions.id, books.title, members.name, transactions.issue_date, transactions.return_date, transactions.rent_fee FROM transactions JOIN books ON transactions.book_id = books.id JOIN members ON transactions.member_id = members.id')
        transactions = cursor.fetchall()
    return render_template('view_transactions.html', transactions=transactions)
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        keyword = request.form['keyword']
        with get_db() as conn:
            cursor = conn.execute('SELECT * FROM books WHERE title LIKE ? OR author LIKE ?', ('%' + keyword + '%', '%' + keyword + '%'))
            books = cursor.fetchall()
            return render_template('view_books.html', books=books)
    return render_template('search.html')
if __name__ == '__main__':
    initialize_db()
    app.run(debug=True)
