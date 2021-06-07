from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from models import User, db
from Workers import *
from engine2_0 import *
from MFTasks import *
from Aristo_Web import get_url,get_user_notification

engine = Engine.get_instance(db)
auth = Blueprint('auth', __name__, template_folder="templates")


@auth.route('/login/<permission>')
def login(permission):
    return render_template('login.html', get_url=get_url,get_user_notification=get_user_notification)


@auth.route('/login/<permission>', methods=['POST'])
def login_post(permission):
    if request.method == "POST":
        session.permanent = True
        req = request.form['tab']
        if req == "sign-in":
            print("here")
            email = request.form['email_con']
            if "justice.gov.il" not in email and permission == 'gov':
                flash('אנא בצעו התחברות כאורחים')
                return redirect(get_url('auth.login', permission="viewer"))
            password = request.form['pass_con']
            user = User.query.filter_by(email=email).first()
            if user:
                if not check_password_hash(user.password, password):
                    flash('הסיסמא שהזנת שגויה')
                    return redirect(get_url('auth.login',permission=permission,get_user_notification=get_user_notification))
                else:
                    login_user(user)
                    return redirect(get_url('main.tenders'))

            flash('הפרטים שהזנת שגויים - אנא נסה שנית')
            return redirect(get_url('auth.login',permission=permission,get_user_notification=get_user_notification))
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
                    if validate_email(new_email):
                        if new_email not in emails:
                            if validate_password(new_pass):
                                try:
                                    permission_emails = []
                                    if (permission == 'gov' and "justice.gov.il" in new_email) or (new_email in permission_emails):
                                        is_gov = True
                                    else:
                                        is_gov = False
                                    user=User(first_name, last_name, new_email, generate_password_hash(new_pass, method='sha256'),is_gov)
                                    db.session.add(user)
                                    db.session.commit()
                                    flash("אנא השלם התחברות")
                                    return redirect(get_url("auth.login",permission=permission))
                                except Exception as e:
                                    print(e)
                                    print("problem")
                                    db.session.rollback()
                                    flash("קרתה תקלה, אנא נסו שנית")
                                    return render_template("login.html", get_url=get_url,permission=permission,get_user_notification=get_user_notification)
                            else:
                                flash("סיסמא חייבת להכיל לפחות 8 אותיות או ספרות")
                        else:
                            flash("אימייל כבר קיים במערכת")
                    else:
                        flash("כתובת אימייל לא תקינה")
                else:
                    flash("אימות סיסמא נכשל")
            except Exception as e:
                print(e)
    return render_template("login.html", get_url=get_url,permission=permission,get_user_notification=get_user_notification)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(get_url('main.Welcome',get_user_notification=get_user_notification))


if __name__ == '__main__':
    pass