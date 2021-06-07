from EmailHandler import *
import time
# try:
import models
# from models import db
# except Exception as e:
#     print(e)
from datetime import datetime,timedelta
import engine2_0
from flask_login import current_user
# import models

def flatten(lst, i=0):
    if lst is None:
        return []
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
            self.error = me.error
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
        self.wait_for_completion()
        return self.error


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
        for task in models.Task.query.filter_by(tender_id=self.tid).all():

            task_id = task.task_id

            for task_note in models.TaskNote.query.filter_by(task_id=task_id).all():
                try:
                    print("start deleting task notes")
                    models.db.session.delete(task_note)
                    models.db.session.commit()
                    print("succuusfully delete task notes")
                except Exception as e:
                    models.db.session.rollback()

            for task_log in models.TaskLog.query.filter_by(task_id=task_id).all():
                try:
                    models.db.session.delete(task_log)
                    models.db.session.commit()
                    print("succuusfully delete task logs")
                except:
                    models.db.session.rollback()

            for user_in_task in models.UserInTask.query.filter_by(task_id=task_id).all():
                try:
                    models.db.session.delete(user_in_task)
                    models.db.session.commit()
                    print("succuusfully delete user_in_task")
                except:
                    models.db.session.rollback()

            try:
                models.db.session.delete(task)
                models.db.session.commit()
                print("task deleted")
            except Exception as e:
                models.db.session.rollback()
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
            notification = models.Notification(user_id=self.user_id,status=False,subject=self.subject,type=self.type,created_time=self.created_time)
            models.db.session.add(notification)
            models.db.session.commit()
        except Exception as e:
            models.db.session.rollback()
            print(e)
        conn = models.get_my_sql_connection()
        cursor = conn.cursor()
        query = """select nid
                    from notifications
                    order by nid desc
                    limit 1;
                """
        cursor.execute(query)
        nid = cursor.fetchone()[0]
        print(nid)
        notification_tender = models.NotificationInTender(nid,self.tender)
        try:
            models.db.session.add(notification_tender)
            models.db.session.commit()
        except Exception as e:
            print(e)
            models.db.session.rollback()

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
            notification = models.Notification(user_id=self.user_id,status=False,subject=self.subject,type=self.type,created_time=self.created_time)
            models.db.session.add(notification)
            models.db.session.commit()
        except Exception as e:
            models.db.session.rollback()
            raise e
        conn = models.get_my_sql_connection()
        cursor = conn.cursor()
        query = """select nid
                    from notifications
                    order by nid desc
                    limit 1;
                """
        cursor.execute(query)
        nid = cursor.fetchone()
        notification_task = models.NotificationInTask(nid[0],self.task)
        try:
            models.db.session.add(notification_task)
            models.db.session.commit()
        except Exception as e:
            print(e)
            models.db.session.rollback()


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
            models.db.session.add(models.Notification(self.user_id,0,"הוסיפו אותך למשימה",self.type,created_time=self.created_time))
            models.db.session.commit()
        except:
            models.db.session.rollback()
        try:
            nid = models.Notification.query.order_by(models.Notification.nid.desc()).first()
            print(nid)
            models.db.session.add(models.NotificationInTask(nid.nid,self.task_id))
            models.db.session.commit()
            print("new task notification added")
        except Exception as e:
            models.db.session.rollback()
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
            for user_in_task in models.UserInTask.query.filter_by(task_id=self.task_id):
                models.db.session.add(models.Notification(user_in_task.user_id,0,"יש הודעה חדשה בצ'אט",self.type,self.created_time))
                models.db.session.commit()
                # print("commited - new chat notification")
                nid = models.Notification.query.order_by(models.Notification.nid.desc()).first()
                models.db.session.add(models.NotificationInTask(nid.nid,task_id=self.task_id))
                models.db.session.commit()
            print("data commited succssfully")
        except Exception as e:
            models.db.session.rollback()
            print("session rolled back! - cannot enter notifications")
            print(e)
            raise e


