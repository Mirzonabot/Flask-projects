from email import message
import email
from operator import methodcaller
from unicodedata import name
from flask import Flask, abort, render_template, request,session,redirect,url_for
from forms import SignUp, LogIn, PetForm
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import uuid as uuid
import os 


app = Flask(__name__)




app.config['SECRET_KEY'] = 'dfewfew123213rwdsgert34tgfd1234trgfsd'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.db'

UPLOAD_FOLDER = 'static/images/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db = SQLAlchemy(app)

class Pet(db.Model):
    __tablename__ = 'pet'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String, unique = True)
    age = db.Column(db.String)
    bio = db.Column(db.String)
    pet_pic = db.Column(db.String(), nullable=True)
    
    posted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    posted_by = db.relationship("User",foreign_keys = [posted_by_id])

    adopted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    abopted_by = db.relationship("User",foreign_keys = [adopted_by_id])
    
    




class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key = True)
    full_name = db.Column(db.String)
    email = db.Column(db.String, unique = True)
    password = db.Column(db.String)
    pets = db.relationship('Pet', foreign_keys = [Pet.posted_by_id], backref = 'poster')
    pets_adopted = db.relationship('Pet', foreign_keys = [Pet.adopted_by_id], backref = 'adopter')
    

db.create_all()


team = User(full_name = "Pet Rescue Team", email = "team@petrescue.co", password = "adminpass")
db.session.add(team)

# Commit changes in the session
try:
    db.session.commit()
except Exception as e: 
    db.session.rollback()



# Create all pets
nelly = Pet(name = "Nelly", age = "5 weeks", bio = "I am a tiny kitten rescued by the good people at Paws Rescue Center. I love squeaky toys and cuddles.")
yuki = Pet(name = "Yuki", age = "8 months", bio = "I am a handsome gentle-cat. I like to dress up in bow ties.")
basker = Pet(name = "Basker", age = "1 year", bio = "I love barking. But, I love my friends more.")
mrfurrkins = Pet(name = "Mr. Furrkins", age = "5 years", bio = "Probably napping.")

# Add all pets to the session
db.session.add(nelly)
db.session.add(yuki)
db.session.add(basker)
db.session.add(mrfurrkins)
try:
    db.session.commit()
except Exception as e: 
    db.session.rollback()

@app.route("/")
def home():
    pets = Pet.query.all()
    # print(session['user'].full_name)
    

    return render_template("home.html",pets = pets)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/signup",methods=["GET","POST"])
def signup():
    form = SignUp()

    if form.validate_on_submit():
        new_user = User(full_name = form.full_name.data, email = form.email.data, password = form.password.data)
        db.session.add(new_user)
        try:
            db.session.commit()
        except Exception as e:
            print(e)
            db.session.rollback()
            return render_template("signup.html", form = form, message = "This Email already exists in the system! Please Log in instead.")
        finally:
            db.session.close()
        return render_template("signup.html",message="Successfully registered!")
    return render_template("signup.html",form = form)

@app.route("/login",methods=["GET","POST"])
def login():
    form = LogIn()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data, password = form.password.data).first()
        if user is None:
            return render_template("login.html", form = form, message = "Wrong Credentials. Please Try Again.")
        else:
            session['user'] = user.id
            session['full_name'] = user.full_name
            return render_template("login.html", message = "Successfully Logged In!")
    
    return render_template("login.html",form = form)


@app.route("/logout")
def logout():
    if 'user' in session:
        session.pop('user')
        session.pop('full_name')
    return redirect(url_for('home', _scheme='http', _external=True))
    





@app.route("/details/<int:pet_id>",methods=["GET","POST"])
def pet_details(pet_id):
    """View function for Showing Details of Each Pet.""" 
    form = PetForm()
    pet = Pet.query.get(pet_id)
    if pet is None: 
        abort(404, description="No Pet was Found with the given ID")
    if form.validate_on_submit():
        pet.name = form.name.data
        pet.age = form.age.data
        pet.bio = form.bio.data
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return render_template("details.html", pet = pet, form = form, message = "A Pet with this name already exists!")
    return render_template("details.html", pet = pet, form = form)

@app.route("/delete/<int:pet_id>",methods=["GET","POST"])
def delete_pet(pet_id):
    pet = Pet.query.get(pet_id)
    if pet is None: 
        abort(404, description="No Pet was Found with the given ID")
    os.remove("static/images/"+pet.pet_pic)
    db.session.delete(pet)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
    return redirect(url_for('home', _scheme='http', _external=True))
@app.route("/adopt/<int:pet_id>",methods=["GET","POST"])
def adopt(pet_id):
    pet = Pet.query.get(pet_id)
    pet.adopted_by_id = session['user']

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
    return redirect(url_for('home', _scheme='http', _external=True))

@app.route("/add_new_pet",methods = ["GET","POST"])
def addPet():
    form = PetForm()
    
    print(session['user'])
    if form.validate_on_submit():
        pic = request.files['pet_pic']
        pic_name = secure_filename(pic.filename)
        pic_name = str(uuid.uuid1()) + "_" + pic_name

        pic.save(os.path.join(UPLOAD_FOLDER, pic_name))
        
        new_Pet = Pet(name = form.name.data, age = form.age.data, pet_pic = pic_name, bio = form.bio.data,posted_by_id=session['user'])
        db.session.add(new_Pet)
        try:
            db.session.commit()
        except Exception as e:
            print(e)
            db.session.rollback()
            return render_template("home.html", form = form, message = "This pet already exists!")
        finally:
            db.session.close()
        return redirect(url_for('home', _scheme='http', _external=True))
    return render_template('newpet.html',form = form)

if __name__ == "__main__":
    app.run(debug = True, host = "0.0.0.0", port = 3000)
