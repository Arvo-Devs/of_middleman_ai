from datetime import datetime
from typing import Dict, List, Any
from utils.creator import get_creator_by_id
from utils.fan import get_fan_by_id
from utils.system_prompt import get_system_prompt_by_id
from supabase import Client
from mistralai import Mistral
from mistralai.models.sdkerror import SDKError
import os
import re

mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

# Sample conversations for AI training examples
SAMPLE_CONVERSATIONS = """fan: I'm definitely interested in you
creator: Then why are you ignoring my PPVs, Alex? 🥺

fan: Have any favorite scenes like that?
creator: I don't have any favorite scene, but I do have a favorite video 😈

fan: What about to make it creamy u can
creator: i can do that baby but you need to tip me first so i can make it for you 😘

fan: yes
creator: fuck it... i need you so bad rn 😩 my pussy is throbbing and i can't stop touching myself thinking about you... wanna help me?

fan: Since it's the Halloween season, you know how there are horror movies where the hot girls are tied up/suspended spreadeagle by the killer?
creator: 😈 I'm in the mood to get tied up and fucked by a real man 😏

fan: Sounds like a start
creator: are you going to make me cum until my pussy dripping wet?

fan: Mmm I want you to cuff me
creator: I want you to feel the anticipation, the desperate need for release. But you're not allowed to cum yet. Not until I say so.

fan: I'm edged
creator: I want you to edge yourself. I want you to feel that pressure building, that intense desire for release. But you're not allowed to cum yet.

fan: Never lol
creator: you're not even a little bit curious about me? 🥺

fan: --
creator: I'm in the mood to be a good girl for you… what do you want me to do? 😇

fan: Not very often but that can change
creator: oh really? what would make you think of me more? 😈

fan: I need you dripping down my chin
creator: 🥵🥵you're making me so horny rn i can't stop rubbing my pussy thinking about your tongue on me🤤

fan: Yeah Babe. Open Your mouth widly
creator: I want to feel your warm breath on my skin as you kiss me all over, I want to feel your hands exploring my body, I want to feel you inside me.

fan: Spread so i can get a taste as well
creator: i want to feel your tongue on my pussy and ass, i want you to eat me out before you fuck me hard 🥵🥵

fan: What
creator: I'm going to tell you something that's going to make you so hard…can you handle it? 😈

fan: What is the ideal cock size for you?
creator: I love a good 8-9 inch cock babe 🙈

fan: Kisses and attention you want eh?
creator: yes pleaseee 🥰

fan: Let me guess a friend
creator: I'm so glad you're here… I've been craving a real connection all day 🥰

fan: Thanks for understanding
creator: i know you would treat me right Cameron 🥰

fan: I do but I'm between jobs right now and can't spend too much
creator: I understand baby, i know you would treat me right if you could 🥰

fan: Sorry just how I felt about this
creator: its fine..

fan: Are you still working?
creator: well this is my work babyy

fan: 30 then
creator: thats the last PPVs for tonight Love please😩💦 dont cut the momentum rn🥵

fan: --
creator: ill add u once u unlock that boo.

fan: ❤️
creator: Hey babe, heres a lil test😍 I know you still want me😈so here's your chance to prove it...

fan: About how are night would be rn if we were together
creator: if you really wanna talk something like that join my VIP first Chris 🥺

fan: --
creator: u want that? 😈

fan: Like you promise I'll get a gift if so do you know how much longer to get the custom so I can get your gift 😫
creator: aww that's cute u really tryna earn that gift huh 😫 i like that energy bby, it's comin soon i promise u'll love it 😏

fan: Wondering what you're wearing
creator: what do you think?🥰

fan: Yes all the time baby
creator: Mmm baby, I just wanna be your nasty little slutt tonight 😈 you ready to play with me? 🙈"""


