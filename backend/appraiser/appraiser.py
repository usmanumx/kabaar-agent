#!/usr/bin/env python3
"""
Appraiser Component for KabaarAgent.
Parses informal, multilingual text or image input using Gemini 3.5 Flash,
with a robust rule-based fallback system.
"""

import os
import re
import sys
import json
import base64
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("Appraiser")

# Try to load .env manually if it exists to avoid dependency on python-dotenv
def load_env_file():
    for path in ['.env', '../.env', '../../.env']:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            k, v = line.split('=', 1)
                            k = k.strip()
                            v = v.strip().strip("'\"")
                            if k and k not in os.environ:
                                os.environ[k] = v
                logger.info(f"Loaded environment variables from {path}")
                break
            except Exception as e:
                logger.warning(f"Error reading env file {path}: {e}")

load_env_file()

def is_base64_image(s: str) -> bool:
    """
    Checks if the input string is a base64 encoded image.
    """
    if not isinstance(s, str):
        return False
    s = s.strip()
    
    # Check for common data URI prefix
    if s.startswith("data:image/"):
        return True
        
    if len(s) < 100:  # Too short to be a valid image
        return False
        
    # Check if characters are valid base64
    if not re.match(r'^[A-Za-z0-9+/=\s]+$', s):
        return False
        
    try:
        # Strip all whitespace for validation
        cleaned = re.sub(r'\s+', '', s)
        # Attempt decode
        decoded = base64.b64decode(cleaned, validate=True)
        # Verify common image headers
        if (decoded.startswith(b'\x89PNG\r\n\x1a\n') or 
            decoded.startswith(b'\xff\xd8\xff') or 
            decoded.startswith(b'GIF8') or 
            b'WEBP' in decoded[:16] or
            decoded.startswith(b'RIFF')):
            return True
    except Exception:
        pass
    return False

