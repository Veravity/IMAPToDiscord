import imaplib
import email
import requests
import yaml
import re
from email.header import decode_header

import logging

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration from YAML file
with open('config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)

# Check the type of the config variable
print(f'Type of config: {type(config)}')

# Extract configuration values
IMAP_SERVER = config.get('IMAP_SERVER', '')
IMAP_PORT = config.get('IMAP_PORT', 993)
IMAP_USERNAME = config.get('IMAP_USERNAME', '')
IMAP_PASSWORD = config.get('IMAP_PASSWORD', '')
DISCORD_WEBHOOK_URL = config.get('DISCORD_WEBHOOK_URL', '')

# Print extracted values for debugging
print(f'IMAP_SERVER: {IMAP_SERVER}')
print(f'IMAP_PORT: {IMAP_PORT}')
print(f'IMAP_USERNAME: {IMAP_USERNAME}')
print(f'IMAP_PASSWORD: {IMAP_PASSWORD}')
print(f'DISCORD_WEBHOOK_URL: {DISCORD_WEBHOOK_URL}')

# Connect to Gmail account via IMAP
mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
mail.login(IMAP_USERNAME, IMAP_PASSWORD)
mail.select('inbox')

# Search for unseen emails
typ, msgnums = mail.search(None, 'UNSEEN')
for msgnum in msgnums[0].split()[::-1]:  # reverse order to get oldest first
    typ, msg_data = mail.fetch(msgnum, '(RFC822)')

    # Parse email
    msg = email.message_from_bytes(msg_data[0][1])
    from_email = email.utils.parseaddr(msg['From'])[1]

    # Decode the subject line
    subject = decode_header(msg['Subject'])[0][0]
    if isinstance(subject, bytes):
        subject = subject.decode()

    body = None

    # Check for HTML or plain text body
    for part in msg.walk():
        content_type = part.get_content_type()
        if content_type == 'text/plain' or content_type == 'text/html':
            body = part.get_payload(decode=True).decode()

            # Extract links containing "https://www.spigotmc.org/resources/" and the word "update"
            links = re.findall(r'(https?://www.spigotmc.org/resources/\S*update\S*)', body)
            link_content = '\n'.join(links)

    # Prepare the rich embed content
    embed_content = {
        "title": f"Plugin Updated! - {subject}",
        "description": f"From: {from_email}\n\n{link_content}"
    }

    # Send email content to Discord via webhook
    data = {
        'embeds': [embed_content]
    }
    response = requests.post(DISCORD_WEBHOOK_URL, json=data)
    if response.status_code != 204:
        print(f'Error sending message to Discord webhook: {response.text}')

# Close the IMAP connection
mail.logout()
