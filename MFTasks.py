from EmailHandler import *
import time
try:
    from models import *
except Exception as e:
    print("couldn't import aristoDB")


class MFTask:
    def __init__(self):
        pass

    def process(self, engine=None):
        print(f"process of {self} wasn't yet overridden")
        pass


class MFResponse:
    def __init__(self):
        self.data = None
        self.complete = False

    def get(self):
        return self.data

    def is_complete(self):
        return self.complete

    def set_data(self,data):
        self.data = data

    def complete(self):
        self.complete = True




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

    def create_template_from_tender_BFS(self, template_tender_id, real_tender_id):
        graph = {}  # {task_template_id : number (0=grey, 1=black)}

        q = []

        lst_of_first_tasks_of_tender = self.con.excecute("""
            SELECT dependant
            FROM
            TasksToTasksTemplate
            WHERE
            tender_id = ? and dependee = null
            """, template_tender_id)
        for row in lst_of_first_tasks_of_tender:
            real_dependent_id = self.create_real_task_from_template_task(template_tender_id, row[0])
            q.append((row[0], real_dependent_id))
            graph[row[0]] = 0

        while len(q) != 0:
            template_dependee_id, real_dependee_id = q.pop(0)  # getting (task template id , task real id)
            lst_of_template_dependants = self.con.excecute("""
            SELECT dependant
            FROM
            TasksToTasksTemplate
            WHERE
            depandee = ?
            """, template_dependee_id)  # = [(depndant1_id), (depandent1_id), (depandent2_id)])
            for row in lst_of_template_dependants:
                if row[0] in graph.keys():
                    continue
                real_dependent_id = self.create_real_task_from_template_task(template_tender_id, row[0])
                self.add_blocked_to_blocking(real_dependee_id, real_dependent_id)
                q.append((row[0], real_dependent_id))
                graph[row[0]] = 1
            graph[template_dependee_id] = 1

    def process(self):
        connection = get_my_sql_connection()
        curser = connection.curser()
        curser.excecute("...")

    def create_real_task_from_template_task(self, template_tender_id, param):
        pass  # todo

    def add_blocked_to_blocking(self, real_dependee_id, real_dependent_id):
        pass  # todo

