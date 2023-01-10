from flask import Flask, render_template, request,\
    session, redirect, flash, url_for
from datetime import datetime
from flask.typing import ResponseReturnValue
from typing import List, Tuple, Any
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "klic"

Query = List[Tuple[Any]]

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, 'database/sberna.db')

def process_query(query: str) -> Query:
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    connection.close()
    return data

@app.route('/')
def home() -> ResponseReturnValue:
    return render_template("index.jinja2", weight=f"{material_per_year()} Kg",
                                           paid=f"{paid_per_year()} Kč")

def material_per_year() -> Any:
    weight_query = "SELECT SUM(mnozstvi) mnozstvi_za_rok FROM " \
            "(SELECT sbery.id_sberu, SUM(mnozstvi) mnozstvi FROM sbery " \
            "JOIN polozka ON (sbery.id_sberu = polozka.id_sberu) " \
            "WHERE sbery.cas_odevzdani > datetime('now', '-1 year') " \
            "GROUP BY sbery.id_sberu);"
    weight = process_query(weight_query)
    return weight[0][0]

def paid_per_year() -> Any:
    paid_query = "SELECT SUM(cena*mnozstvi) castka FROM sbery JOIN polozka " \
            "ON (polozka.id_sberu = sbery.id_sberu) JOIN ceny " \
            "ON (ceny.id_ceny = polozka.id_ceny) " \
            "WHERE sbery.cas_odevzdani > datetime('now', '-1 year');"
    paid = process_query(paid_query)
    return paid[0][0]


@app.route('/statistiky')
def stats() -> ResponseReturnValue:
    return render_template("stats.jinja2",
                           material_total=total_each_material(),
                           yearly_material_total=total_yearly_weight(),
                           income_total=total_yearly_profit())


def total_each_material() -> Any:
    total_weight = "SELECT typy_materialu.nazev, SUM(mnozstvi) celkove_mnozstvi " \
                   "FROM sbery JOIN polozka ON (sbery.id_sberu = polozka.id_sberu) " \
                   "JOIN typy_materialu ON (typy_materialu.id_typu_materialu = " \
                   "polozka.id_typu_materialu) GROUP BY " \
                   "typy_materialu.id_typu_materialu;"
    total = process_query(total_weight)
    return total

def total_yearly_weight() -> Any:
    yearly_weight = "SELECT strftime('%Y',cas_odevzdani) AS rok, SUM(mnozstvi) " \
                    "AS mnozstvi FROM sbery JOIN polozka ON " \
                    "(sbery.id_sberu = polozka.id_sberu) JOIN typy_materialu " \
                    "ON (typy_materialu.id_typu_materialu = " \
                    "polozka.id_typu_materialu) GROUP BY " \
                    "strftime('%Y',cas_odevzdani);"
    yearly = process_query(yearly_weight)
    return yearly

def total_yearly_profit() -> Any:
    total_profit = "SELECT strftime('%Y',cas_odevzdani) AS rok, " \
                   "SUM(cena*mnozstvi) AS cena FROM sbery JOIN polozka ON " \
                   "(sbery.id_sberu = polozka.id_sberu) JOIN ceny ON " \
                   "(polozka.id_ceny = ceny.id_ceny) GROUP BY " \
                   "strftime('%Y',cas_odevzdani)"
    profit = process_query(total_profit)
    return profit



@app.route('/cenik',methods=['GET','POST'])
def pricelist() -> ResponseReturnValue:
    connection = sqlite3.connect(DB_PATH)
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
def login() -> ResponseReturnValue:
    if request.method == 'POST':
        connection = sqlite3.connect(DB_PATH)
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
def profile() -> ResponseReturnValue:
    if "user" in session:
        return render_template("profile.jinja2")
    else:
        return redirect('/prihlaseni')


@app.route('/odhlaseni')
def logout() -> ResponseReturnValue:
    flash("Byli jste odhlášeni", category="success")
    session.pop("user", None)
    return redirect('/prihlaseni')