class UpdateTaskStatus(MFTask):
    def __init__(self,task_id,user_id,status):
        super().__init__()
        self.task_id = task_id
        self.user = models.User.query.filter_by(id=user_id).first()
        self.status = status
        self.init_time = datetime.now()
        self.cursor = None

    def should_advance(self, blocked_id):
        #  check if task should advance from 'blocked' to 'open' by checking if all it blockers are done
        self.cursor.execute(f"""
                        SELECT td.blocking, t.status
                        FROM tasksdependencies as td INNER JOIN Tasks as t 
                        ON td.blocked = t.task_id
                        WHERE blocked = {blocked_id} and blocking != {self.task_id}
                    """)
        lst_of_task_blockers = self.cursor.fetchall()
        for blocker_id, blocker_status in lst_of_task_blockers:
            if blocker_status != "הושלם":
                return False, blocker_id
        return True, None

    def update_dependencies(self):
        self.cursor.execute(f""" SELECT blocked
                    FROM tasksdependencies
                    WHERE blocking = {self.task_id}
                    """)
        lst_of_all_blocked = self.cursor.fetchall()
        for blocked_id in flatten(lst_of_all_blocked):
            if self.should_advance(blocked_id)[0]:
                current_task = models.Task.query.filter_by(task_id=blocked_id).first()
                name = f"{self.user.first_name} {self.user.last_name}"
                if current_task.is_milestone:
                    current_task.status = "פתוח"
                    models.db.session.commit()
                    update_milestone = UpdateTaskStatus(current_task.task_id,self.user.id,"הושלם")
                    update_milestone.process()
                    description = f"{name} השלים את המשימה {self.task_id} ובכך השלים את אבן הדרך"
                else:
                    current_task.status = "פתוח"
                    description = f"{name} השלים את המשימה החוסמת {self.task_id} ובכך שינה את סטטוס המשימה הנוכחית ל-פתוח"
                changeStatusLog = models.TaskLog(self.user.id, blocked_id, self.init_time, description)
                models.db.session.add(changeStatusLog)

    def process(self, engine=None):
        print("start process")
        conn = models.get_my_sql_connection()
        self.cursor = conn.cursor()
        current_task = models.Task.query.filter_by(task_id=self.task_id).first()
        # if current_task.status == "חסום":
        #     raise Exception(f"cannot advanced this task because it blocked by other task")
        current_task.status = self.status
        name = f"{self.user.first_name} {self.user.last_name}"
        description = f"{name} שינה את סטטוס המשימה" + " " + f"ל-{self.status}"
        print(description)
        if self.status == "הושלם":
            self.update_dependencies()
        changeStatusLog = models.TaskLog(self.user.id,self.task_id,self.init_time,description)
        try:
            models.db.session.add(changeStatusLog)
            models.db.session.commit()
            print("status changed - log committed")
        except Exception as e:
            models.db.session.rollback()
            print("there was problem with logging the status change")
            print(e)


class LogNewTask(MFTask):
    def __init__(self,user_id):
        super().__init__()
        self.user = models.User.query.filter_by(id=user_id).first()
        self.init_time = datetime.now()

    def process(self, engine=None):
        print("start add new task procerss")
        name = f"{self.user.first_name} {self.user.last_name}"
        description =  f"{name} הוסיף משימה חדשה " + " " + f"{self.init_time.hour}:{self.init_time.minute} {self.init_time.date()} "
        print(description)
        try:
            conn = models.get_my_sql_connection()
            cursor = conn.cursor()
            query = f"""select task_id from tasks
                        order by task_id desc
                        limit 1;"""
            cursor.execute(query)
            task_id = cursor.fetchone()[0]
            print(task_id)
        except Exception as e:
            print(f"not able to fetch because: {e}")
        createTaskLog = models.TaskLog(self.user.id,task_id,self.init_time,description)
        try:
            models.db.session.add(createTaskLog)
            models.db.session.commit()
            print("task registered - log commited")
        except Exception as e:
            models.db.session.rollback()
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
            models.db.session.add(visitor_note)
            models.db.session.commit()
        except Exception as e:
            models.db.session.rollback()
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
# class CreateTaskDependency(MFTask):
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
#             models.db.session.add(dependency)
#             models.db.session.commit()
#             print(f"db created - between depender - {self.depender_task_id} and dependee - {self.task_id}")
#         except Exception as e:
#             print(e)
#             print("rolled back due to duplication")
#             models.db.session.rollback()





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
        # self.con = models.get_my_sql_connection()
        self.cursor = None
        self.number_of_iterations = models.TaskDependency.query.count()
        self.g = {}

    def check_for_circle(self, current):
        # " searching for the blocking's id in all tasks that is blocked by it using recursion "
        self.number_of_iterations -= 1
        if self.number_of_iterations < 0:
            raise Exception("""
            cannot complete the process.
            probably due to a dependencies circe not related to the latest dependency inserted.""")
        current_all_children = flatten(self.cursor.execute(f"""
            SELECT blocked
            FROM TasksDependencies
            WHERE blocking = {current}
            """))
        for child in current_all_children:
            if child == self.blocking_id:
                raise Exception(f"""
                circle was found, couldn't complete the process:
                {self.blocking} -> {self.blocked_id} -> ... -> {child} -> {self.blocking_id}""")
            self.check_for_circle(child)

    def check_for_circle_DFS(self, current, concat):
        self.g[str(current)] = 1
        concat += " -> " + str(current)
        if current == self.blocking_id:
            return True, concat
        query = f"""SELECT blocked
                    FROM TasksDependencies
                    WHERE blocking = {current}"""
        self.cursor.execute(query)
        current_all_children = flatten(self.cursor.fetchall())
        print(f"current_all_children {current_all_children}")
        for child in current_all_children:
            str_child = str(child)
            if str_child not in self.g.keys():
                self.g[str_child] = 0
            if self.g[str_child] == 0:
                circle, concat = self.check_for_circle_DFS(child, concat)
                if circle:
                    return True, concat
            if self.g[str_child] == 1:
                return True, concat + " -> " + str_child
        self.g[current] = 2
        return False, concat

    def process(self):
        print("inside proccess of create task depend")
        con = models.get_my_sql_connection()
        self.cursor = con.cursor()
        # ----- option A: check for circle with DFS algorithm - safer and more informative but slightly slower -----
        conc = str(self.blocking_id)
        there_is_circle, info = self.check_for_circle_DFS(self.blocked_id, conc)
        if there_is_circle:
            raise Exception(f"""
            a circle found with the new insertion:
            {info}
            """)
        # # ----- option B: check for new circle assuming there isn't a circle already  -----
        # try:
        #     self.check_for_circle(self.blocked_id,cursor)  # an exception will be raised if a circle is found
        # except Exception as e:
        #     print(e)
        #     raise e
        print("no circle found - try to create taskDep obj")
        task_dependency = models.TaskDependency(blocked=self.blocked_id, blocking=self.blocking_id)
        print(task_dependency.blocked,task_dependency.blocking)
        try:
            print("trying to add to db dependencies")
            models.db.session.add(task_dependency)
            models.db.session.commit()
            print("tasks dependency comitted")
        except Exception as e:
            models.db.session.rollback()
            return f"תלות זו קיימת. אנא בחרו משימה אחרת"

        return f"dependency create successfully {self.blocking_id} -> {self.blocked_id}"

