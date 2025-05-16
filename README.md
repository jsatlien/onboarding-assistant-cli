# Onboarding Assistant CLI

A command-line tool for generating and uploading metadata for the Onboarding Assistant.

## Installation

You can install the package globally:

```bash
npm install -g onboarding-assistant-cli
```

Or run it directly using npx:

```bash
npx onboarding-assistant-cli
```

## Prerequisites

- Node.js 14+
- Python 3.6+

The package will check for Python and install required Python dependencies during setup.

## Commands

### Initialize Configuration

Set up your OpenAI API key and Assistant ID:

```bash
npx onboarding-assistant init
```

This will:
- Create necessary directories
- Prompt for your OpenAI API key and Assistant ID
- Generate a configuration file

### Extract Metadata

Extract metadata from your source code:

```bash
npx onboarding-assistant extract <source-dir> --output-dir ./output
```

Options:
- `<source-dir>`: Directory containing your source code (required)
- `--output-dir`, `-o`: Directory where metadata will be saved (default: "./output")

### Upload Embeddings

Upload embeddings to OpenAI:

```bash
npx onboarding-assistant upload --config ./config/assistant_config.yaml
```

Options:
- `--config`, `-c`: Path to configuration file (default: "./config/assistant_config.yaml")
- `--force`, `-f`: Force processing of all files, even if unchanged
- `--verbose`, `-v`: Print verbose output
- `--quiet`, `-q`: Suppress progress bar and non-error output

### All-in-One Workflow

Run the complete workflow (extract metadata and upload embeddings):

```bash
npx onboarding-assistant all <source-dir> --output-dir ./output --config ./config/assistant_config.yaml
```

This combines the extract and upload commands in one step.

## How It Works

This CLI tool is a Node.js wrapper around Python scripts that:

1. Scan your source code to extract contextual metadata
2. Format the metadata for embedding
3. Upload the embeddings to OpenAI
4. Store the results for use with the Onboarding Assistant

## Troubleshooting

If you encounter issues:

- Make sure Python 3.6+ is installed and in your PATH
- Check that your OpenAI API key and Assistant ID are correct
- Ensure your source directory contains valid code files

For more detailed information, see the [Onboarding Assistant documentation](https://github.com/jsatlien/onboarding-assistant).
