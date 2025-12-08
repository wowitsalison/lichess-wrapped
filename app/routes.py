from app import app

@app.route('/')
@app.route('/index')
def index():
    return "this is the home page"