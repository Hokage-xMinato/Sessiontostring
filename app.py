# app.py - Flask Backend for Telethon Session Phone Number Retriever

from flask import Flask, request, jsonify, send_from_directory, Blueprint
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import User
import asyncio
import os

# Initialize Flask app
# By default, Flask looks for 'static' and 'templates' folders.
# We'll place index.html in a 'static' folder.
app = Flask(__name__)

# Create an API Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

@app.route('/')
def serve_index():
    """
    Serves the main HTML page (index.html) from the 'static' directory.
    When you visit the root URL of your deployed service, this will load the web form.
    """
    # Flask will automatically look for 'index.html' inside the 'static' folder.
    return send_from_directory(app.static_folder, 'index.html')

@api_bp.route('/get_phone_number', methods=['POST'])
async def get_phone_number_api(): # Renamed function to avoid conflict with potential other get_phone_number functions
    """
    Handles POST requests from the frontend to the /api/get_phone_number endpoint.
    Receives session string, API ID, and API Hash in JSON format,
    then uses Telethon to retrieve and return the phone number of the
    associated Telegram account.
    """
    data = request.get_json()
    session_string = data.get('session_string')
    api_id = data.get('api_id')
    api_hash = data.get('api_hash')

    # Validate incoming data
    if not all([session_string, api_id, api_hash]):
        return jsonify({
            'success': False,
            'message': 'Missing session string, API ID, or API Hash. All fields are required.'
        }), 400

    client = None # Initialize client to None for finally block
    try:
        # Convert api_id to integer; raises ValueError if not a valid number
        api_id = int(api_id)

        # Initialize Telethon client with StringSession
        # The api_id and api_hash must exactly match those used when the session string was generated.
        client = TelegramClient(StringSession(session_string), api_id, api_hash)

        # Connect to Telegram servers
        await client.connect()

        # Check if the user is authorized with this session string
        if not await client.is_user_authorized():
            return jsonify({
                'success': False,
                'message': 'Session string is invalid or expired. Please ensure API ID/Hash match and the session is active.'
            }), 401 # 401 Unauthorized status

        # Get information about the currently logged-in user
        me = await client.get_me()
        
        # Extract phone number, providing a fallback if not available (unlikely for self-user)
        phone_number = me.phone if me and me.phone else "Not available"

        # Return success response with user details
        return jsonify({
            'success': True,
            'phone_number': f"+{phone_number}",
            'user_id': me.id if me else "N/A",
            'first_name': me.first_name if me else "N/A",
            'last_name': me.last_name if me else "N/A",
            'username': me.username if me else "N/A"
        }), 200

    except ValueError:
        # Handle cases where api_id is not a valid integer
        return jsonify({
            'success': False,
            'message': 'API ID must be a valid integer.'
        }), 400
    except Exception as e:
        # Catch any other unexpected errors during Telethon operations
        print(f"Error during Telethon operation: {e}") # Log the full error for debugging
        return jsonify({
            'success': False,
            'message': f'An unexpected error occurred while processing your request: {str(e)}'
        }), 500 # 500 Internal Server Error status
    finally:
        # Ensure the client connection is always closed, regardless of success or failure
        if client and client.is_connected():
            await client.disconnect()

# Register the blueprint with the app
app.register_blueprint(api_bp)

if __name__ == '__main__':
    # When running locally, Flask will automatically use the PORT environment variable if set,
    # otherwise it defaults to 5000.
    # For production deployments (like Render), Gunicorn will handle port binding.
    app.run(debug=True, host='0.0.0.0', port=os.getenv('PORT', 5000))

