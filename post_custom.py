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
    
    post_text = """Security is no longer just about building walls; it's about building traps and automated countermeasures. 🛡️

I just published a new technical article on my portfolio detailing the enterprise-grade security architecture we are using for our next-generation web and mobile wallet applications. 

In this article, I cover:
✅ Cloudflare Edge Protection & Bot Mitigation
✅ Server Hardening & SSH Isolation
✅ Automated PM2 Intrusion Response (Lockdown)
✅ Codebase Self-Healing via Origin Restoration

If you're building high-stakes infrastructure, you need to assume a breach is possible and engineer resilient systems that neutralize threats instantly. 

Read the full breakdown on my blog below! 👇

#CyberSecurity #DevOps #CloudArchitecture #SoftwareEngineering #BuildInPublic"""

    payload = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": post_text
                },
                "shareMediaCategory": "ARTICLE",
                "media": [
                    {
                        "status": "READY",
                        "description": {"text": "A deep dive into advanced server security protocols, automated lockdown, and codebase self-healing for financial applications."},
                        "originalUrl": "https://moorejae.github.io/about-me/post-10.html",
                        "title": {"text": "Architecting Enterprise-Grade Security for Next-Gen Wallets"}
                    }
                ]
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