class AddUserToTender(MFTask):

    def __init__(self,tid,uid):
        super().__init__()
        self.tid = tid
        self.uid = uid

    def process(self, engine=None):
        user_in_tender = models.UserInTender(tender_id=self.tid, user_id=self.uid)
        try:
            print("start add user to tender")
            models.db.session.add(user_in_tender)
            models.db.session.commit()
            print("user register to tender succusfully")
        except Exception as e:
            models.db.session.rollback()
            print(e)

class AddUserTask(MFTask):
    def __init__(self, first_name, last_name, email, password):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password

    def process(self, engine=None):
        db = models.get_db()
        success = True
        try:
            orm_user = models.User(self.first_name, self.last_name, self.email, self.password)
            models.db.session.add(orm_user)
            models.db.session.commit()
        except Exception as e:
            success = False
            print(e)
            models.get_db().session.rollback()
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
    '''
        @Name : CreateTenderFromTemplate
        @Do: create new tender from template, including all the attached tasks that come as default in every tender.
        @ Param:
                template_id - tender template id.
                contact_user - the contact user from the department which responsible on the tender
                subject = the subject of the tender
                protocol: protocol number of the tender
    '''

    def __init__(self, template_id, contact_user, subject,protocol,finish_date, tender_manager):
        self.template_id = template_id
        self.opening_date = datetime.now().date()
        self.contact_user = contact_user
        self.tender_manager = tender_manager
        # self.contact_user = self.get_contact_id()
        self.subject = subject
        self.protocol = protocol
        self.finish_date = finish_date if finish_date != "" else datetime.now().date()
        print(f"the finish date got set to: {self.finish_date}")
        self.cur = None


    def get_contact_id(self):
        """
        @Do: extract the contact user from department id.
        :return: User object that match to the self.contact_user parameter.
        """
        n = self.contact_user.split(" ")
        print(n)
        return models.User.query.filter_by(first_name=n[0],last_name=n[1]).first().id

    def create_template_from_tender_BFS(self, real_tender_id):
        """
        @Do: fetch all the task templates from the database and create personal instance of them
                attached with the created tender.
        """

        graph = {}  # {task_template_id : {color:(0=white, 1=grey, 2=black), task_real_id:()}}

        q = []

        #  todo  - incorrect query! we should seek for dependee_id where depender_id = 0. we should add it to the db
        self.cur.execute(f"""
            SELECT dependee_id
            FROM TasksDependenciesTemplate
            WHERE tender_id = {self.template_id} and depender_id = 0
            """)  # return list of all beginner tasks for the tender template
        lst_of_first_tasks_of_tender = self.cur.fetchall()
        for row in lst_of_first_tasks_of_tender:
            real_depender_id, real_depender_deadline = self.create_real_task_from_template_task(real_tender_id, row[0], self.opening_date)  # tender_id , task_template
            q.append((row[0], real_depender_id, real_depender_deadline))
            graph[str(row[0])] = {"color":1, "real_task_id":real_depender_id}  # painting the vertex

        while len(q) != 0:
            template_depender_id, real_depender_id, real_depender_deadline = q.pop(0)  # getting (task template id , task real id, task deadline)
            self.update_deadline(real_depender_deadline)
            self.cur.execute(f"""
            SELECT distinct dependee_id
            FROM aristo.TasksDependenciesTemplate
            WHERE depender_id = {template_depender_id}
            """)  # = [(dependee1_id), (dependee2_id), (depender3_id)...])
            lst_of_template_dependees = self.cur.fetchall()
            for row in lst_of_template_dependees:
                if str(row[0]) in graph.keys():
                    if graph[str(row[0])]["color"] == 1:
                        #  if color == 1 then we should only
                        #  update its depender but not create it
                        self.add_blocked_to_blocking(graph[str(row[0])]["real_task_id"], real_depender_id)
                        continue
                    if graph[str(row[0])]["color"] == 2:
                        raise Exception(f"an insolvable circle was found: {row[0]}, {template_depender_id}")
                        # continue
                real_dependee_id, real_dependee_deadline = self.create_real_task_from_template_task(real_tender_id, row[0], real_depender_deadline)
                self.add_blocked_to_blocking(real_dependee_id, real_depender_id)
                q.append((row[0], real_dependee_id, real_dependee_deadline))
                graph[str(row[0])] = {"color": 1, "real_task_id": real_dependee_id}
            graph[str(template_depender_id)]["color"] = 2

    def process(self):
        try:
            conn = models.get_my_sql_connection()
            self.cur = conn.cursor()
            real_tender_id = self.create_real_tender_from_template()
            self.create_template_from_tender_BFS(real_tender_id)
            real_tender = models.Tender.query.filter_by(tid=real_tender_id).first()
            if real_tender.finish_date.date() == real_tender.start_date.date():
                print("finish is start")
                real_tender.finish_date = self.finish_date
            # possible to set finish date from template tasks!! to enable for now
            # models.Tender.query.filter_by(tid=real_tender_id).first().finish_date = self.finish_date
            models.db.session.commit()
            print("\ntender successfully created from template\n")
        except Exception as e:
            models.db.session.rollback()
            raise e

    def create_real_tender_from_template(self):
        "should return a real empty tender id (to fill later on with real tasks from template)"
        print("create_real_tender_from_template")
        tender = models.TenderTemplate.query.filter_by(tid=self.template_id).first()
        new_tender = models.Tender(self.protocol,tender.tenders_committee_Type,tender.procedure_type,
                            self.subject,department=tender.department,start_date=datetime.now(),finish_date=self.finish_date,
                            contact_user_from_department=self.contact_user,tender_manager=self.tender_manager)

        models.db.session.add(new_tender)
        models.db.session.commit()

        query = """select tid from tenders
                    order by tid desc
                    limit 1"""
        self.cur.execute(query)
        # print("got here 1")
        # print(self.cur.fetchone()[0])
        return self.cur.fetchone()[0]



    def create_real_task_from_template_task(self, real_tender_id, template_task_id, opening_date):
        self.cur.execute(f"""
        SELECT *
        FROM TasksTemplate
        WHERE task_id = {template_task_id}
        """)
        task_attributes = self.cur.fetchall()
        temp_task = models.TaskTemplate.query.filter_by(task_id = template_task_id).first()
        attributes = {
            "tender_id": real_tender_id,
            "odt": opening_date,
            "deadline": self.get_date_from_timedelta(opening_date, task_attributes[0][4]),
            "finish": None,
            "status": task_attributes[0][1],
            "subject": task_attributes[0][2],
            "description": task_attributes[0][3],
            "task_owner_id": self.contact_user,
            "is_milestone": temp_task.is_milestone
        }
        task = models.Task(**attributes)  # create real task from the template output
        models.db.session.add(task)
        models.db.session.commit()
        tid = models.Task.query.order_by(models.Task.task_id.desc()).first().task_id
        return tid, attributes["deadline"]


    def add_blocked_to_blocking(self, real_dependee_id, real_depender_id):
        task_dependency = models.TaskDependency(real_dependee_id, real_depender_id)
        models.db.session.add(task_dependency)
            # print(f"task dependancy insertion denied - depender {real_depender_id} | dependee {real_dependee_id}")
        # print(f"task_dependency added:  \nblocking - {task_dependency.blocking}\nblocked - {task_dependency.blocked}")

    def update_deadline(self, later_date):
        # print(later_date,"\t|\t", self.finish_date)
        if isinstance(self.finish_date, str):
            self.finish_date = datetime.strptime(self.finish_date, "%Y-%m-%d").date()
        if later_date > self.finish_date:
            self.finish_date = later_date

    def get_date_from_timedelta(self, opening_date, days_delta):
        """
        :param opening_date: the date a task will be created
        :param days_delta: the amount of days that a task should be taken to handle
        :return: datetime obj with the right deadline for a task
        """
        # print(f"opening date - {type(opening_date)} {opening_date}")
        # print(f"timedelta - {type(opening_date +timedelta(days_delta))} {opening_date +timedelta(days_delta)}")
        # print(f"check in get_date_from_timedelta: given open: {opening_date} \t|\t given delta: {days_delta}\n\t output: {opening_date + timedelta(days_delta)}")
        return opening_date + timedelta(days_delta)

