import psycopg2
import numpy as np
from psycopg2 import sql
# It's best practice to load these from a config file or environment variables
DB_SETTINGS = {
    "dbname": "face_recognition_db",
    "user": "postgres",
    "password": "password",
    "host": "localhost",
    "port": 5432
}
def camera_exists(stream_url: str) -> bool:
    """
    Checks if a camera with the given stream_url already exists in the database.
    """
    conn = get_db_connection()
    if not conn: return False
    exists = False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM cameras WHERE stream_url = %s;", (stream_url,))
            exists = cur.fetchone() is not None
    except (Exception, psycopg2.Error) as error:
        print(f"Error checking if camera exists: {error}")
    finally:
        if conn:
            conn.close()
    return exists
def get_db_connection():
    """Establishes and returns a database connection."""
    try:
        conn = psycopg2.connect(**DB_SETTINGS)
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error: Could not connect to the database. Please check DB_SETTINGS and ensure PostgreSQL is running. Details: {e}")
        return None
# ROLES & DEPARTMENTS (Admin/Setup Tables)
def get_all_roles():
    """READ all available roles."""
    conn = get_db_connection()
    if not conn: return []
    with conn.cursor() as cur:
        cur.execute("SELECT id, role_name FROM roles ORDER BY id;")
        roles = cur.fetchall()
    conn.close()
    return roles
def update_user_department(user_id, department_id):
    """UPDATE a user's department."""
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET department_id = %s WHERE id = %s;", (department_id, user_id))
            conn.commit()
    except (Exception, psycopg2.Error) as error:
        print(f"Error updating user department: {error}")
    finally:
        if conn: conn.close()
def get_all_departments():
    """READ all available departments."""
    conn = get_db_connection()
    if not conn: return []
    with conn.cursor() as cur:
        cur.execute("SELECT id, department_name FROM departments ORDER BY department_name;")
        departments = cur.fetchall()
    conn.close()
    return departments
def add_department(department_name):
    """CREATE a new department."""
    conn = get_db_connection()
    if not conn: return None
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO departments (department_name) VALUES (%s) RETURNING id;", (department_name,))
            dept_id = cur.fetchone()[0]
            conn.commit()
            return dept_id
    except (Exception, psycopg2.Error) as error:
        print(f"Error adding department: {error}")
        return None
    finally:
        conn.close()
def update_department(department_id, new_name):
    """UPDATE a department's name."""
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE departments SET department_name = %s WHERE id = %s;", (new_name, department_id))
            conn.commit()
    except (Exception, psycopg2.Error) as error:
        print(f"Error updating department: {error}")
    finally:
        conn.close()
def delete_department(department_id):
    """DELETE a department. Fails if users are assigned to it."""
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM departments WHERE id = %s;", (department_id,))
            conn.commit()
    except (Exception, psycopg2.Error) as error:
        print(f"Error deleting department (ensure no users are assigned): {error}")
    finally:
        conn.close()
# USERS (Employee Management)
def get_user_for_login(username):
    """
    NEW: Fetches user data needed for login verification.
    Returns user_id, role_name, and hashed_password.
    """
    conn = get_db_connection()
    if not conn: return None
    user_data = None
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT u.id, r.role_name, u.hashed_password
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE u.username = %s AND u.is_active = true;
            """, (username,))
            user_data = cur.fetchone()
    except (Exception, psycopg2.Error) as error:
        print(f"Error fetching user for login: {error}")
    finally:
        if conn:
            conn.close()
    return user_data
def add_user(employee_id, employee_name, username, hashed_password, role_id, department_id):
    """CREATE a new user."""
    conn = get_db_connection()
    if not conn: return None
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (employee_id, employee_name, username, hashed_password, role_id, department_id) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;",
                (employee_id, employee_name, username, hashed_password, role_id, department_id)
            )
            user_id = cur.fetchone()[0]
            conn.commit()
            return user_id
    except (Exception, psycopg2.Error) as error:
        print(f"Error adding user: {error}")
        return None
    finally:
        conn.close()
def get_all_users_with_details():
    """READ all users with their role, department, and face embedding count."""
    conn = get_db_connection()
    if not conn: return []
    with conn.cursor() as cur:
        # UPDATED: This query now joins face_embeddings and counts them
        cur.execute("""
            SELECT
                u.id, u.employee_id, u.employee_name, u.username,
                r.role_name, d.department_name, u.is_active,
                COUNT(fe.id) as face_count
            FROM users u
            JOIN roles r ON u.role_id = r.id
            JOIN departments d ON u.department_id = d.id
            LEFT JOIN face_embeddings fe ON u.id = fe.user_id
            GROUP BY u.id, r.role_name, d.department_name
            ORDER BY u.employee_name;
        """)
        users = cur.fetchall()
    conn.close()
    return users
def update_user(employee_id, update_data):
    """UPDATE a user's details. update_data is a dict of columns to change."""
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            set_query = ", ".join([f"{key} = %s" for key in update_data.keys()])
            query = sql.SQL("UPDATE users SET {} WHERE employee_id = %s;").format(sql.SQL(set_query))
            values = list(update_data.values())
            values.append(employee_id)
            cur.execute(query, tuple(values))
            conn.commit()
    except (Exception, psycopg2.Error) as error:
        print(f"Error updating user: {error}")
    finally:
        conn.close()
