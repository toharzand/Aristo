from flask import render_template, request, redirect, session, url_for, flash,Blueprint, jsonify
from models import *
import time
from datetime import datetime
from engine2_0 import Engine
import random
from flask_login import login_required, current_user
from MFTasks import *
import Workers


# ----------   global vars  ----------
db = get_db()
aristo_engine = None
main = Blueprint('main', __name__)
app_root = models.get_app().config["APPLICATION_ROOT"]
server_name = models.get_app().config["SERVER_NAME"]







def define_globals():
    global aristo_engine
    aristo_engine = Engine.get_instance()

def get_url(endpoint, **values):
    return app_root + url_for(endpoint, **values)


def get_engine():
    return aristo_engine

# def get_url(endpoint, **values):
#     return app_root + url_for(endpoint, **values)

def get_user_notification():
    try:
        user_id = current_user.id
        conn = get_my_sql_connection()
        cursor = conn.cursor()
        query = f"""select * from notifications n
                    inner join notificationsintask
                    on n.nid = notificationsintask.nid
                    where user_id = {user_id}
                    and status = FALSE;"""
        cursor.execute(query)
        data = cursor.fetchall()
        return len(data)
    except Exception as e:
        print(e)
        return 0


@main.route("/",methods=["POST", "GET"])
def root():
    # return redirect("https://icc.ise.bgu.ac.il/njsw21/home")
    # return redirect(f"{app_root}/home")
    return redirect(get_url("main.Welcome"))

@main.route("/Welcome",methods=["POST", "GET"])
def Welcome():
    # return redirect("https://icc.ise.bgu.ac.il/njsw21/home")
    # return redirect(f"{app_root}/home")
    print("here")
    return render_template("welcome.html",get_url=get_url,get_user_notification=get_user_notification)


@main.route("/home",methods=["POST", "GET"])
def home():
    if request.method == "POST":
        session.permanent = True
        print("trying to leave meassage")
        try:
            name = request.form['Name']
            email = request.form['Email']
            msg = request.form['Message']
            aristo_engine.add_task(AddVisitorNote(name,email,msg))
            return render_template("home.html", get_url=get_url,get_user_notification=get_user_notification)
        except Exception as e:
            print("could not handle visitor msg")
    return render_template("home.html", get_url=get_url,get_user_notification=get_user_notification)


@main.route(f"{app_root}/user")
@login_required
def user():
    return render_template("user.html", get_url=get_url)

@main.route("/tenderWizard",methods = ["POST","GET"])
@login_required
def tender_wizard():
    # # todo - delete the following line:
    # res = aristo_engine.add_task(SendEmail("aristotenders@gmail.com","test on system","tests"))
    # if res.error_occurred():
    #     raise res.get_data_once()
    # ######
    procedure_type_lst = ['מכרז פומבי', 'תיחור סגור', 'פנייה פומבית', 'RFI', 'מכרז חשכ"ל', 'הצעת מחיר']
    department_lst = ['רווחה', 'מערכות מידע', 'לוגיסטיקה','לשכה משפטית',"סיוע משפטי","פרקליטות","יחידת החילוט","רשות הפטנטים","היחידה הבינלאומית","אגף הבטחון","הדרכה","דיור","דוברות",'אופוטרופוס כללי',"מדיניות ואסטרטגיה"]
    tenders_committee_Type_lst = ['רכישות', 'תקשוב', 'יועצים']
    if request.method == "POST":
        print("Welcome to the Wizard")
        try:
            com_type = request.form["tenders_committee_Type"]
            protocol = request.form["protocol"]
            dep = request.form["department"]
            proc_type = request.form["procedure_type"]
            contact_user = request.form["contact_user_from_department"]
            finish_date = request.form["finish_date"]
            if finish_date != "" and str_to_datetime(finish_date) < datetime.now():
                flash("תאריך סיום מכרז חייב להיות מאוחר מתאריך פתיחת המכרז(היום)")
                return render_template("tenderWizard.html", get_url=get_url,
                                       users=User.query.filter_by(is_gov=current_user.is_gov).all(),
                                       procedure_type_lst=procedure_type_lst,
                                       department_lst=department_lst,
                                       tenders_committee_Type_lst=tenders_committee_Type_lst,
                                       get_user_notification=get_user_notification)
            print(finish_date)
            print(contact_user)
            subject = request.form["subject"]
            print(com_type,dep,proc_type)
            tid_template = TenderTemplate.query.filter_by(tenders_committee_Type=com_type,procedure_type=proc_type,department=dep).first()
            print("prepare for query, this is id: ", tid_template.tid)
            if tid_template:
                print("good")
            res = aristo_engine.add_task(CreateTenderFromTemplate(tid_template.tid,
                                                                  contact_user,subject,protocol,finish_date, current_user.id), True)
            if res.error_occurred():
                raise res.get_data_once()
            return redirect(get_url("main.tender",tender=Tender.query.order_by(Tender.tid.desc()).first().tid+1,get_user_notification=get_user_notification))
        except Exception as e:
            print("error ", e)
            flash("הפרטים שהזנת שגויים, אנא נסו שנית")

    return render_template("tenderWizard.html", get_url=get_url,users=User.query.filter_by(is_gov=current_user.is_gov).all(),procedure_type_lst=procedure_type_lst,
                           department_lst=department_lst,tenders_committee_Type_lst=tenders_committee_Type_lst,get_user_notification=get_user_notification)


