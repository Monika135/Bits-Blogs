from flask import redirect, url_for
from main import create_app

app = create_app()

@app.route('/')
def home():
    return redirect(url_for('auth.login_page'))

if __name__ == '__main__':
    app.run(debug = True, port = 5001)