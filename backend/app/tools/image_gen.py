import os
import base64
import uuid
from io import BytesIO
from datetime import datetime
from huggingface_hub import InferenceClient
import traceback

# =====================================================
# CONFIGURATION
# =====================================================
IMAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "generated_images")
os.makedirs(IMAGE_DIR, exist_ok=True)
print(f"📁 Image directory: {IMAGE_DIR}")

IMAGE_STORE = {}

class ImageGenTool:
    def __init__(self):
        print("🖼️ Initializing ImageGenTool with free Stable Diffusion XL...")
        
        # Get API key from environment (optional - works without token but rate limited)
        hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_KEY")
        
        if hf_token:
            print("✅ Using Hugging Face API token")
            self.client = InferenceClient(token=hf_token)
        else:
            print("⚠️ No Hugging Face API token found! Using free tier (rate limited)")
            print("⚠️ Get a free token at: https://huggingface.co/settings/tokens")
            self.client = InferenceClient()  # No token = rate limited free tier
        
        # Use Stable Diffusion XL - FREE and works with hf-inference
        # This model is available for free with rate limits
        self.primary_model = "stabilityai/stable-diffusion-xl-base-1.0"
        
        # Fallback models if primary fails
        self.fallback_models = [
            "stabilityai/stable-diffusion-2-1",  # Free, good quality
            "runwayml/stable-diffusion-v1-5",     # Free, faster
            "prompthero/openjourney-v4",          # Free, artistic style
            "dreamshaper/dreamshaper-8"           # Free, high quality
        ]
        
        print(f"🖼️ Using primary model: {self.primary_model}")
        print(f"🖼️ Fallback models available: {len(self.fallback_models)}")

    def generate_with_model(self, prompt: str, model: str, negative_prompt: str = None, num_inference_steps: int = 25):
        """Generate image with a specific model"""
        try:
            print(f"🖼️ Trying model: {model}")
            
            if not negative_prompt:
                negative_prompt = "ugly, blurry, low quality, distorted, watermark, text, bad anatomy, deformed, extra limbs, disfigured, poorly drawn face, mutation, deformed, bad proportions, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck, Photoshop, video game, ugly, tiling, poorly drawn, crazy, out of frame, duplicate, morbid, mutilated, mutated body, anatomical nonsense"
            
            image = self.client.text_to_image(
                prompt=prompt,
                model=model,
                negative_prompt=negative_prompt,
                guidance_scale=7.5,
                num_inference_steps=num_inference_steps
            )
            
            return image
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Check if it's a rate limit or quota error
            if "402" in error_str or "payment" in error_str or "quota" in error_str or "credit" in error_str:
                print(f"⚠️ Model {model} requires payment, skipping...")
            else:
                print(f"❌ Model {model} failed: {e}")
            
            return None

    def generate(self, prompt: str, model: str = None, negative_prompt: str = None, num_inference_steps: int = 25):
        """
        Generate an image using free models with automatic fallback
        
        Args:
            prompt: Text description of the image to generate
            model: Specific model to use (optional)
            negative_prompt: Things to avoid in the image
            num_inference_steps: Number of denoising steps (lower = faster, higher = better quality)
        """
        
        # Clean and prepare the prompt
        prompt = prompt.strip()
        
        # Remove any JSON artifacts or function call leftovers
        prompt = prompt.replace('"prompt":', '').replace('"', '')
        prompt = prompt.replace('{', '').replace('}', '')
        prompt = prompt.replace('<function=', '').replace('</function>', '')
        prompt = prompt.strip()
        
        print(f"🖼️ Generating image for prompt: {prompt[:150]}...")
        print(f"🖼️ Negative prompt: {negative_prompt[:100] if negative_prompt else 'Default'}...")

        # Try primary model first
        if not model:
            print(f"🖼️ Using primary model: {self.primary_model}")
            image = self.generate_with_model(
                prompt, 
                self.primary_model, 
                negative_prompt, 
                num_inference_steps
            )
            
            # If primary fails, try fallback models
            if image is None:
                print("⚠️ Primary model failed, trying fallback models...")
                for fallback_model in self.fallback_models:
                    print(f"🔄 Attempting fallback model: {fallback_model}")
                    image = self.generate_with_model(
                        prompt, 
                        fallback_model, 
                        negative_prompt, 
                        num_inference_steps
                    )
                    if image is not None:
                        print(f"✅ Successfully generated with fallback: {fallback_model}")
                        break
        else:
            # Use specified model
            image = self.generate_with_model(
                prompt, 
                model, 
                negative_prompt, 
                num_inference_steps
            )

        # If all models failed, return error
        if image is None:
            error_msg = "All image generation models failed. Please try again later or with a different prompt."
            print(f"❌ {error_msg}")
            return {
                "type": "error",
                "error": error_msg,
                "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt
            }

        try:
            # Save with timestamp and UUID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sdxl_{timestamp}_{uuid.uuid4().hex[:8]}.png"
            filepath = os.path.join(IMAGE_DIR, filename)

            # Save to disk
            image.save(filepath, format="PNG")
            print(f"✅ Image saved: {filepath}")

            # Convert to base64
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            image_base64 = base64.b64encode(buffer.getvalue()).decode()

            # Generate unique ID
            image_id = f"img_{uuid.uuid4().hex}"

            # Store in memory
            IMAGE_STORE[image_id] = {
                "type": "image",
                "image_id": image_id,
                "filename": filename,
                "filepath": filepath,
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "model": model or self.primary_model,
                "url": f"/images/{filename}",
                "image_base64": image_base64,
                "created_at": timestamp
            }

            print(f"✅ Image generated successfully! ID: {image_id}")
            
            return {
                "type": "image",
                "image_id": image_id,
                "url": f"/images/{filename}",
                "image_base64": image_base64,
                "model": model or self.primary_model,
                "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                "filename": filename,
                "size": f"{image.size[0]}x{image.size[1]}" if hasattr(image, 'size') else "unknown"
            }

        except Exception as e:
            print(f"❌ Error saving/processing image: {e}")
            print(traceback.format_exc())
            
            return {
                "type": "error",
                "error": f"Failed to process generated image: {str(e)}",
                "error_type": type(e).__name__,
                "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt
            }

    def generate_with_enhanced_prompt(self, base_prompt: str, enhancements: list = None):
        """Generate image with enhanced prompt"""
        enhanced_prompt = base_prompt
        if enhancements and isinstance(enhancements, list):
            enhanced_prompt = f"{base_prompt}. {' '.join(enhancements)}"
        
        # Add quality tags for better results
        quality_tags = "high quality, 4k, detailed, professional fashion photography, studio lighting, full body shot"
        enhanced_prompt = f"{enhanced_prompt}, {quality_tags}"
        
        return self.generate(enhanced_prompt)


