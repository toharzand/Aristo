from flask import render_template, request, redirect, session, url_for, flash,Blueprint
from models import *
import time
from datetime import datetime
from engine import *
import random
from flask_login import login_required, current_user


db = get_db()
aristo_engine = Engine.get_instance(db)
main = Blueprint('main', __name__)


@main.route("/")
@main.route("/home")
def home():
    return render_template("home.html")


@main.route("/user")
@login_required
def user():
    return render_template("user.html")


@main.route("/tenders", methods=["POST", "GET"])
@login_required
def tenders():

    def extract_names(values):
        names = []
        for val in values:
            u_id = val[5]
            user_name = User.query.filter_by(id=u_id).first()
            user_name = f"{user_name.first_name} {user_name.last_name}"
            names.append(user_name)
        return names

    print("tenders - became personal")
    if request.method == "POST":
        session.permanent = True
        try:
            if request.form['user']:
                return redirect(url_for("main.tender",tender=request.form['user']))
        except Exception as e:
            print(e)
            try:
                req = request.form['new_tender']
                return redirect(url_for("main.newTender"))
            except Exception as e:
                print(e)
                print("here you need to sort/filter")
                try:
                    req = ('subject',request.form['subject'])
                    tenders = Tender.query.order_by(Tender.subject.desc()).all()
                    values = return_values(tenders)
                    print(values)
                    return render_template("tenders.html",values=values,len=len(values),names=extract_names(values))
                except Exception as e:
                    try:
                        req = ('finish_date',request.form['finish_date'])
                        tenders = Tender.query.order_by(Tender.finish_date.asc()).all()
                        values = return_values(tenders)
                        return render_template("tenders.html", values=values, len=len(values),names=extract_names(values))
                    except Exception as e:
                        try:
                            req = ('department',request.form['department'])
                            tenders = Tender.query.order_by(Tender.department.desc()).all()
                            values = return_values(tenders)
                            return render_template("tenders.html", values=values, len=len(values),names=extract_names(values))
                        except:
                            values = return_values(Tender.query.all())
                            return render_template("tenders.html", values=values, len=len(values),
                                                   names=extract_names(values))

    values = return_values(Tender.query.all())
    return render_template("tenders.html", values=values, len=len(values),names=extract_names(values))


@main.route("/tender/<tender>", methods=["POST", "GET"])
@login_required
def tender(tender):
    print("enter tender")
    if request.method == 'POST':
        session.permanent = True
        try:
            if request.form.get('new_task') == 'new_task':
                return redirect(url_for("main.newTask",tid=tender))
            else:
                return redirect(url_for("main.task",tid=request.form['view_task']))
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


@main.route("/newTender", methods=["POST", "GET"])
@login_required
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
                return redirect(url_for("main.tender",tender=tender.tid,contact_guy=contact_guy))
                # return render_template("tender.html",tender=tender,contact_guy=contact_guy)
            except Exception as e:
                print(e)
                db.session.rollback()
                flash("יש להזין תאריכי התחלת וסיום המכרז")
        except Exception as e:
            print(e)
    return render_template("newTender.html")


@main.route("/newTask/<tid>",methods=["POST", "GET"])
@login_required
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
                return redirect(url_for("main.tender",tender=tid))
            except Exception as e:
                print(e)
                db.session.rollback()
        except Exception as e:
            print(e)

    print("here")
    return render_template("newTask.html")



@main.route('/task/<tid>',methods=["POST", "GET"])
@login_required
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
            user_id = current_user.id
            task_note = TaskNote(user_id,time,task_id,user_msg)
            try:
                db.session.add(task_note)
                db.session.commit()
                print("data has been commited")
            except:
                db.session.rollback()
    print("build task page")
    task = Task.query.filter_by(task_id=tid).first()
    task_logs = TaskLog.query.filter_by(task_id = task.task_id).all()
    notes = TaskNote.query.filter_by(task_id = task.task_id).order_by("time").all()
    names = []
    for note in notes:
        names.append(turn_id_to_name(note.user_id))
    print(names)
    return render_template("task.html",task=task,names = names,task_logs=task_logs,task_notes = notes,len=len(notes))

@main.route("/about")
def about():
    return render_template("about.html")

@main.route("/test",methods=['POST','GET'])
def test():
    if request.method == 'POST':
        print("here")
        print(request.form)

    return render_template("test.html")


def turn_id_to_name(id):
    user = User.query.filter_by(id=id).first()
    return f"{user.first_name} {user.last_name}"