def fallback_parse_text(text: str) -> list:
    """
    Parses informal, multilingual text for scrap items when Gemini API is unavailable.
    """
    logger.info("Executing rule-based fallback parser on text input")
    text = text.lower()
    
    # Material keyword mappings (handling Urdu/Hindi transliterated terms)
    material_keywords = {
        "Copper": ["copper", "tamba", "taamba", "tambi", "peetal", "pital", "tonti", "wire", "wires", "brass"],
        "Iron": ["iron", "loha", "lohay", "sariya", "steel", "patri", "pipe", "pipes", "tath", "sheet"],
        "Aluminum": ["aluminum", "aluminium", "almunium", "almuniom", "jast", "silver", "pot", "pots", "bartan"],
        "Cardboard": ["cardboard", "gatta", "gattay", "carton", "cartons", "paper", "raddi", "kaghaz", "kagaz", "books"]
    }
    
    # Quality/purity keyword mappings
    purity_keywords = {
        "High": ["saaf", "khalis", "pure", "high", "clean", "new", "naya", "achha", "wire", "wires"],
        "Low": ["zang", "rusty", "dirty", "low", "kharab", "kachra", "raddi", "mix", "mixed", "purana", "purani", "tuta", "toota"]
    }
    
    # Weight conversion factors to kg
    unit_multipliers = {
        "kg": 1.0,
        "kgs": 1.0,
        "kilogram": 1.0,
        "kilograms": 1.0,
        "kilo": 1.0,
        "kilos": 1.0,
        "mann": 40.0,
        "man": 40.0,
        "maund": 40.0,
        "maunds": 40.0,
        "ton": 1000.0,
        "tons": 1000.0,
        "tonne": 1000.0,
        "tonnes": 1000.0,
        "g": 0.001,
        "gram": 0.001,
        "grams": 0.001,
        "lb": 0.453592,
        "lbs": 0.453592,
        "pound": 0.453592,
        "pounds": 0.453592
    }
    
    # Find all numeric matches and their possible units
    pattern = r'(\d+(?:\.\d+)?)\s*([a-zA-Z]+)?'
    matches = list(re.finditer(pattern, text))
    
    # Find all material occurrences and their character spans
    material_occurrences = []
    for mat_type, keywords in material_keywords.items():
        for kw in keywords:
            for m in re.finditer(r'\b' + re.escape(kw) + r'\b', text):
                material_occurrences.append({
                    "material": mat_type,
                    "keyword": kw,
                    "start": m.start(),
                    "end": m.end()
                })
                
    # Sort material occurrences by position
    material_occurrences.sort(key=lambda x: x["start"])
    
    # Map matched weights to the closest material in terms of character distance
    assigned_weights = {} # index of material_occurrence -> (weight_kg, distance)
    
    for m in matches:
        num_val = float(m.group(1))
        unit = m.group(2)
        multiplier = 1.0
        
        if unit:
            unit_lower = unit.lower()
            if unit_lower in unit_multipliers:
                multiplier = unit_multipliers[unit_lower]
            else:
                # If the unit matched is actually a material keyword, don't use it as a unit multiplier
                is_mat_kw = False
                for mat_type, keywords in material_keywords.items():
                    if unit_lower in keywords:
                        is_mat_kw = True
                        break
                if is_mat_kw:
                    unit = None
                    
        weight_kg = num_val * multiplier
        
        # Find closest material occurrence
        num_center = (m.start() + m.end()) / 2
        closest_mat_idx = -1
        min_dist = float('inf')
        
        for idx, mat_occ in enumerate(material_occurrences):
            mat_center = (mat_occ["start"] + mat_occ["end"]) / 2
            dist = abs(num_center - mat_center)
            if dist < min_dist:
                min_dist = dist
                closest_mat_idx = idx
                
        # Limit the distance to 40 characters to avoid mapping unrelated weights
        if closest_mat_idx != -1 and min_dist < 40:
            if closest_mat_idx not in assigned_weights or min_dist < assigned_weights[closest_mat_idx]["dist"]:
                assigned_weights[closest_mat_idx] = {
                    "weight": weight_kg,
                    "dist": min_dist
                }

    # Build final list of appraised items
    appraised_items = []
    processed_indices = set()
    
    # Default weights based on material type if no weight is found near it
    default_weights = {
        "Copper": 2.0,
        "Iron": 10.0,
        "Aluminum": 3.0,
        "Cardboard": 5.0
    }
    
    for idx, mat_occ in enumerate(material_occurrences):
        if idx in processed_indices:
            continue
            
        mat_type = mat_occ["material"]
        
        # Determine weight
        if idx in assigned_weights:
            weight = assigned_weights[idx]["weight"]
        else:
            weight = default_weights.get(mat_type, 1.0)
            
        # Determine purity grade from nearby context (30 characters window)
        purity = "Medium"
        start_win = max(0, mat_occ["start"] - 30)
        end_win = min(len(text), mat_occ["end"] + 30)
        window_text = text[start_win:end_win]
        
        found_high = any(kw in window_text for kw in purity_keywords["High"])
        found_low = any(kw in window_text for kw in purity_keywords["Low"])
        
        if found_high and not found_low:
            purity = "High"
        elif found_low and not found_high:
            purity = "Low"
            
        appraised_items.append({
            "material_type": mat_type,
            "estimated_weight_kg": round(weight, 2),
            "purity_grade": purity
        })
        processed_indices.add(idx)

    # Fallback if no materials were explicitly detected
    if not appraised_items:
        weight = 5.0
        if matches:
            num_val = float(matches[0].group(1))
            unit = matches[0].group(2)
            multiplier = 1.0
            if unit and unit.lower() in unit_multipliers:
                multiplier = unit_multipliers[unit.lower()]
            weight = num_val * multiplier
            
        appraised_items.append({
            "material_type": "Iron",
            "estimated_weight_kg": round(weight, 2),
            "purity_grade": "Medium"
        })
        
    # Merge items sharing the same material and purity
    merged_items = {}
    for item in appraised_items:
        key = (item["material_type"], item["purity_grade"])
        if key in merged_items:
            merged_items[key]["estimated_weight_kg"] += item["estimated_weight_kg"]
        else:
            merged_items[key] = item
            
    # Round final merged weights
    result = []
    for val in merged_items.values():
        val["estimated_weight_kg"] = round(val["estimated_weight_kg"], 2)
        result.append(val)
        
    return result

