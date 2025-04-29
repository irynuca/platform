from app import create_app
from flask import Flask

app = create_app()
def format_number(value):
    try:
        value = float(value)
        return "{:,.0f}".format(value)
    except (ValueError, TypeError):
        return value

app.jinja_env.filters['format_number'] = format_number

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)


  
