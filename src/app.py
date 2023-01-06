from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def home():
    return render_template("index.jinja2")


@app.route('/statistiky')
def stats():
    return render_template("stats.jinja2")


@app.route('/cenik')
def pricelist():
    return render_template("pricelist.jinja2")


@app.route('/prihlaseni')
def login():
    return render_template("login.jinja2")


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
