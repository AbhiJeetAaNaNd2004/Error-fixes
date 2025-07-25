import psycopg2
import numpy as np
from psycopg2 import sql, pool
from contextlib import contextmanager
import threading
import logging

# Configure logging for database operations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# It's best practice to load these from a config file or environment variables
DB_SETTINGS = {
    "dbname": "face_recognition_db",
    "user": "postgres",
    "password": "password",
    "host": "localhost",
    "port": 5432
}

# Global connection pool
_connection_pool = None
_pool_lock = threading.Lock()

def initialize_connection_pool(min_connections=5, max_connections=20):
    """Initialize the database connection pool."""
    global _connection_pool
    with _pool_lock:
        if _connection_pool is None:
            try:
                _connection_pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=min_connections,
                    maxconn=max_connections,
                    **DB_SETTINGS
                )
                logger.info(f"Database connection pool initialized with {min_connections}-{max_connections} connections")
            except Exception as e:
                logger.error(f"Failed to initialize connection pool: {e}")
                raise

def get_connection_pool():
    """Get the connection pool, initializing if necessary."""
    global _connection_pool
    if _connection_pool is None:
        initialize_connection_pool()
    return _connection_pool

@contextmanager
def get_db_connection():
    """Context manager for database connections with proper error handling."""
    pool = get_connection_pool()
    conn = None
    try:
        conn = pool.getconn()
        if conn:
            yield conn
        else:
            raise psycopg2.OperationalError("Could not get connection from pool")
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        if conn:
            conn.rollback()
        raise  # Re-raise the exception for proper HTTP error responses
    finally:
        if conn:
            pool.putconn(conn)

def get_db_connection_legacy():
    """Legacy function for backward compatibility. Use get_db_connection() context manager instead."""
    logger.warning("Using legacy get_db_connection(). Consider migrating to context manager.")
    try:
        pool = get_connection_pool()
        return pool.getconn()
    except Exception as e:
        logger.error(f"Error getting legacy connection: {e}")
        return None

def camera_exists(stream_url: str) -> bool:
    """
    Checks if a camera with the given stream_url already exists in the database.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM cameras WHERE stream_url = %s;", (stream_url,))
                return cur.fetchone() is not None
    except Exception as error:
        logger.error(f"Error checking if camera exists: {error}")
        raise

# ROLES & DEPARTMENTS (Admin/Setup Tables)
def get_all_roles():
    """READ all available roles."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, role_name FROM roles ORDER BY id;")
                return cur.fetchall()
    except Exception as error:
        logger.error(f"Error getting all roles: {error}")
        raise

def update_user_department(user_id, department_id):
    """UPDATE a user's department."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET department_id = %s WHERE id = %s;", (department_id, user_id))
                conn.commit()
    except Exception as error:
        logger.error(f"Error updating user department: {error}")
        raise

def get_all_departments():
    """READ all available departments."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, department_name FROM departments ORDER BY department_name;")
                return cur.fetchall()
    except Exception as error:
        logger.error(f"Error getting all departments: {error}")
        raise

def add_department(department_name):
    """CREATE a new department."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO departments (department_name) VALUES (%s) RETURNING id;", (department_name,))
                dept_id = cur.fetchone()[0]
                conn.commit()
                return dept_id
    except Exception as error:
        logger.error(f"Error adding department: {error}")
        raise

def update_department(department_id, new_name):
    """UPDATE a department's name."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE departments SET department_name = %s WHERE id = %s;", (new_name, department_id))
                conn.commit()
    except Exception as error:
        logger.error(f"Error updating department: {error}")
        raise

def delete_department(department_id):
    """DELETE a department. Fails if users are assigned to it."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM departments WHERE id = %s;", (department_id,))
                conn.commit()
    except Exception as error:
        logger.error(f"Error deleting department (ensure no users are assigned): {error}")
        raise

# USERS (Employee Management)
def get_user_for_login(username):
    """
    NEW: Fetches user data needed for login verification.
    Returns user_id, role_name, and hashed_password.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT u.id, r.role_name, u.hashed_password
                    FROM users u
                    JOIN roles r ON u.role_id = r.id
                    WHERE u.username = %s AND u.is_active = true;
                """, (username,))
                return cur.fetchone()
    except Exception as error:
        logger.error(f"Error fetching user for login: {error}")
        raise

def add_user(employee_id, employee_name, username, hashed_password, role_id, department_id):
    """CREATE a new user."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (employee_id, employee_name, username, hashed_password, role_id, department_id) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;",
                    (employee_id, employee_name, username, hashed_password, role_id, department_id)
                )
                user_id = cur.fetchone()[0]
                conn.commit()
                return user_id
    except Exception as error:
        logger.error(f"Error adding user: {error}")
        raise

