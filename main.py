from flask import Flask, request, redirect, render_template, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:root@localhost:3306/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = "jfie838jFJf5h03.s{#"


class Blogz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    content = db.Column(db.String(2000))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    pubdate = db.Column(db.DateTime)

    def __init__(self, title, content, author_id, pubdate = None):
        self.title = title
        self.content = content
        self.author_id = author_id
        if pubdate is None:
            pubdate = datetime.utcnow()
        self.pubdate = pubdate

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    password = db.Column(db.String(20))
    blogs = db.relationship('Blogz', backref='user')

    def __init__(self, username, password):
        self.username = username
        self.password = password

def getAllBlog():
    return Blogz.query.all()

def getAllUser():
    return User.query.all()

@app.before_request
def req_login():
    allowed_routes = ['login', 'signup', 'index', 'blog']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/blog')

@app.route('/signup', methods=['POST','GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify_pw = request.form['verify_pw']
        user = User.query.filter_by(username=username).first()

        username_error=''
        password_error=''
        verify_pw_error=''

        #add new user to database
        if not user and len(password) > 3 and password == verify_pw:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/newpost')

        #verify username
        if username == '' or password == '' or verify_pw == '':
            flash ('Your Username and/or Password is invalid')
            username_error = False
            password_error = False
            verify_pw_error = False

        if username == '':
            username_error = False
            username = ''
            flash('Your username should be between 5 and 20 characters.')

        elif len(username) < 3:
            username_error = False
            username = ''
            flash('Your username should be between 5 and 20 characters.')

        #elif existing_user:
        #    username_error = False
        #    username = ''
        #    flash('The username your are trying to use it already taken - Please try again.')

        #verify Passwords
        if password == '':
            password_error = False
            password = ''
            flash('Please enter password')

        elif len(password) < 5:
            password_error = False
            password = ''
            flash('Your password should be between 5 and 20 characters.')

        elif password != verify_pw:
            password_error = False
            password = ''
            flash('Your passwords do not match - Please try again.')

        return render_template('/newpost.html', username=username, username_error=username_error, password_error=password_error, verify_pw_error=verify_pw_error)

    return render_template("/signup.html")


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        username_error = ""
        password_error = ""

        if user and user.password == password:
            session['username'] = username
            flash('You are logged in!')
            return redirect('/newpost')

        elif user == '':
            username_error = False
            username = ''
            flash('Username is not filled - Try again.')


        elif not user:
            username_error = True
            username = ''
            flash ('Username does not exist')


        if password == "":
            password_error = False
            password = ''
            flash('Your password does not match - Try again')

        return render_template("login.html", username=username, username_error=username_error, password_error=password_error)

    return render_template("login.html")


@app.route('/', methods=['POST', 'GET'])
def index():
    users = User.query.all()
    return render_template('index.html', title='Home', users=users)

@app.route('/singleuser', methods=['GET'])
def showuser():
    users = User.query.filter_by(username=session['user_id']).first()
    user_id = request.args.get('users')
    blogs = Blogz.query.filter_by(username=user_id).all()
    return render_template('singleuser.html', users=users, blogs=blogs)



# TODO: redirected from / showing all blogs
@app.route('/blog', methods=['GET'])
def blog():
    blogs = Blogz.query.all()
    blog_id = request.args.get('id')
    blog_post = Blogz.query.filter_by(id=blog_id).first()
    author_id = blog_post.author_id
    user = User.query.get(author_id)
    return render_template('blog.html', title='Your Blog', blogs=blogs, user_id=blog_id, username=author_id, blog=blog_post, user=user)

# TODO: query all blogs and return/gets the selected blog
@app.route('/selected_blog', methods=['GET'])
def selected_blog():
    blog_id = request.args.get('id')
    blog_post = Blogz.query.get(blog_id)
    author_id = blog_post.author_id
    user = User.query.get(author_id)
    return render_template('selected_blog.html', user_id=blog_id, blog=blog_post, user=author_id, username=user)



# TODO: new post and check for errors
@app.route('/newpost', methods=['POST', 'GET'])
def newpost():
    # currently no errors
    title_error = ''
    content_error = ''
    error_check = False

    if request.method == 'GET':
        return render_template('newpost.html', title="Add a Blog Entry")

    if request.method == 'POST':
        blog_title = request.form['blog_title']
        blog_content = request.form['blog_content']
        blog_pubdate = datetime.now()
        author_id = User.query.filter_by(username=session['username']).first().id

        # no title error send to newpost
        if not blog_title:
            title_error = 'No Title Written'
            error_check = True

            # no content error send to newpost
        if not blog_content:
            content_error = 'Write something!'
            error_check = True

            # redirect to blog
        if error_check:
            return render_template('newpost.html', title_error=title_error, content_error=content_error)

        if (not title_error and not content_error):
            new_blog = Blogz(blog_title, blog_content, author_id)
            db.session.add(new_blog)
            db.session.commit()
            blog_id = str(new_blog.id)
            return redirect('/selected_blog?id='+ blog_id)

    return render_template('newpost.html', title='New Post')


if __name__ == '__main__':
    app.run()