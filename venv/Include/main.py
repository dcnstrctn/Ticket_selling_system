from flask import Flask, request, json
from flask import request, render_template, session, redirect, url_for, flash
from flask_uploads import UploadSet, IMAGES, configure_uploads
from flask_bootstrap import Bootstrap
from flask_wtf import Form
from flask_sqlalchemy import SQLAlchemy
from wtforms import StringField, SubmitField, PasswordField, FloatField, HiddenField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms.validators import Required
import os
from werkzeug.utils import secure_filename
from datetime import timedelta
import MySQLdb

class LogForm(Form):
    email = StringField('Email', validators=[Required()])
    password = PasswordField('Password', validators=[Required()])
    log_in= SubmitField('Log in')

class RegisterForm(Form):
    email = StringField('Email', validators=[Required()])
    password = PasswordField('Password', validators=[Required()])
    username = StringField('Username', validators=[Required()])
    mobilephone = StringField('Mobile Phone', validators=[Required()])
    deliveryaddress = StringField('Delivery Address', validators=[Required()])
    reg = SubmitField('Register')

class PersonalForm(Form):
    password = PasswordField('Password', validators=[Required()])
    username = StringField('Username', validators=[Required()])
    mobilephone = StringField('Mobile Phone', validators=[Required()])
    deliveryaddress = StringField('Delivery Address', validators=[Required()])
    change = SubmitField('Change')

class SearchForm(Form):
    key = StringField("Ticket Name ( Use '-' / '+' to sort prices in descending / ascending order.)")
    search = SubmitField('Search')

images = UploadSet('images', IMAGES)
class AddForm(Form):
    ticketname = StringField('Name', validators=[Required()])
    time = StringField('Time', validators=[Required()])
    place = StringField('Place', validators=[Required()])
    price = FloatField('Price', validators=[Required()])
    description = StringField('Description', validators=[Required()])
    image = FileField('Image', validators=[FileRequired(),
        FileAllowed(images, 'Images only!')])
    post = SubmitField('Post')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:123456@localhost:3306/test?charset=utf8mb4'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['UPLOADED_IMAGES_DEST'] = 'some/path/'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=1)

configure_uploads(app, images)
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True)
    password = db.Column(db.String(64))
    username = db.Column(db.String(64))
    mobilephone = db.Column(db.String(64))
    deliveryaddress = db.Column(db.String(64))
    def __repr__(self):
        return '<User %r>' % self.username

class Ticket(db.Model):
    __tablename__ = 'ticket'
    id = db.Column(db.Integer, primary_key=True)
    ticketname = db.Column(db.String(64))
    time = db.Column(db.String(64))
    place = db.Column(db.String(64))
    price = db.Column(db.Integer)
    description = db.Column(db.String(200))
    remaining = db.Column(db.Integer)
    bitmap = db.Column(db.String(200))
    def __repr__(self):
        return '<Ticket %r>' % self.ticketname

class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id', ondelete='CASCADE'))
    bitmap = db.Column(db.String(200))
    num = db.Column(db.Integer)
    def __repr__(self):
        return '<Order %r>' % self.id

#db.drop_all()
#db.create_all()