def delete_user(employee_id):
    """DELETE a user. ON DELETE CASCADE handles related records."""
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE employee_id = %s;", (employee_id,))
            conn.commit()
    except (Exception, psycopg2.Error) as error:
        print(f"Error deleting user: {error}")
    finally:
        conn.close()
# FACE EMBEDDINGS (Face Recognition Data)
def add_face_embedding(user_id, embedding_vector, image_bytes, embedding_type='enrollment'):
    """
    CREATE a new face embedding record.
    If the type is 'update', it enforces a rolling limit of 20 per user.
    """
    conn = get_db_connection()
    if not conn: return None
    try:
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
    except (Exception, psycopg2.Error) as error:
        print(f"Error adding face embedding: {error}")
        if conn:
            conn.rollback() # Ensure transaction is rolled back on error
        return None
    finally:
        if conn:
            conn.close()
def get_all_face_embeddings():
    """READ all active users' embeddings and labels for the recognition model."""
    conn = get_db_connection()
    if not conn: return np.array([]), []
    with conn.cursor() as cur:
        cur.execute("""
            SELECT u.employee_id, fe.embedding
            FROM face_embeddings fe
            JOIN users u ON fe.user_id = u.id
            WHERE u.is_active = true;
        """)
        records = cur.fetchall()
    conn.close()
    if not records:
        return np.array([]), []
    labels = [rec[0] for rec in records]
    embeddings = [np.frombuffer(rec[1], dtype=np.float32) for rec in records]
    return np.array(embeddings), labels
def get_user_face_images(user_id):
    """READ all source images for a specific user."""
    conn = get_db_connection()
    if not conn: return []
    with conn.cursor() as cur:
        cur.execute("SELECT id, source_image FROM face_embeddings WHERE user_id = %s ORDER BY created_at DESC;", (user_id,))
        images = cur.fetchall()
    conn.close()
    return images
def set_profile_picture(user_id: int, embedding_id: int):
    """Sets a specific embedding as the profile picture for a user."""
    conn = get_db_connection()
    if not conn: return False
    try:
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
    except (Exception, psycopg2.Error) as error:
        print(f"Error setting profile picture: {error}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def get_profile_picture(user_id: int):
    """Retrieves the source image for the user's designated profile picture."""
    conn = get_db_connection()
    if not conn: return None
    with conn.cursor() as cur:
        cur.execute(
            "SELECT source_image FROM face_embeddings WHERE user_id = %s AND is_profile_picture = TRUE LIMIT 1;",
            (user_id,)
        )
        record = cur.fetchone()
    conn.close()
    return record[0] if record else None
    
def delete_face_embedding(embedding_id):
    """
    DELETE a specific face embedding and return its source image.
    Returns the binary image data on success, None on failure.
    """
    conn = get_db_connection()
    if not conn: return None
    image_data = None
    try:
        with conn.cursor() as cur:
            # Use RETURNING to get the source_image of the deleted row
            cur.execute("DELETE FROM face_embeddings WHERE id = %s RETURNING source_image;", (embedding_id,))
            deleted_row = cur.fetchone()
            if deleted_row:
                image_data = deleted_row[0]
            conn.commit()
    except (Exception, psycopg2.Error) as error:
        print(f"Error deleting face embedding: {error}")
        conn.rollback()
    finally:
        conn.close()
    return image_data
# CAMERAS & TRIPWIRES (System Configuration)
def add_camera(name, cam_type, stream_url, res_w, res_h, fps, gpu_id, user=None, pw=None):
    """CREATE a new camera."""
    conn = get_db_connection()
    if not conn: return None
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO cameras (camera_name, camera_type, stream_url, resolution_w, resolution_h, fps, gpu_id, username, encrypted_password) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;",
                (name, cam_type, stream_url, res_w, res_h, fps, gpu_id, user, pw))
            cam_id = cur.fetchone()[0]
            conn.commit()
            return cam_id
    except (Exception, psycopg2.Error) as error:
        print(f"Error adding camera: {error}")
        return None
    finally:
        conn.close()