@app.route('/registrace', methods=['GET','POST'])
def reg() -> ResponseReturnValue:
    if "user" in session:
        return redirect('/profile/')
    if request.method == 'POST':
        connection = sqlite3.connect(DB_PATH)
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
def change_your_details() -> ResponseReturnValue:
    if "user" in session:
        if request.method == 'POST':
            connection = sqlite3.connect(DB_PATH)
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

        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        query = "SELECT jmeno,prijmeni,adresa_trvaleho_bydliste, adresa_docasneho_bydliste, email, telefon, cislo_uctu, heslo FROM uzivatel WHERE id_uzivatele='"+str(session["user"][0][1])+"'"
        cursor.execute(query)
        result = cursor.fetchall()
        return render_template("change_your_details.jinja2",first_name=result[0][0],last_name=result[0][1],permanent_stay=result[0][2],temp_stay=result[0][3],email=result[0][4],phone=result[0][5],bank_id=result[0][6])
    else:
        return redirect('/profile/')
    


@app.route('/profile/zadosti_o_registraci',methods=['GET','POST'])
def applications_for_registration() -> ResponseReturnValue:
    if "user" in session and (session['user'][0][2] == 1 or session['user'][0][2] == 2) and request.method == 'POST':
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        query = "SELECT id_uzivatele FROM uzivatel WHERE telefon='"+request.form['phone']+"' AND potvrzeni=0"
        cursor.execute(query)
        result = cursor.fetchall()
        if len(result) != 0:
            return redirect(url_for('application_for_registration', user_id=result[0][0]))
        else:
            flash("Pod tímto číslem neexistuje čekající registrace", category="error")

    if "user" in session and (session['user'][0][2] == 1 or session['user'][0][2] == 2):
        return render_template("applications_for_registration.jinja2")
    else:
        return redirect('/profile/')
    

@app.route('/profile/zadosti_o_registraci/zadost_o_registraci',methods=['GET','POST'])
def application_for_registration() -> ResponseReturnValue:
    if "user" in session and (session['user'][0][2] == 1 or session['user'][0][2] == 2):
        connection = sqlite3.connect(DB_PATH)
        user_id = request.args['user_id']
        if request.method == 'POST':
            if request.form['button'] == "Potvrdit":
                value="1"
                flash("Registrace byla potvrzena", category="success")
            else:
                flash("Registrace byla zamítnuta", category="success")
                value="2"
            query="UPDATE uzivatel SET potvrzeni='"+value+"', jmeno='"+request.form['first_name']+"', prijmeni='"+request.form['last_name']+"',adresa_trvaleho_bydliste='"+request.form['permanent_stay']+"', adresa_docasneho_bydliste='"+request.form['temp_stay']+"', telefon='"+request.form['phone']+"', cislo_uctu='"+request.form['bank_id']+"' WHERE id_uzivatele='"+user_id+"'"
            connection.execute(query)
            connection.commit()
            return redirect(url_for('applications_for_registration')) 
        cursor = connection.cursor()
        query = "SELECT jmeno,prijmeni,adresa_trvaleho_bydliste, adresa_docasneho_bydliste, email, telefon, cislo_uctu, heslo FROM uzivatel WHERE id_uzivatele='"+user_id+"'"
        cursor.execute(query)
        result = cursor.fetchall()
        return render_template("application_for_registration.jinja2",first_name=result[0][0],last_name=result[0][1],permanent_stay=result[0][2],temp_stay=result[0][3],email=result[0][4],phone=result[0][5],bank_id=result[0][6])
    else:
        return redirect('/profile/')

