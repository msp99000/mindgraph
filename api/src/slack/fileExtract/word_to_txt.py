import aiohttp
import asyncio
from docx import Document
import os

async def download_and_extract_text_from_word(docx_url, token=None):
    """
    Asynchronously download a Word file from a given URL and extract text from it.
    """
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        async with aiohttp.ClientSession() as session:
            async with session.get(docx_url, headers=headers) as response:
                response.raise_for_status()  # Check if the request was successful
                docx_content = await response.read()

        # Save the Word file to a temporary location
        temp_docx_path = 'doc_temp/temp.docx'
        os.makedirs(os.path.dirname(temp_docx_path), exist_ok=True)
        
        with open(temp_docx_path, 'wb') as file:
            file.write(docx_content)

        print("File downloaded and saved temporarily.")

        # Check if the file exists after saving
        if not os.path.exists(temp_docx_path):
            print(f"Error: File not found after saving at {temp_docx_path}")
            return None

        # Extract text from the Word file
        text = extract_word_text(temp_docx_path)
        
        return text
    except aiohttp.ClientError as e:
        print(f"Failed to download Word file: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def extract_word_text(docx_file_path):
    """
    Extract text from a Word file.
    """
    try: 
        doc = Document(str(docx_file_path))
        print(doc,'dddfdfd')
        full_text = []
        for paragraph in doc.paragraphs:
            full_text.append(paragraph.text)
        
        return '\n'.join(full_text)
    except Exception as e:
        print(f"Failed to extract text from Word file: {e}")
        return None

async def word_to_text(docx_url, slack_user_token):
    """
    Asynchronously download a Word file and extract text from it.
    """
    print("Starting Word file text extraction...")
    
    # Download and extract text from the Word file
    text = await download_and_extract_text_from_word(docx_url, slack_user_token)

    if text:
        print("Extracted Text:")
        return text
    else:
        print("Failed to extract text from the Word file.")

    # Optionally, delete the temporary Word file
    temp_docx_path = 'doc_temp/temp.docx'
    if os.path.exists(temp_docx_path):
        os.remove(temp_docx_path)
        print("Temporary file deleted.")

# To run the async function from a synchronous context
# async def run_word_to_text(docx_url, slack_user_token):
#           return asyncio.run(word_to_text(docx_url, slack_user_token))

# Example usage
 