def validate_and_clean_items(items) -> list:
    """
    Validates and cleans the JSON schema returned by the Gemini API.
    """
    if not isinstance(items, list):
        raise ValueError("Response is not a JSON list")
        
    valid_materials = {"Copper", "Iron", "Aluminum", "Cardboard"}
    valid_purities = {"High", "Medium", "Low"}
    
    cleaned = []
    for item in items:
        if not isinstance(item, dict):
            continue
            
        # Standardize material_type
        mat = str(item.get("material_type", "")).strip().capitalize()
        if mat == "Aluminium":
            mat = "Aluminum"
        if mat not in valid_materials:
            # Fallback to nearest or default
            mat = "Iron"
            
        # Standardize estimated_weight_kg
        weight = item.get("estimated_weight_kg")
        try:
            weight = float(weight)
            if weight < 0:
                weight = 0.0
        except (TypeError, ValueError):
            weight = 1.0
            
        # Standardize purity_grade
        purity = str(item.get("purity_grade", "")).strip().capitalize()
        if purity not in valid_purities:
            purity = "Medium"
            
        cleaned.append({
            "material_type": mat,
            "estimated_weight_kg": round(weight, 2),
            "purity_grade": purity
        })
        
    return cleaned

def appraise_with_gemini(input_text_or_image_base64: str) -> list:
    """
    Core function that calls the Gemini API to appraise materials.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is missing")
        
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    is_img = is_base64_image(input_text_or_image_base64)
    
    if is_img:
        s = input_text_or_image_base64.strip()
        mime_type = "image/jpeg"
        if s.startswith("data:image/"):
            header, base64_str = s.split(";base64,", 1)
            mime_type = header.replace("data:", "")
        else:
            base64_str = s
            # Attempt to sniff mime type
            try:
                decoded_header = base64.b64decode(base64_str[:32])
                if decoded_header.startswith(b'\x89PNG\r\n\x1a\n'):
                    mime_type = "image/png"
                elif decoded_header.startswith(b'\xff\xd8\xff'):
                    mime_type = "image/jpeg"
                elif decoded_header.startswith(b'GIF8'):
                    mime_type = "image/gif"
                elif b'WEBP' in decoded_header[:16]:
                    mime_type = "image/webp"
            except Exception:
                pass
                
        image_bytes = base64.b64decode(re.sub(r'\s+', '', base64_str))
        
        prompt = """
Analyze the provided image of scrap materials and identify all scrap items.
For each item, determine:
1. material_type: Must be exactly one of: "Copper", "Iron", "Aluminum", "Cardboard". If it doesn't fit, map it to the closest one.
2. estimated_weight_kg: A float representing the estimated weight in kilograms. If the input specifies weight in other units (like mann/maund, tons, grams, or pounds), convert them to kg (1 mann = 40 kg, 1 ton = 1000 kg, 1 lb = 0.453 kg).
3. purity_grade: Must be exactly one of: "High", "Medium", "Low". Estimate this based on visual appearance of the materials.

