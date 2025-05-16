#!/usr/bin/env node

const { program } = require('commander');
const chalk = require('chalk');
const { PythonShell } = require('python-shell');
const path = require('path');
const fs = require('fs');
const ora = require('ora');
const inquirer = require('inquirer');

// Get the path to the Python scripts
const SCRIPT_DIR = path.join(__dirname, '..', 'lib', 'python');

// Define the CLI program
program
  .name('onboarding-assistant')
  .description('CLI tools for the Onboarding Assistant')
  .version('0.1.0');

// Extract metadata command
program
  .command('extract')
  .description('Extract metadata from source code')
  .argument('<source-dir>', 'Source directory to scan')
  .option('-o, --output-dir <dir>', 'Output directory for metadata', './output')
  .action((sourceDir, options) => {
    console.log(chalk.blue('🔍 Extracting metadata from source code...'));
    
    const spinner = ora('Processing files...').start();
    
    // Make sure the source directory exists
    if (!fs.existsSync(sourceDir)) {
      spinner.fail(chalk.red(`Source directory not found: ${sourceDir}`));
      process.exit(1);
    }
    
    // Run the Python script
    const pyshell = new PythonShell(path.join(SCRIPT_DIR, 'metadata_generator.py'), {
      args: [sourceDir, '--output-dir', options.outputDir],
      mode: 'text'
    });
    
    pyshell.on('message', (message) => {
      // Update spinner text with progress
      spinner.text = message;
    });
    
    pyshell.end((err, code, signal) => {
      if (err) {
        spinner.fail(chalk.red(`Error extracting metadata: ${err.message}`));
        process.exit(1);
      }
      
      spinner.succeed(chalk.green('Metadata extraction complete!'));
      console.log(chalk.blue(`Output saved to: ${options.outputDir}`));
    });
  });

// Upload embeddings command
program
  .command('upload')
  .description('Upload embeddings to OpenAI')
  .option('-c, --config <file>', 'Path to config file', './config/assistant_config.yaml')
  .option('-f, --force', 'Force processing of all files, even if unchanged')
  .option('-v, --verbose', 'Print verbose output')
  .option('-q, --quiet', 'Suppress progress bar and non-error output')
  .action((options) => {
    console.log(chalk.blue('📤 Uploading embeddings to OpenAI...'));
    
    const spinner = ora('Processing embeddings...').start();
    
    // Make sure the config file exists
    if (!fs.existsSync(options.config)) {
      spinner.fail(chalk.red(`Config file not found: ${options.config}`));
      process.exit(1);
    }
    
    // Build the arguments
    const args = ['--config', options.config];
    if (options.force) args.push('--force');
    if (options.verbose) args.push('--verbose');
    if (options.quiet) args.push('--quiet');
    
    // Run the Python script
    const pyshell = new PythonShell(path.join(SCRIPT_DIR, 'upload_embeddings.py'), {
      args: args,
      mode: 'text'
    });
    
    pyshell.on('message', (message) => {
      // Update spinner text with progress
      spinner.text = message;
    });
    
    pyshell.end((err, code, signal) => {
      if (err) {
        spinner.fail(chalk.red(`Error uploading embeddings: ${err.message}`));
        process.exit(1);
      }
      
      spinner.succeed(chalk.green('Embeddings upload complete!'));
    });
  });

