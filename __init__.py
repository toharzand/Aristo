from flask_login import LoginManager
from models import get_db, get_app
import Aristo_Web


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

if __name__ == '__main__':
    engine = Aristo_Web.get_engine()
    engine.initiate()
    app = get_app()
    app = manage_app(app)
    db = get_db()
    db.create_all()
    app.run(debug=True,host="0.0.0.0")
