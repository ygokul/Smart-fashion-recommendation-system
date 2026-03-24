"""
FashAI SmartFit - AI Fashion Stylist Agent
Event-aware fashion assistant with image generation and personalized styling
"""

import os
import json
import time
import traceback
from dotenv import load_dotenv
from typing import Optional, Dict, List, Any
import asyncio
from contextlib import contextmanager

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.tools.image_gen import generate_image, IMAGE_STORE
from app.services.prompts import INSTRUCTION
from app.services.memory import add_message, get_recent_messages, clear_old_messages

# =====================================================
# ENV
# =====================================================
load_dotenv(override=True)

MODEL_ID = os.getenv(
    "GROQ_MODEL_ID",
    "groq/llama-3.3-70b-versatile"
)

groq_model = LiteLlm(
    model=MODEL_ID,
    api_key=os.getenv("GROQ_API_KEY")
)

# =====================================================
# DATABASE CONNECTION FOR PROFILE ACCESS
# =====================================================


# =====================================================
# EVENT-BASED PROMPT ENHANCEMENT (Updated with gender-specific events)
# =====================================================
# Gender-specific event outfits
MALE_EVENT_TYPES = {
    'wedding': {
        'keywords': ['wedding', 'marriage', 'shaadi', 'vivah', 'reception', 'mandap'],
        'outfit_types': ['sherwani', 'wedding suit', 'bandhgala', 'indian wedding attire', 
                        'traditional kurta pajama', 'designer sherwani'],
        'colors': ['ivory', 'gold', 'maroon', 'navy', 'black', 'emerald', 'royal blue'],
        'fabrics': ['silk', 'velvet', 'brocade', 'jacquard', 'raw silk'],
        'accessories': ['safa', 'mojari', 'necklace', 'watch', 'wedding brooch']
    },
    'party': {
        'keywords': ['party', 'celebration', 'birthday', 'anniversary', 'get-together', 'bash'],
        'outfit_types': ['blazer', 'party kurta', 'designer shirt', 'smart casual', 
                        'evening wear', 'party shirt'],
        'colors': ['black', 'navy', 'burgundy', 'charcoal', 'white', 'dark green'],
        'fabrics': ['linen', 'cotton', 'wool blend', 'silk blend'],
        'accessories': ['watch', 'bracelet', 'pocket square', 'loafers']
    },
    'office': {
        'keywords': ['office', 'work', 'corporate', 'business', 'meeting', 'professional'],
        'outfit_types': ['formal suit', 'business attire', 'formal shirt', 'blazer', 
                        'office wear', 'corporate suit'],
        'colors': ['navy', 'charcoal', 'grey', 'white', 'blue', 'black'],
        'fabrics': ['wool', 'cotton', 'linen', 'polyester blend'],
        'accessories': ['tie', 'watch', 'belt', 'formal shoes', 'briefcase']
    },
    'casual': {
        'keywords': ['casual', 'everyday', 'daily wear', 'comfortable', 'relaxed', 'informal'],
        'outfit_types': ['jeans and t-shirt', 'casual shirt', 'polo shirt', 'chinos', 
                        'cargo pants', 'hoodie'],
        'colors': ['denim blue', 'white', 'black', 'grey', 'olive', 'khaki'],
        'fabrics': ['cotton', 'denim', 'linen', 'jersey'],
        'accessories': ['sneakers', 'cap', 'backpack', 'sunglasses']
    },
    'festival': {
        'keywords': ['diwali', 'festival', 'puja', 'religious', 'celebration', 'traditional'],
        'outfit_types': ['kurta pajama', 'ethnic wear', 'traditional kurta', 'designer kurta', 
                        'festive attire', 'indian ethnic'],
        'colors': ['white', 'cream', 'gold', 'maroon', 'navy', 'black'],
        'fabrics': ['cotton', 'linen', 'silk', 'khadi'],
        'accessories': ['mojari', 'necklace', 'bracelet', 'traditional watch']
    },
    'date': {
        'keywords': ['date', 'romantic', 'dinner', 'movie', 'romantic dinner', 'outing'],
        'outfit_types': ['smart casual', 'button-down shirt', 'chinos', 'blazer', 
                        'date night outfit', 'casual blazer'],
        'colors': ['navy', 'burgundy', 'white', 'charcoal', 'dark green'],
        'fabrics': ['cotton', 'linen', 'wool blend'],
        'accessories': ['watch', 'cologne', 'leather shoes', 'belt']
    },
    'beach': {
        'keywords': ['beach', 'vacation', 'holiday', 'summer', 'pool', 'resort'],
        'outfit_types': ['beach shorts', 'linen shirt', 'resort wear', 'summer outfit', 
                        'vacation wear', 'swim trunks'],
        'colors': ['white', 'blue', 'khaki', 'coral', 'pastels'],
        'fabrics': ['linen', 'cotton', 'light fabrics'],
        'accessories': ['sunglasses', 'hat', 'flip flops', 'beach bag']
    },
    'gym': {
        'keywords': ['gym', 'workout', 'exercise', 'fitness', 'yoga', 'training'],
        'outfit_types': ['gym shorts', 't-shirt', 'track pants', 'athleisure', 
                        'workout clothes', 'fitness wear'],
        'colors': ['black', 'grey', 'dark blue', 'bright colors'],
        'fabrics': ['polyester', 'spandex', 'moisture-wicking'],
        'accessories': ['sports shoes', 'fitness tracker', 'water bottle', 'gym bag']
    }
}

