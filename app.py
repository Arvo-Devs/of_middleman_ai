"""
Flask API for Middleman AI - Chat Recommendation System
"""

from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
from functools import wraps
from supabase import create_client,Client
from typing import Dict, List, Any
import os
from datetime import datetime
from dotenv import load_dotenv
from utils.creator import get_creator_by_id
from utils.fan import get_fan_by_id
from utils.system_prompt import get_system_prompt_by_id
from utils.chats import generate_chat_recommendations
# Load environment variables
load_dotenv()
print('Environment:', os.getenv('FLASK_ENV'))
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
CORS(app)  # Enable CORS for all routes

# Environment variables for authentication
LOGIN_USERNAME = os.getenv('LOGIN_USERNAME')
LOGIN_PASSWORD = os.getenv('LOGIN_PASSWORD')
API_KEY = os.getenv('API_KEY')


# Authentication decorators
def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def api_key_required(f):
    """Decorator to require API key for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != API_KEY:
            return jsonify({"error": "Invalid or missing API key"}), 401
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and authentication"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        
        if username == LOGIN_USERNAME and password == LOGIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            if request.is_json:
                return jsonify({"success": True, "message": "Login successful", "api_key": API_KEY}), 200
            return redirect(url_for('index'))
        else:
            if request.is_json:
                return jsonify({"error": "Invalid username or password"}), 401
            return render_template('login.html', error="Invalid username or password")
    
    # GET request - show login page
    if 'logged_in' in session and session['logged_in']:
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/logout', methods=['POST'])
def logout():
    """Logout endpoint"""
    session.clear()
    if request.is_json:
        return jsonify({"success": True, "message": "Logged out successfully"}), 200
    return redirect(url_for('login'))


@app.route('/', methods=['GET'])
@login_required
def index():
    """Serve the main frontend page"""
    return render_template('index.html')



@app.route('/recommended_chats', methods=['POST'])
@api_key_required
def recommended_chats():
    """
    Recommend 5 chat replies based on chat history and user context.
    
    Expected request body:
    {
        "fan_id": "string",
        "creator_id": "string",
        "system_prompt_id": "string",
        "chat_type": "text" | "image" | "video"  # optional
    }
    
    Returns:
    {
        "recommendations": [
            {
                "reply_id": "string",
                "content": "string",
                "confidence": float
            },
            ...
        ]
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        fan_id = data.get("fan_id")
        creator_id = data.get("creator_id")
        chat_type = data.get("chat_type", "text")  # text, image, or video
        
        if not fan_id or not creator_id:
            return jsonify({"error": "fan_id and creator_id are required"}), 400
        
        # Get system_prompt_id from request
        system_prompt_id = data.get("system_prompt_id")
        
        if not system_prompt_id:
            return jsonify({"error": "system_prompt_id is required"}), 400
        
        # Fetch recent chat events for context
        chat_history_response = supabase.table("of_chat_message").select("*").eq("fan_id", fan_id).eq("creator_id", creator_id).order("created_at", desc=True).limit(10).execute()
        
        # Handle case when fan_id and creator_id haven't started conversing yet (null/empty chat history)
        chat_history = chat_history_response.data if chat_history_response.data else []
        
        recommendations = generate_chat_recommendations(
            supabase=supabase,
            creator_id=creator_id,
            fan_id=fan_id,
            system_prompt_id=system_prompt_id,
            chat_history=chat_history,
            chat_type=chat_type
        )
        
        return jsonify({
            "recommendations": recommendations,
            "fan_id": fan_id,
            "creator_id": creator_id,
            "chat_type": chat_type
        }), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route('/chatter_selected_chat_reply', methods=['POST'])
@api_key_required
def chatter_selected_chat_reply():
    """
    Store the selected chat reply in the database.
    
    Expected request body:
    {
        "fan_id": "string",
        "creator_id": "string",
        "reply_content": "string",
        "reply_id": "string",  # optional, if recommendation was selected (stored in metadata)
        "chat_type": "text" | "image" | "video",  # optional (stored in metadata)
        "metadata": {}  # optional additional data
    }
    
    Returns:
    {
        "success": true,
        "message_id": "string",
        "message": "Chat reply stored successfully"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        fan_id = data.get("fan_id")
        creator_id = data.get("creator_id")
        reply_content = data.get("reply_content")
        reply_id = data.get("reply_id")
        chat_type = data.get("chat_type", "text")
        metadata = data.get("metadata", {})
        
        if not fan_id or not creator_id or not reply_content:
            return jsonify({"error": "fan_id, creator_id, and reply_content are required"}), 400
        
        # Prepare metadata with optional fields
        message_metadata = metadata.copy() if metadata else {}
        if reply_id:
            message_metadata["reply_id"] = reply_id
        if chat_type:
            message_metadata["chat_type"] = chat_type
        
        # Insert into of_chat_message table (matches schema)
        message_data = {
            "fan_id": fan_id,
            "creator_id": creator_id,
            "sender": "creator",
            "content": reply_content,
            "metadata": message_metadata
        }
        
        response = supabase.table("of_chat_message").insert(message_data).execute()
        
        if response.data and len(response.data) > 0:
            return jsonify({
                "success": True,
                "message_id": response.data[0].get("id"),
                "message": "Chat reply stored successfully"
            }), 201
        else:
            return jsonify({"error": "Failed to store chat reply"}), 500
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500



@app.route('/get_creator_details', methods=['GET'])
@api_key_required
def creator_details():
    """
    Get creator details from Supabase by creator_id.
    
    Expected request body:
    {
        "creator_id": "string"
    }
    
    Returns:
    {
        "creator": {
            "creator_id": "string",
            "nsfw": boolean,
            "niches": [],
            "persona_tone": [],
            "emojis_enabled": boolean,
            "creator_image": "string",
            ... (all other creator fields)
        }
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        creator_id = data.get("id")
        
        if not creator_id:
            return jsonify({"error": "creator_id is required"}), 400
        
        # Fetch creator data using helper function
        try:
            creator = get_creator_by_id(supabase,creator_id)
        except ValueError:
            return jsonify({"error": "Creator not found"}), 404
        
        return jsonify({
            "creator": creator,
            "creator_id": creator_id
        }), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route('/get_fan_details', methods=['GET'])
@api_key_required
def fan_details():
    """
    Get fan details from Supabase by fan_id.
    
    Expected request body:
    {
        "id": "string"
    }
    
    Returns:
    {
        "fan": {
            "fan_id": "string",
            "lifetime_spend": float,
            ... (all other fan fields)
        },
        "fan_id": "string"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        fan_id = data.get("id")
        
        if not fan_id:
            return jsonify({"error": "fan_id is required"}), 400
        
        # Fetch fan data using helper function
        try:
            fan = get_fan_by_id(supabase,fan_id)
        except ValueError:
            return jsonify({"error": "Fan not found"}), 404
        
        return jsonify({
            "fan": fan,
            "fan_id": fan_id
        }), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route('/get_system_prompt_details', methods=['POST'])
@api_key_required
def get_system_prompt_details():
    """
    Get system prompt details from Supabase by system_prompt_id.
    
    Expected request body:
    {
        "id": "string"
    }
    
    Returns:
    {
        "system_prompt": {
            "id": "string",
            "prompt": "string",
            ... (all other system_prompt fields)
        },
        "system_prompt_id": "string"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        system_prompt_id = data.get("id")
        
        if not system_prompt_id:
            return jsonify({"error": "system_prompt_id is required"}), 400
        
        # Fetch system prompt data using helper function
        try:
            system_prompt = get_system_prompt_by_id(supabase,system_prompt_id)
        except ValueError:
            return jsonify({"error": "System prompt not found"}), 404
        
        return jsonify({
            "system_prompt": system_prompt,
            "system_prompt_id": system_prompt_id
        }), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route('/get_creators', methods=['GET'])
@api_key_required
def get_creators():
    """Get all creators"""
    try:
        creators_response = supabase.table("creator").select("*").execute()
        creators = creators_response.data if creators_response.data else []
        return jsonify({"creators": creators}), 200
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route('/get_fans', methods=['GET'])
@api_key_required
def get_fans():
    """Get all fans"""
    try:
        fans_response = supabase.table("fan").select("*").execute()
        fans = fans_response.data if fans_response.data else []
        return jsonify({"fans": fans}), 200
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route('/get_system_prompts', methods=['GET'])
@api_key_required
def get_system_prompts():
    """Get all system prompts"""
    try:
        prompts_response = supabase.table("system_prompt").select("*").execute()
        prompts = prompts_response.data if prompts_response.data else []
        return jsonify({"system_prompts": prompts}), 200
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route('/get_chat_history', methods=['GET'])
@api_key_required
def get_chat_history():
    """
    Get chat history between a creator and fan.
    
    Query parameters:
    - creator_id: string (required)
    - fan_id: string (required)
    
    Returns:
    {
        "messages": [
            {
                "id": "string",
                "sender": "creator" | "fan",
                "content": "string",
                "created_at": "string"
            },
            ...
        ]
    }
    """
    try:
        creator_id = request.args.get("creator_id")
        fan_id = request.args.get("fan_id")
        
        if not creator_id or not fan_id:
            return jsonify({"error": "creator_id and fan_id are required"}), 400
        
        # Fetch chat history from of_chat_message table
        chat_history_response = supabase.table("of_chat_message").select("*").eq("fan_id", fan_id).eq("creator_id", creator_id).order("created_at", desc=False).execute()
        
        messages = chat_history_response.data if chat_history_response.data else []
        
        return jsonify({
            "messages": messages
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route('/send_fan_message', methods=['POST'])
@api_key_required
def send_fan_message():
    """
    Store a fan message in the database.
    
    Expected request body:
    {
        "fan_id": "string",
        "creator_id": "string",
        "content": "string"
    }
    
    Returns:
    {
        "success": true,
        "message_id": "string",
        "message": "Fan message stored successfully"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        fan_id = data.get("fan_id")
        creator_id = data.get("creator_id")
        content = data.get("content")
        
        if not fan_id or not creator_id or not content:
            return jsonify({"error": "fan_id, creator_id, and content are required"}), 400
        
        # Insert message into of_chat_message table
        message_data = {
            "fan_id": fan_id,
            "creator_id": creator_id,
            "sender": "fan",
            "content": content,
            "created_at": datetime.utcnow().isoformat()
        }
        
        response = supabase.table("of_chat_message").insert(message_data).execute()
        
        if response.data:
            return jsonify({
                "success": True,
                "message_id": response.data[0].get("id"),
                "message": "Fan message stored successfully"
            }), 201
        else:
            return jsonify({"error": "Failed to store fan message"}), 500
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route('/update_creator', methods=['PUT', 'PATCH'])
@api_key_required
def update_creator():
    """
    Update creator details.
    
    Expected request body:
    {
        "id": "string",
        "name": "string",  # optional
        "niches": [],  # optional
        "persona": [],  # optional
        "nsfw": boolean,  # optional
        "emojis_enabled": boolean,  # optional
        ... (any other creator fields)
    }
    
    Returns:
    {
        "success": true,
        "creator": { ... },
        "message": "Creator updated successfully"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        creator_id = data.get("id")
        if not creator_id:
            return jsonify({"error": "id is required"}), 400
        
        # Remove id from update data
        update_data = {k: v for k, v in data.items() if k != "id"}
        
        if not update_data:
            return jsonify({"error": "No fields to update"}), 400
        
        # Update creator in Supabase
        response = supabase.table("creator").update(update_data).eq("id", creator_id).execute()
        
        if response.data and len(response.data) > 0:
            return jsonify({
                "success": True,
                "creator": response.data[0],
                "message": "Creator updated successfully"
            }), 200
        else:
            return jsonify({"error": "Creator not found or update failed"}), 404
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route('/update_fan', methods=['PUT', 'PATCH'])
@api_key_required
def update_fan():
    """
    Update fan details.
    
    Expected request body:
    {
        "id": "string",
        "name": "string",  # optional
        "lifetime_spend": float,  # optional
        ... (any other fan fields)
    }
    
    Returns:
    {
        "success": true,
        "fan": { ... },
        "message": "Fan updated successfully"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        fan_id = data.get("id")
        if not fan_id:
            return jsonify({"error": "id is required"}), 400
        
        # Remove id from update data
        update_data = {k: v for k, v in data.items() if k != "id"}
        
        if not update_data:
            return jsonify({"error": "No fields to update"}), 400
        
        # Update fan in Supabase
        response = supabase.table("fan").update(update_data).eq("id", fan_id).execute()
        
        if response.data and len(response.data) > 0:
            return jsonify({
                "success": True,
                "fan": response.data[0],
                "message": "Fan updated successfully"
            }), 200
        else:
            return jsonify({"error": "Fan not found or update failed"}), 404
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route('/create_creator', methods=['POST'])
@api_key_required
def create_creator():
    """
    Create a new creator.
    
    Expected request body:
    {
        "name": "string",  # optional
        "niches": [],  # optional
        "persona": [],  # optional
        "nsfw": boolean,  # optional
        "emojis_enabled": boolean,  # optional
        ... (any other creator fields)
    }
    
    Returns:
    {
        "success": true,
        "creator": { ... },
        "message": "Creator created successfully"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        # Insert creator into Supabase
        response = supabase.table("creator").insert(data).execute()
        
        if response.data and len(response.data) > 0:
            return jsonify({
                "success": True,
                "creator": response.data[0],
                "message": "Creator created successfully"
            }), 201
        else:
            return jsonify({"error": "Failed to create creator"}), 500
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route('/create_fan', methods=['POST'])
@api_key_required
def create_fan():
    """
    Create a new fan.
    
    Expected request body:
    {
        "name": "string",  # optional
        "lifetime_spend": float,  # optional
        ... (any other fan fields)
    }
    
    Returns:
    {
        "success": true,
        "fan": { ... },
        "message": "Fan created successfully"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        # Insert fan into Supabase
        response = supabase.table("fan").insert(data).execute()
        
        if response.data and len(response.data) > 0:
            return jsonify({
                "success": True,
                "fan": response.data[0],
                "message": "Fan created successfully"
            }), 201
        else:
            return jsonify({"error": "Failed to create fan"}), 500
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route('/create_system_prompt', methods=['POST'])
@api_key_required
def create_system_prompt():
    """
    Create a new system prompt.
    
    Expected request body:
    {
        "system_prompt": "string",  # optional
        ... (any other system_prompt fields)
    }
    
    Returns:
    {
        "success": true,
        "system_prompt": { ... },
        "message": "System prompt created successfully"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        # Insert system prompt into Supabase
        response = supabase.table("system_prompt").insert(data).execute()
        
        if response.data and len(response.data) > 0:
            return jsonify({
                "success": True,
                "system_prompt": response.data[0],
                "message": "System prompt created successfully"
            }), 201
        else:
            return jsonify({"error": "Failed to create system prompt"}), 500
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route('/update_system_prompt', methods=['PUT', 'PATCH'])
@api_key_required
def update_system_prompt():
    """
    Update system prompt details.
    
    Expected request body:
    {
        "id": "string",
        "system_prompt": "string",  # optional
        ... (any other system_prompt fields)
    }
    
    Returns:
    {
        "success": true,
        "system_prompt": { ... },
        "message": "System prompt updated successfully"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        prompt_id = data.get("id")
        if not prompt_id:
            return jsonify({"error": "id is required"}), 400
        
        # Remove id from update data
        update_data = {k: v for k, v in data.items() if k != "id"}
        
        if not update_data:
            return jsonify({"error": "No fields to update"}), 400
        
        # Update system prompt in Supabase
        response = supabase.table("system_prompt").update(update_data).eq("id", prompt_id).execute()
        
        if response.data and len(response.data) > 0:
            return jsonify({
                "success": True,
                "system_prompt": response.data[0],
                "message": "System prompt updated successfully"
            }), 200
        else:
            return jsonify({"error": "System prompt not found or update failed"}), 404
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route('/api-docs/openapi.json', methods=['GET'])
@login_required
def openapi_spec():
    """OpenAPI specification for the API"""
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Middleman AI API",
            "version": "1.0.0",
            "description": "API for Middleman AI Chat Recommendation System"
        },
        "servers": [
            {
                "url": f"{request.scheme}://{request.host}",
                "description": "Current server"
            }
        ],
        "components": {
            "securitySchemes": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key"
                }
            }
        },
        "security": [{"ApiKeyAuth": []}],
        "paths": {
            "/recommended_chats": {
                "post": {
                    "tags": ["Chat"],
                    "summary": "Generate chat recommendations",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["fan_id", "creator_id", "system_prompt_id"],
                                    "properties": {
                                        "fan_id": {"type": "string"},
                                        "creator_id": {"type": "string"},
                                        "system_prompt_id": {"type": "string"},
                                        "chat_type": {"type": "string", "enum": ["text", "image", "video"], "default": "text"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "recommendations": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "reply_id": {"type": "string"},
                                                        "content": {"type": "string"},
                                                        "confidence": {"type": "number"}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/chatter_selected_chat_reply": {
                "post": {
                    "tags": ["Chat"],
                    "summary": "Store selected chat reply",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["fan_id", "creator_id", "reply_content"],
                                    "properties": {
                                        "fan_id": {"type": "string"},
                                        "creator_id": {"type": "string"},
                                        "reply_content": {"type": "string"},
                                        "reply_id": {"type": "string"},
                                        "chat_type": {"type": "string"},
                                        "metadata": {"type": "object"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Created",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "message_id": {"type": "string"},
                                            "message": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/get_creators": {
                "get": {
                    "tags": ["Data"],
                    "summary": "Get all creators",
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "creators": {"type": "array"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/get_fans": {
                "get": {
                    "tags": ["Data"],
                    "summary": "Get all fans",
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "fans": {"type": "array"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/get_system_prompts": {
                "get": {
                    "tags": ["Data"],
                    "summary": "Get all system prompts",
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "system_prompts": {"type": "array"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/get_chat_history": {
                "get": {
                    "tags": ["Chat"],
                    "summary": "Get chat history",
                    "parameters": [
                        {"name": "creator_id", "in": "query", "required": True, "schema": {"type": "string"}},
                        {"name": "fan_id", "in": "query", "required": True, "schema": {"type": "string"}}
                    ],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "messages": {"type": "array"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/send_fan_message": {
                "post": {
                    "tags": ["Chat"],
                    "summary": "Send fan message",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["fan_id", "creator_id", "content"],
                                    "properties": {
                                        "fan_id": {"type": "string"},
                                        "creator_id": {"type": "string"},
                                        "content": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Created",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "message_id": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/create_creator": {
                "post": {
                    "tags": ["Data"],
                    "summary": "Create new creator",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "creator_name": {"type": "string"},
                                        "niches": {"type": "array"},
                                        "persona": {"type": "array"},
                                        "nsfw": {"type": "boolean"},
                                        "emojis_enabled": {"type": "boolean"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Created",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "creator": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/create_fan": {
                "post": {
                    "tags": ["Data"],
                    "summary": "Create new fan",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "fan_name": {"type": "string"},
                                        "lifetime_spend": {"type": "number"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Created",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "fan": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/create_system_prompt": {
                "post": {
                    "tags": ["Data"],
                    "summary": "Create new system prompt",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "system_prompt": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Created",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "system_prompt": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/update_creator": {
                "put": {
                    "tags": ["Data"],
                    "summary": "Update creator",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["id"],
                                    "properties": {
                                        "id": {"type": "string"},
                                        "creator_name": {"type": "string"},
                                        "niches": {"type": "array"},
                                        "persona": {"type": "array"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "creator": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/update_fan": {
                "put": {
                    "tags": ["Data"],
                    "summary": "Update fan",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["id"],
                                    "properties": {
                                        "id": {"type": "string"},
                                        "fan_name": {"type": "string"},
                                        "lifetime_spend": {"type": "number"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "fan": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/update_system_prompt": {
                "put": {
                    "tags": ["Data"],
                    "summary": "Update system prompt",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["id"],
                                    "properties": {
                                        "id": {"type": "string"},
                                        "system_prompt": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "system_prompt": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    return jsonify(spec)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "middleman_ai"}), 200


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)

