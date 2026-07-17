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

def post_article(token, author_urn):
    url = 'https://api.linkedin.com/v2/ugcPosts'
    headers = {
        'Authorization': f'Bearer {token}',
        'X-Restli-Protocol-Version': '2.0.0',
        'Content-Type': 'application/json'
    }
    
    post_text = """Escaping the Serverless Timeout Trap: Building a $0 Enterprise AI Architecture

If you've ever built a heavy LLM application and deployed it to serverless platforms, you know the struggle: the dreaded 10-second timeout kill switch. 

I was recently working on a complex full-stack AI project (Prompt Architect) and ran into this exact wall with Cloudflare Edge Functions. Gemini takes 15+ seconds to process massive prompt alignments, meaning Cloudflare kept silently killing our API responses mid-thought.

Instead of paying hundreds of dollars for dedicated cloud compute, we engineered a completely free, highly distributed 3-tier architecture that completely bypasses the timeout trap and keeps data ultra-secure. 

Here is the exact blueprint we built:

1. Source of Truth: GitHub
Everything starts here. Our entire monorepo lives in GitHub, acting as the absolute center of gravity. Commits automatically trigger deployments to both our frontend and our backend simultaneously.

2. The CDN (Frontend): Cloudflare Pages
We kept the React/Vite UI on Cloudflare Pages to take advantage of their lightning-fast global CDN. The catch? We decoupled the frontend routing, pointing our API fetch requests away from Cloudflare's edge functions and over to our new heavy-lifting backend.

3. The Compute Engine (Backend): Hugging Face Spaces
This is the radical part. We deployed our Node.js/Express API to a Hugging Face Docker Space. Why? Because Hugging Face generously provides 16GB of RAM and 2 vCPUs completely for free. There are no strict 10-second HTTP timeouts here. It is a powerhouse designed specifically for heavy AI workloads. 

4. The Secure Vault (Database): Oracle Cloud VPS
Hugging Face Spaces are public, acting like an open "house blueprint." To protect user data, we deployed an Oracle Cloud Free Tier VPS strictly for database hosting. We used the Hugging Face Secrets Repo to securely store the database connection strings. Anyone can look at our public compute source code, but no one can touch our Oracle data vault.

The Ultimate Hack: The Always-On CRON
The only downside to Hugging Face Spaces is that they go to sleep after 48 hours of inactivity. To bypass this, we wrote a tiny CRON job script on our Oracle server that sends an HTTP ping to our Hugging Face Space every 24 hours. The result? Our massive 16GB compute instance never realizes we are inactive, so it stays awake forever.

We effectively built a scalable, enterprise-grade, distributed AI microservice architecture... for $0/month. 

Has anyone else experimented with Hugging Face Spaces for general Express/Node APIs? I'd love to hear how you are bypassing serverless limitations!

#BuildInPublic #AIArchitecture #HuggingFace #Cloudflare #OracleCloud #WebDevelopment #SoftwareEngineering #TechHacks"""

    payload = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": post_text
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    
    print("Posting article to LinkedIn...")
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        print("Successfully posted to LinkedIn with Article preview!")
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
    post_article(linkedin_token, author_urn)

if __name__ == "__main__":
    main()
