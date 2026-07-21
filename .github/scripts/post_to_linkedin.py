import os
import sys
import requests
import google.generativeai as genai

def get_journal_content():
    try:
        with open('journal.md', 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error reading journal.md: {e}")
        return ""

def generate_post(journal_entry, api_key):
    genai.configure(api_key=api_key)
    
    prompt = f"""
You are an expert engineer sharing a 'building in public' update on LinkedIn.
Based on the following developer journal entry, write ONE single, professional, and engaging LinkedIn post summarizing what was built and WHY it was built.

Here is the exact Blueprint you MUST follow for the post:
- Tone: Authentic, Humanized, Story-driven, Humorous (with light Nigerian tech slangs like 'Omo', 'wahala', 'sapa', 'no cap').
- Structure: Start with a massive hook to grab attention. Tell a story about the struggle of building it. Include a "Fun Fact" related to the tech. End with an engaging Call to Action.

CRITICAL RULES FOR YOUR WRITING STYLE (FAILING THESE IS UNACCEPTABLE):
1. NEVER output meta-labels. Do NOT write "Hook:", "Content Draft:", "Context Draft:", "Media:", or "Hashtags:". Just write the natural prose.
2. DO NOT use any markdown symbols like *, $, or __.
3. DO NOT use markdown headers (e.g., no # or ## or ### before words). The ONLY time you may use the # symbol is at the very bottom for your hashtags.
4. Focus on the journey and the "why".
5. Avoid over-spacing or excessive line breaks. The write-up should flow naturally like human prose.
6. At the very end of the post, add 3 to 5 relevant hashtags (e.g., #BuildInPublic #SoftwareEngineering).

Journal Entry:
{journal_entry}
"""
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt)
    content = response.text.strip()
    
    import re
    # Strip markdown symbols
    for char in ['*', '$', '__']:
        content = content.replace(char, '')
    
    # Strip any lines that start with # (headers), but keep hashtags
    content = re.sub(r'(?m)^#+\s+.*$', '', content)
    
    # Strip double spacing
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    return content.strip()

def generate_and_save_image(journal_entry, api_key):
    # Attempt to generate an image using Gemini Imagen 3
    # Note: Requires Gemini API key to have Imagen access
    genai.configure(api_key=api_key)
    try:
        prompt = f"A sleek, modern digital art illustration representing software engineering and coding. Clean minimalist style, futuristic, no text. Theme based on: {journal_entry[:200]}"
        result = genai.generate_images(
            prompt=prompt,
            number_of_images=1,
            model="imagen-3.0-generate-001",
            aspect_ratio="16:9"
        )
        if result and hasattr(result, 'generated_images') and result.generated_images:
            image_bytes = result.generated_images[0].image.image_bytes
            return image_bytes
    except Exception as e:
        print(f"Image generation failed or not supported by this API key: {e}")
    return None

def get_author_urn(token):
    url = 'https://api.linkedin.com/v2/userinfo'
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        sub = response.json().get('sub')
        if sub:
            return f"urn:li:person:{sub}"
            
    url_me = 'https://api.linkedin.com/v2/me'
    response_me = requests.get(url_me, headers=headers)
    if response_me.status_code == 200:
        person_id = response_me.json().get('id')
        if person_id:
            return f"urn:li:person:{person_id}"
            
    print("Error fetching author URN.")
    sys.exit(1)

def register_and_upload_image(token, author_urn, image_bytes):
    # 1. Register Upload
    register_url = "https://api.linkedin.com/v2/assets?action=registerUpload"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    payload = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": author_urn,
            "serviceRelationships": [{"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}]
        }
    }
    response = requests.post(register_url, headers=headers, json=payload)
    if response.status_code != 200:
        print(f"Failed to register image upload: {response.text}")
        return None
        
    data = response.json()
    upload_url = data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
    asset_urn = data['value']['asset']
    
    # 2. Upload Binary
    upload_headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/octet-stream'
    }
    upload_response = requests.put(upload_url, headers=upload_headers, data=image_bytes)
    if upload_response.status_code not in (200, 201):
        print(f"Failed to upload image binary: {upload_response.text}")
        return None
        
    return asset_urn

def post_to_linkedin(content, token, asset_urn=None):
    author_urn = get_author_urn(token)
    print(f"Posting on behalf of: {author_urn}")
    
    url = 'https://api.linkedin.com/v2/ugcPosts'
    headers = {
        'Authorization': f'Bearer {token}',
        'X-Restli-Protocol-Version': '2.0.0',
        'Content-Type': 'application/json'
    }
    
    share_content = {
        "shareCommentary": {
            "text": content
        },
        "shareMediaCategory": "NONE"
    }
    
    if asset_urn:
        share_content["shareMediaCategory"] = "IMAGE"
        share_content["media"] = [
            {
                "status": "READY",
                "media": asset_urn
            }
        ]
    
    payload = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": share_content
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        print("Successfully posted to LinkedIn!")
    else:
        print(f"Failed to post. Status: {response.status_code}")
        print(response.text)
        sys.exit(1)

def main():
    gemini_key = os.environ.get('GEMINI_API_KEY')
    linkedin_token = os.environ.get('LINKEDIN_ACCESS_TOKEN')
    
    if not all([gemini_key, linkedin_token]):
        print("Missing required environment variables (secrets).")
        sys.exit(1)
        
    journal_entry = get_journal_content()
    if not journal_entry:
        print("Journal entry is empty. Skipping post.")
        return
        
    print("Generating post from journal entry...")
    post_content = generate_post(journal_entry, gemini_key)
    print("--- POST CONTENT ---")
    print(post_content)
    print("--------------------")
    
    print("Attempting to generate image...")
    image_bytes = generate_and_save_image(journal_entry, gemini_key)
    
    asset_urn = None
    if image_bytes:
        print("Image generated successfully. Registering upload with LinkedIn...")
        author_urn = get_author_urn(linkedin_token)
        asset_urn = register_and_upload_image(linkedin_token, author_urn, image_bytes)
        if asset_urn:
            print(f"Image uploaded successfully. Asset URN: {asset_urn}")
        else:
            print("Image upload to LinkedIn failed, falling back to text-only post.")
    
    print("Posting to LinkedIn...")
    post_to_linkedin(post_content, linkedin_token, asset_urn)

if __name__ == "__main__":
    main()