@main.route("/tenders", methods=["POST", "GET"])
@login_required
def tenders():
    print("all tender page")
    if request.method == "POST":
        session.permanent = True
        try:
            if request.form['user']:
                return redirect(get_url("main.tender",tender=request.form['user'],get_user_notification=get_user_notification))
        except Exception as e:
            print(e)
            try:
                req = request.form['new_tender']
                return redirect(get_url("main.newTender",get_user_notification=get_user_notification))
            except Exception as e:
                print(e)
                print("here you need to sort/filter")
                try:
                    req = ('subject',request.form['subject'])
                    print(req)
                    values = get_tenders_to_show(sorted='subject')
                    return render_template("tenders.html",values=values,len=len(values),names=extract_names(values), get_url=get_url,get_user_notification=get_user_notification)
                except Exception as e:
                    try:
                        req = ('finish_date',request.form['finish_date'])
                        print(req)
                        print('choose finish date')
                        values = get_tenders_to_show(sorted='finish_date')
                        return render_template("tenders.html", values=values, len=len(values),names=extract_names(values), get_url=get_url,get_user_notification=get_user_notification)
                    except Exception as e:
                        try:
                            req = ('department',request.form['department'])
                            values = get_tenders_to_show(sorted='department')
                            return render_template("tenders.html", values=values, len=len(values),names=extract_names(values), get_url=get_url,get_user_notification=get_user_notification)
                        except:
                            values = get_tenders_to_show()

                            return render_template("tenders.html", values=values, len=len(values),
                                                   names=extract_names(values), get_url=get_url,get_user_notification=get_user_notification)


    values = get_tenders_to_show()
    # mile_stones = aristo_engine.add_task(addMileStone(current_user),now=True)
    # if mile_stones.error_occurred():
    #     print("raisin error mile_stones.get_data_once()")
    #     raise mile_stones.get_data_once()
    # mile_stones = mile_stones.get_data_once()

    if values is None:
        values = []
    #
    # miles = ["פתיחת מכרז","הגשת הצעות","סיום מכרז","כתיבת מכרז"]
    # miles_to_deliver = [random.choice(miles) for _ in range(0,len(values))]

    return render_template("tenders.html", values=values, len=len(values),names=extract_names(values), get_url=get_url,get_user_notification=get_user_notification)


