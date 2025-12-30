"""
Vote/See Functions - Pure Asyncio
"""
import asyncio
import toml
from telethon.tl import functions, types
from utils.logger import logger

# Load Config
try:
    config = toml.load("config.toml")
    AUTO_JOIN = config.get("poll", {}).get("auto_join", True)
except:
    AUTO_JOIN = True

async def vote_poll(clients, channel_username, msg_id, option_indices):
    """
    Votes in a poll.
    option_indices: list of strings "0", "1" (0-based index of the option)
    """
    logger.info(f"Searching for poll in {channel_username}/{msg_id}...", "VOTE")
    
    poll_found = False
    selected_options = []
    
    # 1. QUIET DISCOVERY LOOP
    # We iterate through all clients to find ONE that can see the poll.
    # We suppress errors here to avoid spamming the console.
    
    found_poll_obj = None
    
    for idx, (s_name, client) in enumerate(clients.items()):
        try:
            # Resolve peer
            try:
                entity = await client.get_entity(channel_username)
            except:
                continue # Can't see channel, skip
            
            if isinstance(entity, types.User):
                logger.error(f"'{channel_username}' is a User, not a Channel/Group!", "VOTE")
                return

            # Get Message
            result = await client.get_messages(entity, ids=int(msg_id))
            
            # Auto-Join Fallback
            if not result and AUTO_JOIN:
                try:
                    await client(functions.channels.JoinChannelRequest(channel_username))
                    await asyncio.sleep(0.5)
                    result = await client.get_messages(entity, ids=int(msg_id))
                except: 
                    pass # Quietly fail join
            
            if result and result.media and isinstance(result.media, types.MessageMediaPoll):
                poll = result.media.poll
                answers = poll.answers 
                
                # Check options validity
                valid_opts = True
                temp_opts = []
                for idx_str in option_indices:
                    try:
                        i_opt = int(idx_str)
                        if 0 <= i_opt < len(answers):
                            temp_opts.append(answers[i_opt].option)
                        else:
                            valid_opts = False
                            break
                    except: 
                        valid_opts = False
                        break
                
                if valid_opts:
                    selected_options = temp_opts
                    found_poll_obj = poll
                    poll_found = True
                    break # FOUND IT! Exit loop.
        except:
            continue
            
    if not poll_found:
        logger.error(f"Could not find poll in {len(clients)} accounts.", "VOTE")
        logger.error("Possible reasons: 1. Invalid link 2. Private channel & no bots inside 3. Bots banned", "VOTE")
        return

    question_text = getattr(found_poll_obj.question, 'text', str(found_poll_obj.question))
    logger.success(f"Poll Found: {question_text[:30]}...", "VOTE")

    # 2. MASS VOTE
    async def _vote(client, s_name):
        try:
            # We don't need to resolve entity again usually if we use string username, 
            # but for safety let's just send it.
            await client(functions.messages.SendVoteRequest(
                peer=channel_username, 
                msg_id=int(msg_id),
                options=selected_options
            ))
            logger.success("Voted", s_name)
        except Exception as e:
            err = str(e)
            if "USER_NOT_PARTICIPANT" in err:
                 if AUTO_JOIN:
                     try:
                        await client(functions.channels.JoinChannelRequest(channel_username))
                        await asyncio.sleep(0.5)
                        # Retry vote
                        await client(functions.messages.SendVoteRequest(
                            peer=channel_username, 
                            msg_id=int(msg_id),
                            options=selected_options
                        ))
                        logger.success("Joined & Voted", s_name)
                        return
                     except: pass
                 logger.error("Not a member", s_name)
            elif "OPTION_INVALID" in err:
                 logger.error("Invalid Option", s_name)
            elif "REVOTE_NOT_ALLOWED" in err:
                 logger.success("Already Voted", s_name)
            else:
                 logger.error(f"Vote error: {e}", s_name)

    # Convert to list for asyncio
    tasks = [asyncio.create_task(_vote(c, n)) for n, c in clients.items()]
    await asyncio.gather(*tasks)

async def view_messages(clients, channel, msg_ids):
    logger.info(f"Viewing {len(msg_ids)} posts with {len(clients)} accounts...", "VIEW")
    
    async def _view(client, s_name):
        try:
            ids = [int(i) for i in msg_ids]
            await client(functions.messages.GetMessagesViewsRequest(
                peer=channel,
                id=ids,
                increment=True
            ))
            logger.success("Viewed", s_name)
        except Exception as e:
            logger.error(f"View error: {e}", s_name)

    tasks = [asyncio.create_task(_view(c, n)) for n, c in clients.items()]
    await asyncio.gather(*tasks)
