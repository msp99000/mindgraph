import aiohttp
import asyncio
from pdfminer.high_level import extract_text
import os

async def download_and_extract_text(pdf_url, token=None):
    """
    Asynchronously download a PDF from a given URL and extract text from it.

    Args:
    - pdf_url (str): URL of the PDF to download.
    - token (str, optional): Bearer token for authorization.

    Returns:
    - str: Extracted text from the PDF, or None if an error occurs.
    """
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        async with aiohttp.ClientSession() as session:
            async with session.get(pdf_url, headers=headers) as response:
                response.raise_for_status()  # Check if the request was successful
                pdf_content = await response.read()

        # Save the PDF file to a temporary location
        temp_pdf_path = 'doc_temp/temp.pdf'
        os.makedirs(os.path.dirname(temp_pdf_path), exist_ok=True)
        with open(temp_pdf_path, 'wb') as file:
            file.write(pdf_content)

        # Extract text from the PDF
        text = extract_pdf_text(temp_pdf_path)
        
        return text
    except aiohttp.ClientError as e:
        print(f"Failed to download PDF: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def extract_pdf_text(pdf_file_path):
    """
    Extract text from a PDF file.

    Args:
    - pdf_file_path (str): Path to the PDF file.

    Returns:
    - str: Extracted text from the PDF, or None if an error occurs.
    """
    try:
        text = extract_text(pdf_file_path)
          # Debug print for extracted text
        return text
    except Exception as e:
        print(f"Failed to extract text from PDF: {e}")
        return None

async def pdf_to_text(pdf_url, slack_user_token):
    """
    Asynchronously download a PDF and extract text from it, then optionally clean up the temporary file.

    Args:
    - pdf_url (str): URL of the PDF to download.
    - slack_user_token (str): Bearer token for authorization.
    """
    print("Starting PDF text extraction...")
    
    # Download and extract text from the PDF
    text = await download_and_extract_text(pdf_url, slack_user_token)

    if text:
        
        print("Extracted Text:")
         
        return text
    else:
        print("Failed to extract text from the PDF.")

    # Optionally, delete the temporary PDF file
    temp_pdf_path = 'doc_temp/temp.pdf'
    if os.path.exists(temp_pdf_path):
        os.remove(temp_pdf_path)
        print("Temporary file deleted.")

# To run the async function from a synchronous context
# def run_pdf_to_text(pdf_url, slack_user_token):
#      return asyncio.run(pdf_to_text(pdf_url, slack_user_token))

 
