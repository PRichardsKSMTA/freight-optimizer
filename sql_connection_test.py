import pyodbc

conn_str = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=ksm-ksmta-sqlsrv-001.database.windows.net;"
    "DATABASE=KSMTA;"
    "UID=dataAutomationUser;"
    "PWD=Vector-Steel-Y3llow12!;"
)

try:
    with pyodbc.connect(conn_str, timeout=5) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT GETDATE()")
        row = cursor.fetchone()
        print("Connected! Server time is:", row[0])
except Exception as e:
    print("Connection failed:", e)
