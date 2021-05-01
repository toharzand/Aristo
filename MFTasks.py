from EmailHandler import *
import time
try:
    from models import *
except Exception as e:
    print("couldn't import aristoDB")
from datetime import datetime
from engine2_0 import *


class MFTask:
    def __init__(self):
        pass

    def process(self, engine=None):
        print(f"process of {self} wasn't yet overridden")
        pass


class MFResponse:
    def __init__(self, task_id):
        self.data = None
        self.is_complete_att = False
        self.__creator_id = task_id

    def get_data_once(self):
        if self.__creator_id in get_futures().keys():
            get_futures().pop(self.__creator_id)
        return self.data

    def is_complete(self) -> bool:
        if get_futures()[self.__creator_id] is not self:
            me = get_futures()[self.__creator_id]
            self.data = me.data
            self.is_complete_att = me.is_complete_att
        return self.is_complete_att

    def set_data(self, data):
        self.data = data

    def complete(self):
        self.is_complete_att = True

    def wait_for_completion(self):
        while True:  # replace with engine termination condition
            cond = Engine.get_instance().get_response_condition()
            with cond:
                if not self.is_complete():
                    cond.wait()
                if self.is_complete():
                    break
        if self.is_complete():
            return self.data


    def __repr__(self):
        return "response of task - " + self.__creator_id
        self.done = True


class DeleteTenderDependencies(MFTask):

    '''
        @Name: DeleteTenderDependencies
        @Parameters:
                    Abstract MFTask object
                    tid: tender id to delete
        @Do:
            get the deleted tender and delete all dependencies (task,tasd notes and task logs)
        @Return:
                None
    '''
    def __init__(self, tid):
        super().__init__()
        self.tid = tid

    def process(self, engine=None):
        print("here - in the engine. starts to delete items")
        # delete related tasks
        for task in Task.query.filter_by(tender_id=self.tid).all():

            task_id = task.task_id

            for task_note in TaskNote.query.filter_by(task_id=task_id).all():
                try:
                    print("start deleting task notes")
                    db.session.delete(task_note)
                    db.session.commit()
                    print("succuusfully delete task notes")
                except Exception as e:
                    db.session.rollback()

            for task_log in TaskLog.query.filter_by(task_id=task_id).all():
                try:
                    db.session.delete(task_log)
                    db.session.commit()
                    print("succuusfully delete task logs")
                except:
                    db.session.rollback()

            for user_in_task in UserInTask.query.filter_by(task_id=task_id).all():
                try:
                    db.session.delete(user_in_task)
                    db.session.commit()
                    print("succuusfully delete user_in_task")
                except:
                    db.session.rollback()

            try:
                db.session.delete(task)
                db.session.commit()
                print("task deleted")
            except Exception as e:
                db.session.rollback()
                print(e)


class addNotificationTender(MFTask):
    def __init__(self,tender,subject,user_id,type):
        super().__init__()
        self.tender = tender
        self.subject = subject
        self.user_id = user_id
        self.type = type
        self.created_time = datetime.now()

    def process(self, engine=None):
        try:
            notification = Notification(user_id=self.user_id,status=False,subject=self.subject,type=self.type,created_time=self.created_time)
            db.session.add(notification)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(e)
        conn = get_my_sql_connection()
        cursor = conn.cursor()
        query = """select nid
                    from notifications
                    order by nid desc
                    limit 1;
                """
        cursor.execute(query)
        nid = cursor.fetchone()[0]
        print(nid)
        notification_tender = NotificationInTender(nid,self.tender)
        try:
            db.session.add(notification_tender)
            db.session.commit()
        except Exception as e:
            print(e)
            db.session.rollback()

class addNotificationTask(MFTask):
    def __init__(self,task,subject,user_id,type):
        super().__init__()
        self.task = task
        self.subject = subject
        self.user_id = user_id
        self.type = type
        self.created_time = datetime.now()

    def process(self, engine=None):
        print("adding new task notification")
        try:
            notification = Notification(user_id=self.user_id,status=False,subject=self.subject,type=self.type,created_time=self.created_time)
            db.session.add(notification)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
        conn = get_my_sql_connection()
        cursor = conn.cursor()
        query = """select nid
                    from notifications
                    order by nid desc
                    limit 1;
                """
        cursor.execute(query)
        nid = cursor.fetchone()
        notification_task = NotificationInTask(nid[0],self.task)
        try:
            db.session.add(notification_task)
            db.session.commit()
        except Exception as e:
            print(e)
            db.session.rollback()


