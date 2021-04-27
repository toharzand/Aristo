from flask import render_template, request, redirect, session, url_for, flash,Blueprint, jsonify
from models import *
import time
from datetime import datetime
from engine import *
import random
from flask_login import login_required, current_user
import MFTasks
import Workers


db = get_db()
aristo_engine = Engine.get_instance(db)
main = Blueprint('main', __name__)


def get_engine():
    return aristo_engine


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

    print("all tender page")
    if request.method == "POST":
        session.permanent = True
        try:
            if request.form['user']:
                # my_obj = aristo_engine.add_task(MFTasks.GetTendersPageRespons(request, db))
                # # time.sleep(10)
                # while not my_obj.is_complete():
                #     time.sleep(0.5)
                #     print("still waiting")
                #     continue
                # print("my obj",my_obj.is_complete())
                print(request.form['user'])
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
                    print("choose by subject")
                    tenders = Tender.query.order_by(Tender.subject.desc()).all()
                    values = return_values(tenders)
                    print("values",values)
                    return render_template("tenders.html",values=values,len=len(values),names=extract_names(values))
                except Exception as e:
                    try:
                        req = ('finish_date',request.form['finish_date'])
                        tenders = Tender.query.filter_by(id=current_user.id).order_by(Tender.finish_date.asc()).all()
                        values = return_values(tenders)
                        return render_template("tenders.html", values=values, len=len(values),names=extract_names(values))
                    except Exception as e:
                        try:
                            req = ('department',request.form['department'])
                            tenders = Tender.query.filter_by(id=current_user.id).order_by(Tender.department.desc()).all()
                            values = return_values(tenders)
                            return render_template("tenders.html", values=values, len=len(values),names=extract_names(values))
                        except:
                            values = return_values(Tender.query.all())
                            return render_template("tenders.html", values=values, len=len(values),
                                                   names=extract_names(values))

    try:
        conn = get_my_sql_connection()
        cursor = conn.cursor()
        query = f"""SELECT distinct tender_id FROM aristodb.usersintasks as u
                    inner join tasks t
                    on u.task_id=t.task_id
                    where user_id={current_user.id};"""
        cursor.execute(query)
        res = [i[0] for i in cursor.fetchall()]
        # values = return_values(Tender.query.all())
        my_lst = []
        for tender in Tender.query.all():
            if tender.tid in res:
                my_lst.append(tender)
        values = return_values(my_lst)
    except Exception as e:
        values = []
        print("here")
        print(e)
        raise e



    return render_template("tenders.html", values=values, len=len(values),names=extract_names(values))


@main.route("/tender/<tender>", methods=["POST", "GET"])
@login_required
def tender(tender):
    print("enter tender")
    if request.method == 'POST':
        session.permanent = True
        print("post - tender")
        try:
            if request.form.get('new_task') == 'new_task':
                return redirect(url_for("main.newTask",tid=tender))
            elif request.form.get('delete'):
                print("response send from delete button")
                try:
                    tender_to_delete = Tender.query.filter_by(tid=tender).first()
                    db.session.delete(tender_to_delete)
                    db.session.commit()
                    # aristo_engine.add_task(DeleteTenderDependencies(tender))
                    print("delete tender and cascade")
                    return redirect(url_for("main.tenders"))
                except Exception as e:
                    db.session.rollback()
                    print("here")
                    print(e)
                # print(f"this is the key:{'delete_tender'} and the value is:{request.form['delete_tender']}")
            else:
                try:
                    req = request.form['view_task']
                    print("over here")
                    print(req)
                    return redirect(url_for("main.task",tid=req))
                except Exception as e:
                    res = request.form['status']
                    print(e)
                    print(res)
                    res = res[1:len(res)-1]
                    res = res.split(",")
                    color = int(res[0])
                    task_id= int(res[1])
                    #user request to change status
                    if color == 1:
                        status = "פתוח"
                    elif color == 2:
                        status = "בעבודה"
                    elif color == 3:
                        status = "חסום"
                    elif color == 4:
                        status = "הושלם"
                    else:
                        status = "Null"
                    current_task = Task.query.filter_by(task_id=task_id).first()
                    current_task.status = status
                    db.session.commit()
                    print("change the status of the task")
                    return redirect(url_for("main.tender",tender=tender))

            return redirect(url_for("main.tenders"))

        except Exception as e:
            raise e
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
                           block_tasks=block_tasks,complete_tasks=complete_tasks,get_user_name = lambda id: User.query.filter_by(id=id).first())


