from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import pickle
import numpy as np
import pandas as pd

popular_df = pd.read_pickle('popular.pkl')
pt = pd.read_pickle('pt.pkl')
books = pd.read_pickle('books.pkl')
similarity_scores = pd.read_pickle('similarity_scores.pkl')


app = Flask(__name__)
app.secret_key = 'secret_key'

# Create a new database and users table
conn = sqlite3.connect('users.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              username TEXT NOT NULL, 
              password TEXT NOT NULL)''')
conn.commit()
conn.close()
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Check if username already exists
        username = request.form['username']
        password = request.form['password']
        password_confirmation = request.form['password_confirmation']

        # Check if passwords match
        if password != password_confirmation:
            return render_template('signup.html', error='Passwords do not match')
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()

        if user is not None:
            conn.close()
            return render_template('signup.html', error='Username already exists')
        else:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            session['username'] = username
            return redirect(url_for('login'))
    else:
        return render_template('signup.html')
# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Check if username and password match
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user is not None:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid credentials')
    else:
        return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


# Index route
@app.route('/')
def index():
    # Check if user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))

    return render_template('index.html',
                           book_name = list(popular_df['Book-Title'].values),
                           author=list(popular_df['Book-Author'].values),
                           image=list(popular_df['Image-URL-M'].values),
                           votes=list(popular_df['num_ratings'].values),
                           rating=list(np.round(popular_df['avg_rating'].values,2))
                           )



# Recommend route
@app.route('/recommend')
def recommend_ui():
    # Check if user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))

    return render_template('recommend.html')

# Recommend books route
@app.route('/recommend_books', methods=['POST'])
def recommend():
    # Check if user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))

    user_input = request.form.get('user_input')
    index = np.where(pt.index == user_input)[0][0]
    similar_items = sorted(list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True)[1:5]

    data = []
    for i in similar_items:
        item = []
        temp_df = books[books['Book-Title'] == pt.index[i[0]]]
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Title'].values))
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Author'].values))
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Image-URL-M'].values))

        data.append(item)

    return render_template('recommend.html', data=data)



if __name__ == '__main__':
    app.run(debug=True)
