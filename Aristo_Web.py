from flask import render_template, request, redirect, session, url_for, flash
from models import *
import time
from datetime import datetime
from engine import *
import random


app = get_app()
db = get_db()
aristo_engine = Engine(db)

@app.route("/")
@app.route("/home")
def home():
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
                            aristo_engine.add_task(AddUserTask(first_name,last_name,new_email,new_pass))
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


@app.route("/tender/<tender>", methods=["POST", "GET"])
def tender(tender):
    print("enter tender")
    if request.method == 'POST':
        session.permanent = True
        try:
            if request.form.get('new_task') == 'new_task':
                return redirect(url_for("newTask",tid=tender))
            else:
                return redirect(url_for("task",tid=request.form['view_task']))
        except Exception as e:
            print(e)
    tender = Tender.query.filter_by(tid=tender).first()
    print(tender)
    contact_guy = User.query.filter_by(id=tender.contact_user_from_department).first()
    open_tasks = Task.query.filter_by(status="פתוח",tender_id=tender.tid).all()
    on_prog_tasks = Task.query.filter_by(status="בעבודה",tender_id=tender.tid).all()
    print(on_prog_tasks)
    block_tasks = Task.query.filter_by(status="חסום",tender_id=tender.tid).all()
    complete_tasks = Task.query.filter_by(status="הושלם",tender_id=tender.tid).all()
    print(open_tasks)
    return render_template("tender.html", tender=tender,contact_guy=contact_guy,
                           open_tasks = open_tasks,on_prog_tasks=on_prog_tasks,
                           block_tasks=block_tasks,complete_tasks=complete_tasks)


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
                return render_template("newTender.html")
            tender_manager = request.form['tender_manager']
            tender = Tender(protocol_number,tenders_committee_Type,procedure_type,
                            subject,department,start_date,finish_date,
                            contact_user_from_department,tender_manager)
            try:
                print(tender.contact_user_from_department)
                contact_guy = User.query.filter_by(id=tender.contact_user_from_department).first()
                db.session.add(tender)
                db.session.commit()
                return redirect(url_for("tender",tender=tender.tid,contact_guy=contact_guy))
                # return render_template("tender.html",tender=tender,contact_guy=contact_guy)
            except Exception as e:
                print(e)
                db.session.rollback()
                flash("יש להזין תאריכי התחלת וסיום המכרז")
        except Exception as e:
            print(e)
    return render_template("newTender.html")


@app.route("/newTask/<tid>",methods=["POST", "GET"])
def newTask(tid):
    if request.method == "POST":
        print("new task")
        session.permanent = True
        try:
            subject = request.form['subject']
            users = request.form['users']
            description = request.form['description']
            deadline = request.form['finish_date']
            if subject == "" or users == "" or description == "" or deadline == "" :
                flash("נא למלא את כל שדות החובה")
            else:
                print(len(subject))
                try:
                    task_file = request.files['selectedFile']
                    print("user enterd file")
                    # print(task_file)
                    print(type(task_file))
                    print(dir(task_file))
                except Exception as e:
                    print("user did not enterd file")
                    task_file = None
            if len(subject) > 15:
                print("must be hereeeeeee")
                flash("נושא המשימה - עד 15 אותיות")
                return render_template("newTask.html")
            # if not (type(user) == 'int'):
            #     flash('must enter number for user identification')
            status = request.form['status']
            print(status)
            # add task to database
            odt = datetime.now()
            finish = None
            task = Task(tid, odt, deadline, finish, status, subject, description)
            try:
                db.session.add(task)
                db.session.commit()
                print("enter_to_db - task")
            except Exception as e:
                print(e)
                print("not able to insert to db")
                db.session.rollback()
            try:
                conn = get_my_sql_connection()
                cursor = conn.cursor()
                query = """select task_id from tasks
                            order by task_id desc
                            limit 1;
                            """
                cursor.execute(query)
                task_id = (cursor.fetchall()[0][0])
                user_in_current_task = UserInTask(task_id, users, "god")
                db.session.add(user_in_current_task)
                db.session.commit()
                return redirect(url_for("tender",tender=tid))
            except Exception as e:
                print(e)
                db.session.rollback()
        except Exception as e:
            print(e)

    print("here")
    return render_template("newTask.html")



@app.route('/task/<tid>',methods=["POST", "GET"])
def task(tid):
    if request.method == "POST":
        session.permanent = True
        if request.form['send']:
            user_msg = request.form['msg']
            time = datetime.now()
            task_id = request.form['send']
            conn = get_my_sql_connection()
            cursor = conn.cursor()
            query = f"""SELECT * FROM aristodb.tasksnotes
                        where task_id = {task_id};"""
            cursor.execute(query)
            user_id = 1
            task_note = TaskNote(user_id,time,task_id,user_msg)
            try:
                db.session.add(task_note)
                db.session.commit()
                print("data has been commited")
            except:
                db.session.rollback()
    print("build task page")
    task = Task.query.filter_by(task_id=tid).first()
    print(task.description)
    contact_guy = UserInTask.query.filter_by(task_id = task.task_id).first()
    contact_guy = User.query.filter_by(id=contact_guy.user_id).first()
    task_logs = TaskLog.query.filter_by(task_id = task.task_id).all()
    notes = TaskNote.query.filter_by(task_id = task.task_id).all()
    print(notes)
    return render_template("task.html",task=task,contact_guy=contact_guy,task_logs=task_logs,task_notes = notes)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/test")
def test():
    return render_template("test.html")


if __name__ == '__main__':
    # db.drop_all()
    db.create_all()
    # fill_db(50, db, User, Tender, Task, TaskLog, TaskNote, UserInTask)
    aristo_engine.initiate()
    app.run(debug=True)
