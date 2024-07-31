import asyncio, re, random, aiohttp, uuid, json
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import pyshorteners, humanfriendly
import pyrogram, asyncio, os, uvloop, uuid, random, subprocess, requests
import re, json, aiohttp, random
from io import BytesIO

#loop = asyncio.get_event_loop()
rapi = pyshorteners.Shortener()

download_urls = ["https://d3.terabox.app", "https://d3.1024tera.com", "https://d4.terabox.app", "https://d4.1024tera.com", "https://d5.terabox.app", "https://d5.1024tera.com"]

async def update_progress(downloaded, total, message, state="Uploading"):
    try:
        percentage = (downloaded / total) * 100
        downloaded_str = humanfriendly.format_size(downloaded)
        total_str = humanfriendly.format_size(total)
        
        # Check if percentage is a multiple of 10
        if int(percentage) % 30 == 0:
            await message.edit_text(f"{state}: {downloaded_str} / {total_str} ({percentage:.0f}%)")
        
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        print(e)
        pass

"""
def download_file(url: str, filename):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()        
        with open(filename, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)                
        return filename
    except Exception as e:
        print(f"Error downloading file: {e}")
        try:
            os.remove(filename)
        except:
            pass
        return False
        
"""

def download_file(url, file_path, retry_count=0):    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))    
        with open(file_path, 'ab') as file:
            file.seek(0, os.SEEK_END) 
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
                    downloaded_size = file.tell()              
                    if downloaded_size >= total_size:
                        break
        return file_path 
    except (requests.exceptions.ChunkedEncodingError, requests.exceptions.ConnectionError) as e:
        if retry_count < 2: 
            print(f"Retrying... (Attempt {retry_count + 1})")
            return download_file(url, file_path, retry_count + 1)
        else:
            print("Maximum retry attempts reached.")
            try:
                os.remove(file_path)
            except:
                pass
            return None
    except Exception as e:
        print(f"Error occurred: {e}")
        try:
            os.remove(file_path)
        except:
            pass
        return None



def download_thumb(url: str):
    try:
        random_uuid = uuid.uuid4()
        uuid_string = str(random_uuid)
        filename = f"downloads/{uuid_string}.jpeg"
        response = requests.get(url)
        response.raise_for_status()
        with open(filename, 'wb') as f:
            f.write(response.content)
        return filename    
    except Exception as e:
        print(f"Error downloading image: {e}")
        try:
            os.remove(filename)
        except:
            pass
        return None


def get_duration(file_path):
    command = [
        "ffprobe",
        "-loglevel",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        file_path,
    ]

    pipe = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, err = pipe.communicate()
    _json = json.loads(out)

    if "format" in _json:
        if "duration" in _json["format"]:
            return float(_json["format"]["duration"])

    if "streams" in _json:
        for s in _json["streams"]:
            if "duration" in s:
                print(float(s["duration"]))
                return float(s["duration"])

    return None


async def create_session():
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Cookie': 'browserid=khXCS03TzvdACGfWjfD-9fdJBWCd83okmrk0apGAEPjCXVWWeTWXwdqk0fU=; lang=en; __bid_n=18e3dd5bb2c9cb73434207; _ga=GA1.1.1811415982.1710434419; __stripe_mid=759ba489-0c3b-40da-a098-dd7ab307d05c9f299d; __bid_n=18e8bfdfc3be4ea4224207; csrfToken=8JPIz5vKB7OFpUJPYTiUzWtW; ndus=Y23AA8KteHuisa-G0gHj13u4hy-0jpGBB1qMIP6j; ndut_fmt=068CF73643C0A6D33CA63114B295CD291FAE96FC359C85F7B519B6EB40AD2769; ab_sr=1.0.1_Y2Q2NzFmMjJjZjI2ZTIwY2Y1OGRmMjdkYjQ4NDNkYWE5ZjM4N2YwNDM4MjViZThmZWNhMDczYWQxMDNlNjVhNmRhMjEwNWNhMDk0M2Q2YjkzOTcyNDk1MjY0MTYwYTJmMmU4ZTZjOWJhNzRiODkxZjRkYmUzODg0ZjRmZjgwMWUzYTViMzQ3NDBmMzQzMGRiZjg5ZWM3YWZlODUzMDdjYQ==; ab_ymg_result={"data":"eb84d2c1e0bdeab29071677f50331dcf2c3ec7fb62a3feafc0f94cccf1b1ccaa34c5bc0d95e6e60a6b02b3d1577127ebfe85ff48d0f62ecbd8c0fea8b5eb38bcffac8cd6e82103ef074257509767fcbb3cd5db615d54b0eebe88148f78b786a885cecadd43c7a3c60b0d6569bda8e2c9966b647c77cbd9f7c88421c1f557d8b7","key_id":"66","sign":"2e10ba72"}; _ga_06ZNKL8C2E=GS1.1.1711745818.2.1.1711746308.15.0.0',
        'Referer': 'https://terabox.app/',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    my_session = aiohttp.ClientSession(headers=headers) 
    return my_session

