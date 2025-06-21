# app.py - Flask Backend for Telethon Session Phone Number Retrieval

from flask import Flask, request, jsonify
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import User
import asyncio
import os

app = Flask(__name__)

# --- Configuration ---
# It's highly recommended to use environment variables for sensitive data
# like API ID and Hash in production. For local testing, you can place them directly
# but DO NOT commit them to public repositories.
# For this example, the user will input them via the web interface.

@app.route('/')
def index():
    """Serves the main HTML page."""
    # In a real app, you'd serve a static HTML file.
    # For this self-contained example, we'll just show instructions.
    return """
    <h1>Telethon Session Phone Number Retriever</h1>
    <p>This is the backend. To use the web interface, please open the 'index.html' file provided separately.</p>
    <p>Ensure your `api_id` and `api_hash` are correctly configured for the session string you provide.</p>
    """

@app.route('/get_phone_number', methods=['POST'])
async def get_phone_number():
    """
    Receives session string, api_id, and api_hash,
    and returns the phone number of the associated Telegram account.
    """
    data = request.get_json()
    session_string = data.get('session_string')
    api_id = data.get('api_id')
    api_hash = data.get('api_hash')

    if not all([session_string, api_id, api_hash]):
        return jsonify({
            'success': False,
            'message': 'Missing session string, API ID, or API Hash.'
        }), 400

    try:
        api_id = int(api_id) # Ensure api_id is an integer

        # Initialize the client using the session string
        # IMPORTANT: The api_id and api_hash MUST match those used to generate the session string.
        client = TelegramClient(StringSession(session_string), api_id, api_hash)

        # Connect the client.
        # Use asyncio.run for synchronous Flask routes calling async Telethon code.
        # This approach is suitable for simple, single-request operations.
        # For more complex/concurrent async operations in Flask, consider a framework like Quart
        # or managing the event loop explicitly, but for simple deployment, this works.
        await client.connect()

        if not await client.is_user_authorized():
            await client.disconnect()
            return jsonify({
                'success': False,
                'message': 'Session string is invalid or expired. Please ensure API ID/Hash match and the session is active.'
            }), 401

        # Get information about the currently logged-in user
        me = await client.get_me()
        
        phone_number = me.phone if me and me.phone else "Not available"

        await client.disconnect()

        return jsonify({
            'success': True,
            'phone_number': f"+{phone_number}",
            'user_id': me.id if me else "N/A",
            'first_name': me.first_name if me else "N/A",
            'last_name': me.last_name if me else "N/A",
            'username': me.username if me else "N/A"
        }), 200

    except ValueError:
        return jsonify({
            'success': False,
            'message': 'API ID must be an integer.'
        }), 400
    except Exception as e:
        print(f"Error during Telethon operation: {e}")
        # General error handling for other Telethon-related issues
        return jsonify({
            'success': False,
            'message': f'An unexpected error occurred: {str(e)}'
        }), 500
    finally:
        # Ensure client is disconnected even if an error occurs during processing
        if 'client' in locals() and client.is_connected():
            await client.disconnect()


if __name__ == '__main__':
    # When running locally, Flask will serve on http://127.0.0.1:5000
    # For deployment, a WSGI server like Gunicorn would be used.
    app.run(debug=True, host='0.0.0.0', port=os.getenv('PORT', 5000))