@main.route("/tender/<tender>", methods=["POST", "GET"])
@login_required
def tender(tender):
    print("enter tender")
    if request.method == 'POST':
        session.permanent = True
        print("post - tender")
        try:
            if request.form.get('new_task') == 'new_task':
                return redirect(get_url("main.newTask",tid=tender))
            elif request.form.get('delete'):
                print("response send from delete button")
                try:
                    tender_to_delete = Tender.query.filter_by(tid=tender).first()
                    if int(tender_to_delete.tender_manager) != current_user.id:
                        print(f"{tender_to_delete.tender_manager != current_user.id} - toy are here")
                        flash("מחיקה לא אושרה. רק מנהל המכרז יכול למחוק מכרז")
                        return redirect(get_url("main.tender",tender=tender_to_delete.tid))
                    tasks_relate_to_tender = Task.query.filter_by(tender_id=tender_to_delete.tid).all()
                    for task in tasks_relate_to_tender:
                        dependencies_to_delete = TaskDependency.query.filter_by(blocked = task.task_id).all()
                        for depend in dependencies_to_delete:
                            db.session.delete(depend)
                    db.session.commit
                    db.session.delete(tender_to_delete)
                    db.session.commit()
                    # aristo_engine.add_task(DeleteTenderDependencies(tender))
                    print("delete tender and cascade")
                    return redirect(get_url("main.tenders",get_user_notification=get_user_notification))
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
                    return redirect(get_url("main.task",tid=req))
                except Exception as e:
                    try:
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
                        # current_task = Task.query.filter_by(task_id=task_id).first()
                        # current_task.status = status
                        # db.session.commit()
                        res = aristo_engine.add_task(UpdateTaskStatus(task_id,current_user.id,status))
                        if res.error_occurred():
                            raise res.get_data_once()
                        print("change the status of the task")
                        return redirect(get_url("main.tender",tender=tender,get_user_notification=get_user_notification))
                    except:
                        # raise e
                        if request.form.get('updateTender'):
                            return redirect(get_url("main.updateTender", tender_id=tender,get_user_notification=get_user_notification))
                        else:
                            raise e
            return redirect(get_url("main.tenders",get_user_notification=get_user_notification))

        except Exception as e:
            raise e
    tender = Tender.query.filter_by(tid=tender).first()
    print(tender)
    contact_guy = User.query.filter_by(id=tender.contact_user_from_department).first()
    manager = User.query.filter_by(id=tender.tender_manager).first()
    open_tasks = Task.query.filter_by(status="פתוח",tender_id=tender.tid).all()
    on_prog_tasks = Task.query.filter_by(status="בעבודה",tender_id=tender.tid).all()
    print(on_prog_tasks)
    block_tasks = Task.query.filter_by(status="חסום",tender_id=tender.tid).all()
    complete_tasks = Task.query.filter_by(status="הושלם",tender_id=tender.tid).all()
    print(open_tasks)
    milestone = ""
    if len(complete_tasks) == len(Task.query.filter_by(tender_id=tender.tid).all()) and len(complete_tasks) > 0:
        milestone = "מכרז הושלם"
    else:
        res = aristo_engine.add_task(GetQueueOfMilestones(tender.tid),now=True)
        if res.error_occurred():
            raise res.get_data_once()
        lst_of_milestones = res.get_data_once()
        if len(lst_of_milestones) == 0:
            milestone = "לא הוגדרו אבני דרך"
        else:
            for i,ms in enumerate(lst_of_milestones):
                if ms.status ==  "הושלם":
                    continue
                else:
                    milestone = ms.subject
                    break

    return render_template("tender.html", tender=tender,contact_guy=contact_guy,manager=manager,
                           open_tasks = open_tasks,on_prog_tasks=on_prog_tasks,
                           block_tasks=block_tasks,complete_tasks=complete_tasks,
                           get_user_name = lambda id: User.query.filter_by(id=id).first(), get_url=get_url
                           ,get_user_notification=get_user_notification,milestone = milestone)


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
                print("inside date time tender")
                print(request.form['start_date'])
                start_date = str_to_datetime(request.form['start_date'])
                finish_date = str_to_datetime(request.form['finish_date'])
                if finish_date < start_date:
                    flash("תאריך סיום מכרז חייב להיות מאוחר מתאריך פתיחת המכרז(היום)")
                    return render_template("newTender.html",
                                           users=User.query.filter_by(is_gov=current_user.is_gov).all(),
                                           get_url=get_url, get_user_notification=get_user_notification)
                print(start_date)
                print(finish_date)
            except Exception as e:
                raise e
                print("inside date time tender exception")
                start_date =datetime.now()
                finish_date = datetime.now()
            try:
                # name = request.form['contact_user_from_department'].split(" ")
                contact_user_id = request.form['contact_user_from_department']
                print("con user: ",contact_user_id)
            except:
                if name == "":
                    flash("יש להזין את שם הגורם מטעם היחידה")
                else:
                    flash("שם איש הקשר לא  נמצא במערכת")
                return render_template("newTender.html",users = User.query.filter_by(is_gov = current_user.is_gov).all(), get_url=get_url)
            tender_manager = current_user.id
            tender = Tender(protocol_number,tenders_committee_Type,procedure_type,
                            subject,department,start_date,finish_date,
                            contact_user_id,tender_manager)
            try:
                print(tender.contact_user_from_department)
                contact_guy = User.query.filter_by(id=tender.contact_user_from_department).first()
                db.session.add(tender)
                db.session.commit()
                tid = Workers.get_last_tender_id()
                print("now enter the engine")
                aristo_engine.add_task(addNotificationTender(tid[0],"מכרז חדש נוצר",current_user.id,type="מכרז"))
                print("job has been transfer to engine - notification in created tender ")
                return redirect(get_url("main.tender",tender=tender.tid,contact_guy=contact_guy,get_user_notification=get_user_notification))
                # return render_template("tender.html",tender=tender,contact_guy=contact_guy)
            except Exception as e:
                print(e)
                db.session.rollback()
                flash("יש להזין תאריכי התחלת וסיום המכרז")
        except Exception as e:
            flash("אנא הזינו נתונים נכונים")
            print(e)
    return render_template("newTender.html",users = User.query.filter_by(is_gov = current_user.is_gov).all(), get_url=get_url,get_user_notification=get_user_notification)


