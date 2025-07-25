# face_enroller.py
import cv2
import numpy as np
from insightface.app import FaceAnalysis
from typing import List
from db import db_utils  # Import your new data access layer
import bcrypt # For password hashing
import argparse
import getpass

class FaceEnroller:
    """
    A class to handle all face enrollment logic, including processing images
    and interacting with the database.
    """
    def __init__(self):
        """
        Initializes the FaceEnroller.
        The FaceAnalysis model is prepared for processing images.
        """
        self.app = FaceAnalysis(name='antelopev2',
                                providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
        self.app.prepare(ctx_id=0, det_size=(416, 416))

    def enroll_new_user(self, employee_id: str, employee_name: str, username: str, password: str, image_paths: List[str], role_id: int = 1, department_id: int = 1):
        """
        Enrolls a completely new user. This involves creating a user record
        and then adding their initial face embeddings.
        """
        if not all([employee_id, employee_name, username, password]):
            print("Error: All user fields are required.")
            return False
        
        if len(image_paths) < 3:
            print("Error: At least 3 images are required for initial enrollment.")
            return False

        # --- 1. Create the user record in the database ---
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user_id = db_utils.add_user(
            employee_id=employee_id, 
            employee_name=employee_name, 
            username=username, 
            hashed_password=hashed_password.decode(), 
            role_id=role_id, 
            department_id=department_id
        )

        if not user_id:
            print(f"Error: Could not create user '{employee_name}'. The employee ID or username might already exist.")
            return False
            
        print(f"User '{employee_name}' created with internal ID: {user_id}")
        
        # --- 2. Process and add their face embeddings ---
        return self.add_faces_to_existing_user(user_id, image_paths, embedding_type='enrollment')

    def add_faces_to_existing_user(self, user_id: int, image_paths: List[str], embedding_type: str = 'update') -> bool:
        """
        Adds new face embeddings to a user who already exists in the database.
        """
        if not image_paths:
            print("Error: No valid image files provided.")
            return False

        valid_count = 0
        for img_path in image_paths:
            try:
                img = cv2.imread(img_path)
                if img is None:
                    print(f"Warning: Could not read image - {img_path}")
                    continue
                
                _, image_bytes = cv2.imencode('.jpg', img)
                faces = self.app.get(img)

                if len(faces) != 1:
                    print(f"Warning: Found {len(faces)} faces in {img_path} (expected 1), skipping.")
                    continue
                
                face = faces[0]
                embedding_vector = face.embedding

                embedding_id = db_utils.add_face_embedding(
                    user_id=user_id,
                    embedding_vector=embedding_vector,
                    image_bytes=image_bytes.tobytes(),
                    embedding_type=embedding_type
                )

                if embedding_id:
                    valid_count += 1
                    print(f"Processed {img_path} - Embedding saved with ID: {embedding_id}")
                
            except Exception as e:
                print(f"Error processing {img_path}: {str(e)}")
                continue
        
        if valid_count > 0:
            print(f"\nSuccess: Added {valid_count} new face embeddings for user ID {user_id}.")
            return True
        else:
            print(f"\nFailure: No valid faces were processed for user ID {user_id}.")
            return False

    def delete_employee(self, employee_id: str) -> bool:
        """
        Deletes a user and all their associated data from the database.
        """
        print(f"Attempting to delete employee: {employee_id}")
        db_utils.delete_user(employee_id)
        return True

    def delete_employee_image(self, embedding_id: int):
        """
        Deletes a single face image/embedding from the database.
        """
        print(f"Attempting to delete embedding with ID: {embedding_id}")
        deleted_image = db_utils.delete_face_embedding(embedding_id)
        if deleted_image:
            print(f"Successfully deleted embedding {embedding_id}.")
            return deleted_image
        return None

# ==============================================================================
# COMMAND-LINE INTERFACE (CLI)
# ==============================================================================

def main_cli():
    """
    Provides a command-line interface for managing face enrollments
    when this script is executed directly.
    """
    parser = argparse.ArgumentParser(
        description="CLI tool for face enrollment management.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands', required=True)

    # --- Command to enroll a new user ---
    parser_enroll = subparsers.add_parser('enroll', help='Enroll a new user with their initial set of face images.')
    parser_enroll.add_argument('--emp-id', required=True, help='The business-facing Employee ID (e.g., "EMP1024").')
    parser_enroll.add_argument('--name', required=True, help='Full name of the employee.')
    parser_enroll.add_argument('--username', required=True, help='The username for logging into the web application.')
    parser_enroll.add_argument('--images', required=True, nargs='+', help='Paths to at least 3 face images, separated by spaces.')

    # --- Command to add faces to an existing user ---
    parser_add_faces = subparsers.add_parser('add-faces', help='Add more face images to an existing user.')
    parser_add_faces.add_argument('--user-id', required=True, type=int, help='The internal database ID of the user (the integer primary key).')
    parser_add_faces.add_argument('--images', required=True, nargs='+', help='Paths to one or more face images to add.')

    # --- Command to delete a user ---
    parser_delete_user = subparsers.add_parser('delete-user', help='Delete a user and all their associated data.')
    parser_delete_user.add_argument('--emp-id', required=True, help='The Employee ID of the user to delete.')

    # --- Command to delete a single face embedding ---
    parser_delete_face = subparsers.add_parser('delete-face', help='Delete a single face embedding from the database.')
    parser_delete_face.add_argument('--embedding-id', required=True, type=int, help='The internal database ID of the specific face embedding.')

    args = parser.parse_args()
    enroller = FaceEnroller()

    if args.command == 'enroll':
        password = getpass.getpass(f"Enter password for new user '{args.username}': ")
        enroller.enroll_new_user(
            employee_id=args.emp_id,
            employee_name=args.name,
            username=args.username,
            password=password,
            image_paths=args.images
        )
    elif args.command == 'add-faces':
        enroller.add_faces_to_existing_user(
            user_id=args.user_id,
            image_paths=args.images,
            embedding_type='update'
        )
    elif args.command == 'delete-user':
        if input(f"Are you sure you want to permanently delete user {args.emp_id}? (y/n): ").lower() == 'y':
            enroller.delete_employee(employee_id=args.emp_id)
        else:
            print("Operation cancelled.")
    elif args.command == 'delete-face':
        if input(f"Are you sure you want to permanently delete embedding {args.embedding_id}? (y/n): ").lower() == 'y':
            enroller.delete_employee_image(embedding_id=args.embedding_id)
        else:
            print("Operation cancelled.")
    else:
        parser.print_help()

if __name__ == '__main__':
    main_cli()
