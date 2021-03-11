from faker import Faker
import random
from datetime import datetime
import numpy as np
from tqdm import tqdm
from aristoDB import *


def enter_tenders_to_db(Tenders,db,number_of_tenders_to_add):
    fake = Faker()
    tenders_committee_Type_lst = ['רכישות', 'תקשוב', 'יועצים']
    procedure_type_lst = ['מכרז פומבי', 'תיחור סגור', 'פנייה פומבית', 'RFI', 'מכרז חשכ"ל', 'הצעת מחיר']
    department_lst = ['רווחה', 'מערכות מידע', 'לוגיסטיקה', 'לשכה משפטית ']
    cont_users = ['צחי יעקב', 'עופר שווקי', 'יהל ישראל', 'יגאל בלפור', 'משה כהן', 'אבי סלומון', 'שחר סינואני',
                  'ליאורה קחטן', 'שרונה בן שיטרית', 'ספיר כלפון', 'סמי גריידי', 'אפרת מצליח', 'אדוה הלוי',
                  'גורם מטעם היחידה', 'עוזי נעים', 'נטע ראובני', 'אלי דווידי', "טלי צ'רני", 'לבנת כהן', 'מיכל שפירא',
                  'יוני קראוני', 'מיסא זועבי', 'דניאלה יפת', 'נועה רוזנפלד', 'קרן נועם', 'יהודה כהן', 'הילה שלום',
                  'לימור ניזרי', 'יהונתן קוליץ', 'מירב כהן', 'דליה בנימין', 'אבי סולומון', 'מנשה מלול', 'ירון זוהר',
                  'ליבנת כהן']
    subjects_lst = ['מתן שירותי הובלה וסבלות', 'עו"ד מתחום דיני העבודה', 'הדר דפנה מזנונים', 'מכרז לשדרוג תשתיות חשמל',
                    'התאמות בגין לקויות למידה', 'שיפוץ בית הדין השרעי', "אחסון מטלטלין חלק ב'", 'שירותי שמאות רכב',
                    'מכרז שמאות לציוד שנתפס', 'שמאות חפצי אומנות', 'מכירת חפצי אומנות וזהב.', 'ימי גיבוש 2020',
                    'לינות קאדים', 'מכרז הדפסות', 'מכרז לרכישת מוצרים AEM', 'מכרז שליחויות', 'מכרז תחזוקה',
                    'מרכז קלט נתונים רשל"ה', 'מתח נמוך', 'פטנטים חיפוש ידע', 'צילום מסמכים', 'צילום מסמכים', 'ט"ו בשבט',
                    'שימור ידע', 'שירותי בינוי תשתיות', 'תווי שי', 'מתן שירותי ביקורת פנים', 'מכרז בנקים',
                    'לסניגוריה הציבורית"', 'חדר כושר לבניין החדש', 'מזנון בשרי', 'מזנון חלבי', 'ניקיון בניין ראשי',
                    'ריהוט וציוד נייד', 'ציוד חשמלי למטבחונים', 'צמחיה בתוך המבנה', 'תמונות ואמצעים אסתטיים',
                    'יועץ ארגונומי', 'מולטימדיה - השלמת ציוד', 'עבודות בינוי ושיפוץ', 'צלונים']
    for i in range(number_of_tenders_to_add):
        protocol = "".join(random.choices([str(i) for i in range(0, 10)], k=8))
        comm = random.choice(tenders_committee_Type_lst)
        proc = random.choice(procedure_type_lst)
        subject = random.choice(subjects_lst)
        depar = random.choice(department_lst)
        start_date = fake.past_date()
        finish_date = fake.future_date()
        cont = random.choice([i for i in range(1,50)])
        manager = random.choice(cont_users)
        tender = Tenders(protocol, comm, proc, subject, depar, start_date, finish_date, cont, manager)
        try:
            db.session.add(tender)
            db.session.commit()
            print('tender added succussfully')
        except Exception as e:
            print(e)
            print('cannot add tender')
            break
    return