You must return a valid JSON array of objects, where each object has the keys: "material_type", "estimated_weight_kg", and "purity_grade".
Do not include any markdown formatting (like ```json), explanations, or extra text. Output ONLY the raw JSON array.
"""
    else:
        prompt = f"""
Analyze the following text description of scrap materials and identify all scrap items:
"{input_text_or_image_base64}"

For each item, determine:
1. material_type: Must be exactly one of: "Copper", "Iron", "Aluminum", "Cardboard". If it doesn't fit, map it to the closest one.
2. estimated_weight_kg: A float representing the estimated weight in kilograms. If the input specifies weight in other units (like mann/maund, tons, grams, or pounds), convert them to kg (1 mann = 40 kg, 1 ton = 1000 kg, 1 lb = 0.453 kg).
3. purity_grade: Must be exactly one of: "High", "Medium", "Low". Estimate this based on description (e.g. "rust", "dirty", "mixed" is Low; "clean", "wires", "new" is High; otherwise Medium).

You must return a valid JSON array of objects, where each object has the keys: "material_type", "estimated_weight_kg", and "purity_grade".
Do not include any markdown formatting (like ```json), explanations, or extra text. Output ONLY the raw JSON array.
"""

    # Try Google GenAI SDK (google-genai)
    try:
        from google import genai
        from google.genai import types
        logger.info(f"Attempting appraisal using google-genai SDK and model '{model_name}'")
        
        client = genai.Client(api_key=api_key)
        
        if is_img:
            contents = [
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                prompt
            ]
        else:
            contents = [prompt]
            
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        
        text_resp = response.text.strip()
        if text_resp.startswith("```json"):
            text_resp = text_resp[7:]
        if text_resp.endswith("```"):
            text_resp = text_resp[:-3]
        text_resp = text_resp.strip()
        
        return validate_and_clean_items(json.loads(text_resp))
        
    except ImportError:
        # Fallback to legacy Google Generative AI SDK (google-generativeai)
        try:
            import google.generativeai as old_genai
            logger.info(f"google-genai not installed. Falling back to google-generativeai SDK and model '{model_name}'")
            
            old_genai.configure(api_key=api_key)
            model = old_genai.GenerativeModel(model_name)
            
            if is_img:
                contents = [
                    {'mime_type': mime_type, 'data': image_bytes},
                    prompt
                ]
            else:
                contents = [prompt]
                
            response = model.generate_content(
                contents,
                generation_config={"response_mime_type": "application/json", "temperature": 0.1}
            )
            
            text_resp = response.text.strip()
            if text_resp.startswith("```json"):
                text_resp = text_resp[7:]
            if text_resp.endswith("```"):
                text_resp = text_resp[:-3]
            text_resp = text_resp.strip()
            
            return validate_and_clean_items(json.loads(text_resp))
            
        except ImportError:
            raise RuntimeError("Neither google-genai nor google-generativeai library is installed.")

def appraise(input_text_or_image_base64: str) -> list:
    """
    Main entrypoint function.
    Returns a list of dictionaries, representing the appraised items.
    """
    try:
        # If API key is present, try Gemini
        if os.environ.get("GEMINI_API_KEY"):
            return appraise_with_gemini(input_text_or_image_base64)
        else:
            logger.warning("GEMINI_API_KEY environment variable is not set. Using rule-based fallback.")
    except Exception as e:
        logger.error(f"Gemini appraisal failed: {e}. Falling back to rule-based parser.")
        
    # If Gemini fails or isn't configured, fall back
    if is_base64_image(input_text_or_image_base64):
        logger.warning("Input is an image, but Gemini failed or is unavailable. Returning generic image fallback.")
        return [
            {
                "material_type": "Iron",
                "estimated_weight_kg": 10.0,
                "purity_grade": "Medium"
            }
        ]
    else:
        return fallback_parse_text(input_text_or_image_base64)

if __name__ == "__main__":
    # CLI Utility implementation
    if len(sys.argv) < 2:
        print("Usage: python appraiser.py <text_description_or_base64_image_or_file_path>", file=sys.stderr)
        sys.exit(1)
        
    input_val = sys.argv[1]
    
    # Check if the argument is a path to an existing file
    if os.path.exists(input_val):
        try:
            with open(input_val, "r", encoding="utf-8") as f:
                content = f.read().strip()
                # Check if file contents are base64 image or raw text
                input_val = content
        except Exception as e:
            print(f"Error reading file {input_val}: {e}", file=sys.stderr)
            sys.exit(1)
            
    try:
        results = appraise(input_val)
        print(json.dumps(results, indent=2))
    except Exception as e:
        print(f"Appraisal failed: {e}", file=sys.stderr)
        sys.exit(1)
