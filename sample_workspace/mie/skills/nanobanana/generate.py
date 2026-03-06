#!/Users/rin/workspace/skills/nanobanana/venv/bin/python3  
"""
Nano Banana Pro — Image Generation via Gemini API
Usage:
    python3 generate.py "scene description"
    python3 generate.py "scene description" --ref photo.jpg
    python3 generate.py --char teddy "eating ramen happily" -o ~/generates/output.jpg
    python3 generate.py --char teddy --char mephi "Character 1 and 2 at a cafe" --ref photo.jpg
    python3 generate.py --char teddy --style manga "debugging code at 3am"
"""
import argparse
import json
import os
import re
import sys
import os

# Python 3.9のパスを全て削除
sys.path = [p for p in sys.path if '3.9' not in p]

# venvのsite-packagesを最優先に追加
venv_site = '/Users/rin/workspace/skills/nanobanana/venv/lib/python3.14/site-packages'
sys.path.insert(0, venv_site)

print(f"[DEBUG] sys.path after cleanup: {sys.path}", file=sys.stderr)
import os

# Python 3.9のパスを全て削除
sys.path = [p for p in sys.path if '3.9' not in p]

# venvのsite-packagesを最優先に追加
venv_site = '/Users/rin/workspace/skills/nanobanana/venv/lib/python3.14/site-packages'
sys.path.insert(0, venv_site)

print(f"[DEBUG] sys.path after cleanup: {sys.path}", file=sys.stderr)
import time

# venvのsite-packagesを強制的に追加                                                                                                
venv_site = '/Users/rin/workspace/skills/nanobanana/venv/lib/python3.14/site-packages'
if venv_site not in sys.path:
    sys.path.insert(0, venv_site)

PRESETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "presets")


def load_preset(character, style=None):
    """Load character preset and optional style."""
    preset_path = os.path.join(PRESETS_DIR, f"{character}.json")
    if not os.path.exists(preset_path):
        print(f"Error: Preset '{character}' not found at {preset_path}", file=sys.stderr)
        sys.exit(1)
    with open(preset_path) as f:
        preset = json.load(f)

    style_name = style or "normal"
    styles = preset.get("styles", {})
    if style_name not in styles:
        available = ", ".join(styles.keys())
        print(f"Error: Style '{style_name}' not found. Available: {available}", file=sys.stderr)
        sys.exit(1)

    style_data = styles[style_name]
    char_desc = preset.get("character", "")
    prompt_features = preset.get("prompt_features", char_desc)
    charsheet_override = style_data.get("charsheet_override", "")
    charsheet = os.path.expanduser(charsheet_override if charsheet_override else preset.get("charsheet", ""))
    prompt_features_override = style_data.get("prompt_features_override", "")
    if prompt_features_override:
        prompt_features = prompt_features_override
    prefix = style_data.get("prompt_prefix", "")
    model = style_data.get("model")

    return {
        "name": preset.get("name", character),
        "character": char_desc,
        "prompt_features": prompt_features,
        "charsheet": charsheet,
        "prefix": prefix,
        "model": model,
    }


def build_prompt(scene, characters, style_prefix=""):
    """Build structured prompt from characters and scene description.
    
    Characters block + Scene block format:
      Characters:
      1. Teddy: light brown hair, white bear-ear hoodie...
      2. Mephi: pink bob hair, small red horns...
      
      Scene: Two characters sitting at a cafe...
    """
    parts = []
    
    if style_prefix:
        parts.append(style_prefix.strip())
    
    if characters:
        parts.append("")
        parts.append("Characters:")
        for i, char in enumerate(characters, 1):
            parts.append(f"{i}. {char['name']}: {char['prompt_features']}")
        parts.append("")
        parts.append(f"Scene: {scene}")
    else:
        parts.append(scene)
    
    return "\n".join(parts)

