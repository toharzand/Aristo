from faker import Faker
import random
from datetime import datetime
import numpy as np
from tqdm import tqdm
from models import *
import models
from flask_login import current_user
import engine2_0
import MFTasks

cont_users = ['צחי יעקב', 'עופר שווקי', 'יהל ישראל', 'יגאל בלפור', 'משה כהן', 'אבי סלומון', 'שחר סינואני',
              'ליאורה קחטן', 'שרונה בן שיטרית', 'ספיר כלפון', 'סמי גריידי', 'אפרת מצליח', 'אדוה הלוי',
              'עוזי נעים', 'נטע ראובני', 'אלי דווידי', "טלי צ'רני", 'לבנת כהן', 'מיכל שפירא',
              'יוני קראוני', 'מיסא זועבי', 'דניאלה יפת', 'נועה רוזנפלד', 'קרן נועם', 'יהודה כהן', 'הילה שלום',
              'לימור ניזרי', 'יהונתן קוליץ', 'מירב כהן', 'דליה בנימין', 'אבי סולומון', 'מנשה מלול', 'ירון זוהר',
              'ליבנת כהן']


def extract_names(values):
    names = []
    for val in values:
        u_id = val[5]
        user_name = models.User.query.filter_by(id=u_id).first()
        user_name = f"{user_name.first_name} {user_name.last_name}"
        u2_id = val[6]
        user2_name = models.User.query.filter_by(id=u2_id).first()
        user2_name = f"{user2_name.first_name} {user2_name.last_name}"
        names.append((user_name,user2_name))
    return names


def get_milestones():

    # get all the user tenders that related to him

    conn = models.get_my_sql_connection()
    cursor = conn.cursor()
    query = f"""SELECT distinct tender_id FROM aristo.usersintasks as u
                inner join tasks t
                on u.task_id=t.task_id
                where user_id={current_user.id};"""
    tenders_for_user = models.Tender.query.filter_by(tender_manager=current_user.id).all()
    tenders_for_user += models.Tender.query.filter_by(contact_user_from_department=current_user.id).all()
    cursor.execute(query)
    res = [i[0] for i in cursor.fetchall()]
    my_lst = []

    for tender_id in res:
        my_lst.append(models.Tender.query.filter_by(tid=tender_id).first())

    my_lst += tenders_for_user

    my_lst = list(set(my_lst))

    milestones = []

    for tender in my_lst:
        complete_tasks = models.Task.query.filter_by(status="הושלם", tender_id=tender.tid).all()
        milestone = ""
        if len(complete_tasks) == len(models.Task.query.filter_by(tender_id=tender.tid).all()) and len(complete_tasks) > 0:
            milestone = "מכרז הושלם"
        else:
            res = engine2_0.Engine.get_instance().add_task(GetQueueOfMilestones(tender.tid), now=True)
            if res.error_occurred():
                raise res.get_data_once()
            lst_of_milestones = res.get_data_once()
            if len(lst_of_milestones) == 0:
                milestone = "לא הוגדרו אבני דרך"
            else:
                for i, ms in enumerate(lst_of_milestones):
                    if ms.status == "הושלם":
                        continue
                    else:
                        milestone = ms.subject
                        break
        milestones.append(milestone)
    return milestones


