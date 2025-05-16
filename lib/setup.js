const fs = require('fs');
const path = require('path');
const chalk = require('chalk');

console.log(chalk.blue('Setting up Onboarding Assistant CLI...'));

// Create output directories if they don't exist
const outputDir = path.join(process.cwd(), 'output');
const routesDir = path.join(outputDir, 'routes');
const modelsDir = path.join(outputDir, 'models');

if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
  console.log(chalk.green('✓ Created output directory'));
}

if (!fs.existsSync(routesDir)) {
  fs.mkdirSync(routesDir, { recursive: true });
  console.log(chalk.green('✓ Created routes directory'));
}

if (!fs.existsSync(modelsDir)) {
  fs.mkdirSync(modelsDir, { recursive: true });
  console.log(chalk.green('✓ Created models directory'));
}

console.log(chalk.green('✓ Setup complete!'));
console.log(chalk.blue('Run "onboarding-assistant --help" to see available commands.'));

// Display usage examples
console.log(chalk.blue('You can now use the Onboarding Assistant CLI:'));
console.log(chalk.blue('  npx onboarding-assistant generate-frontend-context'));
console.log(chalk.blue('  npx onboarding-assistant generate-backend-context'));