class GetQueueOfMilestones(MFTask):
    def __init__(self, tender_id):
        self.tender_id = tender_id
        self.cursor = None
        self.g = {}
        self.result = []

    def DFS(self,current_id):
        self.g[str(current_id)] = 1
        query = f"""SELECT blocked
                            FROM TasksDependencies
                            WHERE blocking = {current_id}"""
        self.cursor.execute(query)
        current_all_children = flatten(self.cursor.fetchall())
        # print(f"current_all_children {current_all_children}")
        for child in current_all_children:
            str_child = str(child)
            if str_child not in self.g.keys():
                self.g[str_child] = 0
            if self.g[str_child] == 0:
                self.DFS(child)
        self.g[str(current_id)] = 2
        task, is_milestone = self.is_milestone(current_id)
        if is_milestone:
            self.result.append(task)
        return


    def topological_sort(self):
        query = f"""
        SELECT task_id
        FROM tasks
        WHERE tender_id = {self.tender_id}
        """
        conn = models.get_my_sql_connection()
        self.cursor = conn.cursor()
        self.cursor.execute(query)
        all_tasks = flatten(self.cursor.fetchall())
        for task_id in all_tasks:
            if str(task_id) not in self.g.keys():
                self.DFS(task_id)
        self.result.reverse()

    def is_milestone(self, task_id):
        task = models.Task.query.filter_by(task_id=task_id).first()
        if task.is_milestone:
            return task, True
        return None, False


    def process(self):
        self.topological_sort()
        return self.result

