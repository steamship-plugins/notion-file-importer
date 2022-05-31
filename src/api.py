"""Notion File Importer Plugin."""

import asyncio

from steamship.app import App, Response, post, create_handler
from steamship.base import MimeTypes
from steamship.base.error import SteamshipError
from steamship.data.file import File
from steamship.plugin.file_importer import FileImporter
from steamship.plugin.inputs.file_import_plugin_input import FileImportPluginInput
from steamship.plugin.outputs.raw_data_plugin_output import RawDataPluginOutput
from steamship.plugin.service import PluginRequest

from src.utils import extract_block_id, notion_block_to_steamship_blocks, validate_notion_url


class NotionFileImporterPlugin(FileImporter, App):
    """"Imports Notion pages as Steamship Block Format."""

    def run(self, request: PluginRequest[FileImportPluginInput]) -> Response[RawDataPluginOutput]:
        """Performs the file import or returns a detailed error explaining what went wrong."""

        # Check to make sure the plugin config defined in `steamship.json` has been provided with an API Key.
        if self.config is None:
            raise SteamshipError(message=f"Empty config provided to FileImportPlugin.")
        if self.config.get('apikey', None) is None:
            raise SteamshipError(
                message=f"Empty `apikey` field provided to FileImportPlugin. Please provide upon initialization.")

        # Check to make sure the user provided a URL to identify what it is they want imported.
        if request.data is None:
            raise SteamshipError(
                message=f"Missing the wrapped FileImportPluginInput request object. Got request: {request}")
        if request.data.url is None:
            raise SteamshipError(message=f"Missing the `url` field in your FileImportPluginInput request. Got request: {request}")
        
        url = validate_notion_url(request.data.url)
        steamship_blocks = asyncio.run(notion_block_to_steamship_blocks(block_id=extract_block_id(url=url), apikey=self.config.get('apikey')))
        print(steamship_blocks)
        steamship_block_json = File.CreateRequest(blocks=steamship_blocks)

        # All plugin responses must be wrapped in the PluginResponse object.
        return Response(data=RawDataPluginOutput(json=steamship_block_json, mime_type=MimeTypes.STEAMSHIP_BLOCK_JSON))

    @post('/import_file')
    def import_file(self, **kwargs) -> Response[RawDataPluginOutput]:
        """HTTP endpoint for our plugin.

        When deployed and instantiated in a Space, this endpoint will be served at:

        https://{username}.steamship.run/{space_id}/{plugin_instance_id}/import_file

        When adapting this template, you can almost always leave the below code unchanged.
        """
        request = FileImporter.parse_request(request=kwargs)
        return self.run(request)


handler = create_handler(NotionFileImporterPlugin)