def generate(prompt, ref_path=None, ref_paths=None, model="nano-banana-pro-preview", output=None, aspect_ratio=None):

    from google import genai
    from google.genai import types

    api_key_path = os.path.expanduser("~/.config/google/gemini_api_key")
    if not os.path.exists(api_key_path):
        print("Error: API key not found at ~/.config/google/gemini_api_key", file=sys.stderr)
        sys.exit(1)

    api_key = open(api_key_path).read().strip()
    client = genai.Client(api_key=api_key)

    # Build content parts
    contents = []
    all_refs = []
    if ref_paths:
        all_refs = ref_paths
    elif ref_path:
        all_refs = [ref_path]
    for rp in all_refs:
        with open(rp, "rb") as f:
            ref_data = f.read()
        mime = "image/jpeg" if rp.lower().endswith((".jpg", ".jpeg")) else "image/png"
        contents.append(types.Part.from_bytes(data=ref_data, mime_type=mime))
    contents.append(prompt)

    # Generate with retry for transient errors (503, 429, etc.)
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                    image_config=types.ImageConfig(aspect_ratio=aspect_ratio) if aspect_ratio else None,
                )
            )
            break
        except Exception as e:
            err_str = str(e)
            retryable = any(code in err_str for code in ["503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "high demand"])
            if retryable and attempt < max_retries - 1:
                wait = 2 ** attempt * 5  # 5s, 10s, 20s, 40s
                print(f"[retry {attempt+1}/{max_retries}] Server busy, retrying in {wait}s...", file=sys.stderr)
                time.sleep(wait)
            else:
                raise

    # Extract image
    if not output:
        ts = int(time.time())
        gen_dir = os.path.expanduser("~/generates")
        os.makedirs(gen_dir, exist_ok=True)
        output = f"{gen_dir}/nanobanana_{ts}.jpg"

    for part in response.candidates[0].content.parts:
        if part.inline_data:
            with open(output, "wb") as f:
                f.write(part.inline_data.data)
            # Save prompt log to ~/logs/nanobanana/
            log_dir = os.path.expanduser("~/logs/nanobanana")
            os.makedirs(log_dir, exist_ok=True)
            log_name = os.path.basename(output) + ".prompt.txt"
            log_path = os.path.join(log_dir, log_name)
            ref_list = ref_paths or ([ref_path] if ref_path else [])
            with open(log_path, "w") as lf:
                lf.write(f"output: {output}\n")
                lf.write(f"model: {model}\n")
                lf.write(f"refs: {ref_list}\n")
                lf.write(f"prompt: {prompt}\n")
            print(output)
            return output
        elif part.text:
            print(f"[text] {part.text[:200]}", file=sys.stderr)

    print("Error: No image in response", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nano Banana Pro image generation")
    parser.add_argument("prompt", help="Scene description (use 'Character N' to reference --char)")
    parser.add_argument("--ref", action="append", default=[], help="Reference image path (repeatable)")
    parser.add_argument("--model", default=None, help="Model name (overrides preset)")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("--aspect", help="Aspect ratio (e.g. 16:9, 9:16, 1:1)")
    parser.add_argument("--char", action="append", default=[], help="Character preset name (repeatable, e.g. --char teddy --char mephi:official)")
    parser.add_argument("--style", default="normal", help="Style variant fallback when --char has no :style suffix")
    parser.add_argument("--dry-run", action="store_true", help="Print prompt without generating")
    args = parser.parse_args()

    refs = args.ref
    model = args.model
    style_prefix = ""
    characters = []

    if args.char:
        for char_arg in args.char:
            # Parse name:style syntax (e.g. "bizenyakiko:dressup")
            if ":" in char_arg:
                char_name, char_style = char_arg.split(":", 1)
                if not char_name or not char_style:
                    print(f"Error: Invalid --char format '{char_arg}'. Use 'name' or 'name:style'.", file=sys.stderr)
                    sys.exit(1)
            else:
                char_name = char_arg
                char_style = args.style  # fallback to global --style

            # Validate preset name
            if not re.match(r'^[a-zA-Z0-9_\-]+$', char_name):
                print(f"Error: Invalid preset name '{char_name}'. Use alphanumeric, underscore, or hyphen only.", file=sys.stderr)
                sys.exit(1)

            char_data = load_preset(char_name, char_style)
            # Resolve outfit if defined in style
            preset_path = os.path.join(PRESETS_DIR, f"{char_name}.json")
            with open(preset_path) as f:
                raw = json.load(f)
            style_data = raw.get("styles", {}).get(char_style or "normal", {})
            outfit_key = style_data.get("outfit")
            if outfit_key and "outfits" in raw:
                outfit_desc = raw["outfits"].get(outfit_key, "")
                if outfit_desc:
                    char_data["prompt_features"] += f", wearing {outfit_desc}"
            characters.append(char_data)
        
        # Add charsheets to refs
        for char_data in characters:
            cs = char_data.get("charsheet", "")
            if cs and os.path.exists(cs) and cs not in refs:
                refs.append(cs)

        # Use first character's style settings as defaults
        first = characters[0]
        style_prefix = first["prefix"]
        if not model and first["model"]:
            model = first["model"]
    
    model = model or "nano-banana-pro-preview"
    prompt = build_prompt(args.prompt, characters, style_prefix)

    if args.dry_run:
        print("=== PROMPT ===")
        print(prompt)
        print(f"\n=== CONFIG ===")
        print(f"Model: {model}")
        print(f"Refs: {refs}")
        print(f"Aspect: {args.aspect}")
        print(f"Output: {args.output}")
        sys.exit(0)

    generate(prompt, ref_paths=refs, model=model, output=args.output, aspect_ratio=args.aspect)
