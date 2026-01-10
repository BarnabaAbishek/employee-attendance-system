import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
import json

def initialize_firebase():
    """
    Initialize Firebase using environment variable or file
    """
    try:
        # Check if Firebase is already initialized
        firebase_admin.get_app()
        return firestore.client(), auth
    except ValueError:
        # Not initialized yet
        pass
    
    # Method 1: Check for environment variable (Render production)
    firebase_config_json = os.environ.get('FIREBASE_CONFIG')
    
    if firebase_config_json:
        # Parse JSON from environment variable
        firebase_config = json.loads(firebase_config_json)
        cred = credentials.Certificate(firebase_config)
    else:
        # Method 2: Use JSON file (local development)
        cred_path = "serviceAccountKey.json"
        if not os.path.exists(cred_path):
            raise FileNotFoundError(
                f"Firebase credentials not found at {cred_path}. "
                "Please add serviceAccountKey.json or set FIREBASE_CONFIG environment variable."
            )
        cred = credentials.Certificate(cred_path)
    
    # Initialize Firebase
    firebase_admin.initialize_app(cred)
    
    # Get Firestore and Auth instances
    db = firestore.client()
    
    print("✅ Firebase initialized successfully!")
    return db, auth

# Initialize Firebase and export both
db, auth = initialize_firebase()

# Export firestore module for use in app.py
firestore_module = firestore