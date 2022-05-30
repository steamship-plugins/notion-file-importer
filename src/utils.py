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

NOTION_PAGE_ID_REGEX = ".*/[A-Za-z0-9-]*([A-Za-z0-9-]{32})"
NOTION_WORKSPACE_REGEX = "[A-Za-z0-9-]+"
NOTION_URL_REGEX = f"https://www.({NOTION_WORKSPACE_REGEX}.notion.site||notion.so(/{NOTION_WORKSPACE_REGEX})?)/[A-Za-z0-9-]+$"

def steamship_blockify(block: str) -> Block:
    """Converts Notion Block JSON to Steamship Block."""
    # TODO: determine which notion blocks should be steamship blocks, tags, or both
    return block

async def fetch_notion_json(url: str, session: ClientSession, headers: Dict) -> Dict:
    """Returns JSON formatted response to Notion API GET request."""
    valid_response = None
    while valid_response is None:
        async with session.get(url=url, headers=headers) as response:
            json_response = await response.json()
            if 'error' in json_response:
                status_code = response.status
                if status_code == 401 or status_code == 403:
                    raise SteamshipError(message='Cannot authorize with Notion', internalMessage=f'Notion returned error: {json_response["error"]}')
                elif status_code == 429:
                    raise SteamshipError(message='Hitting Notion Request Limit', internalMessage=f'Notion returned error: {json_response["error"]}')
                else:
                    raise SteamshipError(message='Unable to query Notion', internalMessage=f'Notion returned error: {json_response["error"]}')
            else:
                valid_response = json_response
    return valid_response

async def fetch_all_block_children(block_id: str, session: ClientSession, headers: Dict) -> List[Dict]:
    """Retrieves list of all Notion Block JSON that are immediate children of block at url by iterating through paginated Notion API responses."""
    paginated_response = await fetch_notion_json(url=f"https://api.notion.com/v1/blocks/{block_id}/children", session=session, headers=headers)
    all_children = paginated_response['results']
    while(paginated_response['has_more']):
        cursor = paginated_children['next_cursor']
        paginated_response = await fetch_notion_json(url=f"https://api.notion.com/v1/blocks/{block_id}/children?next_cursor={cursor}", headers=headers)
        all_children.extend(paginated_response['results'])
    return all_children

async def notion_block_to_steamship_blocks(block_id: str, apikey: str) -> List[Block]:
    """Recursively parses Notion Blocks to build an aggregate list of Steamship Blocks."""
    async with ClientSession() as session:
        headers = {
            "Accept": "application/json",
            "Notion-Version": "2022-02-22",
            "Authorization": "Bearer {}".format(apikey)
        }
        block = await fetch_notion_json(url=f"https://api.notion.com/v1/blocks/{block_id}", session=session, headers=headers)
        steamship_blocks = [steamship_blockify(block)]
        print(block)
        if block['has_children']:
            children = await fetch_all_block_children(block_id=block_id, session=session, headers=headers)
            tasks = []
            for child in children:
                tasks.append(asyncio.ensure_future(notion_block_to_steamship_blocks(block_id=child['id'], apikey=apikey)))
            results = await asyncio.gather(*tasks)
            for nested_blocks in results:
                steamship_blocks.extend(nested_blocks)
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
    block_id_match = re.search(NOTION_PAGE_ID_REGEX, url.lower().strip()).group(1)
    if block_id_match is None:
        raise SteamshipError(
            message=f"Page ID could not be parsed from provided `url`. `url` must end in unique identifier of length 32. Make sure provided url comes from shareable link."
        )
    return url[-32:]