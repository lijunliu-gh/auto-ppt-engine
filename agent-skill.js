const { createCompatibilityMessage, runPythonScript } = require('./scripts/python-bridge');

console.log(createCompatibilityMessage('py-agent-skill.py'));
runPythonScript('py-agent-skill.py', process.argv.slice(2));
