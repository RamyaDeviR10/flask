from flask import Flask,render_template
app = Flask(__name__)


@app.route('/')
def hello_name():
	user='Aravidhan'
	return render_template('index.html', name = user)

if __name__ == '__main__':
    app.run(debug=True)