def datetime_to_str(date):
    return datetime.strftime(date,"%d/%m/%Y")

def str_to_datetime(string):
    return datetime.strptime(string,'%Y-%d-%m')

def return_values(User,Tender,filter_by=None,order_by=None):
    if filter_by is not None:
        tenders = Tender.query.filter_by(tid=filter_by).first()
    elif order_by is not None:
        tender = Tender.query.oreder_by(f"{order_by} desc")
    else:
        tenders = Tender.query.all()
    days = [(t.finish_date - datetime.now()).days for t in tenders]
    values = []
    for i,tender in enumerate(tenders):
        tender.start_date = datetime_to_str(tender.start_date)
        tender.finish_date = datetime_to_str(tender.finish_date)
        # tender_contact_guy = User.query.join(Tender).filter_by()
        # print(tender_contact_guy)
        # con_guy_name = tender_contact_guy.first_name + ' ' + tender_contact_guy.last_name
        # print(con_guy_name)
        values.append((tender.protocol_number,tender.tenders_committee_Type,
                       tender.procedure_type,tender.subject,tender.department,
                       tender.contact_user_from_department,tender.tender_manager,
                       tender.start_date,tender.finish_date,days[i],tender.tid))
    return values



def validate_email(mail):
    import re
    email_re = re.compile("^[\w\.\+\-]+\@[\w]+\.[a-z]{2,3}$")
    if len(email_re.findall(mail)) == 1:
        return True
    else:
        return False

def validate_password(password):
    import re
    pass_re = re.compile("^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$")
    if len(pass_re.findall(password)) == 1:
        return True
    else:
        return True


def enter_fake_users_to_db(number_of_users,db,Users):
    fake = Faker()
    for i in range(number_of_users):
        name = fake.name().split()
        f_name = name[0]
        l_name = name[1]
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


def enter_fake_tasks_to_db(Tender,Task,db,num):
    statuses = ['חסום','הושלם','בעבודה']
    fake = Faker()
    tenders = Tender.query.all()
    for i in range(num):
        tender_id = random.choice([i for i in range(1,len(tenders))])
        odt = fake.past_date()
        dead_line = fake.future_date()
        status = random.choice(statuses)
        subject = f"{random.choice(range(1,60))}כתיבת פרק מספר -"
        description = f"זהו תיאור המשימה"
        task = Task(tender_id=tender_id,odt=odt,deadline=dead_line,finish=None,status=status,subject=subject,description=description)
        # print(task.subject)
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
    for i in range(num):
        user = random.choice(users_id)
        task_id = random.choice(tasks_id)
        init_time = fake.date_time_this_month()
        description = f"זהו תיאור הפעולה בתוך המשימה"
        log = TaskLog(user,task_id,init_time,description)
        try:
            db.session.add(log)
            db.session.commit()
            print("log enter succ")
        except Exception as e:
            print("cannot enter user to db")
            print(e)
            pass


def enter_fake_task_noted(db,User,Task,TaskNote,num):
    fake = Faker()
    users = User.query.all()
    task = Task.query.all()
    users_id = [i for i in range(1,len(users))]
    tasks_id = [i for i in range(1,len(task))]
    for i in range(num):
        user = random.choice(users_id)
        task_id = random.choice(tasks_id)
        init_time = fake.date_time_this_month()
        description = f"זוהי הערה"
        note = TaskNote(user,init_time,task_id,description)
        try:
            db.session.add(note)
            db.session.commit()
            print("log enter succ")
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
    enter_fake_tasks_to_db(Tender,Task,db,12*num)
    enter_fake_task_logs(db,User,Task,TaskLog,18*num)
    enter_fake_task_noted(db,User,Task,TaskNote,18*num)
    enter_fake_user_in_task(db,User,Task,UserInTask,num*6)



def function_for_sorting(request,Tender,db):
    pass
