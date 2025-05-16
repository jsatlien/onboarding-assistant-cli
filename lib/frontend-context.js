/**
 * Frontend Context Generator
 * Extracts Vue files and generates context for embeddings
 */

const fs = require('fs');
const path = require('path');
const chalk = require('chalk');

/**
 * Find all Vue files recursively in a directory
 * @param {string} dir - Directory to search
 * @param {Array} fileList - Accumulator for found files
 * @returns {Array} - List of Vue file paths
 */
function findVueFiles(dir, fileList = []) {
  const files = fs.readdirSync(dir);
  
  files.forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    
    if (stat.isDirectory()) {
      findVueFiles(filePath, fileList);
    } else if (file.endsWith('.vue')) {
      fileList.push(filePath);
    }
  });
  
  return fileList;
}

/**
 * Try to extract route from router configuration
 * @param {string} sourcePath - Root path of the Vue project
 * @param {string} vueFilePath - Path to the Vue file
 * @returns {string|null} - Extracted route or null if not found
 */
function extractRouteFromRouter(sourcePath, vueFilePath) {
  // Common router file locations
  const routerFiles = [
    path.join(sourcePath, 'router', 'index.js'),
    path.join(sourcePath, 'src', 'router', 'index.js'),
    path.join(sourcePath, 'router.js'),
    path.join(sourcePath, 'src', 'router.js'),
    path.join(sourcePath, 'routes.js'),
    path.join(sourcePath, 'src', 'routes.js')
  ];
  
  // Find the first existing router file
  const routerFile = routerFiles.find(file => fs.existsSync(file));
  if (!routerFile) return null;
  
  try {
    // Read router file content
    const routerContent = fs.readFileSync(routerFile, 'utf-8');
    
    // Get the component name from the file path
    const componentName = path.basename(vueFilePath, '.vue');
    
    // Look for import statements or route definitions that match this component
    const relativeFilePath = path.relative(path.dirname(routerFile), vueFilePath)
      .replace(/\\/g, '/') // Normalize path separators
      .replace(/\.vue$/, ''); // Remove .vue extension
    
    // Simple regex to find route definitions
    const routeRegex = new RegExp(
      `path:\\s*['"]([^'"]+)['"][^}]*component:[^}]*(?:${componentName}|${relativeFilePath})`,
      'i'
    );
    
    const match = routerContent.match(routeRegex);
    if (match && match[1]) {
      return match[1];
    }
    
    // More comprehensive search for lazy-loaded components
    const lazyLoadRegex = new RegExp(
      `path:\\s*['"]([^'"]+)['"][^}]*component:[^}]*import\\(['"]\\.\\.?/[^'"]*${componentName}`,
      'i'
    );
    
    const lazyMatch = routerContent.match(lazyLoadRegex);
    if (lazyMatch && lazyMatch[1]) {
      return lazyMatch[1];
    }
  } catch (error) {
    console.log(chalk.yellow(`Warning: Could not parse router file: ${error.message}`));
  }
  
  return null;
}

/**
 * Infer route from file path
 * @param {string} sourcePath - Root path of the Vue project
 * @param {string} vueFilePath - Path to the Vue file
 * @returns {string} - Inferred route
 */
function inferRouteFromPath(sourcePath, vueFilePath) {
  // Remove source path prefix and file extension
  let relativePath = path.relative(sourcePath, vueFilePath)
    .replace(/\.vue$/, '')
    .replace(/\\/g, '/'); // Normalize path separators
  
  // Handle common folder structures
  const pagesPattern = /(?:pages|views|screens)\/(.*)/i;
  const pagesMatch = relativePath.match(pagesPattern);
  
  if (pagesMatch) {
    relativePath = pagesMatch[1];
  }
  
  // Convert to kebab-case route
  let route = '/' + relativePath
    .toLowerCase()
    .replace(/\/index$/, '') // Remove index
    .replace(/\[([^\]]+)\]/g, ':$1') // Convert [param] to :param
    .replace(/\/home$/, ''); // Convert /home to /
  
  // Clean up the route
  route = route
    .replace(/\/+/g, '/') // Remove duplicate slashes
    .replace(/^\/$/, ''); // If empty, use root
  
  return route || '/';
}

/**
 * Get route for a Vue file
 * @param {string} sourcePath - Root path of the Vue project
 * @param {string} vueFilePath - Path to the Vue file
 * @returns {string} - Route for the Vue file
 */
function getRouteForVueFile(sourcePath, vueFilePath) {
  // Try to extract from router first
  const routerRoute = extractRouteFromRouter(sourcePath, vueFilePath);
  if (routerRoute) return routerRoute;
  
  // Fall back to path inference
  return inferRouteFromPath(sourcePath, vueFilePath);
}

/**
 * Generate output filename for a Vue file
 * @param {string} vueFilePath - Path to the Vue file
 * @param {string} route - Route for the Vue file
 * @returns {string} - Output filename
 */
function generateOutputFilename(vueFilePath, route) {
  // Get the original filename with extension
  const originalFilename = path.basename(vueFilePath);
  
  // Convert route to kebab-case filename
  const routeFilename = route
    .replace(/^\//, '') // Remove leading slash
    .replace(/\//g, '-') // Replace slashes with hyphens
    .replace(/:/g, '') // Remove route parameters
    .toLowerCase();
  
  // Use route-based name if available, otherwise use original name
  const baseName = routeFilename || path.basename(vueFilePath, '.vue').toLowerCase();
  
  return `${baseName}.vue.txt`;
}

/**
 * Generate context for Vue files
 * @param {string} sourcePath - Root path of the Vue project
 * @param {string} outputPath - Output directory for context files
 * @returns {Promise<number>} - Number of files processed
 */
async function generateVueContext(sourcePath, outputPath) {
  // Ensure source path exists
  if (!fs.existsSync(sourcePath)) {
    throw new Error(`Source path does not exist: ${sourcePath}`);
  }
  
  // Create output directory if it doesn't exist
  const routesOutputPath = path.join(outputPath, 'routes');
  if (!fs.existsSync(routesOutputPath)) {
    fs.mkdirSync(routesOutputPath, { recursive: true });
  }
  
  // Find all Vue files
  const vueFiles = findVueFiles(sourcePath);
  
  // Process each Vue file
  for (const vueFile of vueFiles) {
    // Get route for the file
    const route = getRouteForVueFile(sourcePath, vueFile);
    
    // Generate output filename
    const outputFilename = generateOutputFilename(vueFile, route);
    
    // Create output file path
    const outputFilePath = path.join(routesOutputPath, outputFilename);
    
    // Read Vue file content
    const vueContent = fs.readFileSync(vueFile, 'utf-8');
    
    // Create header comment
    const relativeFilePath = path.relative(sourcePath, vueFile).replace(/\\/g, '/');
    const header = `// FILE: ${relativeFilePath}\n// ROUTE: ${route}\n\n`;
    
    // Write output file
    fs.writeFileSync(outputFilePath, header + vueContent);
  }
  
  return vueFiles.length;
}

module.exports = {
  generateVueContext
};
