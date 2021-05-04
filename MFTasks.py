from EmailHandler import *
import time
try:
    from models import *
except Exception as e:
    print("couldn't import aristoDB")
from datetime import datetime
import datetime
import engine2_0


def flatten(lst, i=0):
    if i >= len(lst):
        return lst
    if isinstance(lst[i], tuple) or isinstance(lst[i], list):
        if i != len(lst) - 1:
            lst = lst[:i] + list(flatten(lst[i], 0)) + lst[i+1:]
        else:
            lst = lst[:i] + list(flatten(lst[i], 0))
    return flatten(lst, i+1)


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
        self.error = False
        self.__creator_id = task_id


    def get_data_once(self):
        if self.__creator_id in engine2_0.get_futures().keys():
            engine2_0.get_futures().pop(self.__creator_id)
        return self.data

    def is_complete(self) -> bool:
        if engine2_0.get_futures()[self.__creator_id] is not self:
            me = engine2_0.get_futures()[self.__creator_id]
            self.data = me.data
            self.is_complete_att = me.is_complete_att
        return self.is_complete_att

    def set_data(self, data):
        if isinstance(data, Exception):
            self.error = True
        self.data = data

    def complete(self):
        self.is_complete_att = True

    def wait_for_completion(self):
        while True:  # replace with engine termination condition
            cond = engine2_0.Engine.get_instance().get_response_condition()
            with cond:
                if not self.is_complete():
                    cond.wait()
                if self.is_complete():
                    break
        if self.is_complete():
            return self.data

    def error_occurred(self):
        return not self.error


    def __repr__(self):
        return "response of task - " + self.__creator_id


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


class UpdateTaskStatus(MFTask):
    def __init__(self,task_id,user_id,status):
        super().__init__()
        self.task_id = task_id
        self.user = User.query.filter_by(id=user_id).first()
        self.status = status
        self.init_time = datetime.datetime.now()

    def should_advance(self, blocked_id):
        #  check if task should advance from 'blocked' to 'open' by checking if all it blockers are done
        lst_of_task_blockers = get_my_sql_connection().cursor().execute(f"""
                        SELECT td.blocking, t.status
                        FROM tasksdependencies as td INNER JOIN Tasks as t 
                        ON td.blocked = t.task_id
                        WHERE blocked = {blocked_id} and blocking != {self.task_id}
                    """)
        for blocker_id, blocker_status in lst_of_task_blockers:
            if blocker_status == "הושלם":
                continue
            else:
                return False
        return True

    def update_dependencies(self):
        conn = get_my_sql_connection()
        cursor = conn.cursor()
        lst_of_all_blocked = cursor.execute(f""" SELECT blocked
                    FROM tasksdependencies
                    WHERE blocking = {self.task_id}
                    """)
        for blocked_id in flatten(lst_of_all_blocked):
            if self.should_advance(blocked_id):
                current_task = Task.query.filter_by(task_id=blocked_id).first()
                current_task.status = "פתוח"
                name = f"{self.user.first_name} {self.user.last_name}"
                description = f"{name} השלים את המשימה החוסמת {self.task_id} ובכך שינה את סטטוס המשימה הנוכחית ל-פתוח"
                changeStatusLog = TaskLog(self.user.id, blocked_id, self.init_time, description)
                db.session.add(changeStatusLog)

    def process(self, engine=None):
        try:
            print("start process")
            current_task = Task.query.filter_by(task_id=self.task_id).first()
            current_task.status = self.status
            name = f"{self.user.first_name} {self.user.last_name}"
            description = f"{name} שינה את סטטוס המשימה" + " " + f"ל-{self.status}"
            print(description)
            if self.status == "הושלם":
                try:
                    # self.update_dependencies()
                    pass
                except Exception as e:
                    print(e)
                    pass
            changeStatusLog = TaskLog(self.user.id,self.task_id,self.init_time,description)
            db.session.add(changeStatusLog)
            db.session.commit()
            print("status changed - log committed")
        except Exception as e:
            db.session.rollback()
            print("there was problem with logging the status change")
            print(e)


class LogNewTask(MFTask):
    def __init__(self,user_id):
        super().__init__()
        self.user = User.query.filter_by(id=user_id).first()
        self.init_time = datetime.now()

    def process(self, engine=None):
        print("start add new task procerss")
        name = f"{self.user.first_name} {self.user.last_name}"
        description =  f"{name} הוסיף משימה חדשה " + " " + f"{self.init_time.hour}:{self.init_time.minute} {self.init_time.date()} "
        print(description)
        try:
            conn = get_my_sql_connection()
            cursor = conn.cursor()
            query = f"""select task_id from tasks
                        order by task_id desc
                        limit 1;"""
            cursor.execute(query)
            task_id = cursor.fetchone()[0]
            print(task_id)
        except Exception as e:
            print(f"not able to fetch because: {e}")
        createTaskLog = TaskLog(self.user.id,task_id,self.init_time,description)
        try:
            db.session.add(createTaskLog)
            db.session.commit()
            print("task registered - log commited")
        except Exception as e:
            db.session.rollback()
            print("there was problem with logging the task registered")
            raise e

class AddVisitorNote(MFTask):
    """docstring for AddVisitorNote"""
    def __init__(self, name,email,msg):
        super().__init__()
        self.name = name
        self.email = email
        self.msg = msg
        self.time_created = datetime.now()

    def process(self,engine=None):
        visitor_note = ContactNote(self.email,self.name,self.msg,self.time_created)
        try:
            db.session.add(visitor_note)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(e)
        

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