async def fetch_download_link_async(url):
    my_session = await create_session()
    try:
        async with my_session.get(url) as response:
            response.raise_for_status()
            response_data = await response.text()

            js_token = await find_between(response_data, 'fn%28%22', '%22%29')
            log_id = await find_between(response_data, 'dp-logid=', '&')

            if not js_token or not log_id:
                return None

            request_url = str(response.url)
            surl = request_url.split('surl=')[1]
            params = {
                'app_id': '250528',
                'web': '1',
                'channel': 'dubox',
                'clienttype': '0',
                'jsToken': js_token,
                'dplogid': log_id,
                'page': '1',
                'num': '20',
                'order': 'time',
                'desc': '1',
                'site_referer': request_url,
                'shorturl': surl,
                'root': '1'
            }

            async with my_session.get('https://www.terabox.app/share/list', params=params) as response2:
                response_data2 = await response2.json()
                if 'list' not in response_data2:
                    return None
                if response_data2['list'][0]['isdir'] == "1":
                    params.update({
                        'dir': response_data2['list'][0]['path'],
                        'order': 'asc',
                        'by': 'name',
                        'dplogid': log_id
                    })
                    params.pop('desc')
                    params.pop('root')
                    async with my_session.get('https://www.terabox.app/share/list', params=params) as response3:
                        response_data3 = await response3.json()
                        if 'list' not in response_data3:
                            return None
                        return response_data3['list']
                return response_data2['list']

    except aiohttp.ClientResponseError as e:
        print(f"Error fetching download link: {e}")
        return None
    finally:
        await my_session.close()


async def get_url(download_link):
  try:
    async with aiohttp.ClientSession() as session:
        for url in download_urls:
            full_url = url + download_link[download_link.index("/", 8):]
            async with session.get(full_url) as response:
                if response.status == 200:
                    return full_url
    return None
  except Exception as e:
    print(e)
    return None
     
  
async def get_direct_link(url):
    try:
        my_session = await create_session()
        async with my_session.head(url) as response:
            response.raise_for_status()
            direct_link = response.headers.get('Location')
            return direct_link
    except Exception as e:
        print(f"Error fetching direct link: {e}")
        return None
    finally:
        await my_session.close()
      

  
async def get_data(link_data):
  try:
    file_name = link_data["server_filename"]
    file_size = await get_formatted_size_async(link_data["size"])
    download_link = await get_direct_link(link_data["dlink"])
    if not download_link:
        download_link = await get_url(link_data["dlink"])
        if not download_link:
           url = random.choice(download_urls)
           download_link = url + link_data["dlink"][link_data["dlink"].index("/", 8):]
    download_link = rapi.tinyurl.short(download_link)
    thumb = link_data["thumbs"]["url3"]
    return file_name, file_size, link_data["size"], download_link, thumb
  except Exception as e:
    print(e)
    return None, None, None, None, None

def extract_links(message):
    # fetch all links
    try:
        url_pattern = r'https?://\S+'        
        matches = re.findall(url_pattern, message)

        return matches
    except Exception as e:
        print(f"Error extracting links: {e}")
        return []
        

async def get_formatted_size_async(size_bytes):
    try:
        size_bytes = int(size_bytes)
        size = size_bytes / (1024 * 1024) if size_bytes >= 1024 * 1024 else (
            size_bytes / 1024 if size_bytes >= 1024 else size_bytes
        )
        unit = "MB" if size_bytes >= 1024 * 1024 else ("KB" if size_bytes >= 1024 else "bytes")

        return f"{size:.2f} {unit}"
    except Exception as e:
        print(f"Error getting formatted size: {e}")
        return None


async def check_url_patterns_async(url):
    patterns = [
        r"ww\.mirrobox\.com",
        r"www\.nephobox\.com",
        r"freeterabox\.com",
        r"www\.freeterabox\.com",
        r"1024tera\.com",
        r"4funbox\.co",
        r"www\.4funbox\.com",
        r"mirrobox\.com",
        r"nephobox\.com",
        r"terabox\.app",
        r"terabox\.com",
        r"www\.terabox\.ap",
        r"terabox\.fun",
        r"www\.terabox\.com",
        r"www\.1024tera\.co",
        r"www\.momerybox\.com",
        r"teraboxapp\.com",
        r"momerybox\.com",
        r"tibibox\.com",
        r"www\.tibibox\.com",
        r"www\.teraboxapp\.com",
    ]

    for pattern in patterns:
        if re.search(pattern, url):
            return True
    return False


async def find_between(string, start, end):
    start_index = string.find(start) + len(start)
    end_index = string.find(end, start_index)
    return string[start_index:end_index]

async def shorten_url(long_url):
    api_key = '26LFT5xlnvMbhEwux1LCDvftvss2'
    api_url = f"https://api.shareus.io/easy_api?key={api_key}&link={long_url}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.text()
                    return data.strip()  # Remove any extra whitespace
                else:
                    print(f"Failed to shorten URL. Status code: {response.status}")
                    return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
      
async def extract_code(url: str):
    pattern1 = r"/s/(\w+)"
    pattern2 = r"surl=(\w+)"
    match = re.search(pattern1, url)
    if match:
        return match.group(1)
    match = re.search(pattern2, url)
    if match:
        return match.group(1)
    return url


async def shorten_url_async(destination_link):
    api_url = f'https://publicearn.com/api?api=8960075d61d126996682b45d5d8b4503a8d5e717&url={destination_link}'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()               
                    if 'shortenedUrl' in data:
                        shortened_url = data['shortenedUrl']                        
                        return shortened_url
                    else:
                        print("Shortened URL not found in the response")
                        return None
                else:
                    print(f"Request failed with status code: {response.status}")
                    return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


