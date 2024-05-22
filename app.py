from flask import Flask, render_template, request, redirect, url_for, session, json, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import mysql.connector
import random
import string
from werkzeug.utils import secure_filename
import os
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta
from flask import flash

app = Flask(__name__)

app.secret_key = '123456789'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'fkl25220212'
app.config['MYSQL_DB'] = 'rolemoderndb'

app.config['UPLOAD_FOLDER'] = 'static/roomuploads'

Allowed_Extensions = set(['png', 'jpg', 'jpeg', 'gif'])

mysql = MySQL(app)
bcrypt = Bcrypt(app)

@app.route('/')
def landing():
    return render_template('landing.html')

def generate_adminID():
    random_int = ''.join(random.choices(string.digits, k=6))
    random_string = ''.join(random.choices(string.ascii_uppercase, k=6))

    adminid = f'{random_int}{random_string}'
    return adminid



@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'name' in request.form and 'email' in request.form and 'password' in request.form:
        AdminID = generate_adminID()
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM systemadmin WHERE email = %s', (email,))
        account = cursor.fetchone()
        
        if account:
            msg = 'Email already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', name):
            msg = 'Username must contain only characters and numbers!'
        elif not name or not password or not email:
            msg = 'Please fill out the form!'
        else:
            hashed_password = bcrypt.generate_password_hash(password)
            
            cursor.execute('INSERT INTO systemadmin(AdminID, FullName, Email, Password) VALUES (%s, %s, %s, %s)', (AdminID, name, email, hashed_password,))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        msg = 'Please fill out the form!'
    
    return render_template('register.html', msg=msg)

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:

        email = request.form['email']
        password = request.form['password']

        #print(request.form)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM systemadmin WHERE Email = %s', (email,))
        account = cursor.fetchone()

        #print("Acount:", account)
        if account and bcrypt.check_password_hash(account['Password'] , password):
            session['loggedin'] = True
            session['AdminID'] = account['AdminID']
            session['name'] = account['FullName']
            session['email'] = account['Email']
            # Redirect to home page
            return redirect(url_for('dashboard'))
        else:
            msg = 'Incorrect username/password!'
    return render_template('login.html', msg=msg)

@app.route('/logout')
def logout():
   session.pop('loggedin', None)
   session.pop('AdminID', None)
   session.pop('name', None)
   session.pop('email', None)
   return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        cur = mysql.connection.cursor()
        cur.execute('SELECT SUM(TotalCost) AS TODAYS_TOTAL FROM payment WHERE DATE(DateTime) = CURDATE()')
        sales = cur.fetchone()
        cur.execute('SELECT SUM(Occupants) AS TODAYS_POPULATION FROM reservation WHERE DATE(CheckInDate) = CURDATE()')
        population = cur.fetchone()

        cur.execute('SELECT COUNT(*) AS TODAYS_CHECKIN FROM reservation WHERE DATE(CheckInDate) = CURDATE()')
        checkin = cur.fetchone()
        cur.execute('SELECT COUNT(*) AS SYS_ADMIN FROM systemadmin')
        sysadmin = cur.fetchone()
        
        return render_template('dashboard.html', sales=sales, population = population, checkin = checkin, sysadmin = sysadmin)
    return redirect(url_for('login'))



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Allowed_Extensions

def get_room_id():
    random_int = ''.join(random.choices(string.digits, k=3))
    random_string = ''.join(random.choices(string.ascii_uppercase, k=3))

    roomid = f'{random_int}{random_string}'
    return roomid

@app.route('/roomx')
def allrooms():
     if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM room')
        room = cursor.fetchall()
        return render_template('room.html', room = room)
     return redirect(url_for('login'))

@app.route('/roomx', methods=['GET', 'POST'])
def room():
    msg = ''
    if 'loggedin' in session:

        if request.method == 'POST':
            description = request.form['description']
            maxcapacity = request.form['maxcapacity']
            price = request.form['price']
            roomadmin = request.form['roomadmin']
            file = request.files['roomimage']
            RoomNumber = get_room_id()


            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            filename = secure_filename(file.filename)
            if file and allowed_file(file.filename):
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                filenameimage = file.filename
                cursor.execute('INSERT INTO room(RoomNumber, Description, MaximumCapacity, UnitPrice, RoomAdmin, ImagePath) VALUES (%s, %s, %s, %s, %s, %s)', (RoomNumber, description, maxcapacity, price, roomadmin, filenameimage,))
                mysql.connection.commit()
                msg = 'You have successfully registered!'
            return redirect(url_for('room'))
        elif request.method == 'POST':
            msg = 'Please Fill The Form'
        
    

        return render_template('room.html', msg = msg)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/checkin', methods=['GET', 'POST'])
