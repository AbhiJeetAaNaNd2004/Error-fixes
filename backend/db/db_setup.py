import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import bcrypt

# --- IMPORTANT ---
# Replace these with your actual PostgreSQL connection details.
DB_SETTINGS = {
    "dbname": "face_recognition_db",
    "user": "postgres",
    "password": "password",
    "host": "localhost",
    "port": "5432"
}

# --- Hashed password for the default super admin ---
# We hash the password 'admin123' here so we don't store it in plain text.
SUPER_ADMIN_PASSWORD = "admin123"
hashed_super_admin_password = bcrypt.hashpw(
    SUPER_ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt()
).decode('utf-8')


# SQL statements to create the tables. The order is important.
CREATE_TABLE_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS roles (
        id SERIAL PRIMARY KEY,
        role_name VARCHAR(50) UNIQUE NOT NULL,
        is_protected BOOLEAN NOT NULL DEFAULT false
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS departments (
        id SERIAL PRIMARY KEY,
        department_name VARCHAR(100) UNIQUE NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS departments (
        id SERIAL PRIMARY KEY,
        department_name VARCHAR(100) UNIQUE NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        employee_id VARCHAR(50) UNIQUE NOT NULL,
        employee_name VARCHAR(255) NOT NULL,
        username VARCHAR(100) UNIQUE NOT NULL,
        hashed_password VARCHAR(255) NOT NULL,
        role_id INTEGER REFERENCES roles(id),
        department_id INTEGER REFERENCES departments(id),
        department_id INTEGER REFERENCES departments(id), 
        enrollment_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN NOT NULL DEFAULT true
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS cameras (
        id SERIAL PRIMARY KEY,
        camera_name VARCHAR(100) NOT NULL,
        camera_type VARCHAR(20) NOT NULL,
        stream_url VARCHAR(512),
        username VARCHAR(100),
        encrypted_password VARCHAR(255),
        resolution_w INTEGER,
        resolution_h INTEGER,
        fps INTEGER,
        gpu_id INTEGER,
        is_active BOOLEAN NOT NULL DEFAULT true
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS camera_tripwires (
        id SERIAL PRIMARY KEY,
        camera_id INTEGER NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
        tripwire_name VARCHAR(100) NOT NULL,
        direction VARCHAR(20) NOT NULL,
        position FLOAT NOT NULL,
        spacing FLOAT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS face_embeddings (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        embedding BYTEA NOT NULL,
        source_image BYTEA NOT NULL,
        embedding_type VARCHAR(20) NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS attendance_records (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        event_type VARCHAR(10) NOT NULL,
        event_timestamp TIMESTAMP NOT NULL,
        camera_id INTEGER REFERENCES cameras(id),
        source VARCHAR(20) NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS system_settings (
        setting_key VARCHAR(100) PRIMARY KEY,
        setting_value VARCHAR(255) NOT NULL,
        data_type VARCHAR(20) NOT NULL
    );
    """,
        """
    ALTER TABLE face_embeddings ADD COLUMN IF NOT EXISTS is_profile_picture BOOLEAN DEFAULT FALSE;
    """,
    # --- Data Insertion and Trigger Setup ---
    """
    INSERT INTO roles (role_name) VALUES ('employee'), ('admin'), ('super_admin') ON CONFLICT (role_name) DO NOTHING;
    """,
    """
    UPDATE roles SET is_protected = true WHERE role_name = 'super_admin';
    """,
    """
    INSERT INTO departments (department_name) VALUES ('General') ON CONFLICT (department_name) DO NOTHING;
    """,
    """
    INSERT INTO system_settings (setting_key, setting_value, data_type) VALUES
        ('recognition_threshold', '0.6', 'float'),
        ('detection_threshold', '0.5', 'float'),
        ('match_threshold', '0.8', 'float'),
        ('face_quality_threshold', '0.65', 'float'),
        ('embedding_update_cooldown', '10', 'integer'),
        ('max_updates_before_rebuild', '20', 'integer')
    ON CONFLICT (setting_key) DO NOTHING;
    """,
    # --- NEW: Insert the default, non-removable super admin user ---
    f"""
    INSERT INTO users (employee_id, employee_name, username, hashed_password, role_id, department_id, is_active)
    VALUES (
        'SUPER001',
        'Super Admin',
        'superadmin',
        '{hashed_super_admin_password}',
        (SELECT id FROM roles WHERE role_name = 'super_admin'),
        (SELECT id FROM departments WHERE department_name = 'General'),
        true
    ) ON CONFLICT (username) DO NOTHING;
    """,
    # --- Trigger to protect the super_admin role ---
    """
    CREATE OR REPLACE FUNCTION prevent_protected_role_deletion()
    RETURNS TRIGGER AS $$
    BEGIN
        IF OLD.is_protected = true THEN
            RAISE EXCEPTION 'Cannot delete protected role: %', OLD.role_name;
        END IF;
        RETURN OLD;
    END;
    $$ LANGUAGE plpgsql;
    """,
    """
    DROP TRIGGER IF EXISTS trg_prevent_protected_role_deletion ON roles;
    """,
    """
    CREATE TRIGGER trg_prevent_protected_role_deletion
    BEFORE DELETE ON roles
    FOR EACH ROW EXECUTE FUNCTION prevent_protected_role_deletion();
    """,
    # --- NEW: Trigger to protect the super_admin user account ---
    """
    CREATE OR REPLACE FUNCTION prevent_super_admin_deletion()
    RETURNS TRIGGER AS $$
    BEGIN
        IF OLD.username = 'superadmin' THEN
            RAISE EXCEPTION 'Cannot delete the primary super admin account. This account is protected.';
        END IF;
        RETURN OLD;
    END;
    $$ LANGUAGE plpgsql;
    """,
    """
    DROP TRIGGER IF EXISTS trg_prevent_super_admin_deletion ON users;
    """,
    """
    CREATE TRIGGER trg_prevent_super_admin_deletion
    BEFORE DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION prevent_super_admin_deletion();
    """
]

def create_database_if_not_exists():
    conn = None
    try:
        conn = psycopg2.connect(user=DB_SETTINGS['user'], password=DB_SETTINGS['password'], host=DB_SETTINGS['host'], port=DB_SETTINGS['port'])
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute(sql.SQL("SELECT 1 FROM pg_database WHERE datname = %s"), (DB_SETTINGS['dbname'],))
        if not cur.fetchone():
            print(f"Database '{DB_SETTINGS['dbname']}' does not exist. Creating...")
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_SETTINGS['dbname'])))
            print(f"Database '{DB_SETTINGS['dbname']}' created successfully.")
        else:
            print(f"Database '{DB_SETTINGS['dbname']}' already exists.")
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error while trying to create database: {error}")
        exit()
    finally:
        if conn is not None:
            conn.close()

def create_tables_and_triggers():
    conn = None
    try:
        print(f"\nConnecting to '{DB_SETTINGS['dbname']}' to configure schema...")
        conn = psycopg2.connect(
            dbname=DB_SETTINGS['dbname'],
            user=DB_SETTINGS['user'],
            password=DB_SETTINGS['password'],
            host=DB_SETTINGS['host'],
            port=DB_SETTINGS['port']
        )
        cur = conn.cursor()
        print("Configuring tables, triggers, and default users...")
        for statement in CREATE_TABLE_STATEMENTS:
            cur.execute(statement)
        conn.commit()
        print("\nDatabase setup completed successfully!")
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error while configuring schema: {error}")
    finally:
        if conn is not None:
            conn.close()
            print("Database connection closed.")

if __name__ == '__main__':
    create_database_if_not_exists()
    create_tables_and_triggers()