class addUserToTask(MFTask):
    def __init__(self,user_id,task_id,type):
        super().__init__()
        self.user_id = user_id
        self.task_id = task_id
        self.type = type
        self.created_time = datetime.now()

    def process(self, engine=None):
        try:
            print("raise notification")
            db.session.add(Notification(self.user_id,0,"הוסיפו אותך למשימה",self.type,created_time=self.created_time))
            db.session.commit()
        except:
            db.session.rollback()
        try:
            nid = Notification.query.order_by(Notification.nid.desc()).first()
            print(nid)
            db.session.add(NotificationInTask(nid.nid,self.task_id))
            db.session.commit()
            print("new task notification added")
        except Exception as e:
            db.session.rollback()
            print("cannot enter task notification")
            print(e)




class addNotificationsChat(MFTask):
    def __init__(self,task_id):
        super().__init__()
        self.task_id = task_id
        self.type = "משימה"
        self.created_time = datetime.now()

    def process(self, engine=None):
        try:
            print(f"raise notification - someone send massage in chat - task number {self.task_id}")
            for user_in_task in UserInTask.query.filter_by(task_id=self.task_id):
                db.session.add(Notification(user_in_task.user_id,0,"יש הודעה חדשה בצ'אט",self.type,self.created_time))
                db.session.commit()
                # print("commited - new chat notification")
                nid = Notification.query.order_by(Notification.nid.desc()).first()
                db.session.add(NotificationInTask(nid.nid,task_id=self.task_id))
                db.session.commit()
            print("data commited succssfully")
        except Exception as e:
            db.session.rollback()
            print("session rolled back! - cannot enter notifications")
            print(e)
            raise e



class PushNotificationsToUser(MFTask):
    def __init__(self,user_id):
        super().__init__()
        self.user_id = user_id



class DemoTask(MFTask):
    def process(self, engine=None):
        print(f"{self} processing")
        time.sleep(4)

    def __repr__(self):
        return "DemoTask"

class HeartBeat(MFTask):
    '''
        @Name: HeartBeat
        @Parameters:
                    Abstract MFTask object
        @Do:
            check every 10 seconds if the main site is still running. this called the heartbeat of our system.
            if the main site crashes, then the heartbeat will detect it, and do what needed to load back asap.
             - restore the data from database.
             - read the logs, redo transaction that committed and undo transaction that hasn't.
             - load once again the website using the updated data from previous steps.
        @Return:
                fully functional updated site.
    '''
    def process(self ,engine,is_main_running):
        if is_main_running:
            print("<heartbeat>")
            time.sleep(1)
        else:
            print("main site fail - rollback and call backup! hurry, the whole world is upon your shoulders.")
            pass



class DailyTask(MFTask):
    def __init__(self, time_stamp):
        self.all_users_messages = {}
        self.time_stamp = time_stamp

    def process(self, engine=None):
        print(f"{self} processing")
        self.send_all_managers_daily_report()


    def send_all_managers_daily_report(self):
        pass
    # for manager in all tenders do:
    #       for each tender this one managing:
    #           data_string = f"{tender.name, protocol number, subject} you managing:\n"
    #           dict_counters : {
    #               task_changed_status : 0,
    #               on_going_tasks: {task_name: task status calculated from its deadline},
    #               total_inside_task_activity:{task_name: task activity}
    #           }
    #           for each task in a tender:
    #               for each log in TaskLog where self.time_stamp-24 <= log.init_time < self.time_stamp:
    #                   u_a_sa_t = log.split(" ")  # user, action, second action, target
    #                   if a == "changed":
    #

    def __repr__(self):
        return "DailyTask"

class SendEmail(MFTask):
    def __init__(self, receiver ,content, subject="Aristo Updates"):
        super().__init__()
        self.receiver = receiver
        self.content = content
        self.subject = subject

    def process(self, engine=None):
        count_try = 1
        is_trying = True
        while is_trying:
            try:
                sender = EmailSender(self.receiver)
                sender.send_email(self.content, self.subject)
                is_trying = False
            except Exception as e:
                count_try += 1
                if (count_try-1) % 10 == 0:
                    print(e)
                    print(f"failed to send email {count_try - 1} times!")
                time.sleep(10)




