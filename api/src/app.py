from slack.fetch_conversation import slack_fetch_chat
import os
from datetime import datetime, timedelta
# from slack.api.test2 import get_organization_id
# from slack.api.channel_name import get_channel_ids
from dotenv import load_dotenv
load_dotenv()


bearer_token=os. getenv("bearer_token") 

# org_id = get_organization_id(bearer_token)
# print(f"Organization ID: {org_id}")
# channel_id=get_channel_ids(bearer_token)
# print(f"Channel IDs: {channel_id}")
# channel_id = "C077VPJDR4Z"  #gen-ai-sanctum-of-excellence
# channel_id="C07DP6854J0"#symbiosis opration
# channel_id="C07C01CUKA7"#symbiosis General
#channel_id = "C06B81146KH" #C06B81146KH
#channel_id="C070Z5U9145"  #poc-personalized-recommendations
# channel_id="C0698MDP6M8"  #general
# Get today's date and convert to Unix timestamp
# org_id = "upcore technologies"
channel_id="C07E9FJBA5N"# symbiosis-sales
# org_id = "symbiosis "

#  = "symbiosis"
org_id = "upcore technollogies"
latest = datetime.now()
latest_unix = latest.timestamp()


# Get yesterday's date and convert to Unix timestamp
oldest = latest - timedelta(days=1)
oldest_unix = oldest.timestamp()
slack_fetch_chat(bearer_token,channel_id,org_id,limit=1000)
# slack_fetch_chat(bearer_token,channel_id,org_id,oldest_unix,latest_unix,limit=1000)