def enter_tenders_to_db(Tenders,db,number_of_tenders_to_add):
    fake = Faker()
    tenders_committee_Type_lst = ['רכישות', 'תקשוב', 'יועצים']
    procedure_type_lst = ['מכרז פומבי', 'תיחור סגור', 'פנייה פומבית', 'RFI', 'מכרז חשכ"ל', 'הצעת מחיר']
    department_lst = ['רווחה', 'מערכות מידע', 'לוגיסטיקה', 'לשכה משפטית ']
    subjects_lst = ['מתן שירותי הובלה וסבלות', 'עו"ד מתחום דיני העבודה', 'הדר דפנה מזנונים', 'מכרז לשדרוג תשתיות חשמל',
                    'התאמות בגין לקויות למידה', 'שיפוץ בית הדין השרעי', "אחסון מטלטלין חלק ב'", 'שירותי שמאות רכב',
                    'מכרז שמאות לציוד שנתפס', 'שמאות חפצי אומנות', 'מכירת חפצי אומנות וזהב.', 'ימי גיבוש 2020',
                    'לינות קאדים', 'מכרז הדפסות', 'מכרז לרכישת מוצרים AEM', 'מכרז שליחויות', 'מכרז תחזוקה',
                    'מרכז קלט נתונים רשל"ה', 'מתח נמוך', 'פטנטים חיפוש ידע', 'צילום מסמכים', 'צילום מסמכים', 'ט"ו בשבט',
                    'שימור ידע', 'שירותי בינוי תשתיות', 'תווי שי', 'מתן שירותי ביקורת פנים', 'מכרז בנקים',
                    'לסניגוריה הציבורית"', 'חדר כושר לבניין החדש', 'מזנון בשרי', 'מזנון חלבי', 'ניקיון בניין ראשי',
                    'ריהוט וציוד נייד', 'ציוד חשמלי למטבחונים', 'צמחיה בתוך המבנה', 'תמונות ואמצעים אסתטיים',
                    'יועץ ארגונומי', 'מולטימדיה - השלמת ציוד', 'עבודות בינוי ושיפוץ', 'צלונים']
    for i in tqdm(range(number_of_tenders_to_add)):
        protocol = "".join(random.choices([str(i) for i in range(0, 10)], k=8))
        comm = random.choice(tenders_committee_Type_lst)
        proc = random.choice(procedure_type_lst)
        subject = random.choice(subjects_lst)
        depar = random.choice(department_lst)
        start_date = fake.past_date()
        finish_date = fake.future_date()
        cont = random.choice([i for i in range(1,30)])
        manager = random.choice(cont_users)
        tender = Tenders(protocol, comm, proc, subject, depar, start_date, finish_date, cont, manager)
        try:
            db.session.add(tender)
            db.session.commit()
        except Exception as e:
            print(e)
            print('cannot add tender')
            continue
    return

def get_data_notifications(data):
    res = []
    for item in data:
        temp = (item[0],datetime_to_str(item[1].date()),item[2],item[3],item[4],item[5])
        res.append(temp)
    return res

def datetime_to_str(date):
    return datetime.strftime(date,"%d/%m/%Y")

def str_to_datetime(string):
    return datetime.strptime(string,'%Y-%m-%d')

def get_tenders_to_show(sorted_by=None):
    try:
        conn = models.get_my_sql_connection()
        cursor = conn.cursor()
        if sorted_by != None:
            query = f"""SELECT distinct tender_id FROM aristo.usersintasks as u
                        inner join tasks t
                        on u.task_id=t.task_id
                        inner join tenders tn
                        on t.tender_id = tn.tid
                        where u.user_id={current_user.id}
                        order by tn.{sorted_by} desc;"""
            tenders_for_user = models.Tender.query.filter_by(tender_manager=current_user.id).order_by(sorted_by).all()
            tenders_for_user += models.Tender.query.filter_by(contact_user_from_department=current_user.id).order_by(sorted_by).all()
        else:
            query = f"""SELECT distinct tender_id FROM aristo.usersintasks as u
                        inner join tasks t
                        on u.task_id=t.task_id
                        where user_id={current_user.id};"""
            tenders_for_user = models.Tender.query.filter_by(tender_manager=current_user.id).all()
            tenders_for_user += models.Tender.query.filter_by(contact_user_from_department=current_user.id).all()

        cursor.execute(query)
        res = [i[0] for i in cursor.fetchall()]
        my_lst = []

        for tender_id in res:
            my_lst.append(models.Tender.query.filter_by(tid=tender_id).first())
        my_lst += tenders_for_user

        my_lst = list(set(my_lst))
        def sort_tender(sorted_by,lst):
            if sorted_by == 'subject':
                lst = sorted(lst,key=lambda tender:tender.subject,reverse=False)
                return lst
            elif sorted_by == 'finish_date':
                lst = sorted(lst,key=lambda tender:tender.finish_date,reverse=False)
                return lst
            else:
                lst = sorted(lst,key=lambda tender:tender.department,reverse=False)
                return lst

        my_lst = sort_tender(sorted_by,my_lst)
        values = return_values(my_lst,conn)
        for val in values:
            print(val)
        if values is None:
            values = []
        return values
    except Exception as e:
        print("values has not ok")
        models.db.session.rollback()
        return []





