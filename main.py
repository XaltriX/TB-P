import asyncio
from sys import version as pyver

import pyrogram, uvloop
from pyrogram import __version__ as pyrover
from pyrogram import filters, idle
from pyrogram.errors import FloodWait
from pyrogram.types import Message
import pyrogram, asyncio, os, uvloop, time
from pyrogram import Client, filters, idle, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from sys import version as pyver
from pyrogram import __version__ as pyrover
import config
from tools import get_data, fetch_download_link_async, extract_links, check_url_patterns_async, download_file, download_thumb, get_duration, update_progress, extract_code
from pyrogram.errors import FloodWait, UserNotParticipant, WebpageCurlFailed, MediaEmpty
uvloop.install()
import motor.motor_asyncio
loop = asyncio.get_event_loop()

client = motor.motor_asyncio.AsyncIOMotorClient("mongodb+srv://video:video@cluster0.suiny.mongodb.net/")
db = client.rest  # Replace "your_database" with the name of your MongoDB database
file_collection = db.file
usersdb = db.users
urldb = db.urls

API_ID = "24955235"
API_HASH = "f317b3f7bbe390346d8b46868cff0de8"
BOT_TOKEN = "6883841510:AAHyWn0qv3Mj-r0UIbOsmdJ_tzEAAY6OVvQ"
queue_url = {}

def get_readable_time(seconds: int) -> str:
    count = 0
    readable_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", " days"]
    while count < 4:
        count += 1
        if count < 3:
            remainder, result = divmod(seconds, 60)
        else:
            remainder, result = divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        readable_time += time_list.pop() + ", "
    time_list.reverse()
    readable_time += ": ".join(time_list)
    return readable_time 


app = pyrogram.Client(
    "acha",
    API_ID,
    API_HASH,
    bot_token=BOT_TOKEN,
)

START_TIME = time.time()
SUDO_USERS = config.SUDO_USER
ADMIN_USERS = config.ADMIN_USER
save = {}

async def remove_file(unique_id):
    await file_collection.delete_one({'unique_id': unique_id})

async def get_file(unique_id):
    file = await file_collection.find_one({'unique_id': unique_id})
    if file:
        return file.get('file_id')
    else:
        return None

async def store_file(unique_id, file_id):
    file = await file_collection.find_one({'unique_id': unique_id})
    if file:
      return
    await file_collection.insert_one({'unique_id': unique_id, 'file_id': file_id})
  
async def add_served_user(user_id: int):
        is_served = await usersdb.find_one({"user_id": user_id})
        if is_served:
            return
        return await usersdb.insert_one({"user_id": user_id})

async def get_served_users() -> list:
        users_list = []
        async for user in usersdb.find({"user_id": {"$gt": 0}}):
            users_list.append(user)
        return users_list

async def store_url(url, file_id, unique_id, direct_link):
    try:
        url = await extract_code(url)
        document = await urldb.find_one({"url": url})
        if document and unique_id not in document.get("unique_ids", []):
            await urldb.update_one(
                {"url": url},
                {"$addToSet": {"file_ids": file_id, "unique_ids": unique_id, "direct_links": direct_link}},
                upsert=True
            )
        elif not document:
            await urldb.insert_one({"url": url, "file_ids": [file_id], "unique_ids": [unique_id], "direct_links": [direct_link]})
    except Exception as e:
        print(f"Error storing URL, file ID, unique ID, and direct link: {e}")


async def get_file_ids(url):
    try:
        url = await extract_code(url)
        document = await urldb.find_one({"url": url})
        if document:
            file_ids = document.get("file_ids", [])
            direct_links = document.get("direct_links", [])
            file_id_direct_link_pairs = [(file_id, direct_link) for file_id, direct_link in zip(file_ids, direct_links)]
            return file_id_direct_link_pairs
        else:
            return None
    except Exception as e:
        print(f"Error retrieving file IDs and direct links for URL: {e}")
        return None


async def is_join(user_id):
    try:
        await app.get_chat_member(-1002097822007, user_id)  
   #     await app.get_chat_member(-1001922006659, user_id)
        return True
    except UserNotParticipant:
        return False  
    except FloodWait as e:
        await asyncio.sleep(e.value)



@app.on_message(filters.command("start") & filters.private)
async def start_fun(client, message: Message):
    if len(message.command) > 1 and "unqid" in message.command[1]:              
             unq_id = message.command[1].replace("unqid", "")
             file_id = await get_file(unq_id)
             if file_id:
                 hel = await app.send_cached_media(message.chat.id, file_id)
                 return await add_served_user(message.chat.id)
    await message.reply_text("Send Only Terabox urls")
    return await add_served_user(message.chat.id)


