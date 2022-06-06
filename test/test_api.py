import base64
import json
from unittest.mock import patch

from steamship import MimeTypes, File, Tag, DocTag, TagKind
from steamship.plugin.inputs.file_import_plugin_input import FileImportPluginInput
from steamship.plugin.service import PluginRequest

from notion_block import NotionBlock
from src.api import NotionFileImporterPlugin
from test import TEST_DATA

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


class TagKinds:
    pass


@patch('src.utils.fetch_notion_json', _get_test_file("test_block_child_page_no_children.json"))
def test():
    importer = NotionFileImporterPlugin(config={"apikey": "<>"})
    request = PluginRequest(data=FileImportPluginInput(url=URL))
    response = importer.run(request)
    assert (response.data.mime_type == MimeTypes.STEAMSHIP_BLOCK_JSON)
    file_json = _base64_decode(response.data.data)
    file = File.CreateRequest.parse_obj(json.loads(file_json))

    # It has the right number of blocks
    assert len(file.blocks) == 1

    # It has the right text
    assert file.blocks[0].text == "Child Page\n"

    # It has the right file tags
    assert file.tags is None

    # The block has the right block tags
    assert len(file.blocks[0].tags) == 1
    tag = file.blocks[0].tags[0]
    assert tag.kind == TagKind.doc
    assert tag.name == DocTag.page
    assert file.blocks[0].text[tag.start_idx:tag.end_idx] == "Child Page"

