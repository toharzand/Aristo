from EmailHandler import *
import time
try:
    from aristoDB import *
except Exception as e:
    print("couldn't import aristoDB")


class MFTask:
    def __init__(self, sess="127.0.0.1"):
        self.sess = sess

    def process(self, engine=None):
        print(f"process of {self} wasn't yet overridden")
        pass




class DemoTask(MFTask):
    def process(self, engine=None):
        print(f"{self} processing")
        time.sleep(4)

    def __repr__(self):
        return "DemoTask"




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

    def process(self, engine=None):
        sender = EmailSender(self.receiver)
        sender.send_email(self.content)




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