# --- replaced ---
# class createTaskDependency(MFTask):
#
#     def __init__(self,depender_task_id,task_id):
#         super().__init__()
#         self.depender_task_id = depender_task_id
#         self.task_id = task_id
#
#     def process(self, engine=None):
#         #create the dependency
#         try:
#             dependency = TaskDependency(blocking=self.depender_task_id,blocked=self.task_id)
#             db.session.add(dependency)
#             db.session.commit()
#             print(f"db created - between depender - {self.depender_task_id} and dependee - {self.task_id}")
#         except Exception as e:
#             print(e)
#             print("rolled back due to duplication")
#             db.session.rollback()





class DailyTask(MFTask):
    def process(self, engine=None):
        print(f"{self} processing")

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


class CreateTaskDependency:
    def __init__(self, blocking, blocked):
        self.blocked_id = blocked
        self.blocking_id = blocking
        self.con = get_my_sql_connection().cursor()

    def check_for_circle(self, current):
        " searching for the blocking's id in all tasks that is blocked by it using recursion"
        if current == self.blocking_id:
            raise Exception(f"""
                circle was found, couldn't complete the process:
                {self.blocking} -> {self.blocked_id} -> ... {current} -> {self.blocking_id}""")
        current_all_children = flatten(self.con.execute(f"""
            SELECT blocked
            FROM TasksDependencies
            WHERE blocking = {current}
            """))
        for child in current_all_children:
            self.check_for_circle(child)


    def process(self):
        try:
            self.check_for_circle(self.blocked_id)  # an exception will be raised if a circle is found
        except Exception as e:
            print(e)
            raise e
        task_dependency = TaskDependency(blocked=self.blocked_id, blocking=self.blocking_id)
        try:
            db.session.add(task_dependency)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e



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
    def __init__(self, template_id, contact_user, subject):
        self.template_id = template_id
        self.opening_date = datetime.now()
        self.contact_user = contact_user
        self.subject = subject
        self.con = get_my_sql_connection().cursor()
        self.db = get_db()

    def create_template_from_tender_BFS(self, real_tender_id):
        graph = {}  # {task_template_id : {color:(0=white, 1=grey, 2=black), task_real_id:()}}

        q = []

        lst_of_first_tasks_of_tender = self.con.excecute(f"""
            SELECT dependee_id
            FROM TasksDependenciesTemplate
            WHERE tender_id = {self.template_tender_id} and depender_id = null
            """)  # return list of all beginner tasks for the tender template
        for row in lst_of_first_tasks_of_tender:
            real_depender_id, real_depender_deadline, insertion_succeeded = self.create_real_task_from_template_task(real_tender_id, row[0], self.opening_date)  # teder_id , task_template
            q.append((row[0], real_depender_id, real_depender_deadline))
            graph[row[0]] = {"color":1, "real_task_id":real_depender_id}  # painting the vertex

        while len(q) != 0:
            template_depender_id, real_depender_id, real_depender_deadline = q.pop(0)  # getting (task template id , task real id, task deadline)
            lst_of_template_dependees = self.con.excecute(f"""
            SELECT dependee_id
            FROM TasksDependenciesTemplate
            WHERE depender_id = {template_depender_id}
            """)  # = [(dependee1_id), (dependee1_id), (depender2_id)...])
            for row in lst_of_template_dependees:
                if row[0] in graph.keys():
                    if graph[row[0]]["color"] == 1:
                        #  if color == 1 then we should only
                        #  update its depender but not create it
                        self.add_blocked_to_blocking(graph[row[0]]["real_task_id"], real_depender_id)
                        continue
                    if graph[row[0]]["color"] == 2:
                        raise Exception(f"an insolvable circle was found: {row[0]}, {template_depender_id}")
                        # continue
                real_dependee_id, real_dependee_deadline, insertion_succeeded = self.create_real_task_from_template_task(real_tender_id, row[0], real_depender_deadline)
                self.add_blocked_to_blocking(real_dependee_id, real_depender_id)
                q.append((row[0], real_dependee_id, real_dependee_deadline))
                graph[row[0]] = 1
            graph[template_depender_id] = 2

    def process(self):
        real_tender_id = self.create_real_tender_from_template()
        self.create_template_from_tender_BFS(real_tender_id)
        db.session.commit()

    def create_real_tender_from_template(self) -> str:
        "should return a real empty tender id (to fill later on with real tasks from template)"
        # todo - Itay
        pass

    def create_real_task_from_template_task(self, real_tender_id, template_task_id, opening_date):
        task_attributes = self.con.execute(f"""
        SELECT *
        FROM TasksTemplate
        WHERE task_id = {template_task_id}
        """)
        attributes = {
            "tender_id": real_tender_id,
            "odt": opening_date,
            "deadline": self.get_date_from_timedelta(opening_date, task_attributes[0][3]),
            "finish": None,
            "status": task_attributes[0][0],
            "subject": task_attributes[0][1],
            "description": task_attributes[0][2],
        }
        try:
            #  todo - validate attributes for the real task
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


    def get_date_from_timedelta(self, opening_date, days_delta):
        """
        :param opening_date: the date a task will be created
        :param days_delta: the amount of days that a task should be taken to handle
        :return: datetime obj with the right deadline for a task
        """
        return opening_date + datetime.timedelta(days_delta)


class GetTendersPageRespons(MFTask):
    def __init__(self,request,db):
        self.request = request
        self.db = db

    def process(self, engine=None):
        return self.request.form['user']