def get_all_users_with_details():
    """READ all users with their role, department, and face embedding count."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # UPDATED: This query now joins face_embeddings and counts them
                                 cur.execute("""
                     SELECT
                         u.id, u.employee_id, u.employee_name, u.username,
                         r.role_name, d.department_name, d.id as department_id, u.is_active,
                         COUNT(fe.id) as face_count
                     FROM users u
                     JOIN roles r ON u.role_id = r.id
                     JOIN departments d ON u.department_id = d.id
                     LEFT JOIN face_embeddings fe ON u.id = fe.user_id
                     GROUP BY u.id, r.role_name, d.department_name, d.id
                     ORDER BY u.employee_name;
                 """)
                return cur.fetchall()
    except Exception as error:
        logger.error(f"Error getting all users with details: {error}")
        raise

def update_user(employee_id, update_data):
    """UPDATE a user's details. update_data is a dict of columns to change."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                set_query = ", ".join([f"{key} = %s" for key in update_data.keys()])
                query = sql.SQL("UPDATE users SET {} WHERE employee_id = %s;").format(sql.SQL(set_query))
                values = list(update_data.values())
                values.append(employee_id)
                cur.execute(query, tuple(values))
                conn.commit()
    except Exception as error:
        logger.error(f"Error updating user: {error}")
        raise

def delete_user(employee_id):
    """DELETE a user. ON DELETE CASCADE handles related records."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM users WHERE employee_id = %s;", (employee_id,))
                conn.commit()
    except Exception as error:
        logger.error(f"Error deleting user: {error}")
        raise

# FACE EMBEDDINGS (Face Recognition Data)
def add_face_embedding(user_id, embedding_vector, image_bytes, embedding_type='enrollment'):
    """
    CREATE a new face embedding record.
    If the type is 'update', it enforces a rolling limit of 20 per user.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # If this is a dynamic update, manage the rolling window of embeddings
                if embedding_type == 'update':
                    # Count existing 'update' embeddings for the user
                    cur.execute(
                        "SELECT count(*) FROM face_embeddings WHERE user_id = %s AND embedding_type = 'update';",
                        (user_id,)
                    )
                    count = cur.fetchone()[0]
                    if count >= 20:
                        cur.execute(
                            """
                            DELETE FROM face_embeddings
                            WHERE id = (
                                SELECT id FROM face_embeddings
                                WHERE user_id = %s AND embedding_type = 'update'
                                ORDER BY created_at ASC
                                LIMIT 1
                            );
                            """,
                            (user_id,)
                        )
                embedding_binary = embedding_vector.astype(np.float32).tobytes()
                cur.execute(
                    "INSERT INTO face_embeddings (user_id, embedding, source_image, embedding_type) VALUES (%s, %s, %s, %s) RETURNING id;",
                    (user_id, embedding_binary, image_bytes, embedding_type))
                embedding_id = cur.fetchone()[0]
                conn.commit()
                return embedding_id
    except Exception as error:
        logger.error(f"Error adding face embedding: {error}")
        raise

def get_all_face_embeddings():
    """READ all active users' embeddings and labels for the recognition model."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT u.employee_id, fe.embedding
                    FROM face_embeddings fe
                    JOIN users u ON fe.user_id = u.id
                    WHERE u.is_active = true;
                """)
                records = cur.fetchall()
                return np.array([np.frombuffer(rec[1], dtype=np.float32) for rec in records]), [rec[0] for rec in records]
    except Exception as error:
        logger.error(f"Error getting all face embeddings: {error}")
        raise

def get_user_face_images(user_id):
    """READ all source images for a specific user."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, source_image FROM face_embeddings WHERE user_id = %s ORDER BY created_at DESC;", (user_id,))
                return cur.fetchall()
    except Exception as error:
        logger.error(f"Error getting user face images: {error}")
        raise

def set_profile_picture(user_id: int, embedding_id: int):
    """Sets a specific embedding as the profile picture for a user."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # First, unset any other profile picture for this user
                cur.execute(
                    "UPDATE face_embeddings SET is_profile_picture = FALSE WHERE user_id = %s;",
                    (user_id,)
                )
                # Then, set the new profile picture
                cur.execute(
                    "UPDATE face_embeddings SET is_profile_picture = TRUE WHERE id = %s AND user_id = %s;",
                    (embedding_id, user_id)
                )
                conn.commit()
                return True
    except Exception as error:
        logger.error(f"Error setting profile picture: {error}")
        raise