@app.route('/profile/sprava/pridat_uzivatele',methods=['GET','POST'])
def create_user() -> ResponseReturnValue:
    connection = sqlite3.connect(DB_PATH)
    if request.method == 'POST' and "user" in session and session['user'][0][2] == 1:
        cursor = connection.cursor()
        query ="SELECT email,telefon FROM uzivatel WHERE telefon='"+request.form['phone']+"' OR email='"+request.form['email']+"'"
        cursor.execute(query)
        results = cursor.fetchall()
        if (len(results) == 0):
            print(request.form['role'])
            query="INSERT INTO uzivatel (potvrzeni, jmeno, prijmeni, email, heslo, telefon, adresa_trvaleho_bydliste, adresa_docasneho_bydliste, cislo_uctu, id_role) VALUES(1, '"+request.form['first_name']+"', '"+request.form['last_name']+"', '"+request.form['email']+"', '"+request.form['password']+"', '"+request.form['phone']+"', '"+request.form['permanent_stay']+"', '"+request.form['temp_stay']+"', '"+request.form['bank_id']+"', '"+request.form['role']+"');"
            connection.execute(query)
            connection.commit()
            flash("Uživatel byl vytvořen", category="success")
            return redirect('/profile/sprava/pridat_uzivatele')

        else:
            if (results[0][0] == request.form['email']):
                flash("Zadaný e-mail je již používán", category="error")
                return redirect('/profile/sprava/pridat_uzivatele')
            else:
                flash("Zadaný telefon je již používán", category="error")
                return redirect('/profile/sprava/pridat_uzivatele')

    if "user" in session and session['user'][0][2] == 1:
        cursor = connection.cursor()
        query = "SELECT * FROM role"
        cursor.execute(query)
        roles=cursor.fetchall()
        return render_template("create_user.jinja2", roles=roles)
    else:
        return redirect('/profile/')
    


@app.route('/profile/sprava/uprava_uzivatele',methods=['GET','POST'])
def edit_user() -> ResponseReturnValue:
    if "user" in session and session['user'][0][2] == 1:
        user_id = request.args['user_id']
        if request.method == 'POST':
            if request.form['button'] == "Aktualizovat":
                connection = sqlite3.connect(DB_PATH)
                cursor = connection.cursor()
                query = "SELECT heslo FROM uzivatel WHERE id_uzivatele='"+user_id+"'"
                cursor.execute(query)
                result = cursor.fetchall()
                if (len(request.form['password'])==0):
                    newpassword=result[0][0]
                else:
                    newpassword=request.form['password']
                query="UPDATE uzivatel SET id_role='"+request.form['role']+"', jmeno='"+request.form['first_name']+"', prijmeni='"+request.form['last_name']+"',adresa_trvaleho_bydliste='"+request.form['permanent_stay']+"', adresa_docasneho_bydliste='"+request.form['temp_stay']+"', telefon='"+request.form['phone']+"', cislo_uctu='"+request.form['bank_id']+"',heslo='"+newpassword+"' WHERE id_uzivatele='"+user_id+"'"
                connection.execute(query)
                connection.commit()
                flash("Údaje byly aktualizovány", category="success")
                return redirect(url_for('user_management'))
            else:
                connection = sqlite3.connect(DB_PATH)
                query="DELETE FROM uzivatel WHERE id_uzivatele='"+user_id+"'"
                connection.execute(query)
                connection.commit()
                flash("Uživatel byl odstraněn", category="success")
                return redirect(url_for('user_management'))

        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        query = "SELECT jmeno,prijmeni,adresa_trvaleho_bydliste, adresa_docasneho_bydliste, email, telefon, cislo_uctu, heslo,role.nazev,role.id_role FROM uzivatel JOIN role ON(uzivatel.id_role=role.id_role) WHERE id_uzivatele='"+user_id+"'"
        cursor.execute(query)
        user = cursor.fetchall()
        query = "SELECT nazev, id_role FROM role"
        cursor.execute(query)
        roles = cursor.fetchall()
        print(roles)
        print(user[0][8])
        for i in range (len(roles)):
            if(roles[i][0]==str(user[0][8])):
                roles.pop(i)
                break
        print(roles)
        return render_template("edit_user.jinja2",first_name=user[0][0],last_name=user[0][1],permanent_stay=user[0][2],temp_stay=user[0][3],email=user[0][4],phone=user[0][5],bank_id=user[0][6],role=user[0][8],role_id=user[0][9],roles=roles)

        
    else:
        return redirect('/profile/')
    


