const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const chalk = require('chalk');

// Create Python scripts directory if it doesn't exist
const pythonDir = path.join(__dirname, 'python');
if (!fs.existsSync(pythonDir)) {
  fs.mkdirSync(pythonDir, { recursive: true });
}

// Check if Python is installed - with more robust Windows path handling
let pythonCommand = null;

// List of possible Python executable paths on Windows
const possiblePythonPaths = [
  'python',
  'python3',
  'py',
  'C:\\Users\\Jsatl\\AppData\\Local\\Programs\\Python\\Python310\\python.exe',
  'C:\\Users\\Jsatl\\AppData\\Local\\Programs\\Python\\Python311\\python.exe',
  'C:\\Users\\Jsatl\\AppData\\Local\\Programs\\Python\\Python312\\python.exe',
  'C:\\Users\\Jsatl\\AppData\\Local\\Programs\\Python\\Python313\\python.exe',
  'C:\\Program Files\\Python310\\python.exe',
  'C:\\Program Files\\Python311\\python.exe',
  'C:\\Program Files\\Python312\\python.exe',
  'C:\\Program Files\\Python313\\python.exe'
];

console.log(chalk.blue('Checking Python installation...'));

// Try each possible Python path
for (const pythonPath of possiblePythonPaths) {
  try {
    const pythonVersion = execSync(`"${pythonPath}" --version`, { encoding: 'utf8' });
    console.log(chalk.green(`✓ ${pythonVersion.trim()} found at ${pythonPath}`));
    pythonCommand = pythonPath;
    break;
  } catch (error) {
    // Continue to the next path
  }
}

// If no Python installation found
if (!pythonCommand) {
  console.error(chalk.red('❌ Python is not installed or not in PATH'));
  console.error(chalk.yellow('Please install Python 3.6+ from https://www.python.org/downloads/'));
  console.error(chalk.yellow('Make sure to check "Add Python to PATH" during installation'));
  process.exit(1);
}

// Install required Python packages
try {
  console.log(chalk.blue('Installing required Python packages...'));
  
  // Use the detected Python command
  execSync(`"${pythonCommand}" -m pip install --upgrade pip`, { stdio: 'inherit' });
  execSync(`"${pythonCommand}" -m pip install openai pyyaml tqdm`, { stdio: 'inherit' });
  
  console.log(chalk.green('✓ Python packages installed successfully'));
} catch (error) {
  console.error(chalk.red('❌ Failed to install Python packages'));
  console.error(chalk.red(error.message));
  console.error(chalk.yellow('You may need to run pip manually:'));
  console.error(chalk.yellow(`"${pythonCommand}" -m pip install openai pyyaml tqdm`));
  process.exit(1);
}

// Check if Python scripts exist in the python directory
const pythonUtilsDir = path.join(pythonDir, 'utils');

// Make sure the utils directory exists
if (!fs.existsSync(pythonUtilsDir)) {
  fs.mkdirSync(pythonUtilsDir, { recursive: true });
}

// Check if the required Python scripts exist
const metadataGeneratorPath = path.join(pythonDir, 'metadata_generator.py');
const uploadEmbeddingsPath = path.join(pythonDir, 'upload_embeddings.py');
const formatForEmbeddingPath = path.join(pythonUtilsDir, 'format_for_embedding.py');

// Log the status of Python scripts
console.log(chalk.blue('Checking Python scripts...'));

if (fs.existsSync(metadataGeneratorPath)) {
  console.log(chalk.green(`✓ Found metadata_generator.py at ${metadataGeneratorPath}`));
} else {
  console.log(chalk.yellow(`⚠ metadata_generator.py not found at ${metadataGeneratorPath}`));
}

if (fs.existsSync(uploadEmbeddingsPath)) {
  console.log(chalk.green(`✓ Found upload_embeddings.py at ${uploadEmbeddingsPath}`));
} else {
  console.log(chalk.yellow(`⚠ upload_embeddings.py not found at ${uploadEmbeddingsPath}`));
}

if (fs.existsSync(formatForEmbeddingPath)) {
  console.log(chalk.green(`✓ Found format_for_embedding.py at ${formatForEmbeddingPath}`));
} else {
  console.log(chalk.yellow(`⚠ format_for_embedding.py not found at ${formatForEmbeddingPath}`));
}

console.log(chalk.green('✅ Setup completed successfully!'));
console.log(chalk.blue('You can now use the Onboarding Assistant CLI:'));
console.log(chalk.blue('  npx onboarding-assistant init'));
console.log(chalk.blue('  npx onboarding-assistant extract <source-dir>'));
console.log(chalk.blue('  npx onboarding-assistant upload'));