@app.on_message(filters.command("stats") & filters.private & filters.user(SUDO_USERS))
async def stats_func(_, message: Message):
        if db is None:
            return await message.reply_text(
               "MONGO_DB_URI var not defined. Please define it first"
            )
        served_users = await db.users.count_documents({})
        text = f""" **TeraBox Bot Stats:**
        
**Python Version :** {pyver.split()[0]}
**Pyrogram Version :** {pyrover}
**Served Users:** {served_users}
**Uptime:** {get_readable_time(time.time() - START_TIME)}"""
        await message.reply_text(text)

@app.on_message(filters.command("broadcast") & filters.private & filters.user(SUDO_USERS))
async def broadcast_func(_, message: Message):
    if db is None:
            return await message.reply_text(
               "MONGO_DB_URI var not defined. Please define it first"
            )
    if message.reply_to_message:
        x = message.reply_to_message.id
        y = message.chat.id
    elif len(message.command) < 2:
        return await message.reply_text(
            "**Usage**:\n/broadcast [MESSAGE] or [Reply to a Message]"
        )
    else:
        query = message.text.split(None, 1)[1]
    susr = 0
    susers = await get_served_users()
    served_users = [int(user["user_id"]) for user in susers]
    for i in served_users:
        try:
            await app.forward_messages(
                i, y, x
            ) if message.reply_to_message else await app.send_message(
                i, text=query
            )
            susr += 1
        except FloodWait as e:
            flood_time = int(e.value)
            await asyncio.sleep(flood_time)
        except Exception:
            pass
    try:
        await message.reply_text(
            f"**Broadcasted Message to {susr} Users.**"
        )
    except:
        pass


@app.on_message(filters.chat(-1002004278204) & (filters.text | filters.caption))
async def message_handler(client, message):
  text = message.text or message.caption
  if "tera" in text or "box" in text:
       asyncio.create_task(terabox_func(client, message))
  else:
    return await message.reply_text("Send Only Terabox Urls", quote=True)


def box_fil(_, __, message):
    if message.chat.type == enums.ChatType.PRIVATE and (message.text or message.caption):
        text = message.text or message.caption
        return "tera" in text or "box" in text

box_filter = filters.create(box_fil)

@app.on_message(box_filter)
async def private_message_handler(client, message):
        asyncio.create_task(terabox_dm(client, message))


