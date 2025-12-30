"""
Report Functions - Pure Asyncio
"""
import asyncio
from telethon.tl import functions, types
from utils.logger import logger

async def report_spam(clients, channel, post_ids, reason_idx, comment):
    logger.info("Reporting...", "REPORT")
    
    reasons = [
        types.InputReportReasonChildAbuse(),
        types.InputReportReasonCopyright(),
        types.InputReportReasonFake(),
        types.InputReportReasonPornography(),
        types.InputReportReasonSpam(),
        types.InputReportReasonViolence(),
        types.InputReportReasonOther()
    ]
    reason = reasons[reason_idx]
    
    async def _report(client, s_name):
        try:
            # Resolve peer
            if str(channel).isdigit():
                peer = int(channel)
            else:
                peer = channel
            
            # Post IDs should be list of ints
            ids = [int(p) for p in post_ids]
            
            await client(functions.messages.ReportRequest(
                peer=peer,
                id=ids,
                reason=reason,
                message=comment
            ))
            logger.success("Reported", s_name)
        except Exception as e:
            logger.error(f"Failed: {e}", s_name)

    tasks = [asyncio.create_task(_report(c, n)) for n, c in clients.items()]
    await asyncio.gather(*tasks)
