import os
import sys
import requests

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

def register_and_upload_image(token, author_urn, image_path):
    if not os.path.exists(image_path):
        print(f"Image not found at path: {image_path}")
        return None

    with open(image_path, 'rb') as f:
        image_bytes = f.read()

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
        print(f"Failed to register image upload for {image_path}: {response.text}")
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
        print(f"Failed to upload image binary for {image_path}: {upload_response.text}")
        return None
        
    return asset_urn

def post_article(token, author_urn, asset_urns):
    url = 'https://api.linkedin.com/v2/ugcPosts'
    headers = {
        'Authorization': f'Bearer {token}',
        'X-Restli-Protocol-Version': '2.0.0',
        'Content-Type': 'application/json'
    }
    
    post_text = """Decoupling Context: Building Eyeno (A Self-Training AI Second Brain & Prompt Architect)

As engineers, we fight a constant battle with LLM session amnesia. Every time you start a new prompt session, the AI forgets everything about your unique architecture, strict code quality principles, and security boundaries.

To solve this, I designed and built Eyeno—a self-expanding cognitive layer for prompt engineering. 

Here is the exact architecture:

1. The Gateway (Prompt Architect):
An interactive workspace that takes raw, vague drafts and diagnoses them against key parameters (persona, variables, objectives, delimiters). It aligns parameters via interactive Q&A and refines them into masterpiece prompts.

2. The Memory (Eyeno):
A live Obsidian Markdown knowledge base hosted on GitHub. It holds my exact mental models:
- [[Analytic_Workflow]] - Reverse-engineering from target end states.
- [[Creative_Tissue_Layer]] - Cross-discipline analogies (drawing security principles from strategy games).
- [[Epistemic_Logs]] - Actively tracking failures to build mastery.
- [[Anti-Data_Boundaries]] - Refusing strict guardrails to analyze and learn from malicious systems.
Every query triggers a parallel semantic check that merges these private parameters directly into the LLM output.

3. The Continuous Learning Loop (Self-Training):
This is the game-changer. When a prompt is generated, the backend triggers an async background distillation model. It reverse-engineers the successful prompt, extracts reusable patterns, formatting constraints, and domain wikilinks, and commits them as a new Obsidian node back to GitHub.

The system now automatically trains itself on my daily workflows, for free, without manual file uploads.

Check out the full story and implementation details on my technical blog (link in comments/bio)! 

#BuildInPublic #AISecondBrain #PromptEngineering #GCP #SystemsArchitecture #Obsidian #WebDevelopment"""

    share_content = {
        "shareCommentary": {
            "text": post_text
        },
        "shareMediaCategory": "NONE"
    }

    if asset_urns:
        share_content["shareMediaCategory"] = "IMAGE"
        share_content["media"] = [
            {
                "status": "READY",
                "media": urn,
                "title": { "text": f"Asset {i+1}" }
            } for i, urn in enumerate(asset_urns)
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
    
    print("Posting article to LinkedIn...")
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        print("Successfully posted to LinkedIn with Article preview and images!")
    else:
        print(f"Failed to post. Status: {response.status_code}")
        print(response.text)
        sys.exit(1)

def main():
    linkedin_token = os.environ.get('LINKEDIN_ACCESS_TOKEN')
    if not linkedin_token:
        print("Could not find LINKEDIN_ACCESS_TOKEN")
        sys.exit(1)
        
    author_urn = get_author_urn(linkedin_token)
    
    # Upload images
    asset_urns = []
    for img in ["eyeno-graph.png", "prompt-architect-ui.png"]:
        if os.path.exists(img):
            print(f"Uploading image: {img}...")
            urn = register_and_upload_image(linkedin_token, author_urn, img)
            if urn:
                print(f"Uploaded successfully URN: {urn}")
                asset_urns.append(urn)
                
    post_article(linkedin_token, author_urn, asset_urns)

if __name__ == "__main__":
    main()
