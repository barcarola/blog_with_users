from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from flask_gravatar import Gravatar

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog1.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
# Base = declarative_base()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

##CONFIGURE TABLES
class User(UserMixin, db.Model):
    __tablename__ = "Users_table"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(250), nullable=False)
    posts = db.relationship('BlogPost', back_populates='author')
    comments = db.relationship('Comments', back_populates='user')


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(1000), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('Users_table.id'), nullable=False)
    author = db.relationship("User", back_populates='posts')
    comments = db.relationship('Comments', back_populates='posts')

class Comments(db.Model):
    __tablename__= "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('Users_table.id'), nullable=False)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'), nullable=False)
    user = db.relationship("User", back_populates='comments')
    posts = db.relationship("BlogPost", back_populates='comments')



db.create_all()

@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    print('all posts get')
    return render_template("index.html", all_posts=posts)


@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    if request.method == "POST":
        hashed_pw = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8)
        new_user = User(email=form.email.data, password=hashed_pw, name=form.name.data)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('get_all_posts'))
    return render_template("register.html", form=form)

@app.route('/login', methods=["POST", "GET"])
def login():
    form = LoginForm()
    if request.method == "POST":
        if form.validate_on_submit():
            check_user = User.query.filter_by(email=form.email.data).first()
            if check_user != None:
                checking_pw = check_password_hash(check_user.password, form.password.data)
                if checking_pw:
                    login_user(check_user)
                    return redirect(url_for('get_all_posts'))
                else:
                    flash("Incorrect password")
            else:
                flash("Email is not registered")
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["GET", 'POST'])
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    comment_form = CommentForm()
    gravatar = Gravatar(app,
                        size=100,
                        rating='g',
                        default='retro',
                        force_default=False,
                        force_lower=False,
                        use_ssl=False,
                        base_url=None)
    if comment_form.validate_on_submit():
        if request.method == "POST":
            new_comment = Comments(text=comment_form.body.data, user_id=current_user.id, blog_id=post_id)
            db.session.add(new_comment)
            db.session.commit()
            print('fjkljfkljfkl')
            # if I use render_template it will somehow fill ckeditor with previous comment
            # and post it even without me pressing submit. Problem is somehow solved when redirect is used.
            # maybe its because it was a post request, not get and browser gets confused.
            return redirect(url_for('show_post', post_id=post_id))
    else:
        return render_template("post.html", post=requested_post, comment_form=comment_form, gravatar=gravatar)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post", methods=["POST", "GET"])
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            date=date.today().strftime("%B %d, %Y"),
            author_id=int(current_user.id)
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=['POST', 'GET'])
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>")
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))

@app.route('/user/<id>', methods=['GET', 'POST'])
# if I use app route only '/' (without <author>) only with get method, code runs not this func, but get_all_posts' route,
# and this func will never be executed!!!
def filter_user(id):
    user = User.query.get(id)
    print(user.posts)
    print(user)
    return render_template('index.html', all_posts=user.posts)


if __name__ == "__main__":
    app.run(debug=True)
