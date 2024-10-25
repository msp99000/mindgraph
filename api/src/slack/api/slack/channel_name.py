import requests

def get_channel_ids(bearer_token):
    url = "https://slack.com/api/conversations.list"
    
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    
    params = {
        "exclude_archived": True,
        "types": "public_channel,private_channel"
    }
    
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    
    if response.status_code == 200 and data.get("ok"):
        
  
        return data
    else:
        raise Exception(f"Error fetching channel IDs: {data.get('error')}")

def get_organization_id(bearer_token):
            url = "https://slack.com/api/team.info"
            
            headers = {
                "Authorization": f"Bearer {bearer_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers)
            data = response.json()
            
            if response.status_code == 200 and data.get("ok"):
                # organization_id = data["team"]["id"]
                # organization_name = data["team"]["name"]
                return data
            else:
                raise Exception(f"Error fetching organization ID: {data.get('error')}")

