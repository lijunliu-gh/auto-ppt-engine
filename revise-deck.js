const { createCompatibilityMessage, runPythonScript } = require('./scripts/python-bridge');

console.log(createCompatibilityMessage('py-revise-deck.py'));
runPythonScript('py-revise-deck.py', process.argv.slice(2));