@main.route("/newTender", methods=["POST", "GET"])
@login_required
def newTender():
    if request.method == 'POST':
        session.permanent = True
        print("inside new tender")
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
                name = request.form['contact_user_from_department'].split(" ")
                contact_user_id = User.query.filter_by(first_name = name[0],last_name = name[1]).first()
                print("con user: ",contact_user_id.id)
            except:
                if name == "":
                    flash("יש להזין את שם הגורם מטעם היחידה")
                else:
                    flash("שם איש הקשר לא  נמצא במערכת")
                return render_template("newTender.html")
            tender_manager = request.form['tender_manager']
            tender = Tender(protocol_number,tenders_committee_Type,procedure_type,
                            subject,department,start_date,finish_date,
                            contact_user_id.id,tender_manager)
            try:
                print(tender.contact_user_from_department)
                contact_guy = User.query.filter_by(id=tender.contact_user_from_department).first()
                db.session.add(tender)
                db.session.commit()
                tid = Workers.get_last_tender_id()
                aristo_engine.add_task(addNotificationTender(tid[0],"מכרז חדש נוצר",current_user.id,type="מכרז"))
                print("job has been transfer to engine - notification in created tender ")
                return redirect(url_for("main.tender",tender=tender.tid,contact_guy=contact_guy))
                # return render_template("tender.html",tender=tender,contact_guy=contact_guy)
            except Exception as e:
                print(e)
                db.session.rollback()
                flash("יש להזין תאריכי התחלת וסיום המכרז")
        except Exception as e:
            raise e
    return render_template("newTender.html")


@main.route("/newTask/<tid>",methods=["POST", "GET"])
@login_required
def newTask(tid):
    if request.method == "POST":
        print("new task")
        session.permanent = True
        try:
            subject = request.form['subject']
            users = current_user.id
            description = request.form['description']
            deadline = request.form['finish_date']
            if subject == "" or users == "" or description == "" or deadline == "" :
                flash("נא למלא את כל שדות החובה")
            else:
                print(len(subject))
                try:
                    task_file = request.files['selectedFile']
                except Exception as e:
                    print("user did not enterd file")
                    task_file = None
            status = request.form['status']
            odt = datetime.now()
            finish = None
            task = Task(tid,current_user.id, odt, deadline, finish, status, subject, description)
            try:
                db.session.add(task)
                db.session.commit()
            except Exception as e:
                print(e)
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
                user_in_current_task = UserInTask(task_id, users, "creator")
                db.session.add(user_in_current_task)
                db.session.commit()
                aristo_engine.add_task(addNotificationTask(task=task_id,subject="משימה נוספה בהצלחה",user_id=current_user.id,type="משימה"))
                # print(task_id)
                # task = Task.query.filter_by(task_id=task_id).first()
                # task_logs = TaskLog.query.filter_by(task_id=task_id).all()
                # notes = TaskNote.query.filter_by(task_id=task_id).order_by("time").all()
                # names = []
                # for note in notes:
                #     names.append(turn_id_to_name(note.user_id))
                # print("here")
                # print(task.subject)
                # print(task_logs)
                # print(notes)
                # print(names)
                return redirect(url_for("main.task",tid=task_id))
            except Exception as e:
                print(e)
                db.session.rollback()
        except Exception as e:
            print(e)
    return render_template("newTask.html")



@main.route('/task/<tid>',methods=["POST", "GET"])
@login_required
def task(tid):
    if request.method == "POST":
        session.permanent = True
        try:
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
                print("engine is on - popping notifications")
                aristo_engine.add_task(addNotificationsChat(task_id))

            except:
                db.session.rollback()
        except:
            user_to_add = request.form['user']
            try:
                db.session.add(UserInTask(tid,user_to_add,"viewer"))
                db.session.commit()
                print("user has entered to task")
                aristo_engine.add_task(addUserToTask(user_to_add,tid,type="משימה"))
            except Exception as e:
                db.session.rollback()
                print("user already in task!")
    print("build task page")
    task = Task.query.filter_by(task_id=tid).first()
    task_logs = TaskLog.query.filter_by(task_id = tid).all()
    notes = TaskNote.query.filter_by(task_id = tid).order_by("time").all()
    names = []
    for note in notes:
        names.append(turn_id_to_name(note.user_id))
    try:
        user = UserInTask.query.filter_by(task_id=tid,permissions="creator").first()
        user = User.query.filter_by(id=user.user_id).first()
    except Exception as e:
        print(e)
        user = current_user
    users_in_task = UserInTask.query.filter_by(task_id=tid).all()
    new_lst = []
    for userIntask in users_in_task:
        new_lst.append(User.query.filter_by(id=userIntask.user_id).first())
    print("new list",new_lst)
    return render_template("task.html",task=task,names = names,task_logs=task_logs,task_notes = notes,len=len(notes),user=user,all_users = User.query.all(),users_in_tasks=new_lst)

@main.route("/about")
def about():
    return render_template("about.html")

@main.route("/notification",methods=['POST','GET'])
def notification():
    if request.method == 'POST':
        print("here")
        print(request.form)
    return render_template("notification.html")

@main.route("/test",methods=['POST','GET'])
def test():
    if request.method == 'POST':
        print("here")
        print(request.form['myselect'])
    return render_template("test.html")


color = "black"

@main.route('/ajax')
def ajax():
    return render_template('ajax.html',x=color)

@main.route('/update_decimal',methods=['POST','GET'])
def update_decimal():
    if request.method == 'POST':
        print("message deliever")
    color = random.choice(["green","red","yellow"])
    return jsonify('',render_template('update_decimal.html',x=color))



def turn_id_to_name(id):
    user = User.query.filter_by(id=id).first()
    return f"{user.first_name} {user.last_name}"