@main.route("/updateTender/<tender_id>", methods=["POST", "GET"])
@login_required
def updateTender(tender_id):
    if request.method == "POST":
        tender = Tender.query.filter_by(tid=tender_id).first()
        dict = {}
        print("updating tender")
        for key, value in request.form.items():
            if value.strip() != "":
                print(key,value)
                dict[key] = value
        for key,value in dict.items():
            setattr(tender, key, value)
        db.session.commit()
        return redirect(get_url("main.tender",tender=tender_id,get_user_notification=get_user_notification))
    def extract_name_from_tender(tender):
        cont_user, tender_manager = tender.contact_user_from_department, tender.tender_manager
        cont_user = User.query.filter_by(id=cont_user).first()
        tender_manager = User.query.filter_by(id=tender_manager).first()
        return [f"{cont_user.first_name} {cont_user.last_name}",f"{tender_manager.first_name} {tender_manager.last_name}"]
    tender = Tender.query.filter_by(tid=tender_id).first()
    return render_template("updateTender.html",tender=tender,users = User.query.filter_by(is_gov = current_user.is_gov).all(),get_url=get_url,names=extract_name_from_tender(tender),get_user_notification=get_user_notification)






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
            if 'milestone' in request.form.keys():
                is_milestone = True
            else:
                is_milestone = False
            task = Task(tid,current_user.id, odt, deadline, finish, status, subject, description,is_milestone)
            try:
                db.session.add(task)
                db.session.commit()
                print(f"task added succusfully by user number: {current_user.id}")
                x = aristo_engine.add_task(LogNewTask(current_user.id))
                x.wait_for_completion()
                print("this is x.is_complete - ",x.is_complete_att)
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
                return redirect(get_url("main.task",tid=task_id,get_user_notification=get_user_notification))
            except Exception as e:
                print(e)
                db.session.rollback()
        except Exception as e:
            print(e)
    return render_template("newTask.html",get_url=get_url,get_user_notification=get_user_notification)



@main.route('/task/<tid>',methods=["POST", "GET"])
@login_required
def task(tid):
    if request.method == "POST":
        session.permanent = True
        if "updateTask" in request.form.keys():
            return redirect(get_url("main.updateTask", task_id=tid,get_user_notification=get_user_notification))
        try:
            task_id = request.form['createDependency']
            print(task_id)
            return redirect(get_url("main.createDependency",task_id=task_id,get_user_notification=get_user_notification))
        except Exception as e:
            try:
                if request.form.get("delete"):
                    print("on delete")
                    task = Task.query.filter_by(task_id=tid).first()
                    get_user = UserInTask.query.filter_by(task_id=tid,permissions='creator').first()
                    print(current_user.id)
                    print(get_user.user_id)
                    if get_user.user_id != current_user.id:
                        return redirect(get_url("main.task",tid=tid,get_user_notification=get_user_notification))
                    dependencies_to_delete = TaskDependency.query.filter_by(blocked = task.task_id).all()
                    dependencies_to_delete += TaskDependency.query.filter_by(blocking = task.task_id).all()
                    for depend in dependencies_to_delete:
                        db.session.delete(depend)
                    try:
                        db.session.delete(task)
                        db.session.commit()
                        print("task deleted - redirect to tender page", task.tender_id)
                        return redirect(get_url("main.tender", tender=task.tender_id,get_user_notification=get_user_notification))
                    except Exception as e:
                        print(e)
                        db.session.rollback()
                user_msg = request.form['msg']
                time = datetime.now()
                task_id = request.form['send']
                conn = get_my_sql_connection()
                cursor = conn.cursor()
                query = f"""SELECT * FROM aristo.tasksnotes
                            where task_id = {task_id};"""
                cursor.execute(query)
                user_id = current_user.id
                task_note = TaskNote(user_id,time,task_id,user_msg)
                try:
                    db.session.add(task_note)
                    db.session.commit()
                    print("data has been commited")
                    print("engine is on - popping notifications")
                    x = aristo_engine.add_task(addNotificationsChat(task_id))
                    x.wait_for_completion()
                    print("x is - ",x.get_data_once())
                except:
                    db.session.rollback()
            except:
                try:
                    user_to_add = request.form['user']
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
    tender = Tender.query.filter_by(tid=Task.query.filter_by(task_id=tid).first().tender_id).first()
    return render_template("task.html",task=task,names = names,task_logs=task_logs,task_notes = notes,
                           len=len(notes),user=user,all_users = User.query.filter_by(is_gov = current_user.is_gov).all()
                           ,users_in_tasks=new_lst,get_url=get_url,get_user_notification=get_user_notification,tender = tender)


