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

def post_article(token, author_urn, asset_urns, post_text):
    url = 'https://api.linkedin.com/v2/ugcPosts'
    headers = {
        'Authorization': f'Bearer {token}',
        'X-Restli-Protocol-Version': '2.0.0',
        'Content-Type': 'application/json'
    }

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
    
    import time
    
    if os.path.exists('post.md'):
        with open('post.md', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by markdown headers or sections if separated by ---
        sections = [s.strip() for s in content.split('---') if s.strip()]
        
        for i, post_text in enumerate(sections):
            # LinkedIn limit is ~3000 chars, so ensure we don't crash
            if len(post_text) > 2900:
                post_text = post_text[:2900] + "..."
                
            print(f"Posting section {i+1}/{len(sections)}...")
            post_article(linkedin_token, author_urn, [], post_text)
            
            if i < len(sections) - 1:
                print("Waiting 10 seconds before next post to avoid rate limits...")
                time.sleep(10)
    else:
        print("No post.md file found.")

if __name__ == "__main__":
    main()