def checkin():
    if 'loggedin' in session:   
       cursor = mysql.connection.cursor()
       cursor.execute('SELECT * FROM room WHERE Status = "AVAILABLE" ')
       data = cursor.fetchall()
       return render_template('checkin.html',  students=data)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))



@app.route('/room')
def Index():
    if 'loggedin' in session:
      cur = mysql.connection.cursor()
      cur.execute("SELECT  * FROM room")
      
      data = cur.fetchall()
      cur.execute("SELECT FullName FROM roomadmin")
      admin = cur.fetchall()
      cur.close()
      return render_template('room.html', students=data, admin=admin)
    return redirect(url_for('login'))


@app.route('/insert', methods = ['POST'])
def insert():
    if 'loggedin' in session:
        if request.method == "POST":
            flash("Data Inserted Successfully")

            description = request.form['description']
            maxcapacity = request.form['maxcapacity']
            price = request.form['price']
            roomadmin = request.form['roomadmin']
            file = request.files['roomimage']
            RoomNumber = get_room_id()


            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            filename = secure_filename(file.filename)
            if file and allowed_file(file.filename):
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                filenameimage = file.filename
                cursor.execute('INSERT INTO room(RoomNumber, Description, MaximumCapacity, UnitPrice, RoomAdmin, ImagePath) VALUES (%s, %s, %s, %s, %s, %s)', (RoomNumber, description, maxcapacity, price, roomadmin, filenameimage,))
                mysql.connection.commit()
                
            mysql.connection.commit()
            return redirect(url_for('Index'))
    return redirect(url_for('login'))




@app.route('/delete/<string:id_data>', methods = ['GET'])
def delete(id_data):
    if 'loggedin' in session:
        flash("Record Has Been Deleted Successfully")
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM room WHERE RoomID=%s", (id_data,))
        mysql.connection.commit()
        return redirect(url_for('Index'))
    return redirect(url_for('login'))





@app.route('/update',methods=['POST','GET'])
def update():
    if 'loggedin' in session:
        if request.method == 'POST':
            id_data = request.form['id']
            description = request.form['description']
            maxcapacity = request.form['maxcapacity']
            unitprice = request.form['unitprice']
            cur = mysql.connection.cursor()
            cur.execute("""
                UPDATE room
                SET Description=%s, MaximumCapacity=%s, UnitPrice=%s
                WHERE RoomID=%s
                """, (description, maxcapacity, unitprice, id_data))
            flash("Data Updated Successfully")
            mysql.connection.commit()
            return redirect(url_for('Index'))
    return redirect(url_for('login'))
    
def get_invoice():
    intro = 'INV-'
    random_int = ''.join(random.choices(string.digits, k=6))
    random_string = ''.join(random.choices(string.ascii_uppercase, k=6))

    roomid = f'{intro}{random_int}{random_string}'
    return roomid
    
    
