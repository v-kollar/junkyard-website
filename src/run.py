from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def home():
    return render_template("index.jinja2")


@app.route('/statisky')
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


if __name__ == '__main__':
    app.run(debug=True)
