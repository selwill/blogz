from flask import Flask, request, redirect, render_template, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from datetime import datetime
from hashutils import make_pw_hash, check_pw_hash

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:root@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app)

app.secret_key = '}NP+TNKsz6.Z3N@KF9KFCUT^48kUfU'

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(2500))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    pub_date = db.Column(db.DateTime)
    
    def __init__(self, title, body, owner, pub_date=None):
        self.title = title
        self.body = body
        self.owner = owner

        if pub_date is None:
            pub_date = datetime.utcnow()

        self.pub_date = pub_date

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    pw_hash = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.pw_hash = make_pw_hash(password)

@app.before_request
def require_login():
    allowed_routes = ['index', 'login', 'signup', 'blog']

    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')
        
def get_users():
    return User.query.all()

@app.route('/', methods=['POST', 'GET'])
def index():
    return render_template('index.html', title="Blogz! Users", users=get_users())

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_pw_hash(password, user.pw_hash):
            session['username'] = username
            print(session)
            flash('Logged in')
            print(session)
            return redirect('/newpost')
        else:
            if user and user.password != password:
                flash('Your password is incorrect', 'error')
            else:
                flash('Username does not exist', 'error')

    return render_template('login.html')

def is_valid(string):
    if len(string) < 4 or len(string) > 20:
        return False
    else:
        return True

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']

        username_error = ''
        password_error = ''
        verify_error = ''

        existing_user = User.query.filter_by(username=username).first()

        if not existing_user:   

            if (not username) or (not is_valid(username)) or (' ' in username):
                username_error = 'That is not a valid username'
    
            if (not password) or (not is_valid(password)) or (' ' in password):
                password_error = 'That is not a valid password'

            if (verify != password) or (not verify):
                verify_error = 'Passwords do not match'

            if (not username_error) and (not password_error) and (not verify_error):
                new_user = User(username, password)
                db.session.add(new_user)
                db.session.commit()

                session['username'] = username

                return redirect('/newpost')
            else:
                return render_template('signup.html', username=username, username_error=username_error, password_error=password_error, verify_error=verify_error)
        else:
            flash('This username already exists', 'error')            

    return render_template('signup.html')

@app.route('/logout')
def logout():
    del session['username']

    return redirect('/blog')

@app.route('/blog', methods=['POST', 'GET'])
def blog():
    blog_id = request.args.get('blog_id')
    blog_user = request.args.get('user')

    per_page = 3
    page = request.args.get('page', 1, type=int)

    if blog_user:
        user = User.query.filter_by(username=blog_user).first()

        blogs = Blog.query.filter_by(owner=user).order_by(Blog.pub_date.desc()).paginate(page, per_page, False)
        
        next_page = url_for('blog', user=blog_user, page=blogs.next_num) \
            if blogs.has_next else None
        prev_page = url_for('blog', user=blog_user, page=blogs.prev_num) \
            if blogs.has_prev else None

        return render_template('blog.html', title="Blogz! from "+blog_user, blogs=blogs.items, username=blog_user, page=page, next_page=next_page, prev_page=prev_page)

    if blog_id:
        blogs = Blog.query.filter_by(id=blog_id).first()
        
        return render_template('blog.html', title='Blogz!', blogs=blogs)
    else:
        blogs = Blog.query.order_by(Blog.pub_date.desc()).paginate(page, per_page, False)
        
        next_page = url_for('blog', page=blogs.next_num) \
            if blogs.has_next else None
        prev_page = url_for('blog', page=blogs.prev_num) \
            if blogs.has_prev else None

        return render_template('blog.html', title="Blogz!", blogs=blogs.items, page=page, next_page=next_page, prev_page=prev_page)

@app.route('/newpost', methods=['POST', 'GET'])
def newpost():
    owner = User.query.filter_by(username=session['username']).first()

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']

        title_error = ''
        body_error = ''

        if not title.strip():
            title_error = 'Please fill in a title'

        if not body.strip():
            body_error = 'Please fill in the body'

        if not title_error and not body_error:
            new_blog = Blog(title, body, owner)
            db.session.add(new_blog)
            db.session.commit()

            return redirect('/blog?blog_id={0}'.format(new_blog.id))
        else:
            return render_template('newpost.html', title=title, body=body, title_error=title_error, body_error=body_error)
    else:
        return render_template('newpost.html')

if __name__ == '__main__':
    app.run()