@app.route('/reserve', methods = ['POST'])
def reserve():
    if 'loggedin' in session:
        if request.method == 'POST':
            roomid = request.form['roomid']
            customer = request.form['idnumber']
            checkin = datetime.strptime(request.form['checkin'], '%Y-%m-%d')
            checkout = datetime.strptime(request.form['checkout'], '%Y-%m-%d')
            occupants = request.form['occupants']
            invoice = get_invoice()

            cursor = mysql.connection.cursor()
            total_nights = (checkout - checkin).days
            #room_rate = 100  
            

            # Update room status to 'reserved' in the database
            cur = mysql.connection.cursor()
            cur.execute("UPDATE room SET status='RESERVED' WHERE RoomID=%s", (roomid,))

            cursor.execute('SELECT UnitPrice FROM room WHERE RoomID = %s', (roomid))
            cost_per_night = cursor.fetchone()[0]
            total_cost = total_nights * cost_per_night

            # Save reservation details to the database
            cur.execute("INSERT INTO reservation (Customer, InvoiceNumber, RoomID, CheckInDate, CheckOutDate, TotalCost, Occupants) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (customer, invoice, roomid, checkin, checkout, total_cost, occupants))

            mysql.connection.commit()
            cursor.close()
            return redirect('payment')
    return redirect(url_for('login'))
    
    
@app.route('/payment', methods = ['GET','POST'])
def payment():
    if 'loggedin' in session:
      cur = mysql.connection.cursor()
      cur.execute("SELECT  * FROM reservation WHERE Stage='PENDING'")
      data = cur.fetchall()
      cur.close()
      return render_template('payment.html', students=data )
    return redirect(url_for('login'))

def get_reciept():
    intro = '   RMH-'
    random_int = ''.join(random.choices(string.digits, k=7))
    random_string = ''.join(random.choices(string.ascii_uppercase, k=7))

    roomid = f'{intro}{random_int}{random_string}'
    return roomid

@app.route('/makepayment', methods=['GET', 'POST'])
def makepayment():
    if 'loggedin' in session:
        cur = mysql.connection.cursor()
        invoice = request.form['invoice']
        total_cost = request.form['total']
        amount_paid = float(request.form['paid'])
        balance = request.form['balance']
        method = request.form['method']
        description = request.form['description']
        transaction = get_reciept()

        if request.method == 'POST':
            cur.execute('INSERT INTO payment(TransactionNumber, InvoiceNumber, TotalCost, Recieved, Balance, PaymentMethod, Description, RecievedBy)'
                        'VALUES(%s, %s, %s, %s, %s, %s, %s, %s)',(transaction, invoice, total_cost, amount_paid, balance, method, description, session['AdminID']) )
            mysql.connection.commit()
            if float(balance) >= 0:
                cur.execute('UPDATE reservation SET Stage = "COMPLETED" WHERE InvoiceNumber = %s', (invoice,))
                mysql.connection.commit()
            cur.close()
            return redirect('/fetchlatest')
        cur.close()
        return redirect('payment')
    return redirect(url_for('login'))


    return redirect(url_for('login'))

@app.route('/invoice', methods=['GET', 'POST'])
def invoice():
    if 'loggedin' in session:
        if request.method == 'POST':
            invoice = request.form['invoice']
            cur = mysql.connection.cursor()
            cur.execute(""" SELECT reservation.* , payment.*
                        FROM reservation
                        LEFT JOIN payment ON reservation.InvoiceNumber = payment.InvoiceNumber
                        WHERE reservation.InvoiceNumber = %s
                        ORDER BY payment.DateTime DESC
                        LIMIT 1
                        """, (invoice, ))
            combined_data = cur.fetchone()
            cur.close()

        return render_template('invoice.html', data = combined_data)

    return redirect(url_for('login'))

@app.route('/fetchlatest')
def get_invoices():
    cur = mysql.connection.cursor()
    cur.execute('SELECT InvoiceNumber FROM payment ORDER BY DateTime DESC LIMIT 10')
    data = cur.fetchall()
    cur.close()
    return render_template('test.html', data = data)


@app.route('/invoice-print')
def invoiceprint():
    if 'loggedin' in session:
        invoice = 'INV-907551OKVRYV'
        cur = mysql.connection.cursor()
        cur.execute(""" SELECT reservation.* , payment.*
                    FROM reservation
                    LEFT JOIN payment ON reservation.InvoiceNumber = payment.InvoiceNumber
                    WHERE reservation.InvoiceNumber = %s
                    ORDER BY payment.DateTime DESC
                    LIMIT 1
                    """, (invoice, ))
        combined_data = cur.fetchone()
        cur.close()
        return render_template('invoiceprint.html', data = combined_data)
        
    return redirect(url_for('login'))


@app.route('/expired-reservation', methods=['GET','POST'])
def expired_reservation():
    cur = mysql.connection.cursor()
    cur.execute(""" SELECT * FROM reservation WHERE CheckOutDate <= NOW() AND Stage != 'CHECKED-OUT' """)
    data = cur.fetchall()
    cur.close()
    return render_template('checkout.html', students=data )

@app.route('/transactions', methods=['GET', 'POST'])
def transactions():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM payment ')
        data = cursor.fetchall()
        cursor.execute("SELECT SUM(TotalCost) AS TOTAL_SALES FROM payment")
        total = cursor.fetchone()
        cursor.execute("SELECT MAX(TotalCost) AS TOTAL_SALES FROM payment")
        maximum = cursor.fetchone()
        cursor.execute("SELECT MIN(TotalCost) AS TOTAL_SALES FROM payment")
        minimum = cursor.fetchone()
        cursor.execute("SELECT AVG(TotalCost) AS TOTAL_SALES FROM payment")
        avg = cursor.fetchone()
        cursor.execute("SELECT SUM(TotalCost) AS TOTAL_SALES FROM payment WHERE PaymentMethod = 'CASH' ")
        cash = cursor.fetchone()
        cursor.execute("SELECT SUM(TotalCost) AS TOTAL_SALES FROM payment WHERE PaymentMethod = 'MOBILE-MONEY' ")
        mobile = cursor.fetchone()
        cursor.execute("SELECT SUM(TotalCost) AS TOTAL_SALES FROM payment WHERE PaymentMethod = 'BANK-TRANSFER' ")
        bank = cursor.fetchone()
        cursor.execute("SELECT SUM(TotalCost) AS TOTAL_SALES FROM payment WHERE PaymentMethod = 'ONLINE-WALLET' ")
        online = cursor.fetchone()
        return render_template('transactions.html',  data=data,total = total, maximum = maximum, minimum = minimum, avg=avg, cash = cash, mobile = mobile, bank = bank, online = online)
    
    return redirect(url_for('login'))

@app.route('/check-transactions', methods=['GET', 'POST'])
def check_transactions():
    if 'loggedin' in session:
        if request.method == 'POST':
            start = datetime.strptime(request.form['start'], '%Y-%m-%d')
            
            end = datetime.strptime(request.form['end'], '%Y-%m-%d')
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM payment WHERE DATE(DateTime) BETWEEN %s AND %s", (start, end, ))
            data = cursor.fetchall()
            cursor.execute("SELECT SUM(TotalCost) AS TOTAL_SALES FROM payment WHERE DATE(DateTime) BETWEEN %s AND %s", (start, end, ))
            total = cursor.fetchone()
            cursor.execute("SELECT MAX(TotalCost) AS TOTAL_SALES FROM payment WHERE DATE(DateTime) BETWEEN %s AND %s", (start, end, ))
            maximum = cursor.fetchone()
            cursor.execute("SELECT MIN(TotalCost) AS TOTAL_SALES FROM payment WHERE DATE(DateTime) BETWEEN %s AND %s", (start, end, ))
            minimum = cursor.fetchone()
            cursor.execute("SELECT AVG(TotalCost) AS TOTAL_SALES FROM payment WHERE DATE(DateTime) BETWEEN %s AND %s", (start, end, ))
            avg = cursor.fetchone()
            cursor.execute("SELECT SUM(TotalCost) AS TOTAL_SALES FROM payment WHERE DATE(DateTime) BETWEEN %s AND %s AND PaymentMethod = 'CASH' ", (start, end, ))
            cash = cursor.fetchone()
            cursor.execute("SELECT SUM(TotalCost) AS TOTAL_SALES FROM payment WHERE DATE(DateTime) BETWEEN %s AND %s AND PaymentMethod = 'MOBILE-MONEY' ", (start, end, ))
            mobile = cursor.fetchone()
            cursor.execute("SELECT SUM(TotalCost) AS TOTAL_SALES FROM payment WHERE DATE(DateTime) BETWEEN %s AND %s AND PaymentMethod = 'BANK-TRANSFER' ", (start, end, ))
            bank = cursor.fetchone()
            cursor.execute("SELECT SUM(TotalCost) AS TOTAL_SALES FROM payment WHERE DATE(DateTime) BETWEEN %s AND %s AND PaymentMethod = 'ONLINE-WALLET' ", (start, end, ))
            online = cursor.fetchone()
            return render_template('transactions.html',  data=data, total = total, maximum = maximum, minimum = minimum, avg=avg, cash = cash, mobile = mobile, bank = bank, online = online)
    
    return redirect(url_for('login'))

@app.route('/reservation-report', methods=['GET', 'POST'])
def reservation_report():
    if 'loggedin' in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT  * FROM reservation")
        data = cur.fetchall()
        cur.close()
        return render_template('reservationreport.html', data=data )
    return redirect(url_for('login'))

@app.route('/check-reservation-report', methods=['GET', 'POST'])
def check_reservation_report():
    if 'loggedin' in session:
         if request.method == 'POST':
            start = datetime.strptime(request.form['start'], '%Y-%m-%d')
            
            end = datetime.strptime(request.form['end'], '%Y-%m-%d')
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM reservation WHERE DATE(CheckInDate) BETWEEN %s AND %s", (start, end, ))
            data = cursor.fetchall()

            return render_template('reservationreport.html',  data=data)
    return redirect(url_for('login'))

@app.route('/reserved-rooms', methods=['GET', 'POST'])
def reserved_rooms():
    if 'loggedin' in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT  * FROM room WHERE Status='RESERVED' ")
        data = cur.fetchall()
        cur.close()
        return render_template('reservedrooms.html', data=data )
        
    
    return redirect(url_for('login'))

@app.route('/unreserved-rooms', methods=['GET', 'POST'])
def unreserved_rooms():
    if 'loggedin' in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT  * FROM room WHERE Status='AVAILABLE' ")
        data = cur.fetchall()
        cur.close()
        return render_template('unreserved.html', data=data )
    
    return redirect(url_for('login'))

@app.route('/mycustomer', methods=['GET', 'POST'])
def mycustomer():
    if 'loggedin' in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT  * FROM customer")
        data = cur.fetchall()
        cur.close()
        return render_template('mycustomer.html', data=data )
    
    return redirect(url_for('login'))

@app.route('/customer', methods=['GET', 'POST'])
def customer():
    if 'loggedin' in session:
      cur = mysql.connection.cursor()
      cur.execute("SELECT  * FROM customer")
      data = cur.fetchall()
      cur.execute('SELECT IDNumber FROM customer')
      mydata = cur.fetchall()
      cur.close()
      return render_template('customer.html', students=data, mydata = mydata )
    return redirect(url_for('login'))

def get_customer_number():
    intro = 'CUST-'
    random_int = ''.join(random.choices(string.digits, k=4))
    random_string = ''.join(random.choices(string.ascii_uppercase, k=4))

    roomid = f'{intro}{random_int}{random_string}'
    return roomid

@app.route('/insert-customer', methods = ['POST'])
def insertcustomer():
    if 'loggedin' in session:
        if request.method == "POST":
            flash("Data Inserted Successfully")

            name = request.form['name']
            identification = request.form['id']
            idnumber = request.form['idnumber']
            phone = request.form['phone']
            email = request.form['email']
            city = request.form['city']
            customernumber = get_customer_number()


            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('INSERT INTO customer(CustomerNumber, FullName, Identification, IDNumber, Phone, Email, City) VALUES (%s, %s, %s, %s, %s, %s, %s)', (customernumber, name, identification, idnumber, phone, email, city, ))
            mysql.connection.commit()
                
            mysql.connection.commit()
            return redirect(url_for('customer'))
    return redirect(url_for('login'))


@app.route('/customerupdate',methods=['POST','GET'])
def customerupdate():
    if 'loggedin' in session:
        if request.method == 'POST':
            id_data = request.form['id']
            name = request.form['name']
            phone = request.form['phone']
            email = request.form['email']
            city = request.form['city']
            cur = mysql.connection.cursor()
            cur.execute("""
                UPDATE customer
                SET FullName=%s, Phone=%s, Email=%s, City = %s
                WHERE CustomerID=%s
                """, (name, phone, email, city, id_data))
            flash("Data Updated Successfully")
            mysql.connection.commit()
            return redirect(url_for('customer'))
    return redirect(url_for('login'))

@app.route('/checkout/<string:id_data>', methods = ['GET'])
def checkout(id_data):
    if 'loggedin' in session:
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM reservation WHERE ReservationID = %s', (id_data,))
        reservation = cur.fetchone()

        cur.execute('UPDATE reservation SET Stage = "CHECKED-OUT" WHERE ReservationID = %s', (id_data, ))
        mysql.connection.commit()

        room_id = str(reservation[3])
        cur.execute('UPDATE room SET Status = "AVAILABLE" WHERE RoomID = %s', (room_id))
        mysql.connection.commit()

        cur.close()
        return redirect(url_for('expired_reservation'))


    return redirect(url_for('login'))

@app.route('/systemadmin', methods=['GET', 'POST'])
def systemadmin():
    if 'loggedin' in session:
      cur = mysql.connection.cursor()
      cur.execute("SELECT  * FROM systemadmin")
      data = cur.fetchall()
      cur.close()
      return render_template('users.html', students=data )
    return redirect(url_for('login'))

@app.route('/adelete/<string:id_data>', methods = ['GET'])
def adelete(id_data):
    if 'loggedin' in session:
        flash("Record Has Been Deleted Successfully")
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM systemadmin WHERE AdminID=%s", (id_data,))
        mysql.connection.commit()
        return redirect(url_for('systemadmin'))
    return redirect(url_for('login'))

@app.route('/roomadmin', methods=['GET', 'POST'])
def roomadmin():
    if 'loggedin' in session:
      cur = mysql.connection.cursor()
      cur.execute("SELECT  * FROM roomadmin")
      data = cur.fetchall()
      cur.close()
      return render_template('roomadmin.html', students=data )
    return redirect(url_for('login'))


@app.route('/insertradmin', methods = ['POST'])
def insertradmin():
    if 'loggedin' in session:
        if request.method == "POST":
            flash("Data Inserted Successfully")

            name = request.form['name']
            phone = request.form['phone']
            email = request.form['email']


            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('INSERT INTO roomadmin(FullName, Phone, Email ) VALUES (%s, %s, %s)', (name, phone, email, ))
            mysql.connection.commit()
                
            mysql.connection.commit()
            return redirect(url_for('roomadmin'))
    return redirect(url_for('login'))

@app.route('/rdelete/<string:id_data>', methods = ['GET'])
def rdelete(id_data):
    if 'loggedin' in session:
        flash("Record Has Been Deleted Successfully")
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM roomadmin WHERE RAdminID=%s", (id_data,))
        mysql.connection.commit()
        return redirect(url_for('roomadmin'))
    return redirect(url_for('login'))

@app.route('/radminupdate',methods=['POST','GET'])
def radminupdate():
    if 'loggedin' in session:
        if request.method == 'POST':
            id_data = request.form['id']
            name = request.form['name']
            phone = request.form['phone']
            email = request.form['email']
            cur = mysql.connection.cursor()
            cur.execute("""
                UPDATE roomadmin
                SET FullName=%s, Phone=%s, Email=%s
                WHERE RAdminID=%s
                """, (name, phone, email, id_data))
            flash("Data Updated Successfully")
            mysql.connection.commit()
            return redirect(url_for('roomadmin'))
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET','POST'])
def profile():
    if 'loggedin' in session:
      cur = mysql.connection.cursor()
      cur.execute("SELECT  * FROM systemadmin WHERE AdminID = %s", (session['AdminID'],))
      data = cur.fetchone()
      cur.close()
      return render_template('profile.html', student=data )

    return redirect(url_for('login'))

def get_user_from_session():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM systemadmin WHERE AdminID = %s', (session['AdminID'], ))
    user = cur.fetchone()
    cur.close()
    return user

@app.route('/changeassword', methods=['GET', 'POST'])
def changepassword():
    if request.method == 'POST':
        user = get_user_from_session()
        oldpassword = request.form['oldpassword']
        newpassword = request.form['newpassword']
        confirmpassword = request.form['confirmpassword']

        if user and bcrypt.check_password_hash(user[3], oldpassword):
            if newpassword == confirmpassword:
                hashed_password = bcrypt.generate_password_hash(newpassword).decode('utf-8')

                cur = mysql.connection.cursor()
                cur.execute('UPDATE systemadmin SET Password = %s WHERE AdminID = %s', (hashed_password, session['AdminID']))
                mysql.connection.commit()
                cur.close()
                flash('Password change successful', 'success')
                return render_template('profile.html')
            else:
                flash('New password do not match', 'error')
        else:
            flash('invalid Old Password', 'error')

    return render_template('profile.html')



if __name__ == "__main__":
   app.run(debug=True)

   