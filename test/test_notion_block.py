import json

from steamship.data.tags.tag import Tag

from src.notion_block import NotionBlock
from test.test_utils import _read_test_file

__copyright__ = "Steamship"
__license__ = "MIT"


def test_notion_block_heading_1():
    notion_block = NotionBlock(
        block_json=json.loads(_read_test_file("test_block_heading_1.json"))
    )
    assert "Heading #1" == notion_block.get_block_text()
    assert NotionBlock.Type.HEADING_1 == notion_block.type
    assert notion_block.is_major_block_type()
    assert Tag.CreateRequest(
        kind=NotionBlock.NotionTagType, name=NotionBlock.Type.HEADING_1.value, start_idx=0, end_idx=10
    ) == notion_block.get_block_tags()[0]


def test_notion_block_heading_2():
    notion_block = NotionBlock(
        block_json=json.loads(_read_test_file("test_block_heading_2.json"))
    )
    assert "Heading #2" == notion_block.get_block_text()
    assert NotionBlock.Type.HEADING_2 == notion_block.type
    assert notion_block.is_major_block_type()
    assert Tag.CreateRequest(
        kind=NotionBlock.NotionTagType, name=NotionBlock.Type.HEADING_2.value, start_idx=0, end_idx=10
    ) == notion_block.get_block_tags()[0]


def test_notion_block_to_do():
    notion_block = NotionBlock(
        block_json=json.loads(_read_test_file("test_block_to_do.json"))
    )
    assert "To Do" == notion_block.get_block_text()
    assert NotionBlock.Type.TO_DO == notion_block.type
    assert not notion_block.is_major_block_type()
    assert Tag.CreateRequest(
        kind=NotionBlock.NotionTagType, name=NotionBlock.Type.TO_DO.value, start_idx=0, end_idx=5
    ) == notion_block.get_block_tags()[0]


def test_notion_block_paragraph():
    notion_block = NotionBlock(
        block_json=json.loads(_read_test_file("test_block_paragraph.json"))
    )
    assert "This is my paragraph." == notion_block.get_block_text()
    assert NotionBlock.Type.PARAGRAPH == notion_block.type
    assert not notion_block.is_major_block_type()
    assert Tag.CreateRequest(
        kind=NotionBlock.NotionTagType, name=NotionBlock.Type.PARAGRAPH.value, start_idx=0, end_idx=21
    ) == notion_block.get_block_tags()[0]


def test_notion_block_paragraph_rich_text():
    notion_block = NotionBlock(
        block_json=json.loads(_read_test_file("test_block_paragraph_rich_text.json"))
    )
    assert "this is a paragraph that has bold font and also a link to www.google.com and other sites" == notion_block.get_block_text()
    assert NotionBlock.Type.PARAGRAPH == notion_block.type
    tags = notion_block.get_block_tags()
    assert Tag.CreateRequest(
        kind=NotionBlock.NotionTagType, name=NotionBlock.Type.PARAGRAPH.value, start_idx=0, end_idx=88
    ) == notion_block.get_block_tags()[0]
    assert Tag.CreateRequest(
        kind=NotionBlock.NotionTagType, name=NotionBlock.Annotation.BOLD.value, start_idx=24, end_idx=39
    ) == notion_block.get_block_tags()[1]
    assert Tag.CreateRequest(
        kind=NotionBlock.NotionTagType, name=NotionBlock.Annotation.HREF.value, start_idx=57, end_idx=72
    ) == notion_block.get_block_tags()[2]