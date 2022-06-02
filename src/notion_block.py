from enum import Enum

from steamship import DocTag, TagKind, SteamshipError
from steamship.data.tags.tag import Tag

class NotionBlock:
    class Type(Enum):
        HEADING_1 = "heading_1" 
        HEADING_2 = "heading_2" 
        HEADING_3 = "heading_3" 
        PARAGRAPH = "paragraph"
        BULLETED_LIST_ITEM = "bulleted_list_item"
        NUMBERED_LIST_ITEM = "numbered_list_item"
        TO_DO = "to_do"
        TOGGLE = "toggle"
        CHILD_PAGE = "child_page"
        CHILD_DATABASE = "child_database"
        EMBED = "embed"
        IMAGE = "image"
        VIDEO = "video"
        FILE = "file"
        PDF = "pdf"
        BOOKMARK = "bookmark"
        CALLOUT = "callout"
        QUOTE = "quote"
        EQUATION = "equation"
        DIVIDER = "divider"
        TABLE_OF_CONTENTS = "table_of_contents"
        COLUMN = "column"
        COLUMN_LIST = "column_list"
        LINK_PREVIEW = "link_preview"
        SYNCED_BLOCK = "synced_block"
        TEMPLATE = "template",
        LINK_TO_PAGE = "link_to_page"
        TABLE = "table"
        TABLE_ROW = "table_row"
        UNSUPPORTED = "unsupported"

    def __init__(self, block_json):
        """Initializes type and text of NotionBlock object from JSON. Does not set indices."""
        self.type = NotionBlock.Type[block_json['type'].upper()]
        self.text = self._extract_block_text(block_type=self.type, block_json=block_json)
        self.tag = Tag.CreateRequest(kind=TagKind.doc, name=self.type.value) # TODO: need different TagKind

    def is_major_block_type(self) -> bool:
        """Returns true iff Notion Block type is one that, if a child of page block, begins a new Steamship Block."""
        return self.type in [NotionBlock.Type.HEADING_1, NotionBlock.Type.HEADING_2, NotionBlock.Type.HEADING_3]

    def get_block_tag(self) -> str:
        return self.tag
    
    def get_block_text(self) -> str:
        return self.text

    def _extract_block_text(self, block_type: Type, block_json: str) -> str:
        """Returns text based on Notion Block type."""
        block_obj = block_json[block_json['type']]
        # get text from rich text
        if block_type in [NotionBlock.Type.HEADING_1, NotionBlock.Type.HEADING_2, NotionBlock.Type.HEADING_3,
                          NotionBlock.Type.PARAGRAPH, NotionBlock.Type.BULLETED_LIST_ITEM, NotionBlock.Type.NUMBERED_LIST_ITEM, 
                          NotionBlock.Type.TEMPLATE, NotionBlock.Type.TO_DO, NotionBlock.Type.TOGGLE]:
            return ' '.join(map(lambda rich_text: rich_text['text']['content'], block_obj['rich_text']))
        # get text from url
        if block_type in [NotionBlock.Type.BOOKMARK, NotionBlock.Type.EMBED, NotionBlock.Type.LINK_PREVIEW]:
            return block_obj['url']
        # get text from title
        if block_type in [NotionBlock.Type.CHILD_PAGE, NotionBlock.Type.CHILD_DATABASE]:
            return block_obj['title']
        # get text from expression
        if block_type in [NotionBlock.Type.EQUATION]:
            return block_obj['expression']
        # get text from cells
        if block_type in [NotionBlock.Type.TABLE_ROW]:
            text = ','.join(map(lambda cell: cell['plaintext'], block_obj['cells']))
        else:
            return ""