def return_values(tenders,conn,filter_by=None,order_by=None):
    cursor = conn.cursor()
    query = f""" select distinct tender_id from users u
                inner join usersintasks ut
                on u.id=ut.user_id
                inner join tasks t
                on ut.task_id = t.task_id
                where u.id = {current_user.id}
            """
    cursor.execute(query)
    all_tenders_id = cursor.fetchall()
    print("here after change")
    print("all tenders id to present",tenders)
    days = []
    for tender in tenders:
        if tender.finish_date is not None:
            days.append((datetime.now()-tender.start_date).days)
        else:
            days.append(9999)
    values = []
    print("up - the tender manager")
    for i,tender in enumerate(tenders):
        # tender.start_date = datetime_to_str(tender.start_date)
        # if tender.finish_date is None:
        #     tender.finish_date = tender.start_date
        # else:
        #     tender.finish_date = datetime_to_str(tender.finish_date)
        task_comp = models.Task.query.filter_by(status="הושלם",tender_id=tender.tid).all()
        all_task = models.Task.query.filter_by(tender_id=tender.tid).all()
        # print(1)
        task_prog = (len(task_comp)/len(all_task)) if len(all_task) > 0 else 0
        # print(f"task_prog {task_prog}")
        time_that_passed = days[i] if days[i] > 0 else 1
        # print(f"time_that_passed {time_that_passed}")
        overall_time = (tender.finish_date-tender.start_date).days
        # print(f"overall_time {overall_time}")
        time_prog = (time_that_passed/overall_time) if overall_time > 0 else time_that_passed
        # print(f"time_prog {time_prog}")
        progress_bar = (task_prog/time_prog)*100 if time_prog > 0 else (task_prog/(time_prog+1))*100
        # print(progress_bar)
        ######  inserting milestones #######
        milestone = ""
        if len(all_task) == len(task_comp) and len(all_task) > 0:
            milestone = "המכרז הסתיים"
        elif len(all_task) == 0:
            milestone = "ללא משימות"
        else:
            res = engine2_0.Engine.get_instance().add_task(MFTasks.GetQueueOfMilestones(tender.tid))
            if res.error_occurred():
                raise res.get_data_once()
            print(f"milestones for {tender.tid} received")
            all_miles = res.get_data_once()
            for ms in all_miles:
                if ms.status == "חסום":
                    milestone = ms.subject
                    break
        if milestone == "":
            milestone = "ללא אבני דרך"
        ####################################

        values.append((tender.protocol_number,tender.tenders_committee_Type,
                       tender.procedure_type,tender.subject,tender.department,
                       tender.contact_user_from_department,tender.tender_manager,
                       datetime_to_str(tender.start_date),
                       datetime_to_str(tender.finish_date),days[i],tender.tid,int(progress_bar), milestone))
    return values



