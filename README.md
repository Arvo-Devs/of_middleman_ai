# middleman_ai
POC for middleman AI

## Overview

Flask API and web interface for a middleman AI chat recommendation system. The system provides endpoints for recommending chat replies, managing creators/fans/system prompts, and includes a full-featured web UI with chatbot simulation and API documentation.

## Features

- **Chat Recommendations** - AI-powered chat reply suggestions using Mistral AI
- **Creator/Fan/System Prompt Management** - Full CRUD operations via API and UI
- **Interactive Chatbot** - Simulate conversations between creators and fans
- **Web Interface** - Modern, responsive UI with tabbed navigation
- **API Documentation** - Built-in Swagger UI for API exploration
- **Authentication** - Login system with API key protection

## Setup

### Prerequisites

- Python 3.8+
- Supabase account and project
- Mistral AI API key

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file with the following:
   ```
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_KEY=your_supabase_service_role_key
   MISTRAL_API_KEY=your_mistral_api_key
   SECRET_KEY=your_secret_key_for_sessions
   LOGIN_USERNAME=your_username
   LOGIN_PASSWORD=your_password
   API_KEY=your_api_key_for_endpoints
   PORT=5001
   FLASK_ENV=development
   ```

### Running the Application

```bash
python app.py
```

The application will run on `http://localhost:5001` by default.

## Web Interface

Access the web interface at `http://localhost:5001` after logging in.

### Features:
- **Main Interface Tab**: 
  - Select/create creators, fans, and system prompts
  - Generate AI chat recommendations
  - Interactive chatbot for testing conversations
  - View and edit details for all entities
  
- **API Documentation Tab**:
  - Interactive Swagger UI
  - Test endpoints directly from the browser
  - Complete API reference

## API Endpoints

All API endpoints require the `X-API-Key` header with a valid API key.

### Authentication

#### POST `/login`
Login to get API key.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "api_key": "string"
}
```

#### POST `/logout`
Logout and clear session.

---

### Chat Endpoints

#### POST `/recommended_chats`
Generate AI-powered chat reply recommendations.

**Request Body:**
```json
{
  "fan_id": "string",
  "creator_id": "string",
  "system_prompt_id": "string",
  "chat_type": "text"  // optional: "text", "image", or "video"
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "reply_id": "string",
      "content": "string",
      "confidence": 0.8
    }
  ],
  "fan_id": "string",
  "creator_id": "string",
  "chat_type": "text"
}
```

#### POST `/chatter_selected_chat_reply`
Store a selected chat reply in the database.

**Request Body:**
```json
{
  "fan_id": "string",
  "creator_id": "string",
  "reply_content": "string",
  "reply_id": "string",  // optional, stored in metadata
  "chat_type": "text",  // optional, stored in metadata
  "metadata": {}        // optional additional data
}
```

**Response:**
```json
{
  "success": true,
  "message_id": "string",
  "message": "Chat reply stored successfully"
}
```

#### GET `/get_chat_history`
Get chat history between a creator and fan.

**Query Parameters:**
- `creator_id` (required)
- `fan_id` (required)

**Response:**
```json
{
  "messages": [
    {
      "id": "string",
      "sender": "creator" | "fan",
      "content": "string",
      "created_at": "string"
    }
  ]
}
```

#### POST `/send_fan_message`
Store a fan message in the database.

**Request Body:**
```json
{
  "fan_id": "string",
  "creator_id": "string",
  "content": "string"
}
```

**Response:**
```json
{
  "success": true,
  "message_id": "string",
  "message": "Fan message stored successfully"
}
```

---

### Data Management Endpoints

#### Creators

- **GET `/get_creators`** - Get all creators
- **GET `/get_creator_details`** - Get creator by ID (query param: `id`)
- **POST `/create_creator`** - Create new creator
- **PUT `/update_creator`** - Update creator

#### Fans

- **GET `/get_fans`** - Get all fans
- **GET `/get_fan_details`** - Get fan by ID (query param: `id`)
- **POST `/create_fan`** - Create new fan
- **PUT `/update_fan`** - Update fan

#### System Prompts

- **GET `/get_system_prompts`** - Get all system prompts
- **POST `/get_system_prompt_details`** - Get system prompt by ID
- **POST `/create_system_prompt`** - Create new system prompt
- **PUT `/update_system_prompt`** - Update system prompt

---

### Utility Endpoints

#### GET `/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "middleman_ai"
}
```

#### GET `/api-docs/openapi.json`
OpenAPI 3.0 specification for all endpoints.

---

## Database Schema

The API expects the following Supabase tables:

### `creator`
- `id` (uuid, primary key)
- `creator_name` (text)
- `niches` (array)
- `persona` (array)
- `nsfw` (boolean)
- `emojis_enabled` (boolean)
- `creator_image` (text, optional)
- Additional fields as needed

### `fan`
- `id` (uuid, primary key)
- `fan_name` (text)
- `lifetime_spend` (numeric)
- Additional fields as needed

### `system_prompt`
- `id` (uuid, primary key)
- `system_prompt` (text)
- Additional fields as needed

### `of_chat_message`
- `id` (uuid, primary key)
- `creator_id` (uuid, references creator)
- `fan_id` (uuid, references fan)
- `sender` (text, 'creator' or 'fan')
- `content` (text)
- `created_at` (timestamptz)
- `metadata` (jsonb)

---

## Authentication

### Web Interface
- Login required to access the web interface
- Session-based authentication
- Credentials configured via environment variables

### API Endpoints
- All API endpoints require `X-API-Key` header
- API key obtained after successful login
- API key stored in browser localStorage

---

## Usage

### Web Interface Workflow

1. **Login** - Enter username and password
2. **Select Entities** - Choose a creator, fan, and system prompt
3. **Generate Recommendations** - Click "Generate Recommendations" button
4. **Test in Chatbot** - Use the chatbot interface to simulate conversations
5. **View API Docs** - Switch to API Documentation tab to explore endpoints

### API Workflow

1. **Login** - POST to `/login` to get API key
2. **Use API Key** - Include `X-API-Key` header in all requests
3. **Manage Data** - Create/read/update creators, fans, and system prompts
4. **Generate Recommendations** - POST to `/recommended_chats` with context
5. **Store Messages** - POST to `/send_fan_message` or `/chatter_selected_chat_reply`

---

## Architecture

- **Backend**: Flask (Python)
- **Database**: Supabase (PostgreSQL)
- **AI**: Mistral AI for chat recommendations
- **Frontend**: Vanilla JavaScript with modern CSS
- **API Docs**: Swagger UI (OpenAPI 3.0)

---

## Notes

- The system uses Mistral AI for generating contextual chat recommendations
- All API endpoints are protected with API key authentication
- The web interface provides full CRUD operations for all entities
- Chat history is stored in `of_chat_message` table
- System prompts support template variables that are dynamically replaced
- Sample conversations are included in prompts for better AI training

---

## Development

### Project Structure
```
middleman_ai/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Main web interface
├── static/
│   └── js/
│       └── app.js        # Frontend JavaScript
├── utils/
│   ├── creator.py        # Creator helper functions
│   ├── fan.py            # Fan helper functions
│   ├── system_prompt.py  # System prompt helper functions
│   └── chats.py          # Chat recommendation logic
└── ddls/                 # Database schema files
```

---

## License

[Add your license here]
