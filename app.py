import os
from flask import Flask, render_template, request, flash, redirect, session, g, abort, jsonify
from models import db, connect_db, User, Message, likes
from forms import SignupForm, LoginForm, MessageForm, EditProfileForm
from sqlalchemy.exc import IntegrityError
from flask_wtf.csrf import CSRFProtect, generate_csrf

CURR_USER_KEY = "curr_user"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "postgresql:///warbler")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev-secret")  # <--
app.config['WTF_CSRF_ENABLED'] = True

csrf = CSRFProtect()
connect_db(app)
csrf.init_app(app)

def inject_csrf():
    return dict(csrf_token=generate_csrf)
##############################################################################
# User session helpers

@app.before_request
def add_user_to_g():
    g.user = None
    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

def do_login(user):
    session[CURR_USER_KEY] = user.id

def do_logout():
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

##############################################################################
# User routes

@app.route('/signup', methods=["GET", "POST"])
def signup():
    if g.user:
        return redirect(f"/users/{g.user.id}")
    form = SignupForm()
    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Username or email already taken.", "danger")
            return render_template('users/signup.html', form=form)
        do_login(user)
        return redirect(f"/users/{user.id}")
    return render_template('users/signup.html', form=form)

@app.route('/login', methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(f"/users/{g.user.id}")
    form = LoginForm()
    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)
        if user:
            do_login(user)
            return redirect("/home")
        flash("Invalid credentials.", "danger")
    return render_template('users/login.html', form=form)

@app.route('/logout')
def logout():
    do_logout()
    flash("Logged out.", "success")
    return redirect('/login')

@app.route('/users/<int:user_id>')
def users_show(user_id):
    user = User.query.get_or_404(user_id)
    messages = (Message.query
                .filter(Message.user_id == user_id)
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all())
    return render_template('users/show.html', user=user, messages=messages)

@app.route('/users/profile', methods=["GET", "POST"])
def edit_profile():
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = EditProfileForm(obj=g.user)
    if form.validate_on_submit():
        if not User.authenticate(g.user.username, form.password.data):
            flash("Wrong password.", "danger")
            return render_template("users/edit.html", form=form)

        g.user.username = form.username.data
        g.user.email = form.email.data
        g.user.image_url = form.image_url.data or g.user.image_url
        g.user.header_image_url = form.header_image_url.data or g.user.header_image_url
        g.user.bio = form.bio.data  # <--
        g.user.location = form.location.data  # <--
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Username or email already taken.", "danger")
            return render_template("users/edit.html", form=form)

        flash("Profile updated!", "success")
        return redirect(f"/users/{g.user.id}")

    return render_template("users/edit.html", form=form)

##############################################################################
# Follow routes

@app.route('/users/follow/<int:user_id>', methods=['POST'])
def follow_user(user_id):
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    user = User.query.get_or_404(user_id)
    g.user.following.append(user)
    db.session.commit()
    return redirect(f"/users/{user_id}")

@app.route('/users/stop-following/<int:user_id>', methods=['POST'])
def stop_following(user_id):
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    user = User.query.get_or_404(user_id)
    g.user.following.remove(user)
    db.session.commit()
    return redirect(f"/users/{user_id}")

##############################################################################
# Likes routes

@app.route("/messages/<int:msg_id>/like", methods=["POST"])
def toggle_like(msg_id):
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get_or_404(msg_id)
    if msg.user_id == g.user.id:
        flash("You cannot like your own message.", "warning")  # <--
        return redirect(request.referrer or "/")

    if msg in g.user.liked_messages:
        g.user.liked_messages.remove(msg)
    else:
        g.user.liked_messages.append(msg)

    db.session.commit()
    if request.is_json:  # optional AJAX path
        return jsonify({"liked": msg in g.user.liked_messages, "message_id": msg.id})
    return redirect(request.referrer or "/")

@app.route("/users/<int:user_id>/likes")
def user_likes(user_id):
    user = User.query.get_or_404(user_id)
    msgs = (Message.query
            .join(likes, Message.id == likes.c.message_id)
            .filter(likes.c.user_id == user.id)
            .order_by(Message.timestamp.desc())
            .all())
    return render_template("users/likes.html", user=user, messages=msgs)

##############################################################################
# Message routes

@app.route("/messages/new", methods=["GET", "POST"])
def messages_add():
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    form = MessageForm()
    if form.validate_on_submit():
        m = Message(text=form.text.data, user_id=g.user.id)
        db.session.add(m)
        db.session.commit()
        return redirect(f"/users/{g.user.id}")
    return render_template("messages/new.html", form=form)

@app.route("/messages/<int:message_id>", methods=["GET"])
def messages_show(message_id):
    msg = Message.query.get_or_404(message_id)
    return render_template("messages/show.html", message=msg)

@app.route("/messages/<int:message_id>/delete", methods=["POST"])
def messages_destroy(message_id):
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    msg = Message.query.get_or_404(message_id)
    if msg.user_id != g.user.id:
        flash("You can only delete your own messages.", "danger")
        return redirect("/")
    db.session.delete(msg)
    db.session.commit()
    return redirect(f"/users/{g.user.id}")

##############################################################################
# Home feed

@app.route("/")
@app.route("/home")
def homepage():
    if not g.user:
        return render_template("home-anon.html")
    # feed: your messages + those you follow
    follow_ids = [u.id for u in g.user.following] + [g.user.id]
    messages = (Message.query
                .filter(Message.user_id.in_(follow_ids))
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all())
    return render_template("home.html", messages=messages)



##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

# @app.after_request
# def add_header(req):
#     """Add non-caching headers on every request."""

#     req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
#     req.headers["Pragma"] = "no-cache"
#     req.headers["Expires"] = "0"
#     req.headers['Cache-Control'] = 'public, max-age=0'
#     return req
