from dotenv import load_dotenv
load_dotenv()
from flask import Flask
from flask_cors import CORS   


from auth.routes import auth_bp
from backend.routes.file import files_bp
from backend.routes.me import me_bp



app = Flask(__name__)
CORS(app)
app.register_blueprint(auth_bp)
app.register_blueprint(files_bp)
app.register_blueprint(me_bp)


@app.route('/')
def home():
    return 'flask is running'


if __name__ == '__main__':
    app.run(debug=True)
