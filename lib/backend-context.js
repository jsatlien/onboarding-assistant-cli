/**
 * Backend Context Generator
 * Extracts Entity Framework model files and generates context for embeddings
 */

const fs = require('fs');
const path = require('path');
const chalk = require('chalk');

/**
 * Find all C# files recursively in a directory
 * @param {string} dir - Directory to search
 * @param {Array} fileList - Accumulator for found files
 * @returns {Array} - List of C# file paths
 */
function findCSharpFiles(dir, fileList = []) {
  const files = fs.readdirSync(dir);
  
  files.forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    
    if (stat.isDirectory()) {
      findCSharpFiles(filePath, fileList);
    } else if (file.endsWith('.cs')) {
      fileList.push(filePath);
    }
  });
  
  return fileList;
}

/**
 * Check if a C# file is likely an Entity Framework model
 * @param {string} filePath - Path to the C# file
 * @returns {boolean} - True if the file is likely an EF model
 */
function isLikelyEFModel(filePath) {
  // Read file content
  const content = fs.readFileSync(filePath, 'utf-8');
  
  // Check for common EF model patterns
  const isModel = (
    // Check for EF data annotations
    content.includes('[Key]') ||
    content.includes('[Required]') ||
    content.includes('[ForeignKey') ||
    content.includes('[Table') ||
    content.includes('[Column') ||
    
    // Check for navigation properties
    (content.includes('public virtual') && 
     (content.includes('ICollection<') || content.includes('List<'))) ||
    
    // Check for common ID property pattern
    content.includes('public int Id { get; set; }') ||
    content.includes('public Guid Id { get; set; }') ||
    
    // Check for DbSet references
    content.includes('DbSet<') && content.includes('Context')
  );
  
  // Check if file is in a models-related directory
  const isInModelsDir = (
    filePath.includes('Models') || 
    filePath.includes('Entities') || 
    filePath.includes('Domain')
  );
  
  // Return true if either condition is met
  return isModel || isInModelsDir;
}

/**
 * Extract model name from a C# file
 * @param {string} filePath - Path to the C# file
 * @returns {string} - Model name
 */
function extractModelName(filePath) {
  // Default to filename without extension
  let modelName = path.basename(filePath, '.cs');
  
  try {
    // Read file content
    const content = fs.readFileSync(filePath, 'utf-8');
    
    // Try to extract class name
    const classMatch = content.match(/public\s+class\s+(\w+)/);
    if (classMatch && classMatch[1]) {
      modelName = classMatch[1];
    }
  } catch (error) {
    console.log(chalk.yellow(`Warning: Could not extract model name from ${filePath}: ${error.message}`));
  }
  
  return modelName;
}

/**
 * Generate output filename for a C# model file
 * @param {string} filePath - Path to the C# file
 * @param {string} modelName - Name of the model
 * @returns {string} - Output filename
 */
function generateOutputFilename(filePath, modelName) {
  // Use model name in kebab case
  const kebabName = modelName
    .replace(/([a-z])([A-Z])/g, '$1-$2') // Convert camelCase to kebab-case
    .toLowerCase();
  
  return `${kebabName}.cs.txt`;
}

/**
 * Generate context for Entity Framework model files
 * @param {string} modelsPath - Path to the models directory
 * @param {string} outputPath - Output directory for context files
 * @returns {Promise<number>} - Number of files processed
 */
async function generateEFModelContext(modelsPath, outputPath) {
  // Ensure models path exists
  if (!fs.existsSync(modelsPath)) {
    throw new Error(`Models path does not exist: ${modelsPath}`);
  }
  
  // Create output directory if it doesn't exist
  const modelsOutputPath = path.join(outputPath, 'models');
  if (!fs.existsSync(modelsOutputPath)) {
    fs.mkdirSync(modelsOutputPath, { recursive: true });
  }
  
  // Find all C# files
  const csharpFiles = findCSharpFiles(modelsPath);
  
  // Filter for likely EF models
  const modelFiles = csharpFiles.filter(file => isLikelyEFModel(file));
  
  // Process each model file
  for (const modelFile of modelFiles) {
    // Extract model name
    const modelName = extractModelName(modelFile);
    
    // Generate output filename
    const outputFilename = generateOutputFilename(modelFile, modelName);
    
    // Create output file path
    const outputFilePath = path.join(modelsOutputPath, outputFilename);
    
    // Read model file content
    const modelContent = fs.readFileSync(modelFile, 'utf-8');
    
    // Create header comment
    const relativeFilePath = path.relative(modelsPath, modelFile).replace(/\\/g, '/');
    const header = `// FILE: ${relativeFilePath}\n// MODEL: ${modelName} (Entity Framework)\n\n`;
    
    // Write output file
    fs.writeFileSync(outputFilePath, header + modelContent);
  }
  
  return modelFiles.length;
}

module.exports = {
  generateEFModelContext
};