def get_camera_configs():
    """READ all active camera and tripwire configurations."""
    conn = get_db_connection()
    if not conn: return []
    cameras = []
    with conn.cursor() as cur:
        cur.execute("SELECT id, camera_name, camera_type, stream_url, username, encrypted_password, resolution_w, resolution_h, fps, gpu_id FROM cameras WHERE is_active = true ORDER BY id;")
        camera_records = cur.fetchall()
        for rec in camera_records:
            cam_id, name, cam_type, url, user, pw, w, h, fps, gpu = rec
            camera_config = { "id": cam_id, "camera_name": name, "camera_type": cam_type, "stream_url": url, "username": user, "encrypted_password": pw, "resolution_w": w, "resolution_h": h, "fps": fps, "gpu_id": gpu, "tripwires": [] }
            cur.execute("SELECT id, tripwire_name, direction, position, spacing FROM camera_tripwires WHERE camera_id = %s;", (cam_id,))
            tripwire_records = cur.fetchall()
            for tw_rec in tripwire_records:
                camera_config["tripwires"].append({ "id": tw_rec[0], "name": tw_rec[1], "direction": tw_rec[2], "position": tw_rec[3], "spacing": tw_rec[4] })
            cameras.append(camera_config)
    conn.close()
    return cameras
def update_camera(camera_id, update_data):
    """UPDATE a camera's details."""
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            set_query = ", ".join([f"{key} = %s" for key in update_data.keys()])
            query = sql.SQL("UPDATE cameras SET {} WHERE id = %s;").format(sql.SQL(set_query))
            values = list(update_data.values())
            values.append(camera_id)
            cur.execute(query, tuple(values))
            conn.commit()
    except (Exception, psycopg2.Error) as error:
        print(f"Error updating camera: {error}")
    finally:
        conn.close()
def delete_camera(camera_id):
    """DELETE a camera. ON DELETE CASCADE handles tripwires."""
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM cameras WHERE id = %s;", (camera_id,))
            conn.commit()
    except (Exception, psycopg2.Error) as error:
        print(f"Error deleting camera: {error}")
    finally:
        conn.close()

def add_tripwire(camera_id, name, direction, position, spacing):
    """CREATE a new tripwire for a camera."""
    conn = get_db_connection()
    if not conn: return None
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO camera_tripwires (camera_id, tripwire_name, direction, position, spacing) VALUES (%s, %s, %s, %s, %s) RETURNING id;",
                (camera_id, name, direction, position, spacing)
            )
            tw_id = cur.fetchone()[0]
            conn.commit()
            return tw_id
    except (Exception, psycopg2.Error) as error:
        print(f"Error adding tripwire: {error}")
        return None
    finally:
        conn.close()

def update_tripwire(tripwire_id, update_data):
    """UPDATE a tripwire's details. update_data is a dict of columns to change."""
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            # Build the SET part of the SQL query dynamically
            set_query = ", ".join([f"{key} = %s" for key in update_data.keys()])
            query = sql.SQL("UPDATE camera_tripwires SET {} WHERE id = %s;").format(sql.SQL(set_query))
            
            values = list(update_data.values())
            values.append(tripwire_id)
            
            cur.execute(query, tuple(values))
            conn.commit()
            print(f"Tripwire ID {tripwire_id} has been updated.")
    except (Exception, psycopg2.Error) as error:
        print(f"Error updating tripwire: {error}")
        conn.rollback()
    finally:
        conn.close()

def delete_tripwire(tripwire_id):
    """DELETE a tripwire."""
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM camera_tripwires WHERE id = %s;", (tripwire_id,))
            conn.commit()
    except (Exception, psycopg2.Error) as error:
        print(f"Error deleting tripwire: {error}")
    finally:
        conn.close()
