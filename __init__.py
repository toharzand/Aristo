from flask_login import LoginManager
from models import get_db, get_app
import engine2_0
import Aristo_Web
import multiprocessing as mp


def manage_app(app):
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from Aristo_Web import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app


#  -----------    main process    -----------

def main_process(engine_kwargs):
    engine = engine2_0.Engine.get_instance(engine_kwargs)
    engine.initiate()
    Aristo_Web.define_globals()
    flask_main_run()


def flask_main_run():
    app = get_app()
    app = manage_app(app)
    db = get_db()
    db.create_all()
    app.run(host="0.0.0.0", port=443,debug=True)


#  -----------    system initiation    -----------

def initiate_aristo(process1, process2, engine_kwargs):
    p3 = mp.Process(target=main_process, args=(engine_kwargs,), daemon=True)
    process1.start()
    process2.start()
    p3.start()
    process1.join()
    process2.join()
    p3.join()


def main():
    #  define all processes and between-processes shared data arguments:
    kwargs = {}
    manager = mp.Manager()
    flags = manager.dict({"short": False, "long": False})
    kwargs["flags"] = flags
    futures = manager.dict()  # should be weak hash-map
    kwargs["futures"] = futures
    kwargs["short_queue"] = mp.Queue()
    kwargs["short_cond"] = mp.Condition()
    kwargs["long_queue"] = mp.Queue()
    kwargs["long_cond"] = mp.Condition()
    kwargs["response_cond"] = mp.Condition()
    kwargs["shutdown_event"] = mp.Event()
    short_tasker = mp.Process(target=engine2_0.aristo_process_runner, daemon=True,
                              args=("short", kwargs["short_queue"], kwargs["shutdown_event"], kwargs["short_cond"]
                                    , flags, futures, kwargs["response_cond"]))
    long_tasker = mp.Process(target=engine2_0.aristo_process_runner, daemon=True,
                             args=("long", kwargs["long_queue"], kwargs["shutdown_event"], kwargs["long_cond"]
                                   , flags, futures, kwargs["response_cond"]))
    initiate_aristo(short_tasker, long_tasker, kwargs)


if __name__ == '__main__':
    main()
    # engine = Aristo_Web.get_engine()
    # engine.initiate()
    # app = get_app()
    # app = manage_app(app)
    # db = get_db()
    # db.create_all()
    # app.run(debug=True, host="0.0.0.0")
