const { createCompatibilityMessage, runPythonServer } = require('./scripts/python-bridge');

console.log(createCompatibilityMessage('py-skill-server.py'));
runPythonServer('py-skill-server.py', process.argv.slice(2), {
  env: {
    ...process.env,
    PORT: process.env.PORT || '3010'
  }
});
