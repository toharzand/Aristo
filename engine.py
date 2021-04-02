import datetime as dt
try:
    from models import *
except Exception as e:
    print(e)
import time, random
import threading
import collections
from MFTasks import *


class Engine:
    def __init__(self, database):
        self.main_act = collections.deque()
        self.connection_act = collections.deque()
        self.main_is_processing = False
        self.con_is_processing = False
        self.db = database
        self.main_cond = threading.Condition()
        self.con_cond = threading.Condition()
        self.daily_thread = threading.Thread(target=self.daily_update, daemon=True)
        self.main_thread = threading.Thread(target=self.main_run, daemon=True)
        self.connection_thread = threading.Thread(target=self.connection_run, daemon=True)
        self.should_terminate = False

    def add_task(self, var):
        if type(var) == SendEmail:
            self.connection_act.append(var)
            if not self.con_is_processing:
                with self.con_cond:
                    self.con_cond.notifyAll()
        else:
            self.main_act.append(var)
            if not self.main_is_processing:
                with self.main_cond:
                    self.main_cond.notifyAll()
                
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

    def main_run(self):
        print("starting main process")
        while not self.should_terminate:
            self.main_is_processing = True
            with self.main_cond:
                while len(self.main_act)>0:
                    print(f"main act before popping: {self.main_act}")
                    t = self.main_act.popleft()
                    t.process(self)
                self.main_is_processing = False
                if not self.should_terminate:
                    self.main_cond.wait()
        print("main_thread terminated")

    def connection_run(self):
        print("starting connection process")
        while not self.should_terminate:
            self.con_is_processing = True
            with self.con_cond:
                while len(self.connection_act) > 0:
                    print(f"con act before popping: {self.connection_act}")
                    t = self.connection_act.popleft()
                    t.process(self)
                self.con_is_processing = False
                if not self.should_terminate:
                    self.con_cond.wait()
        print("connection_thread terminated")

    def initiate(self):
        try:
            self.daily_thread.start()
            self.main_thread.start()
            self.connection_thread.start()
        except KeyboardInterrupt as e:
            print("ending server")
            self.should_terminate = True
            with self.main_cond as m:
                with self.con_cond as c:
                    m.notifyAll()
                    c.notifyAll()
            raise e





def demo_task_adder(eng):
    test_start = dt.datetime.now()
    for i in range(10):
       r = random.randint(1, 10)
       if r>5:
           eng.add_task(SendEmail("aristotenders@gmail.com", f"test on {test_start}\ntest number {i+1}"))
       time.sleep(r)
       eng.add_task(DemoTask())
    for i in range(3):
       eng.add_task(DemoTask())
    print("done a round")
    time.sleep(2)
    eng.should_terminate = True
    with eng.main_cond:
        with eng.con_cond:
            print(f"engine done all tasks\nconnection_act: {eng.connection_act}\nmain_act: {eng.main_act}")


if __name__ == "__main__":
    db = None
    eng = Engine(db)
    eng.initiate()
    demo_task_adder(eng)