@app.route('/profile/zmena-ceniku/pridani_materialu',methods=['GET','POST'])
def add_material() -> ResponseReturnValue:
    if request.method == 'POST' and "user" in session and session['user'][0][2] == 1:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        query="SELECT nazev FROM typy_materialu"
        cursor.execute(query)
        
        results=cursor.fetchall()
        set = True
        for i in results:
            print(i[0])
            if request.form['type']==i[0]:
                set= False
                break
        if set:
            query="INSERT INTO typy_materialu (nazev) VALUES('"+request.form['type']+"');"
            connection.execute(query)
            connection.commit()
            query="SELECT id_typu_materialu FROM typy_materialu WHERE nazev='"+request.form['type']+"'"
            cursor.execute(query)
            results=cursor.fetchall()
            print(results[0][0])
            now = datetime.utcnow()
            current_time = now.strftime(" %H:%M:%S")
            date = str(request.form['date-until']) + current_time
            print(date)
            query="INSERT INTO ceny (datum_od, datum_do, cena, id_typu_materialu) VALUES(datetime('now'), '"+date+"', '"+str(request.form['price'])+"', '"+str(results[0][0])+"');"
            connection.execute(query)
            connection.commit()
            flash("Materiál byl vložen", category="success")
            return render_template("add_material.jinja2")
        else:
            flash("Materiál s tímto názvem již existuje", category="error")
            return render_template("add_material.jinja2")
    if "user" in session and session['user'][0][2] == 1:
        return render_template("add_material.jinja2")
    else:
        return redirect('/profile/')
    

@app.route('/profile/moje-sbery/detaily-sberu')
def collection_details() -> ResponseReturnValue:
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    query="SELECT nazev, mnozstvi AS hmostnost, cena*mnozstvi AS castka,cena,STRFTIME('%Y-%m-%d', cas_odevzdani) FROM sbery JOIN polozka ON (sbery.id_sberu = polozka.id_sberu) JOIN ceny ON (ceny.id_ceny = polozka.id_ceny) JOIN typy_materialu ON (typy_materialu.id_typu_materialu = polozka.id_typu_materialu) WHERE id_uzivatele = '"+str(session['user'][0][1])+"' AND sbery.id_sberu= '"+request.args['collection_id']+"'"
    cursor.execute(query)
    results=cursor.fetchall()
    print(request.args['collection_id'])
    return render_template("details.jinja2",collection=results)

@app.route('/profile/sprava',methods=['GET','POST'])
def user_management() -> ResponseReturnValue:
    if request.method == 'POST' and "user" in session and session['user'][0][2] == 1:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        query = "SELECT id_uzivatele FROM uzivatel WHERE id_uzivatele='"+request.form['user_id']+"' OR telefon='"+request.form['phone']+"'"
        cursor.execute(query)
        results=cursor.fetchall()
        if len(results) != 0:
            return redirect(url_for('edit_user', user_id=results[0]))
        else:
            flash("Uživatele nelze najít", category="error")
            
    if "user" in session and session['user'][0][2] == 1:
        return render_template('management.jinja2')
    else:
        return redirect('/profile/')
    


@app.route('/profile/moje-sbery',methods=['GET','POST'])
def my_collections() -> ResponseReturnValue:
    if "user" in session:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        query = "SELECT SUM(cena*mnozstvi) AS vyplatit_za_mesic FROM sbery JOIN polozka ON (polozka.id_sberu = sbery.id_sberu) JOIN ceny ON (ceny.id_ceny = polozka.id_ceny) WHERE id_uzivatele = '"+str(session['user'][0][1])+"' AND cas_odevzdani >= DATE('now', 'start of month')"
        cursor.execute(query)
        payment=cursor.fetchall()
        if request.method == 'POST':
            if request.form['button']=="Hledat":
                print(request.form['date-from'])
                print(request.form['date-until'])
                query = "SELECT STRFTIME('%Y-%m-%d', cas_odevzdani) AS datum, SUM(cena*mnozstvi) AS castka,sbery.id_sberu FROM sbery JOIN polozka ON (sbery.id_sberu = polozka.id_sberu) JOIN ceny ON (ceny.id_ceny = polozka.id_ceny) WHERE id_uzivatele = '"+str(session['user'][0][1])+"' AND STRFTIME('%Y-%m-%d', cas_odevzdani) >= '"+str(request.form['date-from'])+"' AND STRFTIME('%Y-%m-%d', cas_odevzdani) <= '"+str(request.form['date-until'])+"' GROUP BY sbery.id_sberu ORDER BY datum DESC"
                cursor.execute(query)
                collections=cursor.fetchall()
                return render_template('my_collections.jinja2',collections=collections,payment=payment[0][0])
            else:

                return redirect(url_for('collection_details', collection_id=request.form['button']))

        query = "SELECT STRFTIME('%Y-%m-%d', cas_odevzdani) AS datum, SUM(cena*mnozstvi) AS castka,sbery.id_sberu FROM sbery JOIN polozka ON (sbery.id_sberu = polozka.id_sberu) JOIN ceny ON (ceny.id_ceny = polozka.id_ceny) WHERE id_uzivatele = '"+str(session['user'][0][1])+"' GROUP BY sbery.id_sberu ORDER BY datum DESC"
        cursor.execute(query)
        collections=cursor.fetchall()
        return render_template('my_collections.jinja2',collections=collections,payment=payment[0][0])

    else:
        return redirect('/profile/')

