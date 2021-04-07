from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from models import User, db
from Workers import *
from engine import *

engine = Engine(db)
auth = Blueprint('auth', __name__)


@auth.route('/login')
def login():
    return render_template('login.html')


@auth.route('/login', methods=['POST'])
def login_post():
    if request.method == "POST":
        session.permanent = True
        req = request.form['tab']
        if req == "sign-in":
            print("here")
            email = request.form['email_con']
            password = request.form['pass_con']

            user = User.query.filter_by(email=email).first()
            if user:
                if not check_password_hash(user.password, password):
                    flash('הסיסמא שהזנת שגויה')
                    return redirect(url_for('auth.login'))
                else:
                    login_user(user)
                    return redirect(url_for('main.tenders'))

            flash('הפרטיפ שהזנת שגויים - אנא נסה שנית')
            return redirect(url_for('auth.login'))

        else:
            print("not in sign in - in sign up")
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            new_pass = request.form['new_pass']
            verify_pass = request.form['verify_pass']
            new_email = request.form['new_email']
            try:
                if new_pass == verify_pass:
                    emails = [u.email for u in User.query.all()]
                    if validate_email(new_email) and new_email not in emails:
                        if validate_password(new_pass):
                            user = User(first_name, last_name, new_email, generate_password_hash(new_pass, method='sha256'))
                            try:
                                db.session.add(user)
                                db.session.commit()
                                flash("אנא השלם התחברות")
                                return redirect(url_for("login.html"))
                            except Exception as e:
                                print(e)
                                print("problem")
                                db.session.rollback()
                                return render_template("login.html")
                        else:
                            flash("סיסמא חייבת להכיל אות גדולה, אות קטנה וספרה")
                    else:
                        flash("כתובת אימייל לא תקינה")
                else:
                    flash("אימות סיסמא נכשל")
            except Exception as e:
                print(e)
    return render_template("login.html")


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))