FEMALE_EVENT_TYPES = {
    'wedding': {
        'keywords': ['wedding', 'marriage', 'shaadi', 'vivah', 'reception', 'mandap'],
        'outfit_types': ['lehenga', 'wedding saree', 'bridal gown', 'designer lehenga', 
                        'anarkali', 'reception dress'],
        'colors': ['red', 'gold', 'maroon', 'pink', 'ivory', 'emerald', 'royal blue'],
        'fabrics': ['silk', 'velvet', 'brocade', 'net', 'organza', 'chiffon'],
        'accessories': ['heavy jewelry', 'maang tikka', 'jhumkas', 'kundan set', 'wedding clutch']
    },
    'party': {
        'keywords': ['party', 'celebration', 'birthday', 'anniversary', 'get-together', 'bash'],
        'outfit_types': ['cocktail dress', 'party lehenga', 'sequin gown', 'glam outfit', 
                        'evening dress', 'party wear saree'],
        'colors': ['black', 'silver', 'gold', 'red', 'navy', 'emerald', 'burgundy'],
        'fabrics': ['sequin', 'satin', 'velvet', 'net', 'lace', 'chiffon'],
        'accessories': ['statement jewelry', 'clutch', 'high heels', 'hair accessories']
    },
    'office': {
        'keywords': ['office', 'work', 'corporate', 'business', 'meeting', 'professional'],
        'outfit_types': ['formal suit', 'business saree', 'formal kurta', 'blazer dress', 
                        'office wear', 'corporate attire'],
        'colors': ['navy', 'black', 'grey', 'white', 'beige', 'pastels', 'olive'],
        'fabrics': ['cotton', 'linen', 'wool', 'polyester', 'crepe'],
        'accessories': ['minimal jewelry', 'watch', 'laptop bag', 'formal shoes']
    },
    'casual': {
        'keywords': ['casual', 'everyday', 'daily wear', 'comfortable', 'relaxed', 'informal'],
        'outfit_types': ['jeans and top', 'casual kurta', 'palazzo set', 'maxi dress', 
                        't-shirt dress', 'kurti with leggings'],
        'colors': ['denim blue', 'white', 'black', 'pastels', 'earth tones', 'stripes'],
        'fabrics': ['cotton', 'linen', 'denim', 'jersey', 'rayon'],
        'accessories': ['minimal jewelry', 'sneakers', 'tote bag', 'sunglasses']
    },
    'festival': {
        'keywords': ['diwali', 'festival', 'puja', 'religious', 'celebration', 'traditional'],
        'outfit_types': ['festive saree', 'lehenga choli', 'festive kurta', 'anarkali', 
                        'ethnic dress', 'designer kurta'],
        'colors': ['bright colors', 'red', 'orange', 'yellow', 'pink', 'green', 'gold'],
        'fabrics': ['silk', 'georgette', 'chiffon', 'cotton', 'velvet'],
        'accessories': ['traditional jewelry', 'bindi', 'jhumkas', 'potli bag']
    },
    'date': {
        'keywords': ['date', 'romantic', 'dinner', 'movie', 'romantic dinner', 'outing'],
        'outfit_types': ['romantic dress', 'date night outfit', 'elegant dress', 
                        'casual chic', 'evening gown'],
        'colors': ['red', 'black', 'white', 'pastels', 'burgundy', 'navy'],
        'fabrics': ['lace', 'satin', 'chiffon', 'velvet', 'silk'],
        'accessories': ['delicate jewelry', 'clutch', 'heels', 'perfume']
    },
    'beach': {
        'keywords': ['beach', 'vacation', 'holiday', 'summer', 'pool', 'resort'],
        'outfit_types': ['beach dress', 'cover-up', 'swimwear', 'resort wear', 
                        'summer outfit', 'maxi dress'],
        'colors': ['white', 'blue', 'coral', 'yellow', 'turquoise', 'stripes'],
        'fabrics': ['cotton', 'linen', 'voile', 'chiffon', 'light fabrics'],
        'accessories': ['sunglasses', 'hat', 'beach bag', 'sandals', 'cover-up']
    },
    'gym': {
        'keywords': ['gym', 'workout', 'exercise', 'fitness', 'yoga', 'training'],
        'outfit_types': ['sports bra and leggings', 'gym wear', 'workout clothes', 
                        'yoga outfit', 'athleisure'],
        'colors': ['black', 'grey', 'bright colors', 'neon', 'dark tones'],
        'fabrics': ['spandex', 'polyester', 'nylon', 'moisture-wicking'],
        'accessories': ['sports shoes', 'fitness tracker', 'water bottle', 'gym bag']
    }
}

NEUTRAL_EVENT_TYPES = {
    'casual': {
        'keywords': ['casual', 'everyday', 'daily wear', 'comfortable', 'relaxed', 'informal'],
        'outfit_types': ['comfortable clothing', 'casual wear', 'relaxed fit', 
                        'everyday clothes', 'simple outfit'],
        'colors': ['neutral tones', 'earth colors', 'black', 'white', 'grey'],
        'fabrics': ['cotton', 'linen', 'comfortable fabrics'],
        'accessories': ['comfortable shoes', 'bag', 'sunglasses']
    },
    'office': {
        'keywords': ['office', 'work', 'corporate', 'business', 'meeting', 'professional'],
        'outfit_types': ['professional attire', 'business wear', 'office clothing', 
                        'corporate outfit', 'work attire'],
        'colors': ['neutral colors', 'black', 'navy', 'grey', 'white'],
        'fabrics': ['professional fabrics', 'cotton', 'wool blend'],
        'accessories': ['professional accessories', 'bag', 'shoes']
    }
}

def detect_event_type(user_input: str) -> Optional[Dict[str, Any]]:
    """Detect event type from user input"""
    user_input_lower = user_input.lower()
    
    # Check all event types (will be filtered by gender later)
    all_events = {**MALE_EVENT_TYPES, **FEMALE_EVENT_TYPES, **NEUTRAL_EVENT_TYPES}
    
    for event_name, event_data in all_events.items():
        for keyword in event_data['keywords']:
            if keyword in user_input_lower:
                return {
                    'event_name': event_name,
                    'event_data': event_data,
                    'confidence': 'high'
                }
    
    # Check for common event phrases
    event_phrases = {
        'going to a wedding': 'wedding',
        'attending a party': 'party',
        'office event': 'office',
        'corporate meeting': 'office',
        'casual outing': 'casual',
        'festival celebration': 'festival',
        'date night': 'date',
        'beach vacation': 'beach',
        'gym session': 'gym'
    }
    
    for phrase, event_name in event_phrases.items():
        if phrase in user_input_lower:
            return {
                'event_name': event_name,
                'event_data': all_events.get(event_name, {}),
                'confidence': 'medium'
            }
    
    return None

def get_event_types_by_gender(gender: Optional[str]) -> Dict[str, Any]:
    """Get appropriate event types based on gender"""
    if gender:
        gender_lower = gender.lower()
        if 'male' in gender_lower:
            return MALE_EVENT_TYPES
        elif 'female' in gender_lower:
            return FEMALE_EVENT_TYPES
        elif 'non-binary' in gender_lower:
            return NEUTRAL_EVENT_TYPES
    
    # Default to combined events for "Prefer not to say" or no gender
    return {**MALE_EVENT_TYPES, **FEMALE_EVENT_TYPES, **NEUTRAL_EVENT_TYPES}

