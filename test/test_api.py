from aiohttp import ClientSession
import asyncio
import base64
import json
import os
import pytest
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from test import TEST_DATA

from steamship import DocTag, TagKind, MimeTypes
from steamship.app import Response
from steamship.base.tasks import TaskState
from steamship.data.block import Block
from steamship.data.tags.tag import Tag
from steamship.plugin.inputs.file_import_plugin_input import FileImportPluginInput
from steamship.plugin.outputs.raw_data_plugin_output import RawDataPluginOutput
from steamship.plugin.service import PluginRequest

from src.api import NotionFileImporterPlugin
from src.utils import fetch_all_block_children, fetch_notion_json, notion_block_to_steamship_content_and_tags

__copyright__ = "Steamship"
__license__ = "MIT"

URL = "https://www.notion.so/Quick-Note-8a7ddc57165549a88da4c073c214ffb9"

def _base64_decode(base64_message: str) -> str:
    base64_bytes = base64_message.encode('ascii')
    message_bytes = base64.b64decode(base64_bytes)
    return message_bytes.decode('utf8')

def _get_test_file(filename: str):
    async def load_mock(**kwargs):
        with (TEST_DATA / filename).open('r') as config_file:
            return json.load(config_file)
    return load_mock

@patch('src.utils.fetch_notion_json', _get_test_file("test_block_child_page_no_children.json"))
def test():
    importer = NotionFileImporterPlugin(config={"apikey": "<>"})
    request = PluginRequest(data=FileImportPluginInput(url=URL))
    response = importer.run(request)
    # assert(response.data.mimeType == MimeTypes.STEAMSHIP_BLOCK_JSON)
    # print(response)
    # assert 1 == 2