def validate_email(mail):
    import re
    email_re = re.compile("(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
    if len(email_re.findall(mail)) == 1:
        return True
    else:
        return False

def validate_password(password):
    import re
    pass_re = re.compile("[A-Za-z0-9@#$%^&+=]{8,}")
    if len(pass_re.findall(password)) == 1:
        return True
    else:
        return False


def enter_fake_users_to_db(number_of_users,db,Users):
    fake = Faker()
    for i in tqdm(range(number_of_users)):
        name = fake.name().split()
        f_name = random.choice(cont_users).split(" ")[0]
        l_name = random.choice(cont_users).split(" ")[0]
        email = f"{f_name}_{l_name}@gmail.com"
        password = "".join([str(np.random.randint(0,10)) for _ in range(8)])
        user = Users(first_name=f_name,last_name=l_name,email=email,password=password)
        try:
            db.session.add(user)
            db.session.commit()
        except:
            db.session.rollback()
            continue
    return

def delete_users_from_db(number_to_delete,db,Users):
    users = Users.query.all()
    for i,user in enumerate(users):
        if i == len(users):
            return
        elif i == number_to_delete:
            return
        else:
            try:
                db.session.delete(user)
                db.session.commit()
            except:
                db.session.rollback()


def enter_fake_tasks_to_db(Tender,Task,db):
    statuses = ['חסום','הושלם','פתוח','בעבודה']
    fake = Faker()
    tenders = Tender.query.all()
    for tender in tenders:
        for status in statuses:
            for i in range(random.randrange(0,10)):
                tender_id = tender.tid
                odt = fake.past_date()
                dead_line = fake.future_date()
                subject = random.choice(['יועמ"ש','ביטחון','חשבות'])
                description = f"זהו תיאור המשימה"
                task = Task(tender_id=tender_id,task_owner_id=5,odt=odt,deadline=dead_line,finish=None,status=status,subject=subject,description=description)
                try:
                    db.session.add(task)
                    db.session.commit()
                except Exception as e:
                    print("cannot enter user to db")
                    print(e)
                    db.session.rollback()


def enter_fake_task_logs(db,User,Task,TaskLog,num):
    fake = Faker()
    users = User.query.all()
    task = Task.query.all()
    users_id = [i for i in range(1,len(users))]
    tasks_id = [i for i in range(1,len(task))]
    for i in tqdm(range(num)):
        user = random.choice(users_id)
        task_id = random.choice(tasks_id)
        init_time = fake.date_time_this_month()
        description = f"זהו תיאור הפעולה בתוך המשימה"
        log = TaskLog(user,task_id,init_time,description)
        try:
            db.session.add(log)
            db.session.commit()
        except:
            pass


def enter_fake_task_noted(db,User,Task,TaskNote,num):
    fake = Faker()
    users = User.query.all()
    task = Task.query.all()
    users_id = [i for i in range(1,len(users))]
    tasks_id = [i for i in range(1,len(task))]
    for i in tqdm(range(num)):
        user = random.choice(users_id)
        task_id = random.choice(tasks_id)
        init_time = fake.date_time_this_month()
        description = f"זוהי הערה"
        note = TaskNote(user,init_time,task_id,description)
        try:
            db.session.add(note)
            db.session.commit()
        except Exception as e:
            print("cannot enter user to db")
            print(e)
            pass


def enter_fake_user_in_task(db,User,Task,UserInTask,num):
    prem = ['god','admin','editor','viewer']
    users = User.query.all()
    task = Task.query.all()
    users_id = [i for i in range(1,len(users))]
    tasks_id = [i for i in range(1,len(task))]
    tafus = []
    for i in tqdm(range(num)):
        user = random.choice(users_id)
        task_id = random.choice(tasks_id)
        if (user,task_id) in tafus:
            print("already inside")
            continue
        else:
            tafus.append((user,task_id))
        permission = random.choice(prem)
        user_in_task = UserInTask(task_id,user,permission)
        try:
            db.session.add(user_in_task)
            db.session.commit()
        except Exception as e:
            continue


def drop_all_tables(db):
    db.session.drop_all()

def fill_db(num,db,User,Tender,Task,TaskLog,TaskNote,UserInTask):
    enter_fake_users_to_db(num,db,User)
    enter_tenders_to_db(Tender,db,6*num)
    enter_fake_tasks_to_db(Tender,Task,db)
    enter_fake_task_logs(db,User,Task,TaskLog,18*num)
    enter_fake_task_noted(db,User,Task,TaskNote,18*num)
    enter_fake_user_in_task(db,User,Task,UserInTask,num*6)


def insert_tender_templates():
    tenders_committee_Type_lst = ['רכישות', 'תקשוב', 'יועצים']
    procedure_type_lst = ['מכרז פומבי', 'תיחור סגור', 'פנייה פומבית', 'RFI', 'מכרז חשכ"ל', 'הצעת מחיר']
    department_lst = ['רווחה', 'מערכות מידע', 'לוגיסטיקה', 'לשכה משפטית ']

    for i in tqdm(range(10)):
        comm = random.choice(tenders_committee_Type_lst)
        proc = random.choice(procedure_type_lst)
        depar = random.choice(department_lst)
        tender = TenderTemplate(comm, proc, depar)
        try:
            db.session.add(tender)
            db.session.commit()
        except Exception as e:
            print(e)
            print('cannot add tender')
            continue
    return


def insert_task_templates():
    statuses = ['חסום', 'הושלם', 'פתוח', 'בעבודה']
    subjects = ['כתיבת פרק בטיחות','כתיבת פרק פתיחה','כתיבת פרק חשבות','כתיבת פרק יועמ"ש','כתיבת פרק ועדת מכרזים','כתיבת פרק יועץ חיצוני','כתיבת פרק מנהל מכרז']
    description = "זהו תיאור המשימה - מוגבל בכמות מילים - נועד על מנת לתאר את המשימה בצורה פשוטה ועניינית"
    for subject in subjects:
        if subject == "כתיבת פרק פתיחה":
            task = TaskTemplate('פתוח',subject,description)
        else:
            task = TaskTemplate('חסום',subject,description)

        print("here")
        print(task.subject)
        try:
            db.session.add(task)
            db.session.commit()
        except Exception as e:
            print(e)
            db.session.rollback()


def insert_data_to_dependencies():
    from queue import Queue
    conn = get_my_sql_connection()
    cursor = conn.cursor()
    opens = """SELECT * from taskstemplate
                where status = 'פתוח';
            """
    blocked = """
                select * from taskstemplate
                 where status = 'חסום';
                """
    cursor.execute(opens)
    open_list = cursor.fetchall()
    cursor.execute(blocked)
    blocked_list = cursor.fetchall()
    all_tenders_templates = TenderTemplate.query.all()
    q = Queue(maxsize=len(open_list)+len(blocked_list))
    for tender in all_tenders_templates:
        for task in open_list:
            q.put(task[0])
        while not q.empty():
            v = q.get()

            


    conn.close()





    # all_tasks = TaskTemplate.query.all()
    # all_tenders = TenderTemplate.query.all()
    #
    #
    # for tender in all_tenders:

def get_last_tender_id():
    conn = models.get_my_sql_connection()
    cursor = conn.cursor()
    query = """select tid
                from tenders
                order by tid desc
                limit 1;
            """
    cursor.execute(query)
    return cursor.fetchone()



def function_for_sorting(request,Tender,db):
    pass

def insertTemplates():
    procedure_type_lst = ['מכרז פומבי', 'תיחור סגור', 'פנייה פומבית', 'RFI', 'מכרז חשכ"ל', 'הצעת מחיר']
    department_lst = ['רווחה', 'מערכות מידע', 'לוגיסטיקה','לשכה משפטית',"סיוע משפטי","פרקליטות","יחידת החילוט","רשות הפטנטים","היחידה הבינלאומית","אגף הבטחון","הדרכה","דיור","דוברות",'אופוטרופוס כללי',"מדיניות ואסטרטגיה"]
    tenders_committee_Type_lst = ['רכישות', 'תקשוב', 'יועצים']
    for i in procedure_type_lst:
        for j in department_lst:
            for k in tenders_committee_Type_lst:
                try:
                    models.db.session.add(models.TenderTemplate(k,i,j))
                    models.db.session.commit()
                except Exception as e:
                    print(e)
                    models.db.session.rollback()


    return None




def insert_task_templates():
    lst_of_tasks = [('פתוח','בקשה לוועדת מכרזים','הפניית בקשה לוועדת מכרזים ליציאה למכרז, '
                                                 'גורם אחראי:אמרכל / דורש רכש של היחידה בצירוף מכתב מנומק וחתום של מנהל היחידה', 14),
                    ('חסום', 'דיון והחלטה ביחס לבקשה',
                     'במשימה זו יש לקיים דיון ביחס לבקשה ולקבל החלטה האם לאשר את הבקשה או האם יש תנאי סף שלא עומדים בקנה אחד עם המדיניות',
                       9),
                    ('חסום', 'הקצאת מלווה מקצועי', 'הקצאת מלווה מקצועי לתהליך הכנת המכרז עד לבחירת הספק המועדף. '
                                                   'גורם אחראי - מנהלת תחום מכרזים – אגף הרכש והמכרזים',   4),
                    ('חסום','כתיבת מסמכי המכרז','במשימה זו נעקוב וננהל אחר כתיבת מסמכי המכרז, המתבצעים '
                                                'בעזרת מערכת נו"ח. גורם אחראי - היחידה המקצועית בסיוע של מלווה המכרז.'
                                                'ראו קבצים מצורפים למשימה.', 13),
                    ('חסום','בקרת התקדמות כתיבת מכרז','בקרה על התקדמות כתיבת מסמכי המכרז בהתאם ללו"ז שהוגדר, '
                                                      'גורם אחראי - בקרת תהליכים באגף הרכש והמכרזים', 12),
                    ('חסום','ייזום מפגש התנעה','במשימה זו יש לקבוע פגישת התנעה למכרז ולרתום את כל '
                                               'השותפים. גורם אחראי - מנהלת תחום מכרזים', 13),
                    ('חסום','אישור מסמכי המכרז','תהליך אישור מסמכי המכרז עובר להתייחסות הגורמים הרלוונטים. '
                                                'גורם אחראי - חשבות, ביטחון, מכרזים, ייעוץ משפטי, ביטוח והיחידה המקצועית', 10),
                    ('חסום','פרסום מכרז','במשימה זו יש לבצע פרסום של המכרז בהתאם לסוג המכרז '
                                         'גורם אחראי - מנהלת תחום מכרזים',  4),
                    ('חסום','הוצאת החלטה - ועדת מכרזים','הגשת בקשה לוועדת המכרזים והוצאת החלטה בסבב לפרסום המכרז, '
                                                        'גורם אחראי - גורם מיחידת המכרזים',  6),
                    ('חסום','כנס ספקים','במשימה זו יתאגדו כל הגורמים הרלוונטים לכדי ארגון כנס ספקים למכרז. '
                                        'גורם אחראי - יחידת המכרזים.', 13),
                    ('חסום', 'מפגש כנס ספקים','גורם אחראי - יחידה מקצועית',  11),
                    ('חסום', 'אישורי השתתפות - סיור קבלנים','שליחת אישורים על השתתפות בסיור קבלנים. '
                                                            'גורם אחראי - מנהלת תחום מכרזים',   4),
                    ('חסום', 'ריכוז שאלות ההברה מהספקים','במשימה זו יש לרכז את כל השאלות שעלו מהספקים בקשר לפרטי המכרז. '
                                                         'גורם אחראי - יחידת המכרזים',   5),
                    ('חסום', 'סבב מענה שאלות ההבהרה','גורם אחראי - מלווה המכרז',   3),
                    ('חסום', 'אישור מענה','תהליך אישור מענה לשאלות ההבהרה והתייחסות הגורמים הרלוונטיים. '
                                          'גורם אחראי -חשבות, ביטחון, מכרזים, ייעוץ משפטי, ביטוח והיחידה המקצועית',  12),
                    ('חסום', 'פרסום מענה לשאלות ההבהרה','גורם אחראי - מנהלת תחום מכרזים',   5),
                    ('חסום', 'וועדת מכרזים - הוצאת החלטה','הגשת בקשה לוועדת המכרזים והוצאת החלטה בסבב לפרסום המענה/דחיית מועדים. '
                                                          'גורם אחראי - גורם מיחידת המכרזים',  12),
                    ('חסום', 'הגשת הצעות','במשימה זו ירוכזו כל ההצעות של המכרז עד פקיעת מועד הגשת ההצעות. '
                                          'גורם אחראי - יחידת מכרזים',   8),
                    ('חסום', 'פתיחת תיבה','גורם אחראי - גורם מיחידת המכרזים',   6),
                    ('חסום', 'בדיקת תנאי סף מנהליים','בדיקת תנאי סף מנהליים. '
                                           'גורם אחראי - יחידת מכרזים',   8),
                    ('חסום', 'בדיקת תנאי סף מקצועיים', 'בדיקת תנאי סף מקצועיים. '
                                           'מנהלת תחום מכרזים – אגף הרכש והמכרזים',   9),
                    ('חסום', 'השלמות', 'ביצוע כל ההשלמות, '
                                           'גורם אחראי - יחידת מכרזים',  15),
                    ('חסום', 'פסילת הצעות', 'פסילת הצעות יש להביא לוועדת מכרזים. '
                                           'גורם אחראי - יחידת מכרזים',  14),
                    ('חסום', 'בדיקת איכות ההצעה','גורם אחראי - יחידת מכרזים',  10),
                    ('חסום', 'ממליצים','גורם אחראי - יחידת מכרזים',  15),
                    ('חסום', 'ראיונות','גורם אחראי - יחידת מכרזים',   6),
                    ('חסום', 'פתיחת הצעות מחיר','פתיחת הצעות מחיר באישור ועדת המכרזים. '
                                                'גורם אחראי - יחידת מכרזים',  11),
                    ('חסום', 'הכרזה על זוכה','אישור תוצאות והכרזה על זוכה. '
                                             'גורם אחראי - יחידת מכרזים',   4),
                    ('חסום', 'מכתבים לספקים','גורם אחראי - יחידת מכרזים',  12),
                    ('חסום', 'עיון בהצעה הזוכה','גורם אחראי - יחידת מכרזים',  10),
                    ('חסום', 'כתיבת מסמכי המכרז', 'במשימה זו נעקוב וננהל אחר כתיבת מסמכי המכרז, המתבצעים '
                                                  'בעזרת מערכת נו"ח. גורם אחראי - היחידה המקצועית בסיוע של מלווה המכרז.'
                                                  'ראו קבצים מצורפים למשימה.', 0, True),
                    ('חסום', 'פרסום מכרז', 'במשימה זו יש לבצע פרסום של המכרז בהתאם לסוג המכרז '
                                           'גורם אחראי - מנהלת תחום מכרזים', 0, True),
                    ('חסום', 'הגשת הצעות', 'במשימה זו ירוכזו כל ההצעות של המכרז עד פקיעת מועד הגשת ההצעות. '
                                           'גורם אחראי - יחידת מכרזים', 0, True),
                    ('חסום', 'פתיחת הצעות מחיר', 'פתיחת הצעות מחיר באישור ועדת המכרזים. '
                                                 'גורם אחראי - יחידת מכרזים', 0, True),
                    ('חסום', 'בחירת זוכה', 'גורם אחראי - יחידת מכרזים', 0, True),
                    ("הושלם", "משימה פותחת של מכרז","מערכת אריסטו", 0)]
    for template_task in lst_of_tasks:
        # if len(template_task) == 5:
        #     task_to_add = TaskTemplate(template_task[0], template_task[1], template_task[2], template_task[3],
        #                                template_task[4])
        # else:
        #     task_to_add = TaskTemplate(template_task[0], template_task[1], template_task[2], template_task[3])
        task_to_add = TaskTemplate(*template_task)
        try:
            db.session.add(task_to_add)
            db.session.commit()
        except Exception as e:
            print(e)
            print(template_task)
            db.session.rollback()
    nll_task = TaskTemplate.query.order_by(TaskTemplate.task_id.desc()).first()
    nll_task.task_id = 0
    db.session.commit()
    # conn = get_my_sql_connection()
    # curser = conn.cursor()
    # curser.execute("""
    # INSERT INTO aristo.taskstemplate (task_id, status, subject, description, time_delta)
    # VALUES (0, "הושלם", "משימה פותחת של מכרז","מערכת אריסטו", 0)
    # """)
    # conn.commit()



def insert_task_dependencies():
    print("here")
    tasks = TaskTemplate.query.all()
    tasks = [t.task_id for t in tasks]
    print(tasks)
    # dict_dependencies = {tasks[0] : [tasks[1]],
    #                      tasks[1] : [tasks[2],tasks[3],tasks[5]],
    #                      tasks[3] : [tasks[4],tasks[6]],
    #                      tasks[6] : [tasks[7]],
    #                      tasks[7] : [tasks[8]],
    #                      tasks[8] : [tasks[9]],
    #                      tasks[9] : [tasks[10]],
    #                      tasks[10] : [tasks[11]],
    #                      tasks[11] : [tasks[12]],
    #                      tasks[12] : [tasks[13]],
    #                      tasks[13] : [tasks[14]],
    #                      tasks[14] : [tasks[15]],
    #                      tasks[15] : [tasks[16]],
    #                      tasks[16] : [tasks[17]],
    #                      tasks[17] : [tasks[18]],
    #                      tasks[18] : [tasks[19],tasks[20],tasks[21]],
    #                      tasks[21] : [tasks[22]],
    #                      tasks[22] : [tasks[23]],
    #                      tasks[23] : [tasks[24]],
    #                      tasks[24] : [tasks[25]],
    #                      tasks[25] : [tasks[26]],
    #                      tasks[26] : [tasks[27]],
    #                      tasks[27] : [tasks[28]],
    #                      tasks[28] : [tasks[29]]}
    dict_dependencies = {tasks[0]: [tasks[1]],
                         tasks[1]: [tasks[2]],
                         tasks[2]: [tasks[3], tasks[4], tasks[6]],
                         tasks[4]: [tasks[5], tasks[7],tasks[31]],
                         tasks[7]: [tasks[8]],
                         tasks[8]: [tasks[9], tasks[32]],
                         tasks[9]: [tasks[10]],
                         tasks[10]: [tasks[11]],
                         tasks[11]: [tasks[12]],
                         tasks[12]: [tasks[13]],
                         tasks[13]: [tasks[14]],
                         tasks[14]: [tasks[15]],
                         tasks[15]: [tasks[16]],
                         tasks[16]: [tasks[17]],
                         tasks[17]: [tasks[18]],
                         tasks[18]: [tasks[19], tasks[33]],
                         tasks[19]: [tasks[20], tasks[21], tasks[22]],
                         tasks[22]: [tasks[23]],
                         tasks[23]: [tasks[24]],
                         tasks[24]: [tasks[25]],
                         tasks[25]: [tasks[26]],
                         tasks[26]: [tasks[27]],
                         tasks[27]: [tasks[28], tasks[34]],
                         tasks[28]: [tasks[29]],
                         tasks[29]: [tasks[30]], # milestone dependencies :
                         tasks[30]: [tasks[35]]
                         }

    for i,tender in tqdm(enumerate(TenderTemplate.query.all())):
        for key in dict_dependencies:
            for task in dict_dependencies[key]:
                if task == key:
                    continue
                try:
                    task_1 = TaskTemplate.query.filter_by(task_id=key).first()
                    task_2 = TaskTemplate.query.filter_by(task_id=task).first()
                    dep = TaskDependenciesTemplate(depender=task_1,dependee=task_2,tender_id=tender.tid)
                    print(dep)
                    db.session.add(dep)

                except Exception as e:
                    db.session.rollback()
                    raise e
    db.session.commit()
    print("commited")




if __name__ == '__main__':
    db.create_all()
    # insertTemplates()
    # insert_task_templates()
    insert_task_dependencies()
    # print(User.query.order_by("first_name").all())
    # users = models.User.query.all()
    # for user in users:
    #     if user.id > 40:
    #         try:
    #             models.db.session.delete(user)
    #             models.db.session.commit()
    #         except:
    #             models.db.session.rollback()
    # dep = TaskDependenciesTemplate(1,2,1)
    # try:
    #     db.session.add(dep)
    #     db.session.commit()
    # except Exception as e:
    #     print("not!")
    #     raise e