def enhance_prompt_for_event(prompt: str, event_info: Dict[str, Any], profile_data: Optional[Dict[str, Any]] = None) -> str:
    """Enhance image generation prompt based on detected event and gender"""
    if not event_info:
        return prompt
    
    event_name = event_info['event_name']
    event_data = event_info['event_data']
    
    # Base event enhancement
    enhancements = [f"for a {event_name} event"]
    
    # Add outfit type suggestion
    if event_data.get('outfit_types'):
        outfit_type = event_data['outfit_types'][0]
        enhancements.append(f"wearing a {outfit_type}")
    
    # Add color suggestions
    if event_data.get('colors'):
        colors = ", ".join(event_data['colors'][:3])
        enhancements.append(f"in {colors} colors")
    
    # Add fabric suggestions
    if event_data.get('fabrics'):
        fabrics = ", ".join(event_data['fabrics'][:2])
        enhancements.append(f"made of {fabrics} fabric")
    
    # Add accessories
    if event_data.get('accessories'):
        accessories = ", ".join(event_data['accessories'][:2])
        enhancements.append(f"with {accessories}")
    
    # Add profile-based enhancements
    if profile_data and profile_data.get('has_profile', False):
        profile_enhancements = []
        
        # Gender context
        gender = profile_data.get('gender')
        if gender:
            if 'male' in gender.lower():
                profile_enhancements.append("masculine style, tailored fit")
            elif 'female' in gender.lower():
                profile_enhancements.append("feminine style, flattering fit")
            elif 'non-binary' in gender.lower():
                profile_enhancements.append("gender-neutral style, comfortable fit")
        
        # Body type considerations
        if profile_data.get('body_type'):
            body_type = profile_data['body_type'].lower()
            body_enhancements = {
                'rectangle': "with defined waist to create curves",
                'hourglass': "that accentuates the natural waist",
                'pear': "with emphasis on upper body, A-line silhouette",
                'apple': "empire waistline, flowy fabric",
                'inverted triangle': "minimal shoulder detailing, A-line bottom"
            }
            if body_type in body_enhancements:
                profile_enhancements.append(body_enhancements[body_type])
        
        # Skin tone color matching
        if profile_data.get('skin_tone'):
            skin_tone = profile_data['skin_tone'].lower()
            skin_tone_colors = {
                'fair': "soft pastel colors",
                'light': "jewel tones like navy and emerald",
                'medium': "earthy tones like olive and terracotta",
                'olive': "deep jewel tones like berry and forest green",
                'tan': "warm colors like coral and gold",
                'dark': "bright colors and metallics"
            }
            if skin_tone in skin_tone_colors:
                profile_enhancements.append(f"in colors that complement {skin_tone} skin tone")
        
        # Face shape context for necklines
        if profile_data.get('face_shape'):
            face_shape = profile_data['face_shape'].lower()
            neckline_recommendations = {
                'oval': 'versatile neckline',
                'round': 'V-neck or scoop neck to elongate face',
                'square': 'round or sweetheart neckline to soften features',
                'heart': 'scoop or boat neck to balance chin',
                'diamond': 'off-shoulder or sweetheart neckline',
                'oblong': 'crew neck or boat neck to widen appearance'
            }
            if face_shape in neckline_recommendations:
                profile_enhancements.append(f"with {neckline_recommendations[face_shape]}")
        
        # Height context for silhouette
        if profile_data.get('height'):
            try:
                height_cm = float(profile_data['height'])
                if height_cm < 160:
                    profile_enhancements.append("petite-friendly silhouette with vertical lines")
                elif height_cm > 175:
                    profile_enhancements.append("elongated silhouette for tall frame")
                else:
                    profile_enhancements.append("balanced silhouette")
            except:
                pass
        
        # Add profile enhancements
        if profile_enhancements:
            enhancements.extend(profile_enhancements)
    
    # Combine all enhancements
    enhanced_prompt = f"{prompt}. {' '.join(enhancements)}. Fashion-forward, realistic, high-quality image showing full outfit."
    
    print(f"🎯 Event-enhanced prompt: {enhanced_prompt}")
    return enhanced_prompt

def generate_event_prompt(user_input: str, event_info: Dict[str, Any], gender: Optional[str] = None) -> str:
    """Generate a prompt for event-based image generation with gender context"""
    event_name = event_info['event_name']
    
    # Get gender-specific base prompts
    gender_context = ""
    if gender:
        if 'male' in gender.lower():
            gender_context = "male fashion, "
        elif 'female' in gender.lower():
            gender_context = "female fashion, "
        elif 'non-binary' in gender.lower():
            gender_context = "gender-neutral fashion, "
    
    # Base prompts for different events
    base_prompts = {
        'wedding': f"elegant and luxurious {gender_context}{event_name} outfit with intricate details",
        'party': f"stylish and glamorous {gender_context}{event_name} outfit with modern design",
        'office': f"professional and sophisticated {gender_context}{event_name} attire",
        'casual': f"comfortable and chic {gender_context}{event_name} outfit",
        'festival': f"vibrant and traditional {gender_context}{event_name} wear",
        'date': f"romantic and attractive {gender_context}{event_name} outfit",
        'beach': f"relaxed and stylish {gender_context}{event_name} vacation outfit",
        'gym': f"functional and trendy {gender_context}{event_name} fitness outfit"
    }
    
    base_prompt = base_prompts.get(event_name, f"appropriate {gender_context}outfit for a {event_name} event")
    
    # Add context from user input
    if "indian" in user_input.lower() or "ethnic" in user_input.lower():
        base_prompt += ", indian ethnic style"
    elif "western" in user_input.lower():
        base_prompt += ", western style"
    elif "fusion" in user_input.lower():
        base_prompt += ", indo-western fusion style"
    
    return base_prompt

# =====================================================
# PROFILE HELPER FUNCTIONS (Updated with gender field)
# =====================================================
from ..data import get_user, get_user_profile

