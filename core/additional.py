"""
Additional Functions - Pure Asyncio
"""
import random
import os
import asyncio
from telethon.tl import functions
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest
from utils.logger import logger

async def update_bio(clients, bio_text):
    logger.info(f"Updating bio for {len(clients)} accounts...", "BIO")
    tasks = []
    for s_name, client in clients.items():
        tasks.append(client(UpdateProfileRequest(about=bio_text)))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    count = 0
    for res in results:
        if not isinstance(res, Exception):
            count += 1
    logger.success(f"Updated bio for {count}/{len(clients)} accounts", "BIO")

async def update_name(clients, names, surnames):
    logger.info(f"Updating names for {len(clients)} accounts...", "NAME")
    tasks = []
    
    async def _update(client, s_name):
        try:
            n = random.choice(names) if names else "John"
            s = random.choice(surnames) if surnames else "Doe"
            await client(UpdateProfileRequest(first_name=n, last_name=s))
            logger.success(f"Changed: {n} {s}", s_name)
        except Exception as e:
            logger.error(f"Name Error: {e}", s_name)

    tasks = [asyncio.create_task(_update(c, n)) for n, c in clients.items()]
    await asyncio.gather(*tasks)

async def update_avatar(clients):
    if not os.path.exists('avatars'):
        logger.error("Folder 'avatars' not found!", "AVATAR")
        return
        
    # Pre-load images into memory to avoid Disk I/O bottlenecks during concurrency
    valid_exts = ('.jpg', '.png', '.jpeg')
    raw_images = []
    
    # Try importing PIL for optimization
    try:
        from PIL import Image
        import io
        HAS_PIL = True
    except ImportError:
        HAS_PIL = False
        logger.warning("Pillow not found. Install it for faster uploads: pip install Pillow", "AVATAR")

    for f in os.listdir('avatars'):
        if f.lower().endswith(valid_exts):
            try:
                f_path = os.path.join('avatars', f)
                
                if HAS_PIL:
                    # Optimize Image in RAM
                    with Image.open(f_path) as img:
                        img = img.convert("RGB")
                        img.thumbnail((1024, 1024)) # Resize to max 1024x1024
                        
                        bio = io.BytesIO()
                        img.save(bio, format="JPEG", quality=80) # Compress
                        optimized_bytes = bio.getvalue()
                        
                        raw_images.append(optimized_bytes)
                        
                        orig_size = os.path.getsize(f_path) / 1024
                        new_size = len(optimized_bytes) / 1024
                        logger.info(f"Loaded {f}: {orig_size:.1f}KB -> {new_size:.1f}KB (Optimized)", "AVATAR")
                else:
                    # Raw load
                    with open(f_path, 'rb') as img_f:
                        raw_images.append(img_f.read())
                        
            except Exception as e:
                logger.error(f"Failed to read {f}: {e}")

    if not raw_images:
        logger.error("No valid images found in 'avatars/'!", "AVATAR")
        return

    logger.info(f"Starting update for {len(clients)} avatars...", "AVATAR")
    
    # High Concurrency (Safe due to small file size now)
    sem = asyncio.Semaphore(20) 
    
    async def _single_avatar(client, s_name):
        async with sem:
            for attempt in range(1, 4): 
                try:
                    img_data = random.choice(raw_images)
                    
                    if attempt == 1:
                        logger.pending(f"Uploading...", s_name)
                    else:
                        logger.warning(f"Retry {attempt}...", s_name)
                    
                    # Upload (30s timeout is plenty for 50KB files)
                    file = await asyncio.wait_for(
                        client.upload_file(img_data), 
                        timeout=30.0
                    )
                    
                    await client(functions.photos.UploadProfilePhotoRequest(file=file))
                    
                    logger.success(f"Avatar Updated", s_name)
                    return
                    
                except asyncio.TimeoutError:
                    if attempt == 3: logger.error("Timeout", s_name)
                except Exception as e:
                    if attempt == 3: logger.error(f"Err: {e}", s_name)
                
                await asyncio.sleep(1) # Backoff

    tasks = [asyncio.create_task(_single_avatar(c, n)) for n, c in clients.items()]
    await asyncio.gather(*tasks)
