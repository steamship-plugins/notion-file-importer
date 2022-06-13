from enum import Enum
from typing import List

from steamship import DocTag, TagKind, SteamshipError
from steamship.data.tags.tag import Tag

class NotionBlock:
    NotionTagType = "notion"

    class Type(Enum):
        BOOKMARK = "bookmark"
        BULLETED_LIST_ITEM = "bulleted_list_item"
        CALLOUT = "callout"
        CHILD_DATABASE = "child_database"
        CHILD_PAGE = "child_page"
        COLUMN = "column"
        COLUMN_LIST = "column_list"
        DIVIDER = "divider"
        EMBED = "embed"
        EQUATION = "equation"
        FILE = "file"
        HEADING_1 = "heading_1"
        HEADING_2 = "heading_2" 
        HEADING_3 = "heading_3"
        IMAGE = "image"
        LINK_PREVIEW = "link_preview"
        LINK_TO_PAGE = "link_to_page"
        NUMBERED_LIST_ITEM = "numbered_list_item"
        PARAGRAPH = "paragraph"
        PDF = "pdf"
        QUOTE = "quote"
        SYNCED_BLOCK = "synced_block"
        TABLE = "table"
        TABLE_OF_CONTENTS = "table_of_contents"
        TABLE_ROW = "table_row"
        TEMPLATE = "template",
        TO_DO = "to_do"
        TOGGLE = "toggle"
        UNKNOWN = "unknown"
        UNSUPPORTED = "unsupported"
        VIDEO = "video"


    class Annotation(Enum):
        BOLD = "bold"
        ITALIC = "italic"
        STRIKETHROUGH = "strikethrough"
        UNDERLINE = "underline"
        CODE = "code"
        COLOR = "color"
        HREF = "href"


    BLOCK_TYPES_WITH_RICH_TEXT = [Type.HEADING_1, Type.HEADING_2, Type.HEADING_3,
                            Type.PARAGRAPH, Type.BULLETED_LIST_ITEM, Type.NUMBERED_LIST_ITEM, 
                            Type.TEMPLATE, Type.TO_DO, Type.TOGGLE]
    BLOCK_TYPES_WITH_URL_TEXT = [Type.BOOKMARK, Type.EMBED, Type.LINK_PREVIEW]


    def __init__(self, block_json):
        """Initializes type and text of NotionBlock object from JSON. Does not set indices."""
        try:
            self.type = NotionBlock.Type[block_json['type'].upper()]
        except:
            self.type = NotionBlock.type['UNKNOWN']
        self.text = self._extract_block_text(block_type=self.type, block_json=block_json)
        self.tags = self._extract_rich_text_block_tags(block_type=self.type, block_json=block_json)

    def is_major_block_type(self) -> bool:
        """Returns true iff Notion Block type is one that begins a new Steamship Block."""
        return self.type in [NotionBlock.Type.HEADING_1, NotionBlock.Type.HEADING_2, NotionBlock.Type.HEADING_3]

    def get_block_tags(self) -> List[Tag.CreateRequest]:
        return self.tags
    
    def get_block_text(self) -> str:
        return self.text

    def _extract_block_text(self, block_type: Type, block_json: str) -> str:
        """
        Returns full block text based on Notion Block type. For Notion Blocks that do not have text, 
        an empty string is returned.
        """
        block_obj = block_json[block_json['type']]
        # get text from rich text
        if block_type in NotionBlock.BLOCK_TYPES_WITH_RICH_TEXT:
            return ''.join(map(lambda rich_text: rich_text['text']['content'], block_obj['rich_text']))
        # get text from url
        if block_type in NotionBlock.BLOCK_TYPES_WITH_URL_TEXT:
            return block_obj['url']
        # get text from title
        if block_type in [NotionBlock.Type.CHILD_PAGE, NotionBlock.Type.CHILD_DATABASE]:
            return block_obj['title']
        # get text from expression
        if block_type in [NotionBlock.Type.EQUATION]:
            return block_obj['expression']
        # get text from cells
        if block_type in [NotionBlock.Type.TABLE_ROW]:
            return ','.join(map(lambda cell: cell['plaintext'], block_obj['cells']))
        else:
            return ""
    
    def _extract_rich_text_block_tags(self, block_type: Type, block_json: str) -> List[Tag.CreateRequest]:
        """Returns tags related to rich text features: bold, italic, strikethrough, underline, code, color."""
        tags = [Tag.CreateRequest(kind=self.NotionTagType, name=self.type.value, start_idx=0, end_idx=len(self.get_block_text()))]
        if block_type in NotionBlock.BLOCK_TYPES_WITH_RICH_TEXT:
            block_obj = block_json[block_json['type']]
            full_text = ""
            for rich_text_element in block_obj['rich_text']:
                start_idx = max(len(full_text) - 1, 0)
                element_plain_text = rich_text_element['plain_text']
                full_text += element_plain_text
                end_idx = max(len(full_text), 0)
                for prop in [NotionBlock.Annotation.BOLD.value, NotionBlock.Annotation.ITALIC.value,
                            NotionBlock.Annotation.STRIKETHROUGH.value, NotionBlock.Annotation.UNDERLINE.value,
                            NotionBlock.Annotation.CODE.value]:
                    if rich_text_element['annotations'][prop]:
                        tags.append(Tag.CreateRequest(
                            kind=self.NotionTagType,
                            name=prop,
                            start_idx = start_idx,
                            end_idx = end_idx
                        ))
                if rich_text_element['annotations'][NotionBlock.Annotation.COLOR.value] != "default":
                    tags.append(Tag.CreateRequest(
                        kind=self.NotionTagType,
                        name=f"{NotionBlock.Annotation.COLOR.value}={rich_text_element['annotations']['color']}",
                        start_idx = start_idx,
                        end_idx = end_idx
                    ))
                if rich_text_element['href'] != 'None':
                    tags.append(Tag.CreateRequest(
                        kind=self.NotionTagType,
                        name=NotionBlock.Annotation.HREF.value,
                        start_idx = start_idx,
                        end_idx = end_idx
                    ))
        return tags