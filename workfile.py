from flask import Flask, render_template, redirect, request, url_for, session,flash
from sqlalchemy import  DateTime,desc
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import expression
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
import os

import base64
from os.path import join, dirname, realpath
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1
app.secret_key="hello user"
UPLOAD_FOLDER = 'static/images'
#UPLOADS_PATH = join(dirname(realpath(__file__)), 'static/uploads/..')
ALLOWED_EXTENSIONS = set(['jpeg', 'jpg', 'png', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:''@localhost/user'


db = SQLAlchemy(app)
migrate = Migrate(app, db)
class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80),nullable=False,unique=True)
    email = db.Column(db.String(120),nullable=False,unique=True)
    password = db.Column(db.String(80),nullable=False)
    register_date = db.Column(DateTime, default=datetime.now)
    productsR = db.relationship('Product', backref="userproduct",
                                cascade="all, delete",  passive_deletes=True,lazy=True)

    def __str__(self):
        return "User(%d, %s, %s, %s )" % (
            self.id, self.username, self.password, self.email )



class Product(db.Model):
    __tablename__ = "product"
    prod_id = db.Column(db.Integer, primary_key=True)
    prod_name = db.Column(db.String(50), nullable=False)
    prod_price = db.Column(db.Float, nullable=False)
    prod_image = db.Column(db.String(200), nullable=False)
    prod_description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    product_date = db.Column(db.Date)
    modified_date = db.Column(db.Date)
    #prod_stock = db.Column(db.Boolean,server_default="false")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"))
    #def __str__(self):
     #   return "Product(%d, %s, %s)" % (
      #      self.prod_id, self.prod_name, self.prod_description )

    def to_dict(self):
        return {
            'prod_id':self.prod_id,
            'user_id':self.user_id,
            'prod_name': self.prod_name,
            'prod_image':self.prod_image,
            'prod_price': self.prod_price,
            'prod_description': self.prod_description,
            'created_at': self.created_at,
            'product_date': self.product_date,
            'modified_date': self.modified_date
        }
db.create_all()
@app.route('/api/data')
def data():
    return {'data': [product.to_dict() for product in  Product.query.filter_by(user_id=session['userid']).all()]}


@app.route('/pythonlogin/',methods=['GET','POST'])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        login = User.query.filter_by(username=username, password=password).first()
        if login is not None:
            session['username'] = username
            session['userid']= login.id
            return redirect(url_for("home"))
        else:
            return redirect(url_for("login"))
    elif request.method == 'GET':
        if 'username' in session:
            return redirect(url_for("home"))

    return render_template("login.html")

@app.route('/pythonlogin/register/',methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        password= request.form['password']
        register = User(username=username, email=email, password=password)
        db.session.add(register)
        db.session.commit()
        return redirect(url_for("login"))
    elif request.method =="GET":
        if 'username'in session:

            return redirect(url_for("home"))

    return render_template("registration.html")

@app.route('/pythonlogin/home',methods=['GET','POST'])
def home():
    if 'username' in session:
        #page = request.args.get('page', 1, type=int)
        #products=Product.query.filter_by(user_id=session['userid']).all()
        products = Product.query.filter_by(user_id=session['userid']).order_by(desc(Product.created_at)) \
            #.paginate(per_page=2, page=page)

        return render_template("home.html",products=products)
    elif 'username' not in session:
        return redirect(url_for("login"))

    else:
        render_template("login.html")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/static/images/<filename>')
def send_uploaded_file(filename=''):
    from flask import send_from_directory
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/pythonlogin/product',methods=['GET','POST'])
def product():
    if 'username' in session:
        if request.method == 'POST':
            prod_name = request.form['prod_name']
            prod_price = request.form['prod_price']
            prod_description = request.form['prod_description']
            prod_stock = request.form['prod_stock']
            product_date = request.form['product_date']
            modified_date = request.form['modified_date']
            userid = session['userid']
            prod_image = request.files['prod_img']
            if prod_image and allowed_file(prod_image.filename):
                filename = secure_filename(prod_image.filename)
                prod_image.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
                prod_save = Product(prod_name=prod_name, prod_price=prod_price, prod_image=prod_image.filename,
                                    prod_description=prod_description, product_date=product_date,
                                    modified_date=modified_date, user_id=userid)
                db.session.add(prod_save)
                db.session.commit()
                return redirect(url_for('home'))
    elif request.method == 'GET':
        if 'username' not in session:
            return redirect(url_for("login"))

    return render_template("product.html")
@app.route("/pythonlogin/update/<int:prod_id>",methods=['GET','POST'])
def update(prod_id):
    if 'username' in session:
        product = Product.query.filter_by(prod_id=prod_id).one()

        if request.method=="POST":
            product.prod_name = request.form['prod_name']
            product.prod_price = request.form['prod_price']
            product.prod_description = request.form['prod_description']
            product.modified_date = request.form['modified_date']
            product.product_date = request.form['product_date']
            # check profile pic
            if request.files['prod_img']:
                product.prod_image = request.files['prod_img']
                #grab image nsme
                filename = secure_filename(product.prod_image.filename)
                pic_name=str(filename)
                # save img
                saver = request.files['prod_img']
                # change file name to str after save
                product.prod_image=pic_name
                saver.save(os.path.join(app.config['UPLOAD_FOLDER'],pic_name))
            db.session.commit()
        else:
            return render_template("edit.html",product=product)
    return redirect(url_for("login"))



@app.route("/pythonlogin/delete/<int:prod_id>",methods=['GET','POST'])
def delete(prod_id):
    if 'username'in session:
        delproduct= Product.query.filter_by(prod_id=prod_id).one()
        db.session.delete(delproduct)
        db.session.commit()
        return redirect(url_for("home"))
    else:
        return redirect(url_for("login"))
@app.route('/pythonlogin/home2',methods=['GET','POST'])
def home2():
    if 'username' in session:
        page = request.args.get('page', 1, type=int)
        #products=Product.query.filter_by(user_id=session['userid']).all()
        products = Product.query.filter_by(user_id=session['userid']).order_by(desc(Product.created_at))\
           .paginate(per_page=2, page=page)

        return render_template("home2.html",products=products)
    elif 'username' not in session:
        return redirect(url_for("login"))

    else:
        render_template("login.html")


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response
@app.route("/pythonlogin/logout")
def logout():
    session.pop('username',None)
    return redirect(url_for('login'))
if __name__ == '__main__':
    app.run(debug=True)