def get_profile_picture(user_id: int):
    """Retrieves the source image for the user's designated profile picture."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT source_image FROM face_embeddings WHERE user_id = %s AND is_profile_picture = TRUE LIMIT 1;",
                    (user_id,)
                )
                record = cur.fetchone()
                return record[0] if record else None
    except Exception as error:
        logger.error(f"Error getting profile picture: {error}")
        raise

def delete_face_embedding(embedding_id):
    """
    DELETE a specific face embedding and return its source image.
    Returns the binary image data on success, None on failure.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Use RETURNING to get the source_image of the deleted row
                cur.execute("DELETE FROM face_embeddings WHERE id = %s RETURNING source_image;", (embedding_id,))
                deleted_row = cur.fetchone()
                if deleted_row:
                    return deleted_row[0]
                conn.commit()
                return None
    except Exception as error:
        logger.error(f"Error deleting face embedding: {error}")
        raise

# CAMERAS & TRIPWIRES (System Configuration)
def add_camera(name, cam_type, stream_url, res_w, res_h, fps, gpu_id, user=None, pw=None):
    """CREATE a new camera."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO cameras (camera_name, camera_type, stream_url, resolution_w, resolution_h, fps, gpu_id, username, encrypted_password) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;",
                    (name, cam_type, stream_url, res_w, res_h, fps, gpu_id, user, pw))
                cam_id = cur.fetchone()[0]
                conn.commit()
                return cam_id
    except Exception as error:
        logger.error(f"Error adding camera: {error}")
        raise

def get_camera_configs():
    """READ all active camera and tripwire configurations."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, camera_name, camera_type, stream_url, username, encrypted_password, resolution_w, resolution_h, fps, gpu_id FROM cameras WHERE is_active = true ORDER BY id;")
                camera_records = cur.fetchall()
                cameras = []
                for rec in camera_records:
                    cam_id, name, cam_type, url, user, pw, w, h, fps, gpu = rec
                    camera_config = { "id": cam_id, "camera_name": name, "camera_type": cam_type, "stream_url": url, "username": user, "encrypted_password": pw, "resolution_w": w, "resolution_h": h, "fps": fps, "gpu_id": gpu, "tripwires": [] }
                    cur.execute("SELECT id, tripwire_name, direction, position, spacing FROM camera_tripwires WHERE camera_id = %s;", (cam_id,))
                    tripwire_records = cur.fetchall()
                    for tw_rec in tripwire_records:
                        camera_config["tripwires"].append({ "id": tw_rec[0], "name": tw_rec[1], "direction": tw_rec[2], "position": tw_rec[3], "spacing": tw_rec[4] })
                    cameras.append(camera_config)
                return cameras
    except Exception as error:
        logger.error(f"Error getting camera configs: {error}")
        raise

def update_camera(camera_id, update_data):
    """UPDATE a camera's details."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                set_query = ", ".join([f"{key} = %s" for key in update_data.keys()])
                query = sql.SQL("UPDATE cameras SET {} WHERE id = %s;").format(sql.SQL(set_query))
                values = list(update_data.values())
                values.append(camera_id)
                cur.execute(query, tuple(values))
                conn.commit()
    except Exception as error:
        logger.error(f"Error updating camera: {error}")
        raise

def delete_camera(camera_id):
    """DELETE a camera. ON DELETE CASCADE handles tripwires."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM cameras WHERE id = %s;", (camera_id,))
                conn.commit()
    except Exception as error:
        logger.error(f"Error deleting camera: {error}")
        raise

def add_tripwire(camera_id, name, direction, position, spacing):
    """CREATE a new tripwire for a camera."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO camera_tripwires (camera_id, tripwire_name, direction, position, spacing) VALUES (%s, %s, %s, %s, %s) RETURNING id;",
                    (camera_id, name, direction, position, spacing)
                )
                tw_id = cur.fetchone()[0]
                conn.commit()
                return tw_id
    except Exception as error:
        logger.error(f"Error adding tripwire: {error}")
        raise

def update_tripwire(tripwire_id, update_data):
    """UPDATE a tripwire's details. update_data is a dict of columns to change."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Build the SET part of the SQL query dynamically
                set_query = ", ".join([f"{key} = %s" for key in update_data.keys()])
                query = sql.SQL("UPDATE camera_tripwires SET {} WHERE id = %s;").format(sql.SQL(set_query))

                values = list(update_data.values())
                values.append(tripwire_id)

                cur.execute(query, tuple(values))
                conn.commit()
                logger.info(f"Tripwire ID {tripwire_id} has been updated.")
    except Exception as error:
        logger.error(f"Error updating tripwire: {error}")
        raise