# Singleton instance
_image_tool_instance = None

def get_image_tool():
    """Get or create the singleton ImageGenTool instance"""
    global _image_tool_instance
    if _image_tool_instance is None:
        _image_tool_instance = ImageGenTool()
    return _image_tool_instance

def generate_image(prompt: str, **kwargs) -> dict:
    """
    Generate an image with free Stable Diffusion models
    
    Args:
        prompt: Text description of the image
        **kwargs: Additional arguments passed to generate()
    
    Returns:
        Dictionary with image data or error information
    """
    print(f"🖼️ generate_image called with prompt: {prompt[:100]}...")
    
    tool = get_image_tool()
    result = tool.generate(prompt, **kwargs)

    if result.get("type") == "error":
        print(f"❌ Image generation failed: {result.get('error')}")
    elif "image_base64" not in result:
        print("⚠️ WARNING: image_base64 missing in result")
    else:
        print(f"✅ Image generated successfully! ID: {result.get('image_id', 'N/A')}")

    return result

def generate_fashion_image(prompt: str, gender: str = None, body_type: str = None, occasion: str = None) -> dict:
    """
    Generate a fashion-specific image with enhanced prompting
    
    Args:
        prompt: Base fashion prompt
        gender: User's gender for personalization
        body_type: User's body type for personalization
        occasion: Event or occasion
    """
    enhancements = []
    
    if gender:
        enhancements.append(f"{gender.lower()} model wearing")
    if body_type:
        enhancements.append(f"flattering for {body_type.lower()} body type")
    if occasion:
        enhancements.append(f"for {occasion} event")
    
    tool = get_image_tool()
    return tool.generate_with_enhanced_prompt(prompt, enhancements)

def get_image_by_id(image_id: str):
    """Retrieve an image by its ID from memory store"""
    return IMAGE_STORE.get(image_id)

def list_images(limit: int = 50):
    """List all generated images in memory (limited to prevent memory issues)"""
    all_images = list(IMAGE_STORE.values())
    # Sort by created_at descending (newest first)
    all_images.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return all_images[:limit]

def clear_old_images(max_age_hours: int = 24):
    """Clear images older than specified hours from memory store"""
    import time
    current_time = time.time()
    to_delete = []
    
    for image_id, image_data in IMAGE_STORE.items():
        # Parse timestamp from filename or created_at
        created_at = image_data.get('created_at', '')
        if created_at:
            try:
                # Convert timestamp string to epoch time
                timestamp = datetime.strptime(created_at, "%Y%m%d_%H%M%S").timestamp()
                age_hours = (current_time - timestamp) / 3600
                if age_hours > max_age_hours:
                    to_delete.append(image_id)
                    
                    # Optionally delete file from disk
                    filepath = image_data.get('filepath')
                    if filepath and os.path.exists(filepath):
                        try:
                            os.remove(filepath)
                            print(f"🗑️ Deleted old image file: {filepath}")
                        except Exception as e:
                            print(f"⚠️ Failed to delete file {filepath}: {e}")
                            
            except Exception as e:
                print(f"⚠️ Error parsing timestamp for {image_id}: {e}")
    
    for image_id in to_delete:
        del IMAGE_STORE[image_id]
    
    if to_delete:
        print(f"🧹 Cleared {len(to_delete)} old images from memory")
    
    return len(to_delete)


# =====================================================
# AUTO-CLEANUP ON IMPORT
# =====================================================
# Clean up images older than 24 hours when module loads
try:
    cleared = clear_old_images(24)
    if cleared > 0:
        print(f"🧹 Auto-cleaned {cleared} old images")
except Exception as e:
    print(f"⚠️ Auto-cleanup failed: {e}")

print("✅ Image generation module ready with free SDXL models")