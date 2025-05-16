# Onboarding Assistant CLI

A command-line tool for generating context files from your application's source code for the Onboarding Assistant. This tool simplifies the process of extracting code from your frontend and backend files and formatting them as text files suitable for direct upload to the OpenAI Assistant via the dashboard.

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
- Configuration file (optional) - YAML file with OpenAI credentials

This tool is pure JavaScript and does not require Python or any other dependencies.

## How It Works

The Onboarding Assistant CLI generates context files from your application's source code. These files are formatted as plain text (.txt) files with appropriate headers and can be directly uploaded to the OpenAI Assistant via the dashboard.

The workflow is simple:

1. Use the CLI to generate context files from your frontend and backend code
2. Upload the generated .txt files to your OpenAI Assistant via the dashboard
3. The Assistant will automatically use these files as context when responding to user queries

## Output Format

Each generated .txt file follows this format:

```
// FILE: path/to/original/file.vue
// ROUTE: /route-name (for frontend files)

[Original file content with preserved formatting]
```

For backend model files:

```
// FILE: path/to/original/file.cs
// MODEL: ModelName (Entity Framework)

[Original file content with preserved formatting]
```

These files are organized in the output directory as follows:

- `output/routes/` - Frontend context files (one per route/component)
- `output/models/` - Backend context files (one per model)

## Commands

### Generate Frontend Context

Generate context files from your frontend source code:

```bash
npx onboarding-assistant generate-frontend -s <source-dir> -o <output-dir> -c <config-file>
```

Or use the interactive mode:

```bash
npx onboarding-assistant generate-frontend
```

This command will:
- Process all Vue files, extracting routes from router configuration when possible
- Output each file as a .txt file in the output/routes/ directory with appropriate headers
- Use the configuration from your YAML file for OpenAI credentials (if provided)

### Generate Backend Context

Generate context files from your backend model files:

```bash
npx onboarding-assistant generate-backend -s <source-dir> -o <output-dir> -c <config-file>
```

Or use the interactive mode:

```bash
npx onboarding-assistant generate-backend
```

This command will:
- Process all model files, detecting Entity Framework models
- Output each model as a .txt file in the output/models/ directory with appropriate headers
- Use the configuration from your YAML file for OpenAI credentials (if provided)

## Using with OpenAI Assistant

After generating the context files, follow these steps to use them with your OpenAI Assistant:

