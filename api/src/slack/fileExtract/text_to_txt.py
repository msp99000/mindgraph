import aiohttp
import asyncio
import os

async def download_and_extract_text_from_txt(txt_url, token=None):
    """
    Asynchronously download a text file from a given URL and extract text from it.

    Args:
    - txt_url (str): URL of the text file to download.
    - token (str, optional): Bearer token for authorization.

    Returns:
    - str: Extracted text from the text file, or None if an error occurs.
    """
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        async with aiohttp.ClientSession() as session:
            async with session.get(txt_url, headers=headers) as response:
                response.raise_for_status()  # Check if the request was successful
                txt_content = await response.text()

        # Save the text file to a temporary location
        temp_txt_path = 'doc_temp/temp.txt'
        os.makedirs(os.path.dirname(temp_txt_path), exist_ok=True)
        with open(temp_txt_path, 'w', encoding='utf-8') as file:
            file.write(txt_content)

        # Return the text content
        return txt_content
    except aiohttp.ClientError as e:
        print(f"Failed to download text file: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

async def txt_to_text(txt_url, slack_user_token):
    """
    Asynchronously download a text file and return its content, then optionally clean up the temporary file.

    Args:
    - txt_url (str): URL of the text file to download.
    - slack_user_token (str): Bearer token for authorization.
    """
    print("Starting text file extraction...")
    
    # Download and extract text from the text file
    text = await download_and_extract_text_from_txt(txt_url, slack_user_token)

    if text:
        print("Extracted Text:")
        return text
    else:
        print("Failed to extract text from the text file.")

    # Optionally, delete the temporary text file
    temp_txt_path = 'doc_temp/temp.txt'
    if os.path.exists(temp_txt_path):
        os.remove(temp_txt_path)
        print("Temporary file deleted.")

# To run the async function from a synchronous context
# def run_txt_to_text(txt_url, slack_user_token):
#     return asyncio.run(txt_to_text(txt_url, slack_user_token))

# Example usage with a .txt file URL