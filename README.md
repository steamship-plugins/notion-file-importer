# Steamship Notion File Importer Plugin Template

This project contains a File Importer Plugin that will fetch a Notion page by URL and return that page in Steamship Block Format.

## Usage

This plugin is auto-deployed to Steamship and available via handle: `notion-file-importer`.

The plugin requires authentication with Notion via an API Key. To generate an API Key for your Notion
workspace:
1.  Go to [My Integrations](https://www.notion.so/my-integrations)
2. Click `Create New Integration`
3. Fill out and submit the form.
5. Copy the API Key, i.e. `Internal Integration Token`, which will start with `secret_`

*By default, your integration does not have permissions to pages in your Notion workspace. You must give your Integration permissions to access pages of interest by clicking `Share` in the top right corner of each page and inviting your integration to the page.*


## Example 

Here is a complete example of using it:

```
from steamship import Steamship
from steamship.data.file import File
from steamship.data.plugin_instance import PluginInstance

# Create your ~/steamship.json credential file by installing the Steamship CLI and running `ship login`
client = Steamship()   

# Create an instance of this plugin. 
plugin_instance = PluginInstance.create(client, plugin_handle="notion-file-importer")

# Import a new file into Steamship using this importer
url = "https://www.notion.so/<workspace>/<pageid>"
task = File.create(client=client, url=url, plugin_instance=plugin_instance)

```

## Tagging Strategy

Notion pages have a natural, nested [block](https://developers.notion.com/reference/block) structure. This importer uses knowledge of Notion's block structure to extract Notion Block Format content.

Outer-level headers (i.e. Notion block of type `header_x` whose parent is the page itself) logically partition Notion pages into Steamship blocks. All other outer-level Notion blocks and all inner-Notion-blocks are considered a continuation of the preceding Steamship block; their text content is included in the Steamship block and they are added as Steamship Tags to the Steamship Block.

Notion Blocks that begin a new Steamship block:
- The first Notion Block in a page
- Outer-level header blocks (Heading 1, Heading 2, Heading 3)

Notion Blocks that are a continuation of the preceding Steamship block:
- Inner-level blocks of any type (i.e. blocks whose parent is *not* the Notion Page itself)
- Outer-level blocks that are not of type header and are not the first of the page

## Developing

We recommend using a Python virtual environments for development.
To set one up, run the following command from this directory:

**Your first time**, create the virtual environment with:

```bash
python3 -m venv .venv
```

**Each time**, activate your virtual environment with:

```bash
source .venv/bin/activate
```

**Your first time**, install the required dependencies with:

```bash
python -m pip install -r requirements.dev.txt
python -m pip install -r requirements.txt
```

### Code Structure

All the code for this plugin is located in the `src/api.py` file:

* The `FileImporterPlugin` class
* The `/import_file` endpoint

### Testing

Tests are located in the `test/test_api.py` file. You can run them with:

```bash
% pytest --asyncio-mode=strict -vv
```

We have provided sample data in the `test_data/` folder.

### Deploying

Deploy this project to Steamship as a new plugin of your own with:

```bash
ship deploy
```

### Sharing

Please share what you've built with hello@steamship.com!

We would love take a look, hear your suggestions, help where we can, and share what you've made with the community.