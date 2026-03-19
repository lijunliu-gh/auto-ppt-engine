const path = require('path');
const { spawn, spawnSync } = require('child_process');

const rootDir = path.resolve(__dirname, '..');
const defaultPythonCommand = process.env.PYTHON || 'python';

function resolvePythonScript(scriptName) {
  return path.join(rootDir, scriptName);
}

function createCompatibilityMessage(target) {
  return `Compatibility wrapper: forwarding to Python smart layer (${target}).`;
}

function runPythonScript(scriptName, args, options = {}) {
  const scriptPath = resolvePythonScript(scriptName);
  const result = spawnSync(defaultPythonCommand, [scriptPath].concat(args || []), {
    cwd: rootDir,
    stdio: 'inherit',
    shell: false,
    ...options
  });

  if (result.error) {
    throw result.error;
  }

  if (typeof result.status === 'number') {
    process.exit(result.status);
  }

  process.exit(0);
}

function runPythonServer(scriptName, args, options = {}) {
  const scriptPath = resolvePythonScript(scriptName);
  const child = spawn(defaultPythonCommand, [scriptPath].concat(args || []), {
    cwd: rootDir,
    stdio: 'inherit',
    shell: false,
    ...options
  });

  child.on('error', (error) => {
    console.error(error.message);
    process.exit(1);
  });

  child.on('exit', (code) => {
    process.exit(typeof code === 'number' ? code : 0);
  });
}

module.exports = {
  createCompatibilityMessage,
  runPythonScript,
  runPythonServer
};