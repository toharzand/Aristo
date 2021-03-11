from flask import render_template, request, redirect, session, url_for, flash
from Workers import *
from aristoDB import *
import time
from datetime import datetime
import engine


app = get_app()
db = get_db()
aristo_engine = engine.Engine(db)

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
                    emails = [u.email for u in User.query.all()]
                    if validate_email(new_email) and new_email not in emails:
                        if validate_password(new_pass):
                            print(validate_password(new_pass))
                            print("user is about to enter db")
                            user = User(first_name, last_name, new_email, new_pass)
                            aristo_engine.add_task(engine.AddUserTask(first_name,last_name,new_email,new_pass))
                            return redirect(url_for("user"))
                        else:
                            flash("סיסמא חייבת להכיל אות גדולה, אות קטנה וספרה")
                    else:
                        flash("כתובת אימייל לא תקינה")
                else:
                    flash("אימות סיסמא נכשל")
            except Exception as e:
                print(e)
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
            return redirect(url_for("tender",tender=req))
        except:
            try:
                req = request.form['new_tender']
                return redirect(url_for("newTender"))
            except Exception as e:
                print(e)
                print("here you need to sort/filter")
                try:
                    req = ('subject',request.form['subject'])
                    tenders = Tender.query.order_by(Tender.subject.desc()).all()
                    values = return_values(tenders)
                    return render_template("tenders.html",values=values,len=len(values))
                except Exception as e:
                    try:
                        req = ('finish_date',request.form['finish_date'])
                        tenders = Tender.query.order_by(Tender.finish_date.asc()).all()
                        values = return_values(tenders)
                        return render_template("tenders.html", values=values, len=len(values))
                    except Exception as e:
                        req = ('department',request.form['department'])
                        tenders = Tender.query.order_by(Tender.department.desc()).all()
                        values = return_values(tenders)
                        return render_template("tenders.html", values=values, len=len(values))
    values = return_values(tenders=Tender.query.all())
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







@app.route("/newTask",methods=["POST", "GET"])
def newTask():
    if request.method == "POST":
        session.permanent = True
        try:
            subject = request.form['subject']
            users = request.form['users']
            description = request.form['description']
            deadline = request.form['finish_date']
            if subject == "" or users == "" or description == "" or deadline == "" :
                flash("נא למלא את כל שדות החובה")
            else:
                try:
                    task_file = request.form['task_file']
                except Exception as e:
                    task_file = None
            try:
                status = request.form['status']
            except:
                status = 'פתוח'

            # add task to database
            tender_id = 15
            odt = datetime.now()
            finish = None
            task = Task(tender_id, odt, deadline, finish, status, subject, description)
            try:
                db.session.add(task)
                db.session.commit()
            except:
                print("not able to insert to db")
                db.session.rollback()

        except Exception as e:
            print(e)

    print("here")
    return render_template("newTask.html")



@app.route("/tender/<tender>", methods=["POST", "GET"])
def tender(tender):
    print("enter")
    if request.method == 'POST':
        session.permanent = True
        return redirect(url_for("newTask"))
    tender = Tender.query.filter_by(tid=(tender)).first()
    contact_guy = User.query.filter_by(id=tender.contact_user_from_department).first()
    return render_template("tender.html", tender=tender,contact_guy=contact_guy)



@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/test")
def test():
    return render_template("test.html")


if __name__ == '__main__':
    db.create_all()
    aristo_engine.initiate()
    app.run(debug=True)
