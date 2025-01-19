from flask import Flask, render_template
import os

app = Flask(__name__, template_folder=os.path.abspath('app/templates'))

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
