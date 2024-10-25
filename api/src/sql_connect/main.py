import logging
from datetime import datetime
from typing import Optional
import psycopg2
from passlib.context import CryptContext

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
import os

database_url = os.getenv('DATABASE_URL')

try:
    # Connect to PostgreSQL using the environment variable
    conn = psycopg2.connect(database_url)
    print("Database conn successful!",conn)

    params = {
            'host': 'db',
            'database': "slackpoc",
            'user': 'postgres',
            'password': 'postgres'
        }
    def create_database_if_not_exists(db_name):
                """Create a database if it does not exist."""
                conn = None
                try:    
                
                    
                    logging.info(f"Connecting to PostgreSQL to create database '{db_name}' if it does not exist...")
                    conn = psycopg2.connect(**params)
                    conn.autocommit = True

                    cursor = conn.cursor()
                    cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_name}'")
                    exists = cursor.fetchone()

                    if not exists:
                        cursor.execute(f"CREATE DATABASE {db_name};")
                        logging.info(f"Database '{db_name}' created successfully.")
                    else:
                        logging.info(f"Database '{db_name}' already exists.")

                    cursor.close()

                except (Exception, psycopg2.DatabaseError) as error:
                    logging.error(f"Error creating database: {error}")
                finally:
                    if conn:
                        conn.close()

    def create_table_if_not_exists(conn):
                """Create the sessionHistory table if it does not exist."""
                try:
                    cursor = conn.cursor()

                    create_table_query = '''
                        CREATE TABLE IF NOT EXISTS "sessionHistory" (
                            id SERIAL PRIMARY KEY,
                            session_id VARCHAR(255),
                            session_name VARCHAR(255),
                            human_query TEXT,
                            ai_response TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    '''
                    cursor.execute(create_table_query)
                    # main thing 
                    conn.commit()
                    logging.info(f"Table 'sessionHistory' checked/created successfully.")

                    cursor.close()

                except (Exception, psycopg2.DatabaseError) as error:
                    logging.error(f"Error creating table: {error}")
                    raise

    def insert_sessionllm_data(db_name, session_id,session_name, human_query, ai_response):
                conn = None
                try:
                    # Create the database if it doesn't exist
                    create_database_if_not_exists(db_name)

                    params = {
                        'host': 'db',
                        'database': db_name,
                        'user': 'postgres',
                        'password': 'postgres'
                    }
                    
                    logging.info(f"Connecting to PostgreSQL database '{db_name}' to insert data...")
                    conn = psycopg2.connect(**params)

                    # Create the table if it doesn't exist
                    create_table_if_not_exists(conn)

                    # Start a transaction
                    with conn:
                        cursor = conn.cursor()

                        insert_query = '''
                            INSERT INTO "sessionHistory" (session_id,session_name, human_query, ai_response, created_at)
                            VALUES (%s, %s, %s, %s,%s)
                            RETURNING id;
                        '''
                        created_at = datetime.now()

                        cursor.execute(insert_query, (session_id,session_name, human_query, ai_response, created_at))
                        inserted_id = cursor.fetchone()[0]
                        logging.info(f"Data inserted successfully with id: {inserted_id}")

                        cursor.close()

                    return inserted_id

                except (Exception, psycopg2.DatabaseError) as error:
                    logging.error(f"Error inserting data: {error}")
                finally:
                    if conn:
                        conn.close()


    def fetch_session_history(session_id: Optional[str] = None):
                
                """Fetch session history from the sessionHistory table."""
                params = {
                    'host': 'db',
                    'database': "slackpoc",
                    'user': 'postgres',
                    'password': 'postgres'
                }

                try:
                    logging.info(f"Connecting to PostgreSQL database '{params['database']}' to fetch session history...")
                    
                    # Connect to the PostgreSQL database
                    conn = psycopg2.connect(**params)
                    
                    # Ensure the table exists
                    create_table_if_not_exists(conn)

                    # Create a cursor
                    with conn.cursor() as cursor:
                        # Query to fetch all session history
                        if session_id:
                            query = """
                                SELECT session_id, session_name, human_query, ai_response, created_at
                                FROM "sessionHistory"
                                WHERE session_id = %s
                                ORDER BY created_at ASC
                                LIMIT 100;
                            """
                            cursor.execute(query, (session_id,))
                        else:
                            query = '''
                            SELECT 
                            session_id,
                            session_name,
                            human_query,
                            ai_response,
                            created_at
                            FROM (
                            SELECT 
                                session_id, 
                                session_name, 
                                human_query, 
                                ai_response, 
                                created_at,
                                ROW_NUMBER() OVER (PARTITION BY session_id ORDER BY created_at DESC) AS rn
                            FROM 
                                "sessionHistory"
                            ) AS subquery
                            WHERE rn = 1 
                            order by created_at desc
                            LIMIT 100


                            '''
                            cursor.execute(query)
                        
                        # Fetch all results
                        results = cursor.fetchall()
                        
                        # Format results into a list of dictionaries for easier handling
                        session_history = [
                            {
                                'session_id': row[0],
                                'session_name': row[1],
                                'human_query': row[2],
                                'ai_response': row[3],
                                'created_at': row[4]
                            }
                            for row in results
                        ]
                        
                        logging.info("Session history fetched successfully.")
                        conn.commit()
                        return session_history

                except (Exception, psycopg2.DatabaseError) as error:
                    logging.error(f"Error fetching session history: {error}")
                    return None  # Return None or handle as needed

                finally:
                    if conn:
                        conn.close()

    def create_table_if_not_exists_and_insert_initial_user(username: str, password: str):
            """Create users table if it does not exist and insert a user for the first time."""

            try:
                conn = psycopg2.connect(**params)
                with conn.cursor() as cursor:
                    # Create table if it does not exist
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS users (
                            username VARCHAR(50) PRIMARY KEY,
                            hashed_password VARCHAR(128) NOT NULL
                        );
                    """)
                    conn.commit()

                    # Check if any users exist in the table
                    cursor.execute("SELECT COUNT(*) FROM users;")
                    user_count = cursor.fetchone()[0]

                    if user_count == 0:
                        # If no users exist, insert the first user
                        hashed_password = pwd_context.hash(password)
                        cursor.execute("""
                            INSERT INTO users (username, hashed_password)
                            VALUES (%s, %s);
                        """, (username, hashed_password))
                        conn.commit()
                        logging.info(f"User '{username}' has been added as the first user.")
                    else:
                        logging.info("Users table exists and already contains data, no new user added.")
            except Exception as e:
                logging.error(f"Error creating table or inserting user: {e}")
            finally:
                if conn:
                    conn.close()


except Exception as e:
    print(f"Error connecting to the database: {e}")