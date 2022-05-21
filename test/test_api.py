import base64
import os

import pytest
from steamship import MimeTypes
from steamship.app import Response
from steamship.base.tasks import TaskState
from steamship.plugin.inputs.file_import_plugin_input import FileImportPluginInput
from steamship.plugin.outputs.raw_data_plugin_output import RawDataPluginOutput
from steamship.plugin.service import PluginRequest

from src.api import NotionFileImporterPlugin

__copyright__ = "Steamship"
__license__ = "MIT"

URL = "https://www.notion.so/Quick-Note-8a7ddc57165549a88da4c073c214ffb9"

def test():
    importer = NotionFileImporterPlugin(config={"apikey": "secret_myYSko8yPt5O8CwJgInPUthUD6XSsWwzKcKmcvXwjrR"})
    request = PluginRequest(data=FileImportPluginInput(url=URL))
    response = importer.run(request)
    # print(response)
    # assert(1 == 2)