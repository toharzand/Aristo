from flask import Flask, render_template, request,redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta



app = Flask(__name__,template_folder='templates')
app.secret_key = "tenderly_secret_key"  # secret app for the session to keep data
app.permanent_session_lifetime = timedelta(minutes=5)  # time untill user forced to log out



app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://itda:28031994@127.0.0.1:3306/new_tender'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)  # create connection with database


class Users(db.Model):
    '''
        @Name : Users
        @Do: create table that contain all the users and the relevant data about them in the database

        @ Param:
                first_name - user first name.
                last_name - user last name.
                email: user email address (must be validate by regular expression)
                password: user password. (must be validate by regular expression)
    '''

    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(10), nullable=False)

    def __init__(self, first_name, last_name, email, password):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password


class Tenders(db.Model):
    __tablename__ = "tenders"

    tid = db.Column(db.Integer, primary_key=True, nullable=False,autoincrement=True)
    tenders_committee_Type = db.Column(db.VARCHAR(20))
    description = db.Column(db.VARCHAR(250), nullable=False)
    start_date = db.Column(db.String(255), nullable=False)
    finish_date = db.Column(db.String(255), nullable=False)
    department = db.Column(db.VARCHAR(50))

    def __init__(self, tenders_committee_Type, description, start_date,finish_date,department,contact_user):
        self.tenders_committee_Type = tenders_committee_Type
        self.description = description
        self.start_date = start_date
        self.finish_date = finish_date
        self.department = department



@app.route("/")
@app.route("/home/")
def home():
     print("hello flask")
     return render_template("home.html")



@app.route("/login",methods=["POST","GET"])
def login():
    if request.method == "POST":
        session.permanent = True
        email = request.form['email']
        password = request.form['password']
        all_users = Users.query.all()
        flag = False
        for user in all_users:
            if user.password == password and user.email==email:
                flag = True
        if flag:
            return redirect(url_for("user"))
        else:
            print("not in db")

    return render_template("login.html")

@app.route("/user/")
def user():
    return render_template("user.html")


lst = ["first_task", "second_task", "third_task", "forth_task"]
@app.route("/rearrange", methods = ["POST", "GET"])
def rearrange():
    print(lst)
    return render_template("rearrange.html")


if __name__ == '__main__':
    # db.create_all()
    app.run(debug=True)


