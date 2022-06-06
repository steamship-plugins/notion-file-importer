import asyncio
import io
import re
from aiohttp import ClientSession
from typing import Dict, List, Optional
from urllib.error import HTTPError

import requests
from steamship import DocTag, TagKind, SteamshipError
from steamship.data.block import Block
from steamship.data.tags.tag import Tag
from steamship.plugin.outputs.raw_data_plugin_output import RawDataPluginOutput

from src.notion_block import NotionBlock

NOTION_PAGE_ID_REGEX = ".*/[A-Za-z0-9-]*([A-Za-z0-9-]{32})"
NOTION_WORKSPACE_REGEX = "[A-Za-z0-9-]+"
NOTION_URL_REGEX = "https://www.([A-Za-z0-9-]+.notion.site||notion.so(/[A-Za-z0-9-]+)?)/[A-Za-z0-9-]*([A-Za-z0-9-]{32})$"

async def fetch_notion_json(url: str, session: ClientSession, headers: Dict) -> Dict:
    """Returns JSON formatted response to Notion API GET request."""
    valid_response = None
    while valid_response is None:
        async with session.get(url=url, headers=headers) as response:
            json_response = await response.json()
            if 'error' in json_response:
                status_code = response.status
                if status_code == 401 or status_code == 403:
                    raise SteamshipError(message='Cannot authorize with Notion', internal_message=f'Notion returned error: {json_response["error"]}')
                elif status_code == 429:
                    raise SteamshipError(message='Hitting Notion Request Limit', internal_message=f'Notion returned error: {json_response["error"]}')
                else:
                    raise SteamshipError(message='Unable to query Notion', internal_message=f'Notion returned error: {json_response["error"]}')
            else:
                valid_response = json_response
    return valid_response

async def fetch_all_block_children(block_id: str, session: ClientSession, headers: Dict) -> List[Dict]:
    """Retrieves list of all Notion Block JSON that are immediate children of block at url by iterating through paginated Notion API responses."""
    paginated_response = await fetch_notion_json(url=f"https://api.notion.com/v1/blocks/{block_id}/children", session=session, headers=headers)
    all_children = paginated_response['results']
    while(paginated_response['has_more']):
        cursor = paginated_response['next_cursor']
        paginated_response = await fetch_notion_json(url=f"https://api.notion.com/v1/blocks/{block_id}/children?next_cursor={cursor}", session=session, headers=headers)
        all_children.extend(paginated_response['results'])
    return all_children

async def notion_block_to_steamship_content_and_tags(block_json: dict, session: ClientSession, headers: Dict):
    """Returns NotionBlock with lists of text and tags (omitting start/stop indices) aggregated from descendant blocks."""
    notion_block_obj = NotionBlock(block_json=block_json)
    text = [notion_block_obj.get_block_text()]
    tags = [notion_block_obj.get_block_tag()]
    if block_json['has_children']:
        children = await fetch_all_block_children(block_id=block_json['id'], session=session, headers=headers)
        tasks = []
        for child in children:
            tasks.append(asyncio.ensure_future(notion_block_to_steamship_content_and_tags(block_json=child, session=session, headers=headers)))
        results = await asyncio.gather(*tasks)
        for _, rec_text, rec_tags in results:
            text.extend(rec_text)
            tags.extend(rec_tags)
    return notion_block_obj, text, tags

async def notion_block_to_steamship_blocks(block_id: str, apikey: str) -> List[Block.CreateRequest]:
    """Builds List of Steamship Blocks from Notion Page Block."""
    async with ClientSession() as session:
        headers = {
            "Accept": "application/json",
            "Notion-Version": "2022-02-22",
            "Authorization": "Bearer {}".format(apikey)
        }
        page_parent_block = await fetch_notion_json(url=f"https://api.notion.com/v1/blocks/{block_id}", session=session, headers=headers)
        steamship_blocks = []
        title = page_parent_block['child_page']['title']
        curr_steamship_block = Block.CreateRequest(
            text = f"{title}\n",
            tags = [
                Tag.CreateRequest(kind=TagKind.doc, name="page", startIdx=0, endIdx=len(title)) # TODO: need different TagKind
            ]
        )
        if page_parent_block['has_children']:
            children = await fetch_all_block_children(block_id=block_id, session=session, headers=headers)
            tasks = []
            for child in children:
                tasks.append(asyncio.ensure_future(notion_block_to_steamship_content_and_tags(block_json=child, session=session, headers=headers)))
            results = await asyncio.gather(*tasks)
            for notion_block, text, tags in results:
                if notion_block.is_major_block_type():
                    steamship_blocks.append(curr_steamship_block)
                    curr_steamship_block = Block.CreateRequest(
                        text = "",
                        tags = []
                    )
                for txt, tg in zip(text, tags):
                    text_to_append = f"\n{txt}" if txt else ""
                    tg.startIdx = len(curr_steamship_block.text)
                    tg.endIdx = tg.startIdx + len(text_to_append)
                    curr_steamship_block.text += text_to_append
                    curr_steamship_block.tags.append(tg)
        if curr_steamship_block.text or len(curr_steamship_block.tags) > 0:
            steamship_blocks.append(curr_steamship_block)
        return steamship_blocks


def validate_notion_url(url: str) -> str:
    """
    Notion page urls of interest can take one of two formats:
        (1) https://www.notion.so/<workspace>/<pageid> with workspace optional
        (2) https://www.<workspace>.notion.site/<pageid>
    Assumption: workspace must be alphanumeric but can include hyphens.
    """
    if not re.match(NOTION_URL_REGEX, url.lower().strip()):
        raise SteamshipError(
            message=f"The provided `url` field did not match either of the following formats: https://www.notion.so/<workspace>/<pageid> or https://www.<workspace>.notion.site/<pageid>. Got url: {url}")
    return url

def extract_block_id(url: str) -> str:
    """Extracts block ID from Notion URL (equivalent to page ID)."""
    block_id_match = re.search(NOTION_PAGE_ID_REGEX, url.lower().strip())
    if block_id_match is None:
        raise SteamshipError(
            message=f"Page ID could not be parsed from provided `url`. `url` must end in unique identifier of length 32. Make sure provided url comes from shareable link."
        )
    return block_id_match.group(1)