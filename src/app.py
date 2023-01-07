from flask import Flask, render_template, request, session, redirect, flash, template_rendered
import sqlite3
app = Flask(__name__)
app.secret_key = "klic"


@app.route('/')
def home():
    connection = sqlite3.connect('sberna.db')
    cursor = connection.cursor()
    query = "SELECT SUM(mnozstvi) mnozstvi_za_rok FROM (SELECT sbery.id_sberu, SUM(mnozstvi) mnozstvi FROM sbery JOIN polozka ON (sbery.id_sberu = polozka.id_sberu) WHERE sbery.cas_odevzdani > datetime('now', '-1 year') GROUP BY sbery.id_sberu)"
    cursor.execute(query)
    weight = cursor.fetchall()
    query = "SELECT SUM(cena) vyplaceni_za_rok FROM (SELECT sbery.id_sberu, SUM(cena) cena FROM sbery JOIN polozka ON (sbery.id_sberu = polozka.id_sberu) JOIN ceny ON (polozka.id_ceny = ceny.id_ceny) WHERE sbery.cas_odevzdani > datetime('now', '-1 year') GROUP BY sbery.id_sberu)"
    cursor.execute(query)
    paid=cursor.fetchall()
    connection.close()
    return render_template("index.jinja2", weight=str(round(weight[0][0]))+" T", paid=str(round(paid[0][0]))+" Kč")


@app.route('/statistiky')
def stats():
    connection = sqlite3.connect('sberna.db')
    cursor = connection.cursor()
    query = "SELECT typy_materialu.nazev, SUM(mnozstvi) celkove_mnozstvi FROM sbery JOIN polozka ON (sbery.id_sberu = polozka.id_sberu) JOIN typy_materialu ON (typy_materialu.id_typu_materialu = polozka.id_typu_materialu) GROUP BY typy_materialu.id_typu_materialu"
    cursor.execute(query)
    material_total=cursor.fetchall()
    query = "SELECT strftime('%Y',cas_odevzdani) AS rok, SUM(mnozstvi) AS mnozstvi FROM sbery JOIN polozka ON (sbery.id_sberu = polozka.id_sberu) JOIN typy_materialu ON (typy_materialu.id_typu_materialu = polozka.id_typu_materialu) GROUP BY strftime('%Y',cas_odevzdani)"
    cursor.execute(query)
    yearly_material_total=cursor.fetchall()
    query = "SELECT strftime('%Y',cas_odevzdani) AS rok, SUM(cena) AS cena FROM sbery JOIN polozka ON (sbery.id_sberu = polozka.id_sberu) JOIN ceny ON (polozka.id_ceny = ceny.id_ceny) GROUP BY strftime('%Y',cas_odevzdani)"
    cursor.execute(query)
    income_total=cursor.fetchall()
    connection.close()
    return render_template("stats.jinja2",material_total=material_total, yearly_material_total=yearly_material_total, income_total=income_total)


@app.route('/cenik',methods=['GET','POST'])
def pricelist():
    connection = sqlite3.connect('sberna.db')
    cursor = connection.cursor()
    if request.method == 'POST':
            search = request.form['search']
            query = "SELECT nazev, cena FROM ceny JOIN typy_materialu ON (ceny.id_typu_materialu = typy_materialu.id_typu_materialu) WHERE datum_od <= datetime('now') AND nazev= '"+search+"' AND datum_do >= datetime('now')"
            cursor.execute(query)
            results = cursor.fetchall()
            connection.close()
            return render_template("pricelist.jinja2",materials=results)
    query = "SELECT nazev, cena FROM ceny JOIN typy_materialu ON (ceny.id_typu_materialu = typy_materialu.id_typu_materialu) WHERE datum_od <= datetime('now') AND datum_do >= datetime('now')"
    cursor.execute(query)
    results = cursor.fetchall()
    connection.close()
    return render_template("pricelist.jinja2",materials=results)


