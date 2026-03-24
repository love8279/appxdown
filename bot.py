import os
import re
import requests
import subprocess
import asyncio
from pyrogram import Client, filters

# Heroku Config Vars
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client("appx_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def get_headers(token):
    return {
        "token": token,
        "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
        "Content-Type": "application/json"
    }

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "✨ **Appx Automation Bot** ✨\n\n"
        "1. Pehle `/login YOUR_TOKEN` bhejein.\n"
        "2. Phir `/download COURSE_ID` se content nikalein."
    )

@app.on_message(filters.command("login"))
async def login(client, message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: `/login TOKEN`")
    token = message.command[1]
    res = requests.get("https://api.appx.co.in/get-profile", headers=get_headers(token))
    if res.status_code == 200:
        await message.reply_text("✅ Token Valid hai! Ab download command use karein.")
    else:
        await message.reply_text("❌ Galat Token.")

@app.on_message(filters.command("download"))
async def download_handler(client, message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: `/download COURSE_ID`")
    
    course_id = message.command[1]
    token = "PASTE_YOUR_DEFAULT_TOKEN_HERE" # Default token ya database se lein
    status = await message.reply_text("⚡ Fetching Course Content...")

    api_url = f"https://api.appx.co.in/get-course-content/{course_id}"
    try:
        data = requests.get(api_url, headers=get_headers(token)).json()
        contents = data.get("data", [])
        
        if not contents:
            return await status.edit("❌ Koi content nahi mila ya ID galat hai.")

        await status.edit(f"Found {len(contents)} items. Downloading shuru...")

        for item in contents:
            title = re.sub(r'[\\/*?:"<>|]', "", item.get("title", "File")).strip()
            url = item.get("link") or item.get("video_link")
            
            if not url: continue

            await status.edit(f"Downloading: `{title}`")
            
            file_name = f"{title}.mp4" if "m3u8" in url else f"{title}.pdf"
            
            try:
                if "m3u8" in url:
                    # Optimized yt-dlp command for Heroku
                    cmd = f'yt-dlp -o "{file_name}" "{url}" --no-check-certificate'
                    subprocess.run(cmd, shell=True)
                else:
                    r = requests.get(url, stream=True)
                    with open(file_name, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)

                # Upload to Telegram
                await client.send_document(message.chat.id, file_name, caption=f"✅ `{title}`")
                if os.path.exists(file_name): os.remove(file_name)

            except Exception as e:
                await message.reply_text(f"⚠️ Error in {title}: {str(e)}")

        await status.edit("✅ Process Complete!")
    except Exception as e:
        await status.edit(f"❌ API Error: {str(e)}")

app.run()