# ATTENDANCE RECORDS (Logging and Management)
def log_attendance_event(user_id, event_type, camera_id, source='face_recognition'):
    """CREATE a new attendance record."""
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO attendance_records (user_id, event_type, event_timestamp, camera_id, source) VALUES (%s, %s, CURRENT_TIMESTAMP, %s, %s);",
                (user_id, event_type, camera_id, source)
            )
            conn.commit()
    except (Exception, psycopg2.Error) as error:
        print(f"Error logging attendance: {error}")
    finally:
        conn.close()

def get_attendance_for_user(user_id, limit=100):
    """READ the most recent attendance records for a user."""
    conn = get_db_connection()
    if not conn: return []
    with conn.cursor() as cur:
        cur.execute("""
            SELECT ar.id, ar.event_type, ar.event_timestamp, c.camera_name, ar.source
            FROM attendance_records ar
            LEFT JOIN cameras c ON ar.camera_id = c.id
            WHERE ar.user_id = %s
            ORDER BY ar.event_timestamp DESC
            LIMIT %s;
        """, (user_id, limit))
        records = cur.fetchall()
    conn.close()
    return records

def delete_attendance_record(record_id):
    """DELETE a specific attendance record (for administrative correction)."""
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM attendance_records WHERE id = %s;", (record_id,))
            conn.commit()
    except (Exception, psycopg2.Error) as error:
        print(f"Error deleting attendance record: {error}")
    finally:
        conn.close()
def get_system_settings():
    """
    READS all tuning parameters from the system_settings table.
    Returns a dictionary of settings cast to their proper data types.
    """
    settings = {}
    conn = get_db_connection()
    if not conn: return settings
    
    try:
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
                    print(f"Warning: Could not cast setting '{key}' with value '{value}' to type '{data_type}'.")
                    
    except (Exception, psycopg2.Error) as error:
        print(f"Error fetching system settings: {error}")
    finally:
        if conn:
            conn.close()
        
    return settings

def update_system_setting(setting_key, setting_value, data_type):
    """
    CREATE or UPDATE a system setting (UPSERT).
    """
    conn = get_db_connection()
    if not conn: return
    
    try:
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
            print(f"System setting '{setting_key}' has been set to '{setting_value}'.")
            
    except (Exception, psycopg2.Error) as error:
        print(f"Error updating system setting: {error}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def delete_system_setting(setting_key):
    """
    DELETE a system setting from the database.
    """
    conn = get_db_connection()
    if not conn: return
    
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM system_settings WHERE setting_key = %s;", (setting_key,))
            conn.commit()
            print(f"System setting '{setting_key}' has been deleted.")
            
    except (Exception, psycopg2.Error) as error:
        print(f"Error deleting system setting: {error}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
def get_user_by_employee_id(employee_id):
    """
    Fetches a single user's basic data by their employee_id.
    Returns the user's internal id, employee_id, and employee_name.
    """
    conn = get_db_connection()
    if not conn: return None
    user_data = None
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, employee_id, employee_name
                FROM users
                WHERE employee_id = %s;
            """, (employee_id,))
            user_data = cur.fetchone()
    except (Exception, psycopg2.Error) as error:
        print(f"Error fetching user by employee_id: {error}")
    finally:
        if conn:
            conn.close()
    return user_data
def get_all_attendance_logs(limit=100):
    """READ all attendance records for all users."""
    conn = get_db_connection()
    if not conn: return []
    with conn.cursor() as cur:
        cur.execute("""
            SELECT ar.id, u.employee_name, ar.event_type, ar.event_timestamp, c.camera_name, ar.source
            FROM attendance_records ar
            JOIN users u ON ar.user_id = u.id
            LEFT JOIN cameras c ON ar.camera_id = c.id
            ORDER BY ar.event_timestamp DESC
            LIMIT %s;
        """, (limit,))
        records = cur.fetchall()
    conn.close()
    return records
def get_tripwires_for_camera(camera_id: int):
    """READ all tripwires for a specific camera."""
    conn = get_db_connection()
    if not conn: return []
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, tripwire_name, direction, position, spacing FROM camera_tripwires WHERE camera_id = %s;",
            (camera_id,)
        )
        tripwires = cur.fetchall()
    conn.close()
    return [
        {"id": t[0], "tripwire_name": t[1], "direction": t[2], "position": t[3], "spacing": t[4]}
        for t in tripwires
    ]