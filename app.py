from flask import Flask
from routes.runsheet import runsheet_bp
from routes.home import home_bp
from routes.customer import customer_bp

app = Flask(__name__)
app.secret_key = '1234'


app.register_blueprint(home_bp)
app.register_blueprint(runsheet_bp)
app.register_blueprint(customer_bp)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
