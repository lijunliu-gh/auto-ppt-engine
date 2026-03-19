const { createCompatibilityMessage, runPythonScript } = require('./scripts/python-bridge');

console.log(createCompatibilityMessage('py-generate-from-prompt.py'));
runPythonScript('py-generate-from-prompt.py', process.argv.slice(2));
