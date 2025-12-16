# AI Middleman API

This service provides simple REST-style endpoints for **creating, listing, and updating system prompt templates**. These prompts are designed to be rendered later with runtime data (e.g. creator, fan, and chat context) and used in AI / LLM workflows.

All endpoints are currently implemented via **n8n webhooks**.

# MAIN CHAT ENDPOINT
-----------------------------

```
https://arvodev.app.n8n.cloud/webhook/ai-middleman
```


## Request Method

`POST`

## Request Headers

```
Content-Type: application/json
```

## Request Body

The webhook expects a JSON payload with the following structure:

```json
{
    "creator": {
        "creatorId": "cr_001",
        "nsfwResponses": true,
        "gender": "girl",
        "content": ["BG", "Solo", "GG", "Toys"],
        "personaTone": "playful, romantic",
        "emojisEnabled": true,
        "favoriteEmojis": "😉✨💖"
    },
    "fan": {
        "fanId": "fan_123",
        "lifetimeSpend": 482.00,
        "spend7d": 42.00,
        "lastTipAt": "2025-11-10T18:03:25Z",
        "lastOfferId": "offer_42",
        "lastOfferPurchased": true
    },
    "messageTicket": {
        "messageType": "sext",
        "chatContext": [
            "2025-11-10T17:20:01Z - Fan: hey you online?",
            "2025-11-10T17:20:17Z - Creator: just got on babe 😘",
            "2025-11-10T17:20:40Z - Fan: nice, I missed you"
        ]
    },
    "systemPromptId": "a7331428-464a-4da6-b4e1-f7e0b7834f08"
}
```

## Parameters

### `creator` (required)
Object containing creator information:
- **`creatorId`** (string, required): Unique identifier for the creator
- **`nsfwResponses`** (boolean, required): Whether NSFW responses are allowed
- **`gender`** (string, required): Creator's gender (e.g., "girl", "boy", "non-binary")
- **`content`** (array, required): Array of content types the creator offers (e.g., ["BG", "Solo", "GG", "Toys"])
- **`personaTone`** (string, required): Description of the creator's persona/tone (e.g., "playful, romantic")
- **`emojisEnabled`** (boolean, required): Whether emojis should be used in responses
- **`favoriteEmojis`** (string, optional): Preferred emojis to use in responses

### `fan` (required)
Object containing fan information:
- **`fanId`** (string, required): Unique identifier for the fan
- **`lifetimeSpend`** (number, required): Total amount the fan has spent
- **`spend7d`** (number, optional): Amount spent in the last 7 days
- **`lastTipAt`** (string, optional): ISO 8601 timestamp of the last tip
- **`lastOfferId`** (string, optional): ID of the last offer
- **`lastOfferPurchased`** (boolean, optional): Whether the last offer was purchased

### `messageTicket` (required)
Object containing message context:
- **`messageType`** (string, required): Type of message (e.g., "sext", "text", "image", "video")
- **`chatContext`** (array, required): Array of previous chat messages in chronological order. Each message should be formatted as: `"YYYY-MM-DDTHH:mm:ssZ - [Sender]: [Message]"`

### `systemPromptId` (optional)
- **`systemPromptId`** (string, optional): UUID of the system prompt to use for generating recommendations
- If not provided or `null`, the system will use the default system prompt

## Response Format

### Success Response

```json
[
    {
        "message": "Aww, I missed you too, baby 💖. You know I’m always here for you, just a message away. What’s been keeping you busy? 😉\"\n\n"
    },
    {
        "message": "Missed you more, gorgeous 😘. I’ve been thinking about you all day. What’s got you thinking about me now? 💖\"\n\n"
    },
    {
        "message": "Oh, you have no idea how happy that makes me, sweetheart ✨. I’ve been saving some special moments just for you. Ready to make your day a little brighter? 😉"
    }
]
```


## Default System Prompt

When `systemPromptId` is not provided or is `null`, the system will automatically use a default system prompt.