def delete_tripwire(tripwire_id):
    """DELETE a tripwire."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM camera_tripwires WHERE id = %s;", (tripwire_id,))
                conn.commit()
    except Exception as error:
        logger.error(f"Error deleting tripwire: {error}")
        raise

# ATTENDANCE RECORDS (Logging and Management)
def log_attendance_event(user_id, event_type, camera_id, source='face_recognition'):
    """CREATE a new attendance record."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO attendance_records (user_id, event_type, event_timestamp, camera_id, source) VALUES (%s, %s, CURRENT_TIMESTAMP, %s, %s);",
                    (user_id, event_type, camera_id, source)
                )
                conn.commit()
    except Exception as error:
        logger.error(f"Error logging attendance: {error}")
        raise

def get_attendance_for_user(user_id, limit=100):
    """READ the most recent attendance records for a user."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT ar.id, ar.event_type, ar.event_timestamp, c.camera_name, ar.source
                    FROM attendance_records ar
                    LEFT JOIN cameras c ON ar.camera_id = c.id
                    WHERE ar.user_id = %s
                    ORDER BY ar.event_timestamp DESC
                    LIMIT %s;
                """, (user_id, limit))
                return cur.fetchall()
    except Exception as error:
        logger.error(f"Error getting attendance for user: {error}")
        raise

def delete_attendance_record(record_id):
    """DELETE a specific attendance record (for administrative correction)."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM attendance_records WHERE id = %s;", (record_id,))
                conn.commit()
    except Exception as error:
        logger.error(f"Error deleting attendance record: {error}")
        raise

def get_system_settings():
    """
    READS all tuning parameters from the system_settings table.
    Returns a dictionary of settings cast to their proper data types.
    """
    settings = {}
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT setting_key, setting_value, data_type FROM system_settings;")
                records = cur.fetchall()

                for key, value, data_type in records:
                    try:
                        if data_type == 'float':
                            settings[key] = float(value)
                        elif data_type == 'integer':
                            settings[key] = int(value)
                        else:
                            settings[key] = str(value)
                    except ValueError:
                        logger.warning(f"Warning: Could not cast setting '{key}' with value '{value}' to type '{data_type}'.")

    except Exception as error:
        logger.error(f"Error fetching system settings: {error}")
        raise

    return settings

def update_system_setting(setting_key, setting_value, data_type):
    """
    CREATE or UPDATE a system setting (UPSERT).
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # This query will insert a new row, or update the existing one if the key already exists.
                cur.execute("""
                    INSERT INTO system_settings (setting_key, setting_value, data_type)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (setting_key) DO UPDATE SET
                        setting_value = EXCLUDED.setting_value,
                        data_type = EXCLUDED.data_type;
                """, (setting_key, str(setting_value), data_type))
                conn.commit()
                logger.info(f"System setting '{setting_key}' has been set to '{setting_value}'.")

    except Exception as error:
        logger.error(f"Error updating system setting: {error}")
        raise

def delete_system_setting(setting_key):
    """
    DELETE a system setting from the database.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM system_settings WHERE setting_key = %s;", (setting_key,))
                conn.commit()
                logger.info(f"System setting '{setting_key}' has been deleted.")

    except Exception as error:
        logger.error(f"Error deleting system setting: {error}")
        raise

def get_user_by_employee_id(employee_id):
    """
    Fetches a single user's basic data by their employee_id.
    Returns the user's internal id, employee_id, and employee_name.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, employee_id, employee_name
                    FROM users
                    WHERE employee_id = %s;
                """, (employee_id,))
                return cur.fetchone()
    except Exception as error:
        logger.error(f"Error fetching user by employee_id: {error}")
        raise

def get_all_attendance_logs(limit=100):
    """READ all attendance records for all users."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT ar.id, u.employee_name, ar.event_type, ar.event_timestamp, c.camera_name, ar.source
                    FROM attendance_records ar
                    JOIN users u ON ar.user_id = u.id
                    LEFT JOIN cameras c ON ar.camera_id = c.id
                    ORDER BY ar.event_timestamp DESC
                    LIMIT %s;
                """, (limit,))
                return cur.fetchall()
    except Exception as error:
        logger.error(f"Error getting all attendance logs: {error}")
        raise

def get_tripwires_for_camera(camera_id: int):
    """READ all tripwires for a specific camera."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, tripwire_name, direction, position, spacing FROM camera_tripwires WHERE camera_id = %s;",
                    (camera_id,)
                )
                return [
                    {"id": t[0], "tripwire_name": t[1], "direction": t[2], "position": t[3], "spacing": t[4]}
                    for t in cur.fetchall()
                ]
    except Exception as error:
        logger.error(f"Error getting tripwires for camera: {error}")
        raise