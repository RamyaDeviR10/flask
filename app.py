from flask import Flask,render_template,jsonify,request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy import Column,Integer,String,Float,DateTime 
from sqlalchemy.sql import func
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity
)
import os
from flask_mail import Mail,Message

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///' + os.path.join(basedir,'recipe_db')
app.config['JWT_SECRET_KEY']='Login_secret'
app.config['MAIL_SERVER']='smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = 'f91063c2c56154'
app.config['MAIL_PASSWORD'] = 'c9c3093af1ed66'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False


db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt=JWTManager(app)
mail=Mail(app)



@app.cli.command('db_create')
def db_create():
	db.create_all()
	print('Database created!')

@app.cli.command('db_drop')
def db_drop():
	db.drop_all()
	print('Database dropped!')


@app.cli.command('db_seed')
def db_seed():
	Dosa=Recipe(recipe_name='Dosa',recipe_type='Breakfast/Dinner',shared_by='Ramya')
	Idly=Recipe(recipe_name='Idly',recipe_type='Breakfast/Dinner',shared_by='Aravindhan')
	Coffee=Recipe(recipe_name='Coffee',recipe_type='Snacks/Drinks',shared_by='Aisha')
	Tea=Recipe(recipe_name='Tea',recipe_type='Snacks/Drinks',shared_by='Anjun')

	db.session.add(Dosa)
	db.session.add(Idly)
	db.session.add(Coffee)
	db.session.add(Tea)

	test_user=User(first_name='Ramya',last_name='Devi',email='userramya@recipe.com',password='Recipe@10')

	db.session.add(test_user)
	db.session.commit()
	print('Database Seeded!')


@app.route('/')
def hello_name():
	user='Aravindhan/Ramya'
	return "Hello World!! Its a API testing page"

# Extracting from DB

@app.route('/recipes',methods=['GET'])
def get_recipes():
	recipes_list=Recipe.query.all()
	result = recipes_schema.dump(recipes_list)
	return jsonify(result)

@app.route('/register',methods=['POST'])
def register():
	email=request.form['email']
	test=User.query.filter_by(email=email).first()
	if test:
		return jsonify('Email already exists!')
	else:
		first_name=request.form['first_name']
		last_name=request.form['last_name']
		password=request.form['password']
		user=User(first_name=first_name,last_name=last_name,email=email,password=password)
		db.session.add(user)
		db.session.commit()
		return jsonify('User Created Successfully')

@app.route('/login',methods=['POST'])
def login():
	if request.is_json:		
		email=request.json['email']
		password=request.json['password']
	else:
		email=request.form['email']
		password=request.form['password']

	test = User.query.filter_by(email=email,password=password).first()

	if test:
		access_token=create_access_token(identity=email)
		return jsonify(message='Login Successfully!',access_token=access_token)
	else:
		return jsonify('Invalid Credentials')


@app.route('/retrieve_password/<email>',methods=['GET'])
def retrieve_password(email):
	user=User.query.filter_by(email=email).first()
	
	if user:
		msg=Message("Your password is " + user.password,sender="recipesadmin@recipe.com",recipients=[email])
		mail.send(msg)
		return jsonify('Password sent to registered Mail Id')
	else:
		return jsonify('Email Id doesnt exists!')

@app.route('/recipe_details/<recipe_name>',methods=['GET'])
def recipe_details(recipe_name):
	recipe=Recipe.query.filter_by(recipe_name=recipe_name).first()
	if recipe:
		result=recipe_schema.dump(recipe)
		return jsonify(result)
	else:
		return jsonify('Recipe doesnt exists!')

@app.route('/recipe_add',methods=['POST'])
@jwt_required
def add_recipe():
	recipe_name=request.form['recipe_name']
	shared_by=request.form['shared_by']
	test = Recipe.query.filter_by(recipe_name=recipe_name,shared_by=shared_by).first()
	print(test)
	if test:
		return jsonify('You have already posted this recipe on our website!'+ recipe_name)
	else:
		recipe_type=request.form['recipe_type']
		recipe=Recipe(recipe_name=recipe_name,recipe_type=recipe_type,shared_by=shared_by)
		db.session.add(recipe)
		db.session.commit()
		return jsonify('Successfully added the recipe '+ recipe_name)

@app.route('/recipe_update',methods=['PUT'])
def update_recipe():
	recipe_id=int(request.form['recipe_id'])
	recipe=Recipe.query.filter_by(recipe_id=recipe_id).first()

	if recipe:
		recipe.recipe_name=request.form['recipe_name']
		recipe.recipe_type=request.form['recipe_type']
		recipe.shared_by=request.form['shared_by']
		recipe.shared_on=func.now()
		db.session.commit()
		return jsonify('Recipe details updated Successfully '+recipe.recipe_name)
	else:
		return jsonify('Recipe doesnt exists!!')	


# Database Modules
class User(db.Model):
	__tablename__ ="user"
	uid = Column(Integer,primary_key=True)
	first_name = Column(String)
	last_name=Column(String)
	email=Column(String,unique=True)
	password=Column(String)

class Recipe(db.Model):
	__tablename__="Recipes"
	recipe_id=Column(Integer,primary_key=True,auto_increment=True)
	recipe_name=Column(String)
	recipe_type=Column(String)
	shared_by=Column(String)
	shared_on=Column(DateTime(timezone=True),default=func.now())

#class Ingredients(db.Model):


class UserSchema(ma.Schema):
	class Meta:
		fields=('id','first_name','last_name','email','password')

class RecipeSchema(ma.Schema):
	class Meta:
		fields=('recipe_id','recipe_name','recipe_type','shared_on','shared_by')

user_schema = UserSchema()
user_schema = UserSchema(many=True)

recipe_schema = RecipeSchema()
recipes_schema = RecipeSchema(many=True)

if __name__ == '__main__':
    app.run(debug=True)