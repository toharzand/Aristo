from flask import render_template, request, redirect, session, url_for, flash
from Workers import *
from aristoDB import *
import time

app = get_app()
db = get_db()

@app.route("/")
@app.route("/home")
def home():
    print("hello flask")
    return render_template("home.html")


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        session.permanent = True
        req = request.form['tab']
        if req == "sign-in":
            print("here")
            email = request.form['email_con']
            password = request.form['pass_con']
            users = User.query.all()
            for user in users:
                if user.password == password and user.email == email:
                    print("user in database - ready to move to profile")
                    flash("login successfully")
                    session["user"] = user.email
                    return redirect(url_for("user"))
            print("here")
            flash("סיסמא או מייל שגויים - לחץ על הרשמה")
        else:
            print("not in sign in - in sign up")
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            new_pass = request.form['new_pass']
            verify_pass = request.form['verify_pass']
            new_email = request.form['new_email']
            try:
                if new_pass == verify_pass:
                    if validate_email(new_email):
                        if validate_password(new_pass):
                            print("user is about to enter db")
                            user = User(first_name, last_name, new_email, new_pass)
                            try:
                                db.session.add(user)
                                db.session.commit()
                                flash("הרשמתך נקלטה בהצלחה, מיד תועברי לעמוד הפרופיל שלך")
                                time.sleep(5)
                                return redirect(url_for("user"))
                            except Exception as e:
                                print(e)
                                print("user cannot enter database")
                                db.session.rollback()
                                flash("תהליך יצירת משתמש נכשל - נסה שנית")
                        else:
                            flash("סיסמא חייבת להכיל אות גדולה, אות קטנה וספרה")
                    else:
                        flash("כתובת אימייל לא תקינה")
                else:
                    flash("אימות סיסמא נכשל")
            except Exception as e:
                print(e)
    print("return")
    return render_template("login.html")


@app.route("/user")
def user():
    return render_template("user.html")


@app.route("/tenders", methods=["POST", "GET"])
def tenders():
    if request.method == "POST":
        session.permanent = True
        try:
            req = request.form['user']
            tender_to_show = Tender.query.filter_by(tid=req).first()
            contact_guy = User.query.filter_by(id=tender_to_show.contact_user_from_department).first()
            return render_template("tender.html", tender=tender_to_show,contact_guy=contact_guy)
        except Exception as e:
            try:
                req = request.form['new_tender']
                return redirect(url_for("newTender"))
            except Exception as e:
                print(e)
                print("here you need to sort/filter")
                try:
                    req = ('subject',request.form['subject'])
                    print("req")
                    tender = Tender.query.order_by(Tender.subject.desc()).all()
                    print(tender.query.first())
                    return render_template("home.html")
                except:
                    try:
                        req = ('subject',request.form['start_date'])
                        Tender.query.order_by(Tender.start_date.desc()).all()
                    except:
                        req = ('subject',request.form['department'])
                        Tender.query.order_by(Tender.department.desc()).all()



            # values = function_for_sorting(request,Tender,db)
            #     return render_template("tenders.html", values=values, len=len(values))
    values = return_values(User,Tender)
    return render_template("tenders.html", values=values, len=len(values))


@app.route("/newTender", methods=["POST", "GET"])
def newTender():
    if request.method == 'POST':
        session.permanent = True
        try:
            protocol_number = request.form['protocol_number']
            tenders_committee_Type = request.form['tenders_committee_Type']
            procedure_type = request.form['procedure_type']
            subject = request.form['subject']
            department = request.form['department']
            try:
                start_date = str_to_datetime(request.form['start_date'])
                finish_date = str_to_datetime(request.form['finish_date'])
            except:
                start_date = datetime.now()
                finish_date = datetime.now()
            try:
                contact_user_from_department = int(request.form['contact_user_from_department'])
            except:
                flash("יש להזין את שם הגורם מטעם היחידה")
            tender_manager = request.form['tender_manager']
            tender = Tender(protocol_number,tenders_committee_Type,procedure_type,
                            subject,department,start_date,finish_date,
                            contact_user_from_department,tender_manager)
            try:
                db.session.add(tender)
                db.session.commit()
                flash("מכרז נוצר בהצלחה - מיד תועבר לעמוד המכרז")
                contact_guy = User.query.filter_by(id=tender.contact_user_from_department).first()
                return render_template("tender.html",tender=tender,contact_guy=contact_guy)
            except Exception as e:
                print(e)
                db.session.rollback()
                flash("יש להזין תאריכי התחלת וסיום המכרז")
        except Exception as e:
            print(e)
    return render_template("newTender.html")


@app.route("/tender/<tender>", methods=["POST", "GET"])
def tender(tender):
    print("heree")
    return render_template("tender.html", tender=tender)


@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/test")
def test():
    return render_template("test.html")


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