def replace_template_variables(
    template: str,
    creator: Dict[str, Any],
    fan: Dict[str, Any],
    chat_history: List[Dict[str, Any]]
) -> str:
    """
    Replace template variables in system prompt with actual values.
    
    Template variables:
    - {{creator_name}} - Creator's name
    - {{fan_name}} - Fan's name
    - {{lifetime_spend}} - Fan's lifetime spend
    - {{creator_niche}} - Creator's niches (comma-separated)
    - {{creator_personality}} - Creator's personality/persona tone (comma-separated)
    - {{emojis_enabled}} - Whether emojis are enabled (Yes/No)
    - {{nsfw_enabled}} - Whether NSFW is allowed (Yes/No)
    - {{emojis_used}} - Emojis to use
    - {{chat logs}} - Formatted chat history
    
    Args:
        template: System prompt template with {{variables}}
        creator: Creator data dictionary
        fan: Fan data dictionary
        chat_history: List of chat message dictionaries
        
    Returns:
        System prompt with variables replaced
    """
    # Extract values from creator
    creator_name = creator.get("name", creator.get("creator_name", "Creator"))
    creator_niches = creator.get("niches", [])
    creator_persona = creator.get("persona", [])
    emojis_enabled = creator.get("emojis_enabled", False)
    emojis_used = creator.get("emojis_used", "")
    nsfw_enabled = creator.get("nsfw", False)
    
    # Extract values from fan
    fan_name = fan.get("name", fan.get("fan_name", "Fan"))
    lifetime_spend = fan.get("lifetime_spend", 0)
    
    # Format creator niches (handle list or string)
    if isinstance(creator_niches, list):
        creator_niche_str = ", ".join(str(item) for item in creator_niches) if creator_niches else "None"
    else:
        creator_niche_str = str(creator_niches) if creator_niches else "None"
    
    # Format creator personality (handle list or string)
    if isinstance(creator_persona, list):
        creator_personality_str = ", ".join(str(item) for item in creator_persona) if creator_persona else "None"
    else:
        creator_personality_str = str(creator_persona) if creator_persona else "None"
    
    # Format emojis_used (handle list or string)
    if isinstance(emojis_used, list):
        emojis_used_str = ", ".join(str(item) for item in emojis_used) if emojis_used else ""
    else:
        emojis_used_str = str(emojis_used) if emojis_used else ""
    
    # Format chat logs
    if chat_history:
        chat_logs = []
        for chat in chat_history:
            # Format each chat message
            role = chat.get("role", chat.get("sender", "unknown"))
            content = chat.get("content", chat.get("message", ""))
            timestamp = chat.get("created_at", "")
            chat_logs.append(f"[{role}]: {content}")
        chat_logs_str = "\n".join(chat_logs)
    else:
        chat_logs_str = "No previous chat history."
    
    # Replace template variables (ensure all values are strings)
    replacements = {
        "{{creator_name}}": str(creator_name),
        "{{fan_name}}": str(fan_name),
        "{{lifetime_spend}}": str(lifetime_spend),
        "{{creator_niche}}": str(creator_niche_str),
        "{{creator_personality}}": str(creator_personality_str),
        "{{emojis_enabled}}": "Yes" if emojis_enabled else "No",
        "{{nsfw_enabled}}": "Yes" if nsfw_enabled else "No",
        "{{emojis_used}}": str(emojis_used_str),
        "{{chat logs}}": str(chat_logs_str)
    }
    
    # Perform replacements
    result = template
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    
    return result