@app.route('/', methods=['GET', 'POST'])
def check_log():
    form = LogForm()
    if form.validate_on_submit():
        x = User.query.filter_by(email=form.email.data, password=form.password.data).first()
        if(x==None):
            flash('Invalid username or password.')
        else:
            if(x.id==1):
                return redirect(url_for('hello_administrator'))
            else:
                session['username'] = x.username
                session['id'] = x.id
                return redirect(url_for('hello_user'))
    return render_template('check_log.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        x = User.query.filter_by(email=form.email.data).count()
        if(x==0):
            user = User(email=form.email.data, password=form.password.data, username=form.username.data, mobilephone=form.mobilephone.data, deliveryaddress=form.deliveryaddress.data)
            db.session.add(user)
            db.session.commit()
            flash('You can log in now.')
            return redirect(url_for('check_log'))
        else:
            flash('Change the email as it has been used.')
    return render_template('register.html', form=form)

@app.route('/personal', methods=['GET', 'POST'])
def personal():
    form = PersonalForm()
    temp = User.query.filter_by(id=session['id']).first()
    if form.validate_on_submit():
        temp.password = form.password.data
        temp.username = form.username.data
        temp.mobilephone = form.mobilephone.data
        temp.deliveryaddress = form.deliveryaddress.data
        db.session.add(temp)
        db.session.commit()
        session['username']=temp.username
        flash('Personal information has been changed.')
        return redirect(url_for('hello_user'))
    else:
        form.username.data = temp.username
        form.mobilephone.data = temp.mobilephone
        form.deliveryaddress.data = temp.deliveryaddress
    return render_template('personal.html', form=form, email=temp.email)

@app.route('/administrator')
def hello_administrator():
    return render_template('administrator_welcome.html')

@app.route('/user')
def hello_user():
    return render_template('user_welcome.html', username=session['username'])

def getImage(x):
    return "static/" + str(x) + ".jpg"

@app.route('/buyticket', methods=['GET', 'POST'])
def buyTicket():
    form = SearchForm()
    tickets = Ticket.query.all()
    if form.validate_on_submit():
        if (form.key.data == "+"):
            tickets = Ticket.query.order_by(Ticket.price.asc()).all()
        elif (form.key.data == "-"):
            tickets = Ticket.query.order_by(Ticket.price.desc()).all()
        elif (form.key.data != ""):
            tickets = Ticket.query.filter_by(ticketname=form.key.data).all()
    return render_template('buy_ticket.html', tickets=tickets, getImage=getImage, form=form)

@app.route('/ticketManagement', methods=['GET', 'POST'])
def ticketManagement():
    form = SearchForm()
    tickets = Ticket.query.all()
    if form.validate_on_submit():
        if(form.key.data=="+"):
            tickets = Ticket.query.order_by(Ticket.price.asc()).all()
        elif(form.key.data=="-"):
            tickets = Ticket.query.order_by(Ticket.price.desc()).all()
        elif (form.key.data != ""):
            tickets = Ticket.query.filter_by(ticketname=form.key.data).all()
    return render_template('ticket_management.html', tickets=tickets, getImage=getImage, form=form)

@app.route('/addTicket', methods=['GET', 'POST'])
def addTicket():
    form = AddForm()
    if form.validate_on_submit():
        ticket = Ticket(ticketname=form.ticketname.data, time=form.time.data, place=form.place.data, price=form.price.data, remaining=200, description=form.description.data, bitmap="0"*200)
        db.session.add(ticket)
        db.session.commit()
        image = form.image.data
        x = Ticket.query.filter_by(ticketname=form.ticketname.data).all()[-1]
        file_path = os.path.join('static', str(x.id)+".jpg")
        image.save(file_path)
        flash('New ticket has been added.')
        return redirect(url_for('ticketManagement'))
    return render_template('add_ticket.html', form=form)

@app.route('/delete', methods=['GET', 'POST'])
def delete():
    data = request.get_data().decode("utf-8")
    id = data.split("=")[1]
    temp = Ticket.query.filter_by(id=id).first()
    db.session.delete(temp)
    db.session.commit()
    file_path = os.path.join('static', str(id) + ".jpg")
    os.remove(file_path)
    flash('The ticket has been deleted.')
    return("yes")

@app.route('/cancel', methods=['GET', 'POST'])
def cancel():
    data = request.get_data().decode("utf-8")
    id = data.split("=")[1]
    temp = Order.query.filter_by(id=id).first()
    ticket = Ticket.query.filter_by(id=temp.ticket_id).first()
    ticket.remaining += temp.num
    new_bitmap = ""
    for i in range(200):
        if temp.bitmap[i] == '1':
            new_bitmap += '0'
        else:
            new_bitmap += ticket.bitmap[i]
    ticket.bitmap = new_bitmap
    db.session.add(ticket)
    db.session.delete(temp)
    db.session.commit()
    flash('The order has been cancelled.')
    return("yes")

@app.route('/chooseSeat/<id>', methods=['GET', 'POST'])
def choose_seat(id):
    temp = Ticket.query.filter_by(id=id).first()
    session['choose_id'] = id
    return render_template('choose_seat.html', bitmap=temp.bitmap)

@app.route('/buy', methods=['GET', 'POST'])
def buy():
    data = request.get_data().decode("utf-8")
    bitmap = data.split("=")[1]
    print(bitmap)
    order = Order(user_id=session['id'], ticket_id=session['choose_id'], bitmap = bitmap, num=0)
    temp = Ticket.query.filter_by(id=session['choose_id']).first()
    new_bitmap = ""
    for i in range(200):
        if bitmap[i] == '1':
            new_bitmap += '1'
            order.num += 1
            temp.remaining = temp.remaining - 1
        else:
            new_bitmap += temp.bitmap[i]
    temp.bitmap = new_bitmap
    db.session.add(order)
    db.session.add(temp)
    db.session.commit()
    flash('The tickets have been bought.')
    return("yes")

@app.route('/seatInformation/<id>', methods=['GET', 'POST'])
def seatInformation(id):
    temp = Order.query.filter_by(id=id).first()
    return render_template('seat_information.html', bitmap=temp.bitmap)

@app.route('/seatInformation_ad/<id>', methods=['GET', 'POST'])
def seatInformation_ad(id):
    temp = Order.query.filter_by(id=id).first()
    return render_template('seat_information_ad.html', bitmap=temp.bitmap)

@app.route('/modifyTicket/<id>', methods=['GET', 'POST'])
def modify(id):
    form = AddForm()
    temp = Ticket.query.filter_by(id=id).first()
    form.post.label.text = "Modify"
    if form.validate_on_submit():
        temp.ticketname=form.ticketname.data
        temp.time=form.time.data
        temp.place=form.place.data
        temp.price=form.price.data
        temp.description=form.description.data
        db.session.add(temp)
        db.session.commit()
        image = form.image.data
        file_path = os.path.join('static', str(id) + ".jpg")
        image.save(file_path)
        flash('The ticket has been modified.')
        return redirect(url_for('ticketManagement'))
    else:
        form.ticketname.data = temp.ticketname
        form.time.data = temp.time
        form.place.data = temp.place
        form.price.data = temp.price
        form.description.data = temp.description
    return render_template('modify_ticket.html', form=form)

@app.route('/orderManagement', methods=['GET', 'POST'])
def orderManagement():
    orders = Order.query.all()
    return render_template('order_management.html', orders=orders, getImage=getImage, Ticket=Ticket, User=User)

@app.route('/myorder', methods=['GET', 'POST'])
def myOrder():
    orders = Order.query.filter_by(user_id=session['id']).all()
    return render_template('my_order.html', orders=orders, getImage=getImage, Ticket=Ticket, User=User)

@app.route('/statistics', methods=['GET', 'POST'])
def statistics():
    total = Order.query.count()
    if(total==0):
        flash('There is no order.')
        return redirect(url_for('hello_administrator'))
    else:
        income = 0
        orders = Order.query.all()
        for order in orders:
            income = income + Ticket.query.filter_by(id=order.ticket_id).first().price * order.num
        mysqldb = MySQLdb.connect("localhost", "root", "123456", "test", charset='utf8')
        cursor = mysqldb.cursor()
        sql = "SELECT id from ticket ORDER BY remaining ASC"
        cursor.execute(sql)
        results = cursor.fetchall()
        best_sell = results[0]
        sql = "select user.id, sum(ticket.price * `order`.num) as num from user, ticket, `order` where ticket.id = order.ticket_id and user.id = `order`.user_id group by id order by num DESC"
        cursor.execute(sql)
        results = cursor.fetchall()
        big_user = results[0]
        mysqldb.close()
        return render_template('statistics.html', total=total, income=income, best_sell=best_sell, Ticket=Ticket, big_user=big_user, User=User)
if __name__ == '__main__':
    app.run(debug=True, host = 'localhost')