@app.route('/prihlaseni', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        connection = sqlite3.connect('sberna.db')
        cursor = connection.cursor()
        query = "SELECT potvrzeni,id_uzivatele,id_role  FROM uzivatel WHERE email= '"+request.form['email']+"' AND heslo= '"+request.form['password']+"'"
        cursor.execute(query)
        results = cursor.fetchall()
        if len(results) == 0:
            connection.close()
            flash("Zadali jste špatné přihlašovací údaje", category="error")
            return render_template("login.jinja2")
        elif results[0][0] == 0:
            flash("Váš účet nebyl potvrzen", category="error")
            return render_template("login.jinja2")
        else:
            session["user"]=results
            connection.close()
            return redirect('/profile/')
    else:
        if "user" in session:
            return redirect('/profile/')
        return render_template("login.jinja2")


@app.route('/profile/')
def profile():
    if "user" in session:
        return render_template("profile.jinja2")
    else:
        return redirect('/prihlaseni')


@app.route('/odhlaseni')
def logout():
    flash("Byli jste odhlášeni", category="success")
    session.pop("user", None)
    return redirect('/prihlaseni')

@app.route('/registrace', methods=['GET','POST'])
def reg():
    if request.method == 'POST':
        connection = sqlite3.connect('sberna.db')
        cursor = connection.cursor()
        query ="SELECT email,telefon FROM uzivatel WHERE telefon='"+request.form['phone']+"' OR email='"+request.form['email']+"'"
        cursor.execute(query)
        results = cursor.fetchall()
        if (len(results) == 0):
            query="INSERT INTO uzivatel (potvrzeni, jmeno, prijmeni, email, heslo, telefon, adresa_trvaleho_bydliste, adresa_docasneho_bydliste, cislo_uctu, id_role) VALUES(0, '"+request.form['first_name']+"', '"+request.form['last_name']+"', '"+request.form['email']+"', '"+request.form['password']+"', '"+request.form['phone']+"', '"+request.form['permanent_stay']+"', '"+request.form['temp_stay']+"', '"+request.form['bank_id']+"', 3);"
            connection.execute(query)
            connection.commit()
            flash("Byli jste zaregistrování", category="success")
            return render_template("reg.jinja2")

        else:
            if (results[0][0] == request.form['email']):
                flash("Zadaný e-mail je již používán", category="error")
                return render_template("reg.jinja2")
            else:
                flash("Zadaný telefon je již používán", category="error")
                return render_template("reg.jinja2")

    return render_template("reg.jinja2")

@app.route('/profile/zmena_svych_udaju',methods=['GET','POST'])
def change_your_details():
    if "user" in session:
        if request.method == 'POST':
            connection = sqlite3.connect('sberna.db')
            cursor = connection.cursor()
            query = "SELECT heslo FROM uzivatel WHERE id_uzivatele='"+str(session["user"][0][1])+"'"
            cursor.execute(query)
            result = cursor.fetchall()
            if (len(request.form['password'])==0):
                newpassword=result[0][0]
            else:
                newpassword=request.form['password']
            query="UPDATE uzivatel SET jmeno='"+request.form['first_name']+"', prijmeni='"+request.form['last_name']+"',adresa_trvaleho_bydliste='"+request.form['permanent_stay']+"', adresa_docasneho_bydliste='"+request.form['temp_stay']+"', telefon='"+request.form['phone']+"', cislo_uctu='"+request.form['bank_id']+"',heslo='"+newpassword+"' WHERE id_uzivatele='"+str(session['user'][0][1])+"'"
            connection.execute(query)
            connection.commit()
            flash("Údaje byly aktualizovány", category="success")

        connection = sqlite3.connect('sberna.db')
        cursor = connection.cursor()
        query = "SELECT jmeno,prijmeni,adresa_trvaleho_bydliste, adresa_docasneho_bydliste, email, telefon, cislo_uctu, heslo FROM uzivatel WHERE id_uzivatele='"+str(session["user"][0][1])+"'"
        cursor.execute(query)
        result = cursor.fetchall()
        return render_template("change_your_details.jinja2",first_name=result[0][0],last_name=result[0][1],permanent_stay=result[0][2],temp_stay=result[0][3],email=result[0][4],phone=result[0][5],bank_id=result[0][6])
    else:
        return redirect('/profile/')
    


@app.route('/zadosti_o_registraci')
def applications_for_registration():
    if "user" in session and (session['user'][0][2] == 1 or session['user'][0][2] == 2):
        return render_template("applications_for_registration.jinja2")
    else:
        return redirect('/profile/')
    

@app.route('/zadost_o_registraci')
def application_for_registration():
    if "user" in session and (session['user'][0][2] == 1 or session['user'][0][2] == 2):
        return render_template("application_for_registration.jinja2")
    else:
        return redirect('/profile/')

@app.route('/pridani_uzivatele')
def create_user():
    if "user" in session and session['user'][0][2] == 1:
        return render_template("create_user.jinja2")
    else:
        return redirect('/profile/')
    


@app.route('/uprava_uzivatele')
def edit_user():
    if "user" in session and session['user'][0][2] == 1:
        return render_template("edit_user.jinja2")
    else:
        return redirect('/profile/')
    


@app.route('/pridani_materialu')
def add_material():
    if "user" in session and session['user'][0][2] == 1:
        return render_template("add_material.jinja2")
    else:
        return redirect('/profile/')
    

@app.route('/detaily-sberu')
def collection_details():
    return render_template("details.jinja2")

@app.route('/profile/sprava')
def user_management():
    if "user" in session and session['user'][0][2] == 1:
        return render_template('management.jinja2')
    else:
        return redirect('/profile/')
    


@app.route('/profile/moje-sbery')
def my_collections():
    if "user" in session:
        return render_template('my_collections.jinja2')
    else:
        return redirect('/profile/')

@app.route('/profile/zadani-sberu')

def insert_collection():
    if "user" in session and (session['user'][0][2] == 1 or session['user'][0][2] == 2):
        return render_template('add_collections.jinja2')
    else:
        return redirect('/profile/')

if __name__ == '__main__':
    app.run(debug=True)
