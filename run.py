from app import create_app, start_scheduler

if __name__ == "__main__":
    app = create_app()
    start_scheduler()
    app.run(host='0.0.0.0', port=5000, debug=True)