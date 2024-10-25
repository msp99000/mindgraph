import aiohttp
import asyncio
import json
import os
from datetime import datetime
from slack.fileExtract.pdf_to_txt import pdf_to_text
from slack.fileExtract.word_to_txt import word_to_text
from slack.fileExtract.text_to_txt import txt_to_text

async def slack_fetch_chat(bearer_token, channel_id, organization_name, oldest_unix="", latest_unix="", limit=""):
    async def fetch_slack_channelN(channel_id, bearer_token):
        url = f"https://slack.com/api/conversations.info?channel={channel_id}"
        headers = {"Authorization": f"Bearer {bearer_token}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Error: {response.status}")
                    return None

    channel_info = await fetch_slack_channelN(channel_id, bearer_token)
    channel_name = channel_info['channel']['name']

    async def fetch_slack_conversation(c, b):
        url = "https://slack.com/api/conversations.history"
        headers = {"Authorization": f"Bearer {b}"}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json={"channel": c, "oldest": oldest_unix, "latest": latest_unix, "limit": limit}) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Error: {response.status}")
                    return None

    async def user_info(user_ids, bearer_token):
        user_info_list = []
        async with aiohttp.ClientSession() as session:
            for user_id in user_ids:
                url = "https://slack.com/api/users.info"
                headers = {"Authorization": f"Bearer {bearer_token}"}
                params = {"user": user_id}
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        user_info_list.append(await response.json())
                    else:
                        print(f"Error fetching user info for user ID {user_id}. Status code: {response.status}")
                        user_info_list.append(None)
        return user_info_list

    async def preprocess_messages(messages, bearer_token):
        processed_messages = []
        process_userids = set()
        user_info_dict = {}

        for message in messages:
            user_id = message.get("user")
            if user_id:
                process_userids.add(user_id)

        u_data_from_func = await user_info(list(process_userids), bearer_token)

        for user_d in u_data_from_func:
            if user_d and "user" in user_d:
                user_id = user_d["user"]["id"]
                user_info_dict[user_id] = {
                    "name": user_d["user"]["name"],
                    "display_name": user_d["user"]["profile"]["display_name"],
                }

        def unix_to_human_readable(unix_timestamp):
            unix_timestamp = float(unix_timestamp)
            date_time = datetime.fromtimestamp(unix_timestamp)
            return date_time.strftime('%Y-%m-%d')

        def unix_to_human_readable_time(unix_timestamp):
            unix_timestamp = float(unix_timestamp)
            date_time = datetime.fromtimestamp(unix_timestamp)
            return date_time.strftime('%I:%M:%S %p')

        for message in messages:
            user_id = message.get("user", "")
            user_data = user_info_dict.get(user_id, {"name": "", "display_name": ""})
            
            files = message.get("files", [])
            url_private_download = ''
            filetype = ""

            for file in files:
                url_private_download = file.get('url_private_download', '')
                filetype = file.get('filetype', '')
                if url_private_download:
                    break

            text_from_files = ''
            if url_private_download:
                if filetype == "docx":
                    text_from_files = await word_to_text(url_private_download, bearer_token)
                elif filetype == "pdf":
                    text_from_files = await pdf_to_text(url_private_download, bearer_token)
                elif filetype == "text":
                    text_from_files = await txt_to_text(url_private_download, bearer_token)
                else:
                    text_from_files = "Unsupported file type"
            else:
                text_from_files = "No files to process"

            # Remove spaces from text and limit to 10 characters
            # Generate unique_key based on channel, user, timestamp, and a truncated version of the text
            text_without_spaces = message.get("text", "").replace(" ", "").lower()[:10]
            unique_key = f"{channel_id}_{user_id}_{message.get('ts', '').lower()}_{text_without_spaces}"

            # Check if client_msg_id is present; if not, use unique_key
            client_msg_id = message.get("client_msg_id", unique_key)

            # Process the message with the proper client_msg_id
            processed_message = {
                "channel_id": channel_id,
                "channel_name": channel_name,
                "organization_name": organization_name,
                "timestamp": message.get("ts", "").lower(),
                "date": unix_to_human_readable(message.get("ts", 0)),
                "time": unix_to_human_readable_time(message.get("ts", 0)),
                "client_msg_id": client_msg_id,  # Use either the real client_msg_id or unique_key
                "user_id": user_id,
                "user_name": user_data["name"].lower(),
                "display_name": user_data["display_name"].lower(),
                "text": message.get("text", "").lower(),
                "attachments": message.get("attachments", []),
                "files": files,
                "Extract_text": text_from_files
            }

            processed_messages.append(processed_message)
            print(preprocess_messages,"preprocessing data")

        return processed_messages

    # Main logic
    if channel_id and bearer_token:
        conversation_data = await fetch_slack_conversation(channel_id, bearer_token)
        if conversation_data and "messages" in conversation_data:
            processed_messages = await preprocess_messages(conversation_data["messages"], bearer_token)
            
            structured_data = [{
                "channel_id": channel_id,
                "messages": processed_messages,
            }]

            directory = "db/"
            organization_directory = os.path.join(directory, organization_name)
            channel_directory = os.path.join(organization_directory, channel_name)
            os.makedirs(channel_directory, exist_ok=True)

            file_path = os.path.join(channel_directory, f'{channel_name}.json')
            
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r") as f:
                        existing_data = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    existing_data = [{"channel_id": channel_id, "messages": []}]

                # Create a set of existing message timestamps for faster lookup
                existing_message_timestamps = {msg['client_msg_id'] for msg in existing_data[0]['messages']}

                # Filter and add only new messages
                new_messages = []
                for msg in structured_data[0]['messages']:
                    if msg['client_msg_id'] not in existing_message_timestamps:
                        new_messages.append(msg)
                        existing_message_timestamps.add(msg['client_msg_id'])  # Update the set with the new timestamp

                # Prepend new messages to the existing messages
                existing_data[0]['messages'] = new_messages + existing_data[0]['messages']

                # Write the updated data back to the file
                with open(file_path, "w") as f:
                    json.dump(existing_data, f, indent=4)

                print(f"New data added to file: {file_path}")
                print(f"Number of new messages added: {len(new_messages)}")

            else:
                with open(file_path, "w") as f:
                  return  json.dump(structured_data, f, indent=4)
                
                print(f"New file created: {file_path}")

            print("Conversation data has been saved to JSON file.")
        else:
            print("Failed to fetch or process conversation data.")



