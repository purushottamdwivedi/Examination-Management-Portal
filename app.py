"""Application entry point: creates the Flask app and wires everything together."""
from flask import Flask, render_template
import config
from database import init_db, close_db
from utils import current_user, today
from routes import auth, admin, examiner, student, api

def create_app():
    app = Flask(__name__)
    app.secret_key = config.SECRET_KEY
    app.teardown_appcontext(close_db)

    for module in (auth, admin, examiner, student, api):
        app.register_blueprint(module.bp)

    @app.context_processor
    def inject():
        return dict(user=current_user(), today=today(), EXAM_TYPES=config.EXAM_TYPES, EXAM_STATUS=config.EXAM_STATUS)

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('error.html', msg='Access denied.'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('error.html', msg='Page not found.'), 404

    init_db()
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