async def get_user_profile(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user profile and user details from JSON data for personalization"""
    if not user_id:
        print(f"⚠️ No user_id provided for profile lookup")
        return None

    user = get_user(user_id)
    if not user:
        print(f"⚠️ No user found with ID {user_id}")
        return None

    profile = get_user_profile(user_id)
    
    # Combine user data and profile data
    combined_data = {
        "user_info": {
            "user_id": user['id'],
            "username": user['username'],
            "email": user['email'],
            "subscription_tier": user.get('subscription_tier', 'free'),
            "created_at": str(user.get('created_at')) if user.get('created_at') else None
        }
    }
    
    if profile:
        combined_data.update(profile)
        combined_data['has_profile'] = True
        
        # Print complete profile info
        gender_info = f"Gender: {profile.get('gender', 'Not specified')}, "
        print(f"✅ Loaded complete profile for user {user_id}: {gender_info}Body={profile.get('body_type')}, Skin={profile.get('skin_tone')}")
    else:
        print(f"⚠️ No profile found for user {user_id}, but user exists")
        combined_data['has_profile'] = False
        # Add default profile structure with gender
        combined_data.update({
            'gender': None,
            'body_type': None,
            'skin_tone': None,
            'face_shape': None,
            'hair_type': None,
            'style_preferences': [],
            'measurements': {},
            'height': None,
            'weight': None,
            'bust': None,
            'waist': None,
            'hips': None,
            'is_complete': False,
            'completed_sections': 0
        })
    
    return combined_data

def enhance_prompt_with_profile(prompt: str, profile_data: Dict[str, Any]) -> str:
    """Enhance image generation prompt with user profile information including gender"""
    
    if not profile_data or not profile_data.get('has_profile', False):
        return prompt
    
    enhanced_prompt = prompt
    enhancements = []
    
    # Add gender context first (most important for fashion)
    gender = profile_data.get('gender')
    if gender:
        if 'male' in gender.lower():
            enhancements.append("male model wearing")
        elif 'female' in gender.lower():
            enhancements.append("female model wearing")
        elif 'non-binary' in gender.lower():
            enhancements.append("gender-neutral fashion model wearing")
        else:
            enhancements.append("person wearing")
    else:
        enhancements.append("person wearing")
    
    # Add body type context
    if profile_data.get('body_type'):
        body_type = profile_data['body_type'].lower()
        body_type_mapping = {
            'rectangle': 'rectangular body shape with balanced proportions',
            'hourglass': 'hourglass figure with defined waist',
            'pear': 'pear-shaped body with wider hips than shoulders',
            'apple': 'apple-shaped body with fuller midsection',
            'inverted triangle': 'inverted triangle body with broader shoulders'
        }
        if body_type in body_type_mapping:
            enhancements.append(f"flattering for {body_type_mapping[body_type]}")
    
    # Add skin tone context for color recommendations
    if profile_data.get('skin_tone'):
        skin_tone = profile_data['skin_tone'].lower()
        skin_tone_colors = {
            'fair': 'soft pastels like blush pink, baby blue, mint green',
            'light': 'jewel tones like navy, burgundy, emerald green',
            'medium': 'earthy tones like olive green, mustard yellow, terracotta',
            'olive': 'deep jewel tones like berry, wine, forest green',
            'tan': 'warm tones like coral, orange, gold, chocolate brown',
            'dark': 'bright colors like fuchsia, royal blue, emerald, metallics'
        }
        if skin_tone in skin_tone_colors:
            enhancements.append(f"in colors that complement {skin_tone} skin tone")
    
    # Add face shape context for necklines
    if profile_data.get('face_shape'):
        face_shape = profile_data['face_shape'].lower()
        neckline_recommendations = {
            'oval': 'versatile neckline',
            'round': 'V-neck or scoop neck to elongate face',
            'square': 'round or sweetheart neckline to soften features',
            'heart': 'scoop or boat neck to balance chin',
            'diamond': 'off-shoulder or sweetheart neckline',
            'oblong': 'crew neck or boat neck to widen appearance'
        }
        if face_shape in neckline_recommendations:
            enhancements.append(f"with {neckline_recommendations[face_shape]}")
    
    # Add height context for silhouette
    if profile_data.get('height'):
        try:
            height_cm = float(profile_data['height'])
            if height_cm < 160:
                enhancements.append("petite-friendly silhouette with vertical lines")
            elif height_cm > 175:
                enhancements.append("elongated silhouette for tall frame")
            else:
                enhancements.append("balanced silhouette")
        except:
            pass
    
    # Add style preferences
    if profile_data.get('style_preferences') and profile_data['style_preferences']:
        style_prefs = profile_data['style_preferences']
        if isinstance(style_prefs, list) and len(style_prefs) > 0:
            enhancements.append(f"with {', '.join(style_prefs[:2])} elements")
    
    # Add subscription tier consideration
    user_info = profile_data.get('user_info', {})
    if user_info.get('subscription_tier') == 'premium':
        enhancements.append("premium quality, detailed design")
    
    # Combine enhancements
    if enhancements:
        # Remove "person wearing" if it's already part of the prompt
        if "person wearing" in enhancements[0] and "wearing" in enhanced_prompt:
            enhanced_prompt = enhanced_prompt.replace("wearing", enhancements[0])
            enhanced_prompt += f". {', '.join(enhancements[1:])}. Fashion-forward, realistic, high-quality image showing full outfit on model."
        else:
            enhanced_prompt += f". {', '.join(enhancements)}. Fashion-forward, realistic, high-quality image showing full outfit on model."
        print(f"🎨 Enhanced prompt with profile: {enhanced_prompt}")
    
    return enhanced_prompt

def get_styling_advice(profile_data: Dict[str, Any], event_info: Optional[Dict[str, Any]] = None) -> str:
    """Generate personalized styling advice based on profile and event"""
    advice = []
    
    # Event-specific advice (gender-aware)
    if event_info:
        event_name = event_info['event_name']
        gender = profile_data.get('gender') if profile_data else None
        
        advice.append(f"**For your {event_name} event:**")
        
        if event_info['event_data'].get('outfit_types'):
            outfit_suggestions = ", ".join(event_info['event_data']['outfit_types'][:2])
            advice.append(f"- Consider {outfit_suggestions}")
        
        if event_info['event_data'].get('colors'):
            color_suggestions = ", ".join(event_info['event_data']['colors'][:3])
            advice.append(f"- Colors like {color_suggestions} work well")
        
        # Gender-specific advice for events
        if gender:
            if 'male' in gender.lower() and event_name in ['wedding', 'party']:
                advice.append("- Make sure your outfit is well-tailored for a sharp look")
            elif 'female' in gender.lower() and event_name in ['wedding', 'party']:
                advice.append("- Choose jewelry that complements your outfit without overpowering it")
    
    # Profile-based advice (including gender)
    if profile_data and profile_data.get('has_profile', False):
        # User info reference
        user_info = profile_data.get('user_info', {})
        if user_info.get('username'):
            advice.append(f"👋 **Personalized for {user_info['username']}:**")
        
        # Gender-specific advice
        gender = profile_data.get('gender')
        if gender:
            gender_advice = {
                'male': "Focus on fit and tailoring for a polished appearance",
                'female': "Balance proportions and choose flattering silhouettes",
                'non-binary': "Choose clothing that expresses your personal style comfortably"
            }
            gender_lower = gender.lower()
            for key, msg in gender_advice.items():
                if key in gender_lower:
                    advice.append(f"**As a {gender}:** {msg}")
                    break
        
        # Body type advice
        if profile_data.get('body_type'):
            body_advice = {
                'rectangle': "Add definition with belts or cinched waists to create curves",
                'hourglass': "Fitted styles that accentuate your waist will highlight your proportions",
                'pear': "A-line silhouettes and details on upper body balance proportions",
                'apple': "Empire waistlines and flowy fabrics create flattering silhouette",
                'inverted triangle': "Balance broader shoulders with A-line bottoms"
            }
            body_type = profile_data['body_type'].lower()
            if body_type in body_advice:
                advice.append(f"**For your {body_type} body type:** {body_advice[body_type]}")
        
        # Color advice
        if profile_data.get('skin_tone'):
            color_advice = {
                'fair': "Pastels and soft colors complement fair skin beautifully",
                'light': "Jewel tones make light skin tone glow with radiance",
                'medium': "Earthy tones and rich colors work wonderfully with medium skin",
                'olive': "Deep jewel tones and berry shades enhance olive skin tones",
                'tan': "Warm colors like coral and gold highlight tan skin gorgeously",
                'dark': "Bright colors and metallics create stunning contrast with darker skin"
            }
            skin_tone = profile_data['skin_tone'].lower()
            if skin_tone in color_advice:
                advice.append(f"**For your {skin_tone} skin tone:** {color_advice[skin_tone]}")
    
    if advice:
        return "\n\n💡 **Personalized Styling Tips**:\n" + "\n".join(advice)
    
    return ""

def create_profile_context_for_llm(profile_data: Dict[str, Any]) -> str:
    """Create a detailed profile context string for LLM prompts"""
    if not profile_data or not profile_data.get('has_profile', False):
        return ""
    
    context_parts = []
    
    # Gender (most important for fashion)
    gender = profile_data.get('gender')
    if gender:
        context_parts.append(f"Gender: {gender}")
    
    # Body measurements and type
    if profile_data.get('body_type'):
        context_parts.append(f"Body Type: {profile_data['body_type']}")
    
    # Physical attributes
    if profile_data.get('height'):
        context_parts.append(f"Height: {profile_data['height']}cm")
    if profile_data.get('weight'):
        context_parts.append(f"Weight: {profile_data['weight']}kg")
    
    # Appearance
    if profile_data.get('skin_tone'):
        context_parts.append(f"Skin Tone: {profile_data['skin_tone']}")
    if profile_data.get('face_shape'):
        context_parts.append(f"Face Shape: {profile_data['face_shape']}")
    if profile_data.get('hair_type'):
        context_parts.append(f"Hair Type: {profile_data['hair_type']}")
    
    # Style preferences
    if profile_data.get('style_preferences') and profile_data['style_preferences']:
        prefs = ", ".join(profile_data['style_preferences'])
        context_parts.append(f"Style Preferences: {prefs}")
    
    # Measurements
    measurements = profile_data.get('measurements', {})
    if measurements:
        measurement_strs = []
        for key, value in measurements.items():
            if value:
                measurement_strs.append(f"{key}: {value}")
        if measurement_strs:
            context_parts.append(f"Measurements: {', '.join(measurement_strs)}")
    
    if context_parts:
        return "User Profile: " + "; ".join(context_parts)
    
    return ""

# =====================================================
# FASHION IMAGE GENERATION TOOLS ONLY (Updated with gender)
# =====================================================
async def generate_event_based_image_tool(user_input: str, event_info: Dict[str, Any], user_id: Optional[int] = None) -> str:
    """Generate event-based fashion image with user profile personalization"""
    print(f"🎯 Event-based image tool called for event: {event_info['event_name']}")
    
    # Get user profile if available
    profile_data = None
    gender = None
    if user_id:
        profile_data = await get_user_profile(user_id)
        if profile_data and profile_data.get('has_profile', False):
            gender = profile_data.get('gender')
    
    # Update event data based on gender
    if gender:
        gender_specific_events = get_event_types_by_gender(gender)
        event_info['event_data'] = gender_specific_events.get(event_info['event_name'], event_info['event_data'])
    
    # Generate base prompt for the event with gender context
    base_prompt = generate_event_prompt(user_input, event_info, gender)
    
    # First enhance with event information
    event_enhanced_prompt = enhance_prompt_for_event(base_prompt, event_info, profile_data)
    
    # Then enhance with profile data
    final_prompt = enhance_prompt_with_profile(event_enhanced_prompt, profile_data)
    
    print(f"🎯 Final event-based prompt: {final_prompt}")
    
    try:
        result = generate_image(final_prompt)
        print(f"✅ Event-based fashion image generated successfully for {event_info['event_name']}")
        
        # Store event and profile context in metadata
        event_context = {
            "event_type": event_info['event_name'],
            "gender_specific": gender is not None,
            "outfit_suggestions": event_info['event_data'].get('outfit_types', [])[:2]
        }
        
        profile_context = {}
        user_info_context = {}
        if profile_data:
            profile_context = {
                "gender": profile_data.get('gender'),
                "body_type": profile_data.get('body_type'),
                "skin_tone": profile_data.get('skin_tone'),
                "face_shape": profile_data.get('face_shape'),
                "height": profile_data.get('height')
            }
            if profile_data.get('user_info'):
                user_info_context = {
                    "username": profile_data['user_info'].get('username'),
                    "subscription_tier": profile_data['user_info'].get('subscription_tier')
                }
        
        minimal_result = {
            "type": "image",
            "image_id": result.get("image_id"),
            "prompt": final_prompt,
            "original_input": user_input,
            "event_context": event_context,
            "filename": result.get("filename"),
            "size": result.get("size"),
            "url": result.get("url"),
            "profile_context": profile_context,
            "user_info_context": user_info_context,
            "personalized": bool(profile_data and profile_data.get('has_profile', False)),
            "event_based": True
        }
        
        return json.dumps(minimal_result)
        
    except Exception as e:
        error_msg = f"Error generating event-based fashion image: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        return json.dumps({"error": error_msg, "type": "error"})

async def generate_fashion_image_tool(prompt: str, user_id: Optional[int] = None, event_info: Optional[Dict[str, Any]] = None) -> str:
    """Main fashion image generation tool with event detection and gender support"""
    print(f"🔧 Fashion image tool called with prompt: '{prompt}' | User ID: {user_id}")
    
    # Get user profile early to get gender for event detection
    profile_data = None
    gender = None
    if user_id:
        profile_data = await get_user_profile(user_id)
        if profile_data and profile_data.get('has_profile', False):
            gender = profile_data.get('gender')
    
    # Check if event is mentioned in the prompt
    if not event_info:
        event_info = detect_event_type(prompt)
    
    # If event detected, update event data based on gender
    if event_info and gender:
        gender_specific_events = get_event_types_by_gender(gender)
        event_info['event_data'] = gender_specific_events.get(event_info['event_name'], event_info['event_data'])
    
    # If event detected, use event-based generation
    if event_info:
        return await generate_event_based_image_tool(prompt, event_info, user_id)
    
    # Otherwise use standard generation with profile
    # Clean the prompt
    try:
        if prompt.startswith('{'):
            data = json.loads(prompt)
            if 'prompt' in data:
                prompt = data['prompt']
                print(f"🔧 Extracted prompt from JSON: '{prompt}'")
    except:
        pass
    
    # Enhance prompt with profile data (including gender)
    enhanced_prompt = prompt
    if profile_data:
        enhanced_prompt = enhance_prompt_with_profile(prompt, profile_data)
        print(f"🎨 Enhanced prompt with profile data (Gender: {gender})")
    
    try:
        result = generate_image(enhanced_prompt)
        print(f"✅ Fashion image generated successfully")
        
        # Store profile context in metadata
        profile_context = {}
        user_info_context = {}
        if profile_data:
            profile_context = {
                "gender": profile_data.get('gender'),
                "body_type": profile_data.get('body_type'),
                "skin_tone": profile_data.get('skin_tone'),
                "face_shape": profile_data.get('face_shape'),
                "height": profile_data.get('height')
            }
            if profile_data.get('user_info'):
                user_info_context = {
                    "username": profile_data['user_info'].get('username'),
                    "subscription_tier": profile_data['user_info'].get('subscription_tier')
                }
        
        minimal_result = {
            "type": "image",
            "image_id": result.get("image_id"),
            "prompt": enhanced_prompt,
            "original_prompt": prompt,
            "filename": result.get("filename"),
            "size": result.get("size"),
            "url": result.get("url"),
            "profile_context": profile_context,
            "user_info_context": user_info_context,
            "personalized": bool(profile_data and profile_data.get('has_profile', False)),
            "event_based": False
        }
        
        return json.dumps(minimal_result)
        
    except Exception as e:
        error_msg = f"Error generating fashion image: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        return json.dumps({"error": error_msg, "type": "error"})

# =====================================================
# TOOL FUNCTIONS FOR AGENT
# =====================================================
async def fashion_image_tool_authenticated(prompt: str) -> str:
    """Image generation tool for authenticated users"""
    print(f"🔧 Authenticated fashion image tool called with prompt: '{prompt}'")
    # This function will be called by the agent, but we'll handle user_id in the wrapper
    return await generate_fashion_image_tool(prompt, None)

async def fashion_image_tool_anonymous(prompt: str) -> str:
    """Image generation tool for anonymous users"""
    print(f"🔧 Anonymous fashion image tool called with prompt: '{prompt}'")
    return await generate_fashion_image_tool(prompt, None)

# =====================================================
# AGENT CREATION
# =====================================================
# Create agents for different contexts
anonymous_agent = LlmAgent(
    name="fashai_stylist_anonymous",
    model=groq_model,
    instruction=INSTRUCTION,
    tools=[fashion_image_tool_anonymous]  # Only fashion image tool
)

authenticated_agent = LlmAgent(
    name="fashai_stylist_authenticated",
    model=groq_model,
    instruction=INSTRUCTION,
    tools=[fashion_image_tool_authenticated]  # Only fashion image tool
)

session_service = InMemorySessionService()

anonymous_runner = Runner(
    agent=anonymous_agent,
    app_name="agents",
    session_service=session_service,
)

authenticated_runner = Runner(
    agent=authenticated_agent,
    app_name="agents",
    session_service=session_service,
)

# =====================================================
# FASHION AWARE AGENT WRAPPER (Updated with gender context)
# =====================================================
class FashionAwareAgentWrapper:
    def __init__(self, anonymous_runner, authenticated_runner, session_service):
        self.anonymous_runner = anonymous_runner
        self.authenticated_runner = authenticated_runner
        self.session_service = session_service
    
    async def _ensure_session(self, session_id: str):
        """Ensure session exists"""
        try:
            await self.session_service.create_session(
                app_name="agents",
                user_id="default_user",
                session_id=session_id
            )
        except Exception:
            pass  # Session already exists

    def _clean_history_for_llm(self, session_id: str):
        """Get conversation history but remove large content like base64 images"""
        messages = get_recent_messages(session_id, count=20)
        cleaned_messages = []
        
        for msg in messages:
            content = msg.get("content", "")
            
            # Skip messages with very long content (likely base64 images)
            if len(content) > 10000:  # Skip very long messages
                role = msg.get("role", "")
                if role == "assistant":
                    # Replace with a short summary
                    cleaned_messages.append({
                        "role": role,
                        "content": "[Image was generated and displayed to user]"
                    })
                continue
            elif len(content) > 500:  # Truncate long text
                cleaned_messages.append({
                    "role": msg.get("role", ""),
                    "content": content[:500] + "..."
                })
            else:
                cleaned_messages.append(msg)
        
        return cleaned_messages

    def _is_fashion_query(self, query: str) -> bool:
        """Check if the query is fashion-related"""
        fashion_keywords = [
            'outfit', 'dress', 'wear', 'clothes', 'fashion', 'style', 'look', 'attire', 
            'saree', 'kurta', 'lehenga', 'salwar', 'western', 'fusion', 'ethnic',
            'garment', 'ensemble', 'apparel', 'wardrobe', 'couture', 'design',
            'blouse', 'skirt', 'pants', 'shirt', 'top', 'jacket', 'coat',
            'accessory', 'jewelry', 'shoes', 'bag', 'scarf', 'hat',
            'color', 'pattern', 'fabric', 'material', 'texture',
            'formal', 'casual', 'party', 'wedding', 'office', 'event',
            'recommend', 'suggest', 'advice', 'help with', 'what to wear',
            'body type', 'skin tone', 'face shape', 'fit', 'size',
            # Gender-specific keywords
            'men', 'women', 'male', 'female', 'masculine', 'feminine', 'unisex',
            # Event-related keywords
            'going to', 'attending', 'event', 'occasion', 'function',
            'wedding', 'party', 'office', 'corporate', 'casual',
            'festival', 'date', 'beach', 'gym', 'workout',
            # Image generation keywords
            'generate', 'create', 'show me', 'picture', 'image', 'photo', 'visual',
            'design', 'draw', 'illustration', 'render'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in fashion_keywords)

    async def stream_generate(self, session_id: str, user_input: str, user_id: Optional[int] = None):
        """Generate response with event detection and personalized fashion advice including gender"""
        await self._ensure_session(session_id)
        from app.services.memory import clear_old_messages
        clear_old_messages(session_id, keep_last=10)
        
        # Check if this is a fashion-related query
        is_fashion_query = self._is_fashion_query(user_input)
        
        # Detect event type from user input
        event_info = detect_event_type(user_input)
        event_detected = event_info is not None
        
        # Get user profile for context (only for authenticated users)
        profile_data = None
        profile_available = False
        gender = None
        if user_id:
            profile_data = await get_user_profile(user_id)
            if profile_data and profile_data.get('has_profile', False):
                profile_available = True
                gender = profile_data.get('gender')
                print(f"👤 Profile loaded for user {user_id}: Gender={gender}, Body={profile_data.get('body_type')}, Skin={profile_data.get('skin_tone')}")
        
        # Update event info based on gender
        if event_detected and gender:
            gender_specific_events = get_event_types_by_gender(gender)
            event_info['event_data'] = gender_specific_events.get(event_info['event_name'], event_info['event_data'])
        
        # Prepare enhanced input with profile and event context
        enhanced_input = user_input
        
        if is_fashion_query:
            # Create detailed profile context for LLM
            profile_context = create_profile_context_for_llm(profile_data) if profile_data else ""
            
            if profile_context:
                enhanced_input = f"{user_input}\n\n{profile_context}"
                print(f"👗 Enhanced fashion query with detailed profile context")
            
            if event_detected:
                # Add event context to the query
                event_name = event_info['event_name']
                gender_context = f" (gender-appropriate for {gender})" if gender else ""
                enhanced_input = f"{enhanced_input}\n\nThis is for a {event_name} event{gender_context}."
                print(f"🎯 Event detected: {event_name}{gender_context}")
        
        # Add user message to memory
        from app.services.memory import add_message
        add_message(session_id, "user", user_input[:500])
        
        print(f"📤 Starting stream for session: {session_id}")
        print(f"📤 Query type: {'FASHION' if is_fashion_query else 'General'}")
        print(f"📤 Event detected: {event_detected} ({event_info['event_name'] if event_detected else 'None'})")
        print(f"📤 Profile available: {profile_available}")
        print(f"📤 Gender: {gender or 'Not specified'}")
        
        new_message = types.Content(
            role="user",
            parts=[types.Part(text=enhanced_input[:500])]
        )
        
        try:
            # Track if we need to generate event-based image
            should_generate_event_image = is_fashion_query and event_detected
            image_generated = False
            last_image_id = None
            
            # Choose the right runner based on authentication
            runner = self.authenticated_runner if user_id else self.anonymous_runner
            
            async for event in runner.run_async(
                user_id="default_user",
                session_id=session_id,
                new_message=new_message
            ):
                # Check for tool calls in the event
                if hasattr(event, 'tool_calls') and event.tool_calls:
                    print(f"🛠️ Found {len(event.tool_calls)} tool calls")
                    
                    for tool_call in event.tool_calls:
                        tool_name = tool_call.name
                        print(f"🛠️ Processing tool call: {tool_name}")
                        
                        # Get tool arguments
                        tool_args = {}
                        if hasattr(tool_call, 'args'):
                            try:
                                if isinstance(tool_call.args, str):
                                    tool_args = json.loads(tool_call.args)
                                else:
                                    tool_args = tool_call.args
                            except:
                                tool_args = {"prompt": str(tool_call.args)}
                        
                        prompt = tool_args.get('prompt', '') or tool_args.get('query', '') or enhanced_input
                        
                        # Handle the tool call based on its name
                        if tool_name in ["fashion_image_tool_anonymous", "fashion_image_tool_authenticated"]:
                            print(f"🛠️ Calling fashion image tool with prompt: '{prompt[:100]}...'")
                            
                            result = await generate_fashion_image_tool(
                                prompt, 
                                user_id, 
                                event_info if event_detected else None
                            )
                            
                            image_generated = True
                            
                            # Send image response
                            try:
                                meta = json.loads(result)
                                if meta.get("type") == "image":
                                    image_id = meta.get("image_id")
                                    last_image_id = image_id
                                    
                                    if image_id and image_id in IMAGE_STORE:
                                        image_data = IMAGE_STORE[image_id]
                                        
                                        image_response = {
                                            "type": "image",
                                            "image_id": image_id,
                                            "prompt": image_data.get("prompt", prompt),
                                            "original_prompt": meta.get("original_prompt", prompt),
                                            "filename": image_data.get("filename", ""),
                                            "url": f"http://127.0.0.1:8000/images/{image_data.get('filename', '')}",
                                            "image_base64": image_data.get("image_base64", ""),
                                            "model": image_data.get("model", "stabilityai/stable-diffusion-2-1"),
                                            "size": image_data.get("size", "512x512"),
                                            "format": image_data.get("format", "PNG"),
                                            "profile_context": meta.get("profile_context", {}),
                                            "user_info_context": meta.get("user_info_context", {}),
                                            "personalized": meta.get("personalized", False),
                                            "event_based": meta.get("event_based", False),
                                            "event_context": meta.get("event_context", {})
                                        }
                                        
                                        print(f"📤 SENDING FASHION IMAGE: {image_response['filename']}")
                                        print(f"   Gender in profile: {meta.get('profile_context', {}).get('gender', 'Not specified')}")
                                        yield json.dumps(image_response)
                                        
                                        # Add to conversation history with gender context
                                        from app.services.memory import add_message
                                        event_text = f" for {event_info['event_name']} event" if event_info else ""
                                        gender_text = f" (Gender: {meta.get('profile_context', {}).get('gender', 'Not specified')})" if profile_available else ""
                                        add_message(session_id, "assistant", 
                                                  f"[Fashion Image Generated{event_text}{gender_text}: {image_data['prompt'][:50]}...]")
                            except json.JSONDecodeError as je:
                                print(f"❌ JSON decode error: {je}")
                                # Send as text if not JSON
                                text_response = {
                                    "type": "text",
                                    "content": result[:1000]
                                }
                                yield json.dumps(text_response)
                            except Exception as e:
                                print(f"❌ Error processing image response: {e}")
                                yield json.dumps({
                                    "type": "error",
                                    "content": f"Image generation error: {str(e)}"
                                })
                        
                        # Continue to next event
                        continue
                
                # Text content from LLM
                if hasattr(event, 'content') and event.content:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            text = part.text
                            print(f"📤 Text from LLM: '{text[:100]}...'")
                            
                            # Skip redundant "image generated" text if we already sent image
                            if image_generated and ("generated" in text.lower() or "created" in text.lower() or "here is" in text.lower() or "image" in text.lower()):
                                print(f"⏩ Skipping redundant text about image generation")
                                continue
                            
                            # Add personalized styling advice for fashion queries
                            if is_fashion_query and (profile_available or event_detected):
                                styling_advice = get_styling_advice(profile_data, event_info)
                                if styling_advice and styling_advice not in text:
                                    text += styling_advice
                                    print(f"💡 Added personalized styling advice (Gender: {gender})")
                            
                            from app.services.memory import add_message
                            truncated_text = text[:500] if len(text) > 500 else text
                            add_message(session_id, "assistant", truncated_text)
                            
                            yield json.dumps({
                                "type": "text",
                                "content": text,
                                "has_profile": profile_available,
                                "is_fashion": is_fashion_query,
                                "event_detected": event_detected,
                                "event_name": event_info['event_name'] if event_detected else None,
                                "gender": gender
                            })
            
            # Fallback: If we didn't generate an image but it's a fashion query with event
            if not image_generated and is_fashion_query and event_detected:
                print(f"🔍 No image generated for event, triggering fallback event image...")
                # Generate event-based image directly
                result = await generate_event_based_image_tool(user_input, event_info, user_id)
                
                try:
                    meta = json.loads(result)
                    if meta.get("type") == "image":
                        image_id = meta.get("image_id")
                        last_image_id = image_id
                        
                        if image_id and image_id in IMAGE_STORE:
                            image_data = IMAGE_STORE[image_id]
                            
                            image_response = {
                                "type": "image",
                                "image_id": image_id,
                                "prompt": image_data.get("prompt", user_input),
                                "original_prompt": meta.get("original_prompt", user_input),
                                "filename": image_data.get("filename", ""),
                                "url": f"http://127.0.0.1:8000/images/{image_data.get('filename', '')}",
                                "image_base64": image_data.get("image_base64", ""),
                                "model": image_data.get("model", "stabilityai/stable-diffusion-2-1"),
                                "size": image_data.get("size", "512x512"),
                                "format": image_data.get("format", "PNG"),
                                "profile_context": meta.get("profile_context", {}),
                                "user_info_context": meta.get("user_info_context", {}),
                                "personalized": meta.get("personalized", False),
                                "event_based": meta.get("event_based", False),
                                "event_context": meta.get("event_context", {})
                            }
                            
                            print(f"📤 SENDING FALLBACK FASHION IMAGE: {image_response['filename']}")
                            yield json.dumps(image_response)
                            
                            # Add to conversation history
                            from app.services.memory import add_message
                            event_text = f" for {event_info['event_name']} event"
                            gender_text = f" (Gender: {meta.get('profile_context', {}).get('gender', 'Not specified')})" if profile_available else ""
                            add_message(session_id, "assistant", 
                                      f"[Fallback Fashion Image Generated{event_text}{gender_text}: {image_data['prompt'][:50]}...]")
                except Exception as e:
                    print(f"❌ Error in fallback image generation: {e}")
        
        except Exception as e:
            print(f"❌ Stream error: {str(e)}")
            traceback.print_exc()
            yield json.dumps({
                "type": "error",
                "content": f"Stream error: {str(e)}"
            })
        
        print(f"✅ Stream generation completed for session: {session_id}")

    async def generate(self, session_id: str, user_input: str, user_id: Optional[int] = None):
        """Non-streaming generation with profile and event integration"""
        await self._ensure_session(session_id)
        from app.services.memory import clear_old_messages
        clear_old_messages(session_id, keep_last=10)
        
        # Check if this is a fashion-related query
        is_fashion_query = self._is_fashion_query(user_input)
        
        # Detect event type
        event_info = detect_event_type(user_input)
        
        # Get user profile for context
        profile_data = None
        gender = None
        if user_id:
            profile_data = await get_user_profile(user_id)
            if profile_data and profile_data.get('has_profile', False):
                gender = profile_data.get('gender')
        
        # Update event info based on gender
        if event_info and gender:
            gender_specific_events = get_event_types_by_gender(gender)
            event_info['event_data'] = gender_specific_events.get(event_info['event_name'], event_info['event_data'])
        
        # Prepare enhanced input with profile and event context
        enhanced_input = user_input
        
        # Create detailed profile context for LLM
        profile_context = create_profile_context_for_llm(profile_data) if profile_data else ""
        if profile_context:
            enhanced_input = f"{user_input}\n\n{profile_context}"
        
        if is_fashion_query:
            if event_info:
                gender_context = f" (gender-appropriate for {gender})" if gender else ""
                enhanced_input = f"{enhanced_input}\n\nThis is for a {event_info['event_name']} event{gender_context}."
        
        # Truncate input
        truncated_input = enhanced_input[:500] if len(enhanced_input) > 500 else enhanced_input
        from app.services.memory import add_message
        add_message(session_id, "user", truncated_input)
        
        # Choose the right runner based on authentication
        runner = self.authenticated_runner if user_id else self.anonymous_runner

        full_text = ""
        new_message = types.Content(
            role="user",
            parts=[types.Part(text=truncated_input)]
        )
        
        try:
            async for event in runner.run_async(
                user_id="default_user",
                session_id=session_id,
                new_message=new_message
            ):
                if hasattr(event, 'content') and event.content and event.content.parts:
                    text = "".join(p.text for p in event.content.parts if hasattr(p, 'text') and p.text)
                    full_text += text
                    
                    # Add personalized styling advice for fashion queries
                    if is_fashion_query and (profile_data or event_info):
                        styling_advice = get_styling_advice(profile_data, event_info)
                        if styling_advice and styling_advice not in full_text:
                            full_text += styling_advice
                    
                    # Truncate before storing
                    truncated_text = text[:500] if len(text) > 500 else text
                    from app.services.memory import add_message
                    add_message(session_id, "assistant", truncated_text)
                
                if hasattr(event, 'tool_results') and event.tool_results:
                    for tool_result in event.tool_results:
                        try:
                            if hasattr(tool_result, 'content'):
                                meta = json.loads(tool_result.content)
                                
                                # Handle different tool results
                                if meta.get('type') == 'image':
                                    image_id = meta.get("image_id")
                                    if image_id and image_id in IMAGE_STORE:
                                        image = IMAGE_STORE[image_id]
                                        # Add profile and event context to image response
                                        image["profile_context"] = meta.get("profile_context", {})
                                        image["user_info_context"] = meta.get("user_info_context", {})
                                        image["personalized"] = meta.get("personalized", False)
                                        image["event_based"] = meta.get("event_based", False)
                                        image["event_context"] = meta.get("event_context", {})
                                        from app.services.memory import add_message
                                        add_message(session_id, "assistant", 
                                                   f"[Fashion Image Generated (Gender: {meta.get('profile_context', {}).get('gender', 'Not specified')}): {image['prompt'][:100]}...]")
                                        return image
                                    
                        except:
                            pass
                            
        except Exception as e:
            print(f"❌ Generation error: {str(e)}")
            return {"type": "error", "content": str(e)}

        if full_text:
            return {"type": "text", "content": full_text.strip()}
        
        return {"type": "text", "content": "No response generated"}
    
    async def clear_session_memory(self, session_id: str):
        """Clear session memory"""
        from app.services.memory import clear_session
        clear_session(session_id)
        return {"status": "success", "message": "Session memory cleared"}


# =====================================================
# MAIN AGENT EXPORT
# =====================================================
llm = FashionAwareAgentWrapper(anonymous_runner, authenticated_runner, session_service)

# Export for main.py
__all__ = ['llm', 'FashionAwareAgentWrapper', 'get_user_profile', 'detect_event_type', 
           'MALE_EVENT_TYPES', 'FEMALE_EVENT_TYPES', 'NEUTRAL_EVENT_TYPES']