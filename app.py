from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from selenium_scrape_containers import scrape_and_save



def create_app():
    app = Flask(__name__)
    app.secret_key = '1234'

    # Register route blueprints
    from routes.runsheet import runsheet_bp
    from routes.home import home_bp
    from routes.customer import customer_bp
    from routes.pickup_routes import pickup_bp
    from routes.incoming_routes import incoming_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(runsheet_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(pickup_bp)
    app.register_blueprint(incoming_bp)

    # Register Dash app
    from dash_apps.statistics_dash import init_dashboard
    init_dashboard(app)

    return app


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(scrape_and_save, 'cron', hour='7,12,16,20', minute=0)
    scheduler.start()


if __name__ == "__main__":
    app = create_app()
    start_scheduler()
    app.run(host='0.0.0.0', port=5000, debug=True)