1. Log in to the [OpenAI platform](https://platform.openai.com/)
2. Navigate to your Assistant or create a new one
3. In the Assistant settings, go to the "Knowledge" section
4. Click "Upload files" and select all the .txt files from your output directory
5. Save your changes

Now your Assistant will have access to the context from your application's source code when responding to user queries.

## Backend Integration

When sending user queries to the Assistant API from your backend, include the current route in the message content to help the Assistant retrieve the most relevant context. For example:

```csharp
string userMessage = $"The user is currently on {currentRoute} and has asked: {userQuestion}";  
```

This ensures the Assistant has enough contextual keywords to retrieve the correct file from its knowledge base.

## Complete Workflow

Here's the workflow for setting up and using the Onboarding Assistant:

1. **Set up an OpenAI Assistant**
   - Create an OpenAI account and get an API key
   - Create a new Assistant with appropriate instructions
   - Enable the Retrieval feature in the Assistant settings

2. **Generate frontend context**
   - Run `npx onboarding-assistant generate-frontend -s <source-dir> -o <output-dir> -c <config-file>`
   - Or use the interactive mode and follow the prompts
   - This generates .txt files with the full source code of your frontend components

3. **Generate backend context (if applicable)**
   - Run `npx onboarding-assistant generate-backend -s <source-dir> -o <output-dir> -c <config-file>`
   - Or use the interactive mode and follow the prompts
   - This generates .txt files with the full source code of your backend models

4. **Upload the generated .txt files to your OpenAI Assistant**
   - Go to your Assistant in the OpenAI platform
   - Navigate to the Knowledge section
   - Upload the generated .txt files from the output/routes/ and output/models/ directories
   - These files will be used as context for your Assistant

5. **Integrate the Onboarding Assistant into your application**
   - When sending user queries to the Assistant API, include the current route in the message
   - Let OpenAI's retrieval system automatically find and use the relevant context
   - No need for manual context filtering or embedding logic

## How It Works

1. **Scan your source code files**
   - Recursively finds all Vue files or C# model files in the specified directory
   - For Vue files, attempts to extract routes from router configuration files
   - For C# files, identifies Entity Framework models using common patterns

2. **Generate context files**
   - Creates .txt files with the full source code of each file
   - Adds minimal header comments with file path and route/model information
   - Preserves original formatting and indentation

3. **Output organized files**
   - Frontend files are saved to output/routes/ with kebab-case filenames
   - Backend files are saved to output/models/ with kebab-case filenames
   - Files are ready to be uploaded directly to your OpenAI Assistant

4. **Manual upload to OpenAI Assistant**
   - You upload the generated .txt files to your OpenAI Assistant via the dashboard
   - OpenAI's Retrieval system indexes the content for semantic search
   - No need for custom embedding generation or vector storage

5. **Dynamic context retrieval**
   - When a user asks a question, the current route is included in the query
   - OpenAI's Retrieval system automatically finds the most relevant context
   - The Assistant uses this context to provide accurate, tailored responses


## Output Format

The CLI generates text files with the following structure:

### Frontend Route Files

```
// FILE: path/to/original/file.vue
// ROUTE: /dashboard

<template>
  <div class="dashboard">
    <h1>Dashboard</h1>
    <!-- Original content preserved -->
  </div>
</template>

<script>
// Original script content preserved
</script>
```

### Backend Model Files

```
// FILE: path/to/original/file.cs
// MODEL: DashboardWidget

namespace MyApp.Models
{
    public class DashboardWidget
    {
        // Original model content preserved
    }
}
```

## Framework Compatibility

The CLI tool is designed to work with specific frontend and backend frameworks:

### Frontend Support
- **Vue.js**: Full support for Vue components and route extraction

### Backend Support
- **Entity Framework Core**: Support for C# model classes used with Entity Framework

Additional framework support may be added in future versions.

## OpenAI Assistant Setup

Before generating context files, you need to set up an OpenAI Assistant with the Retrieval feature enabled.

### Step 1: Set Up Your OpenAI Account

1. Visit https://platform.openai.com/ and sign in or create an account
2. Ensure you have access to the Assistants API

### Step 2: Create an Assistant

1. Navigate to https://platform.openai.com/assistants
2. Click "Create Assistant"
3. Fill out the basic information:
   - Name: "Onboarding Assistant" (or your preferred name)
   - Instructions: Include details about your application and how the assistant should help users
   - Model: Choose GPT-4 or newer for best results
4. **Important**: Enable the Retrieval feature by toggling it on
5. Save your assistant

### Step 3: Upload Context Files

1. After generating context files with the CLI tool, return to your Assistant in the OpenAI dashboard
2. In the Knowledge section, click "Upload files"
3. Select all the .txt files from your output directory (both routes and models)
4. Wait for the files to be processed and indexed
5. Save your changes

Your Assistant is now ready to use with the context from your application!

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.


## License

MIT


## Troubleshooting

If you encounter issues:

- Ensure your source directory contains valid code files
- Check that the output directory is writable
- For Vue files, make sure they follow standard Vue SFC format
- For Entity Framework models, ensure they follow standard C# class patterns
- If files are not being processed correctly, check the console output for specific errors

For more detailed information, see the [Onboarding Assistant documentation](https://github.com/jsatlien/onboarding-assistant).

## Configuration File

You can use a YAML configuration file to provide your OpenAI credentials:

```yaml
openai:
  api_key: "your-api-key"
  assistant_id: "your-assistant-id"
```

This file is optional and only needed if you plan to use additional features that interact directly with the OpenAI API.
