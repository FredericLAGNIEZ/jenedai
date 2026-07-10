
# def create_postgres_table():
#     '''
#     Create the cpd_incidents table in Postgres DB (cpd_db) if it doesn't exist.
#     '''
#     # establish connection to DB
#     conn = psycopg2.connect(
#         host="localhost",
#         port="5433",
#         database="cpd_db",
#         user=os.getenv("POSTGRES_USER"),
#         password=os.getenv("POSTGRES_PASSWORD")
#     )

#     # create cursor object to execute SQL
#     cur = conn.cursor()
    
#     # execute query to create the table
#     create_table_query = '''
#         CREATE TABLE IF NOT EXISTS cpd_incidents (
#             date_time TIMESTAMP,
#             id INTEGER PRIMARY KEY,
#             type TEXT,
#             subtype TEXT,
#             location TEXT,
#             description TEXT,
#             last_updated TIMESTAMP,
#             year INTEGER,
#             month INTEGER,
#             day INTEGER,
#             hour INTEGER, 
#             minute INTEGER,
#             second INTEGER
#         )
#     '''
#     cur.execute(create_table_query)

#     # commit changes
#     conn.commit()

#     # close cursor and connection
#     cur.close()
#     conn.close()

# @task
# def load_into_postgres(df):
#     '''
#     Loads the transformed data passed in as a DataFrame 
#     into the 'cpd_incidents' table in our Postgres instance.
#     '''
#     # create table to insert data into as necessary
#     create_postgres_table()

#     # create Engine object to connect to DB
#     engine = create_engine())
        
#     # # insert data into Postgres DB into the 'cpd_incidents' table
#     # df.to_sql('cpd_incidents', engine, if_exists='replace')