class GetTendersPageRespons(MFTask):
    def __init__(self,request,db):
        self.request = request
        self.db = db

    def process(self, engine=None):
        return self.request.form['user']

class addMileStone(MFTask):
    def __init__(self,cur_user):
        self.user = cur_user
        self.cursor = None

    def get_tenders(self):
        query = f"""SELECT distinct tender_id FROM aristo.usersintasks as u
                    inner join tasks t
                    on u.task_id=t.task_id
                    where user_id={current_user.id};"""
        tenders_for_user = models.Tender.query.filter_by(tender_manager=current_user.id).all()
        tenders_for_user += models.Tender.query.filter_by(contact_user_from_department=current_user.id).all()
        self.cursor.execute(query)
        res = [i[0] for i in self.cursor.fetchall()]
        my_lst = []

        for tender_id in res:
            my_lst.append(models.Tender.query.filter_by(tid=tender_id).first())

        my_lst += tenders_for_user
        return list(set(my_lst))


    def process(self, engine=None):
        conn = models.get_my_sql_connection()
        self.cursor = conn.cursor()
        tenders = self.get_tenders()
        milestones = []

        for tender in tenders:
            complete_tasks = models.Task.query.filter_by(status="הושלם", tender_id=tender.tid).all()
            milestone = ""
            if len(complete_tasks) == len(models.Task.query.filter_by(tender_id=tender.tid).all()) and len(complete_tasks) > 0:
                milestone = "מכרז הושלם"
            else:
                res = aristo_engine.add_task(GetQueueOfMilestones(tender.tid), now=True)
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


if __name__ == '__main__':
    lst_of_milestones = GetQueueOfMilestones(46).process()
    for ms in lst_of_milestones:
        print(ms.description)
