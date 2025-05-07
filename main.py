from app import create_app
from flask import Flask
from datetime import datetime
import locale

app = create_app()

# Number formatting
def format_number(value):
    try:
        value = float(value)
        return "{:,.0f}".format(value)
    except (ValueError, TypeError):
        return value

# Romanian date formatting
def ro_date(value):
    try:
        date_obj = datetime.strptime(value, "%Y-%m-%d")

        # Try setting Romanian locale
        try:
            locale.setlocale(locale.LC_TIME, "ro_RO.UTF-8")
        except locale.Error:
            MONTHS_RO = {
                "January": "ianuarie", "February": "februarie", "March": "martie",
                "April": "aprilie", "May": "mai", "June": "iunie",
                "July": "iulie", "August": "august", "September": "septembrie",
                "October": "octombrie", "November": "noiembrie", "December": "decembrie"
            }
            en_month = date_obj.strftime("%B")
            month = MONTHS_RO.get(en_month, en_month)
        else:
            month = date_obj.strftime("%B")

        return f"{date_obj.day} {month} {date_obj.year}"

    except Exception:
        return value
    
def todate(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except:
        return None

def now():
    return datetime.now()

# Register filters in Jinja
app.jinja_env.filters['format_number'] = format_number
app.jinja_env.filters['ro_date'] = ro_date
app.jinja_env.filters["todate"] = todate
app.jinja_env.globals["now"] = now

# Run app
if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