class AddUserTask(MFTask):
    def __init__(self, first_name, last_name, email, password):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password

    def process(self, engine=None):
        db = get_db()
        success = True
        try:
            orm_user = User(self.first_name, self.last_name, self.email, self.password)
            db.session.add(orm_user)
            db.session.commit()
        except Exception as e:
            success = False
            print(e)
            get_db().session.rollback()
            print("user adding denied", print(self))
        if success:
            cont = f"""
            שלום {self.first_name, self.last_name}!
            הרשמתך במערכת אריסטו נקלטה בהצלחה!
            כעת תוכל להשתמש במשתמש שלך בכל עת
            שם משתמש: {self.email}
            סיסמה: {self.password}
            """
        else:
            cont = """
            שלום
            הרשמתך עבור אימייל זה לא נקלטה במערכת
            אנא, בצע הרשמה חוזרת עד לקבלת הודעת אישור

            במידה והנך נתקל בהודעה זו בשנית,
            אנא צור קשר עם המערכת באמצעות השבה לכתובת מייל זו
            תודה
            צוות אריסטו
            """
        engine.add_task(SendEmail(self.email, cont))


class CreateTenderFromTemplate(MFTask):
    def __init__(self, template_id):
        self.template_id = template_id
        self.con = get_my_sql_connection().cursor()
        self.db = get_db()

    def create_template_from_tender_BFS(self, template_tender_id, real_tender_id, openning_date):
        graph = {}  # {task_template_id : number (0=grey, 1=black)}

        q = []

        lst_of_first_tasks_of_tender = self.con.excecute("""
            SELECT dependant
            FROM
            TaskDependenciesTemplate
            WHERE
            tender_id = ? and dependant = null
            """, template_tender_id)  # return list of all beginner tasks for the tender template
        for row in lst_of_first_tasks_of_tender:
            real_depender_id, real_depender_deadline, insertion_succeeded = self.create_real_task_from_template_task(real_tender_id, row[0], openning_date)  # teder_id , task_template
            q.append((row[0], real_depender_id, real_depender_deadline))
            graph[row[0]] = 0  # painting the vertex

        while len(q) != 0:
            template_dependee_id, real_dependee_id, real_dependee_deadline = q.pop(0)  # getting (task template id , task real id, task deadline)
            lst_of_template_dependants = self.con.excecute("""
            SELECT dependant
            FROM
            TaskDependenciesTemplate
            WHERE
            depandee = ?
            """, template_dependee_id)  # = [(depender1_id), (depender1_id), (depender2_id)...])
            for row in lst_of_template_dependants:
                if row[0] in graph.keys():
                    continue
                real_depender_id, real_depender_deadline, insertion_succeeded = self.create_real_task_from_template_task(real_tender_id, row[0], real_dependee_deadline)
                self.add_blocked_to_blocking(real_dependee_id, real_depender_id)
                q.append((row[0], real_depender_id, real_depender_deadline))
                graph[row[0]] = 1
            graph[template_dependee_id] = 1

    def process(self):
        connection = get_my_sql_connection()
        curser = connection.curser()
        curser.excecute("...")

    def create_real_task_from_template_task(self, real_tender_id, template_task_id, openning_date):
        task_attributes = self.con.execute("""
        SELECT *
        FROM TaskTemplate
        WHERE tid = ?
        """, template_task_id)
        attributes = {
            "tender_id": real_tender_id,
            "odt": openning_date,
            "deadline": self.get_date_from_timedelta(openning_date, task_attributes[0][3]),
            "finish": None,
            "status": task_attributes[0][0],
            "subject": task_attributes[0][1],
            "description": task_attributes[0][2],
        }
        try:
            task = Task(**attributes)  # create real task from the template output
            db.session.add(task)
            db.session.commit()
            success = True
        except Exception as e:
            success = False
            print(e)
            get_db().session.rollback()
            print("task adding denied", print(f"real_tender_id {real_tender_id} | template_task_id {template_task_id}"))
        return task.task_id, attributes["deadline"], success


    def add_blocked_to_blocking(self, real_dependee_id, real_depender_id):
        try:
            task_dependency = TaskDependency(real_dependee_id, real_depender_id)
            self.db.session.add(task_dependency)
            db.session.commit()
        except Exception as e:
            print(e)
            get_db().session.rooback()
            print(f"task dependancy insertion denied - depender {real_depender_id} | dependee {real_dependee_id}")


    def get_date_from_timedelta(self, openning_date, days_delta):
        """
        :param openning_date: the date a task will be created
        :param days_delta: the amount of days that a task should be taken to handle
        :return: datetime obj with the right deadline for a task
        """
        pass  # todo



class GetTendersPageRespons(MFTask):
    def __init__(self,request,db):
        self.request = request
        self.db = db

    def process(self, engine=None):
        return self.request.form['user']