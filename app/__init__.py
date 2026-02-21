import os
from flask import Flask, render_template
from .routes import bp


def create_web_app():
    """Create and configure the Flask web application."""
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
    )

    app.register_blueprint(bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    return app
