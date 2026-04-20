import os
import sys
import argparse
import asyncio
import re
from pathlib import Path
from telegram import Bot
from telegram.constants import ParseMode

def extract_teaser(file_path: Path, article_url: str, link_text: str) -> str:
    """
    Extracts the Telegram teaser from the markdown file and inserts the link.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the teaser section
    teaser_marker = "# Пост для Telegram-канала"
    if teaser_marker not in content:
        raise ValueError(f"Marker '{teaser_marker}' not found in {file_path}")

    teaser_content = content.split(teaser_marker)[1].strip()
    
    # Construct the HTML link
    html_link = f'<a href="{article_url}">{link_text}</a>'
    
    # Replace the placeholder [Ссылка] with the actual HTML link
    if "[Ссылка]" in teaser_content:
        teaser_content = teaser_content.replace("[Ссылка]", html_link)
    else:
        # If no placeholder, append the link at the end (fallback)
        teaser_content += f"\n\n🔗 {html_link}"
    
    # Convert Markdown bold (**text**) to HTML bold (<b>text</b>)
    teaser_content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', teaser_content)
    
    return teaser_content

async def send_telegram_message(chat_id: str, token: str, message: str):
    """
    Sends the message to Telegram.
    """
    bot = Bot(token=token)
    print(f"Sending message to {chat_id}...")
    try:
        # Use ParseMode.HTML to support the link and bold text
        await bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.HTML, disable_web_page_preview=False)
        print("Successfully sent message to Telegram!")
    except Exception as e:
        print(f"Failed to send message: {e}")
        sys.exit(1)

async def main():
    parser = argparse.ArgumentParser(description='Publish article teaser to Telegram')
    parser.add_argument('--file', type=Path, required=True, help='Path to the article Markdown file source')
    parser.add_argument('--chat-id', type=str, required=True, help='Telegram Chat ID')
    parser.add_argument('--url', type=str, required=True, help='URL of the full article')
    parser.add_argument('--link-text', type=str, default="Читать статью", help='Text for the link anchor')
    
    args = parser.parse_args()
    
    if not args.file.exists():
        print(f"Error: File {args.file} not found")
        sys.exit(1)

    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set")
        sys.exit(1)

    try:
        teaser_text = extract_teaser(args.file, args.url, args.link_text)
        print("--- Teaser Preview ---")
        print(teaser_text)
        print("----------------------")
        
        await send_telegram_message(args.chat_id, bot_token, teaser_text)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
