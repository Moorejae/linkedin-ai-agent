import os
import sys
import requests
import google.generativeai as genai

def get_journal_content():
    # Read the contents of journal.md
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
Based on the following developer journal entry, write a professional and engaging LinkedIn post summarizing what was built and WHY it was built.

CRITICAL RULES FOR YOUR WRITING STYLE:
1. Focus on the journey and the "why". Do not reveal confidential product ideas, raw code, or sensitive data.
2. DO NOT use markdown symbols like *, #, $, or __ in the text.
3. Avoid over-spacing or excessive line breaks. The write-up should flow naturally like human prose.
4. Do not make it sound like unrefined AI work. Be authentic, humble, and technical but accessible.

Journal Entry:
{journal_entry}
"""
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    content = response.text.strip()
    
    # Post-generation cleanup to ensure strict compliance with user's formatting rules
    for char in ['*', '#', '$', '__']:
        content = content.replace(char, '')
    
    return content.strip()

def post_to_linkedin(content, token, person_urn):
    url = 'https://api.linkedin.com/v2/ugcPosts'
    headers = {
        'Authorization': f'Bearer {token}',
        'X-Restli-Protocol-Version': '2.0.0',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "author": f"urn:li:person:{person_urn}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": content
                },
                "shareMediaCategory": "NONE"
            }
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
    person_urn = os.environ.get('LINKEDIN_PERSON_URN')
    
    if not all([gemini_key, linkedin_token, person_urn]):
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
        
    print("Posting to LinkedIn...")
    post_to_linkedin(post_content, linkedin_token, person_urn)

if __name__ == "__main__":
    main()
