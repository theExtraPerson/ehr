
from application import create_app

app = create_app()

# with app.app_context():
#     print(app.jinja_env.list_templates())

if __name__ == '__main__':
    app.run(debug=True)