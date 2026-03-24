import os
import re
import requests
import subprocess
from pyrogram import Client, filters

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
    await message.reply_text("✅ **Bot Active!**\nUse `/login TOKEN` and then `/download COURSE_ID`.")

@app.on_message(filters.command("login"))
async def login(client, message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: `/login YOUR_TOKEN`")
    token = message.command[1]
    res = requests.get("https://api.appx.co.in/get-profile", headers=get_headers(token))
    if res.status_code == 200:
        await message.reply_text("✅ Login Success!")
    else:
        await message.reply_text("❌ Invalid Token.")

@app.on_message(filters.command("download"))
async def download_handler(client, message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: `/download COURSE_ID`")
    
    course_id = message.command[1]
    token = "YOUR_DEFAULT_TOKEN" # Yahan apna token daal sakte hain
    status = await message.reply_text("🔎 Content fetch ho raha hai...")

    api_url = f"https://api.appx.co.in/get-course-content/{course_id}"
    try:
        response = requests.get(api_url, headers=get_headers(token)).json()
        data = response.get("data", [])
        
        if not data:
            return await status.edit("❌ Course empty hai ya ID galat hai.")

        for item in data:
            name = re.sub(r'[\\/*?:"<>|]', "", item.get("title", "File")).strip()
            url = item.get("link") or item.get("video_link")
            if not url: continue

            await status.edit(f"📥 Downloading: `{name}`")
            file_name = f"{name}.mp4" if "m3u8" in url else f"{name}.pdf"

            try:
                if "m3u8" in url:
                    # ffmpeg location logic added
                    cmd = f'yt-dlp -o "{file_name}" "{url}" --no-check-certificate'
                    subprocess.run(cmd, shell=True)
                else:
                    r = requests.get(url, stream=True)
                    with open(file_name, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)

                await client.send_document(message.chat.id, file_name, caption=f"✅ `{name}`")
                if os.path.exists(file_name): os.remove(file_name)

            except Exception as e:
                await message.reply_text(f"⚠️ Error: {name}\n`{str(e)}`")

        await status.edit("🎯 Saara content process ho gaya!")
    except Exception as e:
        await status.edit(f"❌ Error: {str(e)}")

app.run()
        