async def terabox_func(client, message):
        urls = extract_links(message.text)
        if not urls:
          return await message.reply_text("No Urls Found")
        try:
            for url in urls:
                if not await check_url_patterns_async(str(url)):
                    await message.reply_text("⚠️ Not a valid Terabox URL!", quote=True)
                    continue
                try:
                    await app.send_message(message.from_user.id, ".")
                except:
                    button = InlineKeyboardButton("Click Here", url="https://t.me/TeraBox_tEST_BoT?start=True")
                    keyboard = InlineKeyboardMarkup([[button]])
                    return await message.reply_text("First start me in private", quote=True, reply_markup=keyboard)                
                files = await get_file_ids(url)
                if files:
                  for file, link in files:
                    try:
                       await app.send_cached_media(message.from_user.id, file, caption=f"**Direct File Link**: {link}")
                    except FloodWait as e:
                       await asyncio.sleep(e.value)
                    except Exception as e:
                       continue
                  continue
                user_id = int(message.from_user.id)
                if user_id in queue_url and str(url) in queue_url[user_id]:
                        return await message.reply_text("This Url is Already In Process Wait")
                if user_id not in queue_url:
                     queue_url[user_id] = {}
                queue_url[user_id][url] = True
                nil = await message.reply_text("🔎 Processing URL...", quote=True)
                try:
                   link_data = await fetch_download_link_async(url)
                   if link_data is None:
                       await message.reply_text("No download link available for this URL", quote=True)
                       continue
                except Exception as e:
                   print(e)
                   await message.reply_text("Some Error Occurred", quote=True)
                   continue 
                for link in link_data:
                    name, size, size_bytes, dlink, thumb  = await get_data(link)
                    if dlink:
                      try:                         
                         if int(size_bytes) < 524288000 and name.lower().endswith(('.mp4', '.mkv', '.webm', '.Mkv')):
                             ril = await client.send_video(message.from_user.id, dlink, has_spoiler=True, caption=f"**Title**: `{name}`\n**Size**: `{size}`")
                             file_id = (ril.video.file_id if ril.video else (ril.document.file_id if ril.document else (ril.animation.file_id if ril.animation else (ril.sticker.file_id if ril.sticker else (ril.photo.file_id if ril.photo else ril.audio.file_id if ril.audio else None)))))
                             unique_id = (ril.video.file_unique_id if ril.video else (ril.document.file_unique_id if ril.document else (ril.animation.file_unique_id if ril.animation else (ril.sticker.file_unique_id if ril.sticker else (ril.photo.file_unique_id if ril.photo else ril.audio.file_unique_id if ril.audio else None)))))                         
                             direct_url = f"https://t.me/TeraBox_tEST_BoT?start=unqid{unique_id}"
                             await nil.edit_text(f"Completed\n\n**File Direct Link:** [Link]({direct_url})", disable_web_page_preview=True)
                             await store_file(unique_id, file_id)
                             await store_url(url, file_id, unique_id, direct_url)
                         else:
                              await client.send_photo(message.from_user.id, thumb, has_spoiler=True, caption=f"**Title**: `{name}`\n**Size**: `{size}`\n**Download Link**: {dlink}")
                              await nil.edit_text("Completed")
                      except FloodWait as e:
                         await asyncio.sleep(e.value)
                      except Exception as e:
                         print(e)
                         try:
                               vid_path = await loop.run_in_executor(None, download_file, dlink, name)
                               thumb_path = await loop.run_in_executor(None, download_thumb, thumb)
                               dur = await loop.run_in_executor(None, get_duration, vid_path)                                                                 
                               ril = await client.send_video(message.from_user.id, vid_path, has_spoiler=True, thumb=thumb_path, caption=f"**Title**: `{name}`\n**Size**: `{size}`", duration=int(dur))
                               file_id = (ril.video.file_id if ril.video else (ril.document.file_id if ril.document else (ril.animation.file_id if ril.animation else (ril.sticker.file_id if ril.sticker else (ril.photo.file_id if ril.photo else ril.audio.file_id if ril.audio else None)))))
                               unique_id = (ril.video.file_unique_id if ril.video else (ril.document.file_unique_id if ril.document else (ril.animation.file_unique_id if ril.animation else (ril.sticker.file_unique_id if ril.sticker else (ril.photo.file_unique_id if ril.photo else ril.audio.file_unique_id if ril.audio else None)))))                               
                               direct_url = f"https://t.me/TeraBox_tEST_BoT?start=unqid{unique_id}"
                               await nil.edit_text(f"Completed\n\n**File Direct Link:** [Link]({direct_url})", disable_web_page_preview=True)
                               await store_file(unique_id, file_id)
                               await store_url(url, file_id, unique_id, direct_url)                       
                         except FloodWait as e:
                              await asyncio.sleep(e.value)
                         except Exception as e:
                           print(e)                          
                           await client.send_photo(message.from_user.id, thumb, has_spoiler=True, caption=f"**Title**: `{name}`\n**Size**: `{size}`\n**Download Link**: {dlink}")
                           await nil.edit_text("Completed")
                         finally:
                                if vid_path and os.path.exists(vid_path):
                                   os.remove(vid_path)
                                if thumb_path and os.path.exists(thumb_path):
                                     os.remove(thumb_path)
        except FloodWait as e:
          await asyncio.sleep(e.value)
        except Exception as e:
            print(e)
            await message.reply_text("Some Error Occurred", quote=True)
        finally:
            user_id = int(message.from_user.id)
            if user_id in queue_url:
                 del queue_url[user_id]



