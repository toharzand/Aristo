import datetime as dt
try:
    from aristoDB import *
except Exception as e:
    print(e)
import time, random
import threading
import collections
import EMailHandler


class MFTask:
    def __init__(self, sess = "127.0.0.1"):
        self.sess = sess

    def process(self):
        print(f"process of {self} wasn't yet overridden")
        pass


class DemoTask(MFTask):
    def __init__(self,sess = "127.0.0.1"):
        super().__init__(sess)

    def process(self):
        print(f"{self} processing")
        time.sleep(4)

    def __repr__(self):
        return "DemoTask"


class DailyTask(MFTask):
    def __init__(self):
        super().__init__()

    def process(self):
        print(f"{self} processing")

    def __repr__(self):
        return "DailyTask"


class SendEmail(MFTask):
    def process(self, receiver, content):
        sender = EMailHandler.EmailSender(receiver)
        sender.sender_email(content)


class AddUserTask(MFTask):
    def __init__(self,first_name,last_name,email,password):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password

    def process(self):
        db = get_db()
        try:
            orm_user = User(self.first_name,self.last_name,self.email,self.password)
            db.session.add(orm_user)
            db.session.commit()
        except Exception as e:
            print(e)
            get_db().session.rollback()
            print("user adding denied", print(self))





class Engine:
    def __init__(self, database):
        self.act = collections.deque()
        self.is_processing = False
        self.db = database
        self.cond = threading.Condition()
        self.daily_thread = threading.Thread(target=self.daily_update, daemon=True)
        self.main_thread = threading.Thread(target=self.process, daemon=True)
        self.should_terminate = False

    def add_task(self, var):
        self.act.append(var)
        if not self.is_processing:
            with self.cond:
                self.cond.notifyAll()
                
    def daily_update(self):
        while not self.should_terminate:
            # td = dt.datetime.today().replace(day=dt.datetime.today().day,
            #                                  hour=2, minute=0, second=0,
            #                                  microsecond=0) + dt.timedelta(days=1)
            td= dt.datetime.today()+dt.timedelta(seconds=60)
            delta_t = td - dt.datetime.today()
            tot_sec = delta_t.total_seconds()
            time.sleep(tot_sec)
            self.add_task(DailyTask())
        print("daily_thread terminated")

    def process(self):
        print("starting main process")
        while not self.should_terminate:
            self.is_processing = True
            with self.cond:
                while len(self.act)>0:
                    print(f"act condition before popping: {self.act}")
                    t = self.act.popleft()
                    t.process()
                self.is_processing = False
                if not self.should_terminate:
                    self.cond.wait()
        print("main_thread terminated")

    def initiate(self):
        try:
            self.daily_thread.start()
            self.main_thread.start()
        except KeyboardInterrupt as e:
            print("ending server")
            self.should_terminate = True
            raise e





def demo_task_adder(eng):
    pass
    # while not eng.should_terminate:
#    for i in range(10):
#        r = random.randint(1, 10)
#        time.sleep(r)
#        eng.add_task(DemoTask())
#    for i in range(3):
#        eng.add_task(DemoTask())
#    print("done a round")
#    eng.should_terminate = True



if __name__ == "__main__":
    # db = None
    # eng = Engine(db)
    # eng.initiate()
    # demo_task_adder(eng)
    email_test()
