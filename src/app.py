from flask import Flask, render_template, request, session, redirect
import sqlite3
app = Flask(__name__)
app.secret_key = "klic"


@app.route('/')
def home():
    return render_template("index.jinja2")


@app.route('/statistiky')
def stats():
    return render_template("stats.jinja2")


@app.route('/cenik')
def pricelist():
    return render_template("pricelist.jinja2")


@app.route('/prihlaseni', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        connection = sqlite3.connect('sberna.db')
        cursor = connection.cursor()
        email = request.form['email']
        password = request.form['password']
        query = "SELECT jmeno,prijmeni,email,heslo FROM uzivatel WHERE email= '"+email+"' AND heslo= '"+password+"'"
        cursor.execute(query)
        results = cursor.fetchall()
        #print(name,password)
        if len(results) == 0:
            return render_template("login.jinja2")
        else:
            session["user"]=results
            return redirect('/profile/')
    else:
        if "user" in session:
            return redirect('/profile/')
        return render_template("login.jinja2")


@app.route('/profile/')
def profile():
    if "user" in session:
        return render_template("profile.jinja2",name=session["user"])
    else:
        return redirect('/prihlaseni')


@app.route('/odhlaseni')
def logout():
    session.pop("user", None)
    return redirect('/prihlaseni')

@app.route('/registrace')
def reg():
    return render_template("reg.jinja2")

@app.route('/zmena_svych_udaju')
def change_your_details():
    return render_template("change_your_details.jinja2")


@app.route('/zadosti_o_registraci')
def application_for_registration():
    return render_template("application_for_registration.jinja2")


@app.route('/pridani_uzivatele')
def create_user():
    return render_template("create_user.jinja2")


@app.route('/uprava_uzivatele')
def edit_user():
    return render_template("edit_user.jinja2")


@app.route('/pridani_materialu')
def add_material():
    return render_template("add_material.jinja2")



if __name__ == '__main__':
    app.run(debug=True)