async def terabox_dm(client, message):
        if not await is_join(message.from_user.id):
            return await message.reply_text("you need to join @CheemsBackup before using me")
        urls = extract_links(message.text)
        if not urls:
          return await message.reply_text("No Urls Found")
        try:
            for url in urls:
                if not await check_url_patterns_async(str(url)):
                    await message.reply_text("⚠️ Not a valid Terabox URL!", quote=True)
                    continue                              
                files = await get_file_ids(url)
                if files:
                  for file, link in files:
                    try:
                       await app.send_cached_media(message.chat.id, file, caption=f"**Direct File Link**: {link}")
                    except FloodWait as e:
                      await asyncio.sleep(e.value)
                    except Exception as e:
                       continue
                  continue                
                user_id = int(message.from_user.id)
                if user_id in queue_url and str(url) in queue_url[user_id]:
                        return await message.reply_text("This Url is Already In Process Wait")
                if user_id not in queue_url:
                     queue_url[user_id] = {}
                queue_url[user_id][url] = True
                nil = await message.reply_text("🔎 Processing URL...", quote=True)
                try:
                   link_data = await fetch_download_link_async(url)
                   if link_data is None:
                       await message.reply_text("No download link available for this URL", quote=True)
                       continue
                except Exception as e:
                   print(e)
                   await message.reply_text("Some Error Occurred", quote=True)
                   continue 
                for link in link_data:
                    name, size, size_bytes, dlink, thumb  = await get_data(link)
                    if dlink:
                      try:                        
                         if int(size_bytes) < 524288000 and name.lower().endswith(('.mp4', '.mkv', '.webm', '.Mkv')):
                            ril = await client.send_video(-1002004278204, dlink, caption="Indian")
                            file_id = (ril.video.file_id if ril.video else (ril.document.file_id if ril.document else (ril.animation.file_id if ril.animation else (ril.sticker.file_id if ril.sticker else (ril.photo.file_id if ril.photo else ril.audio.file_id if ril.audio else None)))))
                            unique_id = (ril.video.file_unique_id if ril.video else (ril.document.file_unique_id if ril.document else (ril.animation.file_unique_id if ril.animation else (ril.sticker.file_unique_id if ril.sticker else (ril.photo.file_unique_id if ril.photo else ril.audio.file_unique_id if ril.audio else None)))))                         
                            direct_url = f"https://t.me/TeraBox_tEST_BoT?start=unqid{unique_id}"
                            await ril.copy(message.chat.id, caption=f"**Title**: `{name}`\n**Size**: `{size}`\n\n**Direct File Link**: {direct_url}")
                            await nil.edit_text("Completed")
                            await store_file(unique_id, file_id)
                            await store_url(url, file_id, unique_id, direct_url)
                         else:
                             await client.send_photo(message.chat.id, thumb, has_spoiler=True, caption=f"**Title**: `{name}`\n**Size**: `{size}`\n**Download Link**: {dlink}")
                             await nil.edit_text("Completed")                     
                      except FloodWait as e:
                         await asyncio.sleep(e.value)
                      except Exception as e:
                         print(e)
                         try:                           
                               vid_path = await loop.run_in_executor(None, download_file, dlink, name)
                               thumb_path = await loop.run_in_executor(None, download_thumb, thumb)
                               dur = await loop.run_in_executor(None, get_duration, vid_path)                                                                 
                               ril = await client.send_video(-1002004278204, vid_path, thumb=thumb_path, duration=int(dur), caption="Indian")
                               file_id = (ril.video.file_id if ril.video else (ril.document.file_id if ril.document else (ril.animation.file_id if ril.animation else (ril.sticker.file_id if ril.sticker else (ril.photo.file_id if ril.photo else ril.audio.file_id if ril.audio else None)))))
                               unique_id = (ril.video.file_unique_id if ril.video else (ril.document.file_unique_id if ril.document else (ril.animation.file_unique_id if ril.animation else (ril.sticker.file_unique_id if ril.sticker else (ril.photo.file_unique_id if ril.photo else ril.audio.file_unique_id if ril.audio else None)))))                     
                               direct_url = f"https://t.me/TeraBox_tEST_BoT?start=unqid{unique_id}"
                               await ril.copy(message.chat.id, caption=f"**Title**: `{name}`\n**Size**: `{size}`\n\n**Direct File Link**: {direct_url}")
                               await nil.edit_text("Completed")
                               await store_file(unique_id, file_id)
                               await store_url(url, file_id, unique_id, direct_url)
                         except FloodWait as e:
                              await asyncio.sleep(e.value)
                         except Exception as e:
                           print(e)                     
                           await client.send_photo(message.chat.id, thumb, has_spoiler=True, caption=f"**Title**: `{name}`\n**Size**: `{size}`\n**Download Link**: {dlink}")
                           await nil.edit_text("Completed")
                         finally:
                                if vid_path and os.path.exists(vid_path):
                                   os.remove(vid_path)
                                if thumb_path and os.path.exists(thumb_path):
                                     os.remove(thumb_path)
        except FloodWait as e:
          await asyncio.sleep(e.value)
        except Exception as e:
            print(e)
            await message.reply_text("Some Error Occurred", quote=True)
        finally:
            user_id = int(message.from_user.id)
            if user_id in queue_url:
                del queue_url[user_id]


async def init():
    await app.start()
    print("[LOG] - Yukki Chat Bot Started")
    await idle()
  
if __name__ == "__main__":
    loop.run_until_complete(init())