// Init command - create config files
program
  .command('init')
  .description('Initialize configuration for the Onboarding Assistant')
  .action(async () => {
    console.log(chalk.blue('🚀 Initializing Onboarding Assistant...'));
    
    // Create directories
    const configDir = path.join(process.cwd(), 'config');
    const outputDir = path.join(process.cwd(), 'output');
    
    if (!fs.existsSync(configDir)) {
      fs.mkdirSync(configDir, { recursive: true });
    }
    
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }
    
    // Ask for OpenAI credentials
    const answers = await inquirer.prompt([
      {
        type: 'input',
        name: 'apiKey',
        message: 'Enter your OpenAI API key (starts with "sk-"):',
        validate: (input) => {
          if (!input.startsWith('sk-')) {
            return 'API key must start with "sk-"';
          }
          return true;
        }
      },
      {
        type: 'input',
        name: 'assistantId',
        message: 'Enter your OpenAI Assistant ID (starts with "asst_"):',
        validate: (input) => {
          if (!input.startsWith('asst_')) {
            return 'Assistant ID must start with "asst_"';
          }
          return true;
        }
      },
      {
        type: 'list',
        name: 'embeddingModel',
        message: 'Select embedding model:',
        choices: [
          { name: 'text-embedding-3-small (Recommended)', value: 'text-embedding-3-small' },
          { name: 'text-embedding-3-large (Higher quality, more expensive)', value: 'text-embedding-3-large' },
          { name: 'text-embedding-ada-002 (Legacy)', value: 'text-embedding-ada-002' }
        ],
        default: 'text-embedding-3-small'
      }
    ]);
    
    // Create config file
    const configPath = path.join(configDir, 'assistant_config.yaml');
    const configContent = `# Onboarding Assistant Configuration
# Generated on ${new Date().toISOString()}

# OpenAI API credentials
openai_api_key: "${answers.apiKey}"
assistant_id: "${answers.assistantId}"

# Embedding model to use
embedding_model: "${answers.embeddingModel}"

# Paths for metadata and embeddings
metadata_path: "./output"
index_path: "./output/embeddings.json"

# Format for embeddings (currently only OpenAI is supported)
embedding_format: "openai"
`;
    
    fs.writeFileSync(configPath, configContent);
    
    console.log(chalk.green('✅ Configuration initialized successfully!'));
    console.log(chalk.blue(`Configuration saved to: ${configPath}`));
    console.log(chalk.yellow('\nNext steps:'));
    console.log(chalk.yellow('1. Run metadata extraction: onboarding-assistant extract <source-dir>'));
    console.log(chalk.yellow('2. Upload embeddings: onboarding-assistant upload'));
  });

// All-in-one command
program
  .command('all')
  .description('Run the complete workflow: extract metadata and upload embeddings')
  .argument('<source-dir>', 'Source directory to scan')
  .option('-o, --output-dir <dir>', 'Output directory for metadata', './output')
  .option('-c, --config <file>', 'Path to config file', './config/assistant_config.yaml')
  .option('-f, --force', 'Force processing of all files, even if unchanged')
  .action((sourceDir, options) => {
    console.log(chalk.blue('🚀 Running complete Onboarding Assistant workflow...'));
    
    // First extract metadata
    console.log(chalk.blue('\n🔍 Step 1: Extracting metadata from source code...'));
    
    const extractSpinner = ora('Processing files...').start();
    
    // Make sure the source directory exists
    if (!fs.existsSync(sourceDir)) {
      extractSpinner.fail(chalk.red(`Source directory not found: ${sourceDir}`));
      process.exit(1);
    }
    
    // Run the metadata extraction script
    const extractPyshell = new PythonShell(path.join(SCRIPT_DIR, 'metadata_generator.py'), {
      args: [sourceDir, '--output-dir', options.outputDir],
      mode: 'text'
    });
    
    extractPyshell.on('message', (message) => {
      extractSpinner.text = message;
    });
    
    extractPyshell.end((err, code, signal) => {
      if (err) {
        extractSpinner.fail(chalk.red(`Error extracting metadata: ${err.message}`));
        process.exit(1);
      }
      
      extractSpinner.succeed(chalk.green('Metadata extraction complete!'));
      
      // Then upload embeddings
      console.log(chalk.blue('\n📤 Step 2: Uploading embeddings to OpenAI...'));
      
      const uploadSpinner = ora('Processing embeddings...').start();
      
      // Make sure the config file exists
      if (!fs.existsSync(options.config)) {
        uploadSpinner.fail(chalk.red(`Config file not found: ${options.config}`));
        process.exit(1);
      }
      
      // Build the arguments
      const args = ['--config', options.config];
      if (options.force) args.push('--force');
      
      // Run the upload script
      const uploadPyshell = new PythonShell(path.join(SCRIPT_DIR, 'upload_embeddings.py'), {
        args: args,
        mode: 'text'
      });
      
      uploadPyshell.on('message', (message) => {
        uploadSpinner.text = message;
      });
      
      uploadPyshell.end((err, code, signal) => {
        if (err) {
          uploadSpinner.fail(chalk.red(`Error uploading embeddings: ${err.message}`));
          process.exit(1);
        }
        
        uploadSpinner.succeed(chalk.green('Embeddings upload complete!'));
        console.log(chalk.green('\n✅ Onboarding Assistant workflow completed successfully!'));
      });
    });
  });

// Parse command line arguments
program.parse();

// If no command is provided, show help
if (!process.argv.slice(2).length) {
  program.outputHelp();
}