@main.route("/updateTask/<task_id>",methods=["POST","GET"])
@login_required
def updateTask(task_id):
    task = Task.query.filter_by(task_id=task_id).first()
    print(task.task_id)
    if request.method == "POST":
        print(f"update task number - {task_id}")
        dict = {}
        for key, value in request.form.items():
            if value.strip() != "":
                print(key,value)
                dict[key] = value
        for key,value in dict.items():
            setattr(task, key, value)
        db.session.commit()
        return redirect(get_url("main.task",tid=task_id,get_user_notification=get_user_notification))
    return render_template("updateTask.html",task=task,get_url=get_url,get_user_notification=get_user_notification)






@main.route("/createDependency/<task_id>",methods=["POST","GET"])
@login_required
def createDependency(task_id):
    print("inside create dependency")
    if request.method == "POST":
        session.permanent = True
        try:
            depender_task_id = request.form['depender_task']
            x=aristo_engine.add_task(CreateTaskDependency(depender_task_id,task_id))
            if x.error_occurred():
                if x.get_data_once() == "תלות זו קיימת. אנא בחרו משימה אחרת":
                    flash(x.get_data_once())
                flash("בחירה לא חוקית. ניסית ליצור תלות מעגלית!")
            else:
                print(x.get_data_once())
                return redirect(get_url("main.task", tid=task_id,get_user_notification=get_user_notification))
        except Exception as e:
            flash("תלות זו כבר קיימת! אנא בחר משימה אחרת")
    task = Task.query.filter_by(task_id=task_id).first()
    tender = Tender.query.filter_by(tid=task.tender_id).first()
    print(tender)
    contact_guy = User.query.filter_by(id=tender.contact_user_from_department).first()
    open_tasks = Task.query.filter_by(status="פתוח",tender_id=tender.tid).all()
    on_prog_tasks = Task.query.filter_by(status="בעבודה",tender_id=tender.tid).all()
    print(on_prog_tasks)
    block_tasks = Task.query.filter_by(status="חסום",tender_id=tender.tid).all()
    complete_tasks = Task.query.filter_by(status="הושלם",tender_id=tender.tid).all()
    print(open_tasks)
    return render_template("createDependency.html", tender=tender,contact_guy=contact_guy,
                           open_tasks = open_tasks,on_prog_tasks=on_prog_tasks,
                           block_tasks=block_tasks,complete_tasks=complete_tasks,
                           get_user_name = lambda id: User.query.filter_by(id=id).first()
                           , get_url=get_url,get_user_notification=get_user_notification)






@main.route("/about")
def about():
    return render_template("about.html",get_url=get_url)

@main.route("/notification",methods=['POST','GET'])
@login_required
def notification():
    if request.method == 'POST':
        print("here - notifications")
        print(request.form)
        try:
            nid_to_delete = request.form['delete_notification']
            nid_to_delete = Notification.query.filter_by(nid=nid_to_delete).first()
            db.session.delete(nid_to_delete)
            db.session.commit()
            print("note has been deleted")
        except Exception as e:
            db.session.rollback()
            print(e)
    try:
        print(current_user.id)
        user_id = current_user.id
        conn = get_my_sql_connection()
        cursor = conn.cursor()
        query = f"""select task_id,created_time,status,subject,type,n.nid from notifications n
                    inner join notificationsintask
                    on n.nid = notificationsintask.nid
                    where user_id = {user_id};"""
        cursor.execute(query)
        data = cursor.fetchall()
        data = get_data_notifications(data)
    except Exception as e:
        raise e
    return render_template("notification.html", data=data,get_url=get_url,get_user_notification=get_user_notification)

@main.route("/markAsRead/<nid>",methods=['POST','GET'])
def markAsRead(nid):
    notification = Notification.query.filter_by(nid=nid).first()
    notification_in_task = NotificationInTask.query.filter_by(nid=nid).first()
    task_id = notification_in_task.task_id
    notification.status = True
    db.session.commit()
    return redirect(get_url("main.task",tid=task_id))


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