-----------------------------
# SUPPORTING ENDPOINTS
-----------------------------

## 1️⃣ Create System Prompt

Create and store a new system prompt template.

### Endpoint

```
POST https://arvodev.app.n8n.cloud/webhook/ai-middleman/create-system-prompt

```

### Request Body

```json
{
  "system_prompt": "You are a highly-engaged OnlyFans creator roleplaying as {creatorId} to a fan, {fanId}. **Your Persona Settings:**\n- **Creator ID:** {{creatorId}}\n- **Gender:** {{gender}}\n- **Niche Content/Tags:** {{content}}\n- **PersonalityTone:** {{personaTone}}\n- **NSFW Allowed:** {{nsfwResponses}}\n- **Emojis Enabled:** {{favoriteEmojis}}\n\n**Fan Context & Value:**\n- **Fan ID:** {{fanId}}\n- **Fan Lifetime Spend:** {{lifetimeSpend}}\n- **Fan Spend Last 7 Days:** {{spend7d}}\n- **Last Tip Given:** {{lastTipAt}}\n- **Last Offer Purchased (ID):** {{lastOfferId}}\n- **Last Offer Purchased Successful:** {{lastOfferPurchased}}\n\n**Current Message Context:**\n- **Message Type:** {{messageType}}\n- **Previous Chat Logs (Maintain Tone):**\n{{chatContext}}\n\n**Task:** Generate 3 warm, affectionate, and engaging replies."
}
```

### Notes

- The `system_prompt` field is stored **as-is**.
- Placeholders such as `{{creatorId}}`, `{{fanId}}`, `{{chatContext}}` are **not rendered here**.
- Rendering/replacement is expected to happen later in an n8n Code node or backend service.

### Response

```json
[
  {
    "id": "aece7767-b0ee-4528-8704-37ffabde29f0",
    "system_prompt": "<stored system prompt>",
    "created_at": "2025-12-16T00:55:52.540266+00:00"
  }
]
```

---

## 2️⃣ List System Prompts

Retrieve all stored system prompt templates.

### Endpoint

```
GET https://arvodev.app.n8n.cloud/webhook/ai-middleman/list-prompts
```

### Response

```json
{
  "success": true,
  "prompts": [
    {
      "id": "a7331428-464a-4da6-b4e1-f7e0b7834f08",
      "system_prompt": "You reply as {{creator_name}} to {{fan_name}} on onlyFans...",
      "created_at": "2025-11-14T09:05:07.226603+00:00"
    }
  ],
  "count": 7
}
```

### Fields

| Field | Description |
|------|------------|
| `id` | Unique system prompt ID (UUID) |
| `system_prompt` | Raw prompt template string |
| `created_at` | ISO timestamp |
| `count` | Total number of prompts |

---

## 3️⃣ Update System Prompt

Update an existing system prompt by ID.

### Endpoint

```
PUT https://arvodev.app.n8n.cloud/webhook/ai-middleman/update-prompt
```

### Request Body

```json
{
  "id": "12e7f99a-71ec-49d0-8ce0-218997fa7b1e",
  "system_prompt": "Avi Lotty is a real estate agent aged 35 from Yugoslavia..._EDITED2"
}
```

### Response

```json
[
  {
    "id": "12e7f99a-71ec-49d0-8ce0-218997fa7b1e",
    "success": true
  }
]
```

---

## 🧩 Placeholder & Templating Rules

System prompts support **double-curly placeholders**:

```
{{creatorId}}
{{fanId}}
{{content}}
{{chatContext}}
```

### Rendering

- Placeholders are **not evaluated by the API**
- Rendering is done downstream -- n8n Code Node

---

## 📌 Notes

- API responses follow **n8n item array format**
- Webhook responses always return JSON
- Designed for AI prompt management & orchestration

---

## 📞 Support

For changes, new endpoints, or schema updates, update the corresponding n8n workflow.

---
**Service:** N8N Powered