@app.route('/profile/zadani-sberu',methods=['GET','POST'])

def insert_collection() -> ResponseReturnValue:
    if "user" in session and (session['user'][0][2] == 1 or session['user'][0][2] == 2):
        connection = sqlite3.connect(DB_PATH)
        if request.method == 'POST':
            cursor = connection.cursor()
            query = "SELECT id_typu_materialu FROM typy_materialu"
            cursor.execute(query)
            results=cursor.fetchall()
            for i in results:
                material=(request.form.getlist(str(i[0])))
                print(material[0])
        cursor = connection.cursor()
        query = "SELECT id_typu_materialu, nazev FROM typy_materialu"
        cursor.execute(query)
        results=cursor.fetchall()
        return render_template('add_collections.jinja2',materials=results)
    else:
        return redirect('/profile/')

@app.route('/profile/zmena-ceniku',methods=['GET','POST'])
def change_pricelist() -> ResponseReturnValue:
    if "user" in session and session['user'][0][2] == 1:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        if request.method == 'POST':
            if request.form['button']== "search":
                query = "SELECT ceny.id_typu_materialu, nazev,datum_do,cena FROM ceny JOIN typy_materialu ON (ceny.id_typu_materialu = typy_materialu.id_typu_materialu) WHERE datum_od <= datetime('now') AND datum_do >= datetime('now') AND typy_materialu.nazev='"+str(request.form['search'])+"'"
                cursor.execute(query)
                results=cursor.fetchall()
                return render_template('pricelist-change.jinja2',catalogue=results)
            return redirect(url_for('edit_material', material_id=request.form['button']))
        query = "SELECT ceny.id_typu_materialu, nazev,datum_do,cena FROM ceny JOIN typy_materialu ON (ceny.id_typu_materialu = typy_materialu.id_typu_materialu) WHERE datum_od <= datetime('now') AND datum_do >= datetime('now')"
        cursor.execute(query)
        results=cursor.fetchall()
        return render_template('pricelist-change.jinja2',catalogue=results)
    else:
        return redirect('/profile/')
@app.route('/profile/zmena-ceniku/uprava-polozky',methods=['GET','POST'])
def edit_material() -> ResponseReturnValue:
    if "user" in session and session['user'][0][2] == 1:
        connection = sqlite3.connect(DB_PATH)
        if request.method == 'POST':
            query="UPDATE ceny SET datum_do = datetime('now') WHERE datum_od <= datetime('now') AND datum_do >= datetime('now') AND id_typu_materialu = '"+str(request.args['material_id'])+"'"
            connection.execute(query)
            connection.commit()
            now = datetime.utcnow()
            current_time = now.strftime(" %H:%M:%S")
            date = str(request.form['date-until']) + current_time
            print(date)
            query="INSERT INTO ceny (datum_od, datum_do, cena, id_typu_materialu) VALUES(datetime('now'), '"+date+"', '"+str(request.form['price'])+"', '"+str(request.args['material_id'])+"');"
            connection.execute(query)
            connection.commit()
            flash("Cena byla aktualizována", category="succcess")
            return redirect('/profile/')
        cursor = connection.cursor()
        query = "SELECT nazev FROM typy_materialu WHERE id_typu_materialu='"+str(request.args['material_id'])+"'"
        cursor.execute(query)
        results=cursor.fetchall()
        return render_template('edit_material.jinja2',material=results[0][0])
    else:
        return redirect('/profile/')


if __name__ == '__main__':
    app.run(debug=True)