def generate_chat_recommendations(
    supabase: Client,
    creator_id: str,
    fan_id: str,
    system_prompt_id: str,
    chat_history: List[Dict[str, str]],
    chat_type: str = "text"
) -> List[Dict[str, Any]]:
    """
    Generate 5 chat reply recommendations based on context.
    
    This is a placeholder implementation. In production, you would:
    1. Use an LLM (OpenAI, Anthropic, etc.) to generate contextual replies
    2. Consider creator persona, tone, niches
    3. Factor in fan lifetime spend for personalization
    4. Use system prompts for guidance
    5. Respect NSFW settings
    6. Adapt to chat type (text/image/video)
    
    Args:
        creator_id: Creator ID to fetch creator data
        fan_id: Fan ID to fetch fan data
        system_prompt_id: System prompt ID to fetch system prompt data
        chat_history: List of previous chat messages
        chat_type: Type of chat (text/image/video)
    
    Returns:
        List of 5 recommendation dictionaries
    """
    # Fetch creator, fan, and system prompt data using helper functions
    try:
        creator = get_creator_by_id(supabase,creator_id)
    except ValueError:
        raise ValueError("Creator not found")
    
    try:
        fan = get_fan_by_id(supabase,fan_id)
    except ValueError:
        raise ValueError("Fan not found")
    
    try:
        system_prompt_data = get_system_prompt_by_id(supabase,system_prompt_id)
        print('system_prompt_id', system_prompt_id)
        print('system_prompt_data', system_prompt_data)
    except ValueError:
        raise ValueError("System prompt not found")
    
    # Placeholder implementation - replace with actual LLM integration
    recommendations = []
    
    # Extract context
    creator_persona = creator.get("persona", [])
    creator_niches = creator.get("niches", [])
    
    # Get system prompt text (note: field name is "system_prompt" not "prompt")
    system_prompt_template = system_prompt_data.get("system_prompt", "")
    print('creator', creator)
    print('fan', fan)
    # Replace template variables with actual values
    system_prompt = replace_template_variables(
        template=system_prompt_template,
        creator=creator,
        fan=fan,
        chat_history=chat_history
    )
    
    # Append sample conversations to the system prompt for AI training examples
    system_prompt = system_prompt + "\n\nSample conversation examples:\n" + SAMPLE_CONVERSATIONS
    
    print('system_prompt', system_prompt)
    
    # Prepare messages for Mistral API
    messages = []
    
    # Add system prompt as the first message
    messages.append({
        "role": "system",
        "content": system_prompt
    })
    
    # Format chat history for Mistral (convert to proper message format)
    formatted_chat_history = []
    for chat in chat_history:
        # Map chat message to Mistral format
        role = chat.get("role", chat.get("sender", "user"))
        # Normalize role to "user" or "assistant"
        if role.lower() in ["fan", "user", "customer"]:
            role = "user"
        elif role.lower() in ["creator", "assistant", "bot"]:
            role = "assistant"
        
        content = chat.get("content", chat.get("message", ""))
        if content:  # Only add non-empty messages
            formatted_chat_history.append({
                "role": role,
                "content": content
            })
    
    # Add formatted chat history to messages
    messages.extend(formatted_chat_history)
    
    # Generate 3 recommendations using Mistral AI in a single API call
    try:
        # Add a user message asking for 3 different reply options
        request_message = {
            "role": "user",
            "content": """Generate exactly 3 different reply options. Each reply should be unique, warm, affectionate, and appropriate. Format your response as follows:

Reply 1: [your first reply here]
Reply 2: [your second reply here]
Reply 3: [your third reply here]

Make sure each reply is distinct and shows different ways to make the fan feel special and valued."""
        }
        
        # Create messages for Mistral API call
        recommendation_messages = messages + [request_message]
        
        # Call Mistral API once to get 3 recommendations
        response = mistral_client.chat.complete(
            model="mistral-small-latest",
            messages=recommendation_messages,
            temperature=0.8,  # Good balance for creativity and consistency
            max_tokens=500  # Increased to accommodate 3 replies
        )
        
        # Extract the generated content
        generated_content = response.choices[0].message.content
        
        # Parse the response to extract 3 recommendations
        # Try to find patterns like "Reply 1:", "Reply 2:", "Reply 3:" or numbered lists
        
        # Pattern to match "Reply 1:", "Reply 2:", "Reply 3:" or "1.", "2.", "3."
        reply_patterns = [
            r'Reply\s*1[:\-]\s*(.+?)(?=Reply\s*2|Reply\s*3|$)',
            r'Reply\s*2[:\-]\s*(.+?)(?=Reply\s*3|$)',
            r'Reply\s*3[:\-]\s*(.+?)$',
            r'1[\.\)]\s*(.+?)(?=2[\.\)]|$)',
            r'2[\.\)]\s*(.+?)(?=3[\.\)]|$)',
            r'3[\.\)]\s*(.+?)$'
        ]
        
        parsed_replies = []
        
        # Try to extract replies using patterns
        for pattern in reply_patterns[:3]:  # Try "Reply X:" patterns first
            matches = re.findall(pattern, generated_content, re.IGNORECASE | re.DOTALL)
            if matches:
                parsed_replies = [match.strip() for match in matches]
                break
        
        # If pattern matching didn't work, try splitting by newlines and looking for numbered items
        if not parsed_replies or len(parsed_replies) < 3:
            lines = generated_content.split('\n')
            for line in lines:
                line = line.strip()
                # Look for lines that start with numbers or "Reply"
                if re.match(r'^(Reply\s*[1-3]|[\d]+[\.\)])', line, re.IGNORECASE):
                    # Extract content after the number/prefix
                    content = re.sub(r'^(Reply\s*[1-3][:\-]?\s*|[\d]+[\.\)]\s*)', '', line, flags=re.IGNORECASE).strip()
                    if content and content not in parsed_replies:
                        parsed_replies.append(content)
        
        # If we still don't have 3 replies, split the content into 3 parts
        if len(parsed_replies) < 3:
            # Split by common delimiters or just split the text into 3 roughly equal parts
            parts = re.split(r'\n\n+|\n---\n|Reply\s*[1-3]', generated_content, flags=re.IGNORECASE)
            parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 10]
            
            if len(parts) >= 3:
                parsed_replies = parts[:3]
            elif len(parts) > 0:
                # If we have fewer parts, distribute them
                parsed_replies = parts
                # Pad with the last part if needed
                while len(parsed_replies) < 3:
                    parsed_replies.append(parsed_replies[-1] if parsed_replies else generated_content)
            else:
                # Fallback: split the entire content into 3 parts
                content_length = len(generated_content)
                chunk_size = content_length // 3
                parsed_replies = [
                    generated_content[i:i+chunk_size].strip()
                    for i in range(0, content_length, chunk_size)
                ][:3]
        
        # Create recommendation objects from parsed replies
        for i, reply_content in enumerate(parsed_replies[:3], 1):
            recommendation = {
                "reply_id": f"rec_{i}_{datetime.utcnow().timestamp()}",
                "content": reply_content.strip(),
                "confidence": 0.9 - ((i - 1) * 0.1),  # Decreasing confidence: 0.9, 0.8, 0.7
                "chat_type": chat_type
            }
            recommendations.append(recommendation)
        
        # If we got fewer than 3 recommendations, raise an error
        if len(recommendations) < 3:
            raise ValueError(f"Failed to generate enough recommendations. Only got {len(recommendations)} recommendations.")
    
    except SDKError as e:
        # If Mistral API fails, raise an error instead of returning placeholders
        error_msg = f"Mistral API error: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)
    
    except Exception as e:
        # Re-raise the exception so it can be handled by the calling function
        error_msg = f"Error generating recommendations: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)
    
    return recommendations