import multiprocessing as mp
from MFTasks import DailyTask, MFResponse
import threading
import datetime as dt
import time


def get_futures():
    eng = Engine.get_instance()
    return eng.futures


class Engine:
    __instance = None

    @staticmethod
    def get_instance(kwargs=None):
        if Engine.__instance is None:
            if kwargs is None:
                raise Exception("Engine singleton wasn't yet initiated with its arguments")
            print("initiating engine")
            Engine(**kwargs)
        return Engine.__instance

    def __init__(self, short_queue, short_cond, long_queue, long_cond, shutdown_event, flags, futures, response_cond):
        if Engine.__instance is None:
            Engine.__instance = self
        else:
            raise Exception("Engine singleton returned instead of re-created")
        self.short_q = short_queue
        self.long_q = long_queue
        self.short_c = short_cond
        self.long_c = long_cond
        self.shutdown = shutdown_event
        self.flags = flags
        self.futures = futures
        self.response_c = response_cond
        self.daily_thread = threading.Thread(target=self.daily_update, daemon=True)
        self.should_terminate = False

    def daily_update(self):
        while not self.should_terminate:
            # td = dt.datetime.today().replace(day=dt.datetime.today().day,
            #                                  hour=2, minute=0, second=0,
            #                                  microsecond=0) + dt.timedelta(days=1)
            td = dt.datetime.today() + dt.timedelta(seconds=60)
            delta_t = td - dt.datetime.today()
            tot_sec = delta_t.total_seconds()
            time.sleep(tot_sec)
            self.add_task(DailyTask())
        print("daily_thread terminated")

    def get_response_condition(self):
        return self.response_c

    def add_task(self, mf_task, now=False):
        args = {"q": self.long_q, "c": self.long_c, "flag": self.flags["long"]}
        if now:
            args = {"q": self.short_q, "c": self.short_c, "flag": self.flags["short"]}
        task_id = str(id(mf_task))
        returned_response = MFResponse(task_id)
        self.futures[task_id] = returned_response
        args["q"].put((mf_task, task_id,))
        if not args["flag"]:
            with args["c"]:
                args["c"].notify_all()
        return returned_response

    def initiate(self):
        self.daily_thread.start()

    def terminate_processes(self):
        self.should_terminate = True
        self.shutdown.set()
        with self.short_c:
            self.short_c.notify_all()
        with self.long_c:
            self.long_c.notify_all()


#  -----------    working processes    -----------

def aristo_process_runner(process_name, queue, shutdown_event, cond, flags, futures, response_cond):
    print(f"starting {process_name} process")
    while not shutdown_event.is_set():
        flags[process_name] = True
        with cond:
            print(f"{process_name} process condition acquired")
            while not queue.empty():
                print(f"{process_name} Q before popping: {queue.qsize()}")
                t, task_id = queue.get()
                data = t.process()
                if task_id in futures.keys():  # if not responsive then we don't care for the response
                    response = futures[task_id]
                    response.set_data(data)
                    response.complete()
                    with response_cond:
                        futures[task_id] = response
                        response_cond.notify_all()
            flags[process_name] = False
            if not shutdown_event.is_set():
                print(f"{process_name} process condition released. waiting...")
                cond.wait()  # waking up in case of new tasks in the queue or getting shutdown event
    print(f"{process_name} process terminated")


#  -----------    main process    -----------

def main_process(engine_kwargs):
    engine = Engine.get_instance(engine_kwargs)
    #  todo - initiate flask app here


#  -----------    system initiation    -----------

def initiate_aristo(process1, process2, engine_kwargs):
    p3 = mp.Process(target=main_process, args=(engine_kwargs,), daemon=True)
    process1.start()
    process2.start()
    p3.start()
    process1.join()
    process2.join()
    p3.join()


if __name__ == '__main__':
    kwargs = {}
    manager = mp.Manager()
    flags = manager.dict({"short": False, "long": False})
    kwargs["flags"] = flags
    futures = manager.dict()  # should be weak hash-map
    kwargs["futures"] = futures  # contains - { mf task id : [response ,  condition for notify] }
    kwargs["short_queue"] = mp.Queue()
    kwargs["short_cond"] = mp.Condition()
    kwargs["long_queue"] = mp.Queue()
    kwargs["long_cond"] = mp.Condition()
    kwargs["response_cond"] = mp.Condition()
    kwargs["shutdown_event"] = mp.Event()
    short_tasker = mp.Process(target=aristo_process_runner, daemon=True,
                              args=("short", kwargs["short_queue"], kwargs["shutdown_event"], kwargs["short_cond"]
                                    , flags, futures, kwargs["response_cond"]))
    long_tasker = mp.Process(target=aristo_process_runner, daemon=True,
                             args=("long", kwargs["long_queue"], kwargs["shutdown_event"], kwargs["long_cond"]
                                   , flags, futures, kwargs["response_cond"]))
    initiate_aristo(short_tasker, long_tasker, kwargs)