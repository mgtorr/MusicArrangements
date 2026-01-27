#!/usr/bin/env node

/**
 * MuseScore 4 Plugin Installer
 *
 * Automatically detects the MuseScore 4 plugin directory on Windows, macOS, and Linux,
 * and copies the LLMBridge.qml plugin file there.
 *
 * Usage:
 *   node scripts/install-plugin.js
 *   npm run install-plugin
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

// Plugin source file
const PLUGIN_NAME = 'LLMBridge.qml';
const SCRIPT_DIR = __dirname;
const PROJECT_ROOT = path.dirname(SCRIPT_DIR);
const PLUGIN_SOURCE = path.join(PROJECT_ROOT, 'plugin', PLUGIN_NAME);

// Colors for terminal output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  cyan: '\x1b[36m',
};

function log(message, color = colors.reset) {
  console.log(`${color}${message}${colors.reset}`);
}

function logSuccess(message) {
  log(`✓ ${message}`, colors.green);
}

function logWarning(message) {
  log(`⚠ ${message}`, colors.yellow);
}

function logError(message) {
  log(`✗ ${message}`, colors.red);
}

function logInfo(message) {
  log(`ℹ ${message}`, colors.cyan);
}

/**
 * Get potential MuseScore 4 plugin directories based on the platform
 */
function getPluginDirectories() {
  const platform = os.platform();
  const homeDir = os.homedir();
  const directories = [];

  switch (platform) {
    case 'win32':
      // Windows paths
      directories.push(
        path.join(homeDir, 'Documents', 'MuseScore4', 'Plugins'),
        path.join(homeDir, 'Documents', 'MuseScore 4', 'Plugins'),
        // OneDrive Documents folder
        path.join(homeDir, 'OneDrive', 'Documents', 'MuseScore4', 'Plugins'),
        path.join(homeDir, 'OneDrive', 'Documents', 'MuseScore 4', 'Plugins'),
        // Alternative locations
        path.join(process.env.APPDATA || '', 'MuseScore', 'MuseScore4', 'Plugins'),
      );
      break;

    case 'darwin':
      // macOS paths
      directories.push(
        path.join(homeDir, 'Documents', 'MuseScore4', 'Plugins'),
        path.join(homeDir, 'Documents', 'MuseScore 4', 'Plugins'),
        // iCloud Documents
        path.join(homeDir, 'Library', 'Mobile Documents', 'com~apple~CloudDocs', 'Documents', 'MuseScore4', 'Plugins'),
        // Application Support
        path.join(homeDir, 'Library', 'Application Support', 'MuseScore', 'MuseScore4', 'Plugins'),
      );
      break;

    case 'linux':
      // Linux paths
      directories.push(
        path.join(homeDir, 'Documents', 'MuseScore4', 'Plugins'),
        path.join(homeDir, 'Documents', 'MuseScore 4', 'Plugins'),
        path.join(homeDir, '.local', 'share', 'MuseScore', 'MuseScore4', 'Plugins'),
        // Flatpak
        path.join(homeDir, '.var', 'app', 'org.musescore.MuseScore', 'Documents', 'MuseScore4', 'Plugins'),
        // Snap
        path.join(homeDir, 'snap', 'musescore', 'current', 'Documents', 'MuseScore4', 'Plugins'),
      );
      break;

    default:
      logWarning(`Unknown platform: ${platform}`);
  }

  return directories;
}

/**
 * Find the first existing plugin directory or create one
 */
function findOrCreatePluginDirectory() {
  const directories = getPluginDirectories();

  // First, try to find an existing directory
  for (const dir of directories) {
    if (fs.existsSync(dir)) {
      return { path: dir, created: false };
    }
  }

  // If no directory exists, try to create the first one
  // Check if the parent (Documents/MuseScore4) exists or can be created
  for (const dir of directories) {
    const parentDir = path.dirname(dir);
    const grandParentDir = path.dirname(parentDir);

    // Check if grandparent exists (e.g., Documents)
    if (fs.existsSync(grandParentDir)) {
      try {
        fs.mkdirSync(dir, { recursive: true });
        return { path: dir, created: true };
      } catch (err) {
        // Continue to next option
      }
    }
  }

  return null;
}

/**
 * Copy the plugin file to the destination
 */
function copyPlugin(destDir) {
  const destPath = path.join(destDir, PLUGIN_NAME);

  // Check if source exists
  if (!fs.existsSync(PLUGIN_SOURCE)) {
    throw new Error(`Plugin source file not found: ${PLUGIN_SOURCE}`);
  }

  // Check if destination already exists
  const exists = fs.existsSync(destPath);

  // Copy the file
  fs.copyFileSync(PLUGIN_SOURCE, destPath);

  return { destPath, updated: exists };
}

/**
 * Main installation function
 */
function main() {
  console.log('');
  log('╔════════════════════════════════════════════════╗', colors.cyan);
  log('║     MuseScore 4 Plugin Installer               ║', colors.cyan);
  log('║     LLM Bridge - AI Music Assistant            ║', colors.cyan);
  log('╚════════════════════════════════════════════════╝', colors.cyan);
  console.log('');

  // Check platform
  const platform = os.platform();
  const platformNames = {
    'win32': 'Windows',
    'darwin': 'macOS',
    'linux': 'Linux',
  };
  logInfo(`Detected platform: ${platformNames[platform] || platform}`);

  // Check source file
  if (!fs.existsSync(PLUGIN_SOURCE)) {
    logError(`Plugin source file not found!`);
    logError(`Expected at: ${PLUGIN_SOURCE}`);
    process.exit(1);
  }
  logSuccess(`Found plugin source: ${PLUGIN_SOURCE}`);

  // Find or create plugin directory
  logInfo('Searching for MuseScore 4 plugin directory...');
  const result = findOrCreatePluginDirectory();

  if (!result) {
    logError('Could not find or create MuseScore 4 plugin directory!');
    console.log('');
    logInfo('Please manually copy the plugin to one of these locations:');
    getPluginDirectories().forEach(dir => {
      console.log(`  - ${dir}`);
    });
    console.log('');
    logInfo('Or create the directory and run this script again.');
    process.exit(1);
  }

  if (result.created) {
    logSuccess(`Created plugin directory: ${result.path}`);
  } else {
    logSuccess(`Found plugin directory: ${result.path}`);
  }

  // Copy the plugin
  try {
    const copyResult = copyPlugin(result.path);
    if (copyResult.updated) {
      logSuccess(`Updated plugin: ${copyResult.destPath}`);
    } else {
      logSuccess(`Installed plugin: ${copyResult.destPath}`);
    }
  } catch (err) {
    logError(`Failed to copy plugin: ${err.message}`);
    process.exit(1);
  }

  // Success message
  console.log('');
  log('════════════════════════════════════════════════', colors.green);
  logSuccess('Plugin installed successfully!');
  log('════════════════════════════════════════════════', colors.green);
  console.log('');
  logInfo('Next steps:');
  console.log('  1. Open MuseScore 4');
  console.log('  2. Go to Plugins → Plugin Manager');
  console.log('  3. Enable "LLM Bridge"');
  console.log('  4. Restart MuseScore 4');
  console.log('  5. Access via Plugins → LLM Bridge');
  console.log('');
}

// Handle command line arguments
const args = process.argv.slice(2);

if (args.includes('--help') || args.includes('-h')) {
  console.log(`
MuseScore 4 Plugin Installer

Usage:
  node scripts/install-plugin.js [options]

Options:
  --help, -h     Show this help message
  --list, -l     List potential plugin directories
  --check, -c    Check if plugin is installed

Description:
  This script automatically detects your MuseScore 4 plugin directory
  and copies the LLMBridge.qml plugin file there.

Supported platforms:
  - Windows
  - macOS
  - Linux (including Flatpak and Snap)
`);
  process.exit(0);
}

if (args.includes('--list') || args.includes('-l')) {
  console.log('\nPotential MuseScore 4 plugin directories:\n');
  const directories = getPluginDirectories();
  directories.forEach(dir => {
    const exists = fs.existsSync(dir);
    const status = exists ? colors.green + '✓ exists' : colors.yellow + '✗ not found';
    console.log(`  ${status}${colors.reset}  ${dir}`);
  });
  console.log('');
  process.exit(0);
}

if (args.includes('--check') || args.includes('-c')) {
  console.log('\nChecking plugin installation status...\n');
  const directories = getPluginDirectories();
  let found = false;

  for (const dir of directories) {
    const pluginPath = path.join(dir, PLUGIN_NAME);
    if (fs.existsSync(pluginPath)) {
      logSuccess(`Plugin found at: ${pluginPath}`);

      // Check file modification time
      const stats = fs.statSync(pluginPath);
      console.log(`  Last modified: ${stats.mtime.toLocaleString()}`);
      found = true;
    }
  }

  if (!found) {
    logWarning('Plugin not found in any known location');
  }
  console.log('');
  process.exit(found ? 0 : 1);
}

// Run main installation
main();
