import json
import os
from unittest.mock import patch

import pytest
from aiohttp import ClientSession
from steamship import TagKind, SteamshipError
from steamship.data.block import Block
from steamship.data.tags.tag import Tag

from src.utils import extract_block_id, fetch_all_block_children, notion_block_to_steamship_blocks, \
    notion_block_to_steamship_content_and_tags, validate_notion_url

__copyright__ = "Steamship"
__license__ = "MIT"


def _read_test_file(filename: str) -> str:
    folder = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(folder, '..', 'test_data', filename), 'r') as f:
        return f.read()


@pytest.mark.asyncio
@patch('src.utils.fetch_notion_json')
async def test_fetch_all_block_children_no_children(mock_fetch_notion_json):
    mock_fetch_notion_json.return_value = {
        'results': [],
        'has_more': False,
    }
    async with ClientSession() as session:
        all_children = await fetch_all_block_children(block_id="dummy", session=session, headers={})
        assert (len(all_children) == 0)


@pytest.mark.asyncio
@patch('src.utils.fetch_notion_json')
async def test_fetch_all_block_children_has_childen_one_page(mock_fetch_notion_json):
    child_json = _read_test_file("test_block_paragraph.json")
    mock_fetch_notion_json.return_value = {
        'results': [child_json],
        'has_more': False,
    }
    async with ClientSession() as session:
        all_children = await fetch_all_block_children(block_id="dummy", session=session, headers={})
        assert (1 == len(all_children))
        assert (child_json == all_children[0])


@pytest.mark.asyncio
@patch('src.utils.fetch_notion_json')
async def test_fetch_all_block_children_has_childen_two_pages(mock_fetch_notion_json):
    paragraph_block_json = _read_test_file("test_block_paragraph.json")
    first_results = []
    for i in range(100):
        first_results.append(paragraph_block_json)
    second_results = [paragraph_block_json]
    mock_fetch_notion_json.side_effect = [{
        'results': first_results,
        'has_more': True,
        'next_cursor': 0,
    },
        {
            'results': second_results,
            'has_more': False,
            'next_cursor': 100,
        }
    ]
    async with ClientSession() as session:
        all_children = await fetch_all_block_children(block_id="dummy", session=session, headers={})
        assert (101 == len(all_children))


@pytest.mark.asyncio
@patch('src.utils.fetch_all_block_children')
async def test_notion_block_to_steamship_content_and_tags_singleton(mock_fetch_all_block_children):
    paragraph_block_json = json.loads(_read_test_file("test_block_paragraph.json"))
    mock_fetch_all_block_children.return_value = []
    async with ClientSession() as session:
        return_block_json, text, tags = await notion_block_to_steamship_content_and_tags(
            block_json=paragraph_block_json,
            session=session,
            headers={}
        )
        assert "This is my paragraph." == text[0]
        assert Tag.CreateRequest(kind=TagKind.doc, name="paragraph") == tags[0]


@pytest.mark.asyncio
@patch('src.utils.fetch_all_block_children')
async def test_notion_block_to_steamship_content_and_tags_one_child(mock_fetch_all_block_children):
    mock_fetch_all_block_children.return_value = [
        json.loads(_read_test_file("test_block_paragraph.json"))
    ]
    heading_with_child_block_json = json.loads(_read_test_file("test_block_heading_with_children.json"))
    async with ClientSession() as session:
        return_block_json, text, tags = await notion_block_to_steamship_content_and_tags(
            block_json=heading_with_child_block_json,
            session=session,
            headers={}
        )
        assert 2 == len(text)
        assert 2 == len(tags)
        assert ["Heading With Children", "This is my paragraph."] == text
        assert Tag.CreateRequest(kind=TagKind.doc, name="heading_1") == tags[0]
        assert Tag.CreateRequest(kind=TagKind.doc, name="paragraph") == tags[1]


@pytest.mark.asyncio
@patch('src.utils.fetch_notion_json')
async def test_notion_block_to_steamship_blocks_singleton(mock_fetch_notion_json):
    mock_fetch_notion_json.return_value = json.loads(_read_test_file("test_block_child_page_no_children.json"))
    async with ClientSession() as session:
        blocks = await notion_block_to_steamship_blocks(
            block_id="dummy_id",
            apikey="dummy_apikey"
        )
        assert 1 == len(blocks)
        tags = [Tag.CreateRequest(
            kind=TagKind.doc,
            name="page",
            startIdx=0,
            endIdx=10
        )]
        assert Block.CreateRequest(text="Child Page\n", tags=tags) == blocks[0]


@pytest.mark.asyncio
@patch('src.utils.fetch_notion_json')
@patch('src.utils.fetch_all_block_children')
async def test_notion_block_to_steamship_blocks_children(mock_fetch_all_block_children, mock_fetch_notion_json):
    mock_fetch_notion_json.return_value = json.loads(_read_test_file("test_block_child_page.json"))
    mock_fetch_all_block_children.return_value = [json.loads(_read_test_file("test_block_bookmark.json"))]
    async with ClientSession() as session:
        blocks = await notion_block_to_steamship_blocks(
            block_id="dummy_id",
            apikey="dummy_apikey"
        )
        assert 1 == len(blocks)
        tags = [
            Tag.CreateRequest(
                kind=TagKind.doc,
                name="page",
                startIdx=0,
                endIdx=10
            ),
            Tag.CreateRequest(
                kind=TagKind.doc,
                name="bookmark",
                startIdx=11,
                endIdx=115
            )
        ]
        assert Block.CreateRequest(
            text="Child Page\n\nhttps://www.nytimes.com/2018/03/12/travel/havana-cuba.html?rref=collection%2Fsectioncollection%2Ftravel",
            tags=tags) == blocks[0]


def test_validate_notion_url_ill_formatted_id():
    with pytest.raises(SteamshipError, match="`url` field did not match"):
        validate_notion_url(url="https://www.notion.so/steamship/123")


def test_validate_notion_url_ill_formatted_domain():
    with pytest.raises(SteamshipError, match="`url` field did not match"):
        validate_notion_url(url="https://www.notion.com/steamship/Quick-Note-8a7ddc57165549a88da4c073c214ffb9")


def test_validate_notion_url_well_formatted():
    url = "https://www.notion.so/steamship/test-8a7ddc57165549a88da4c073c214ffb9"
    validated_url = validate_notion_url(url=url)
    assert validated_url == url


def test_validate_notion_url_well_formatted_no_workspace():
    url = "https://www.notion.so/test-8a7ddc57165549a88da4c073c214ffb9"
    validated_url = validate_notion_url(url=url)
    assert validated_url == url


def test_extract_block_id_ill_formatted():
    with pytest.raises(SteamshipError, match="Page ID could not be parsed"):
        extract_block_id(url="https://www.notion.so/steamship/123")


def test_extract_block_id_well_formatted():
    block_id = extract_block_id(url=f"https://www.notion.so/steamship/test-8a7ddc57165549a88da4c073c214ffb9")
    assert ("8a7ddc57165549a88da4c073c214ffb9" == block_id)
