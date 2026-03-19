const { spawnSync } = require('child_process');

const npmCommand = process.platform === 'win32' ? 'npm.cmd' : 'npm';

const commands = [
  [npmCommand, ['run', 'smoke:generate']],
  [npmCommand, ['run', 'smoke:source']],
  [npmCommand, ['run', 'smoke:revise']],
  [npmCommand, ['run', 'smoke:skill']]
];

for (const [command, args] of commands) {
  const result = spawnSync(command, args, {
    stdio: 'inherit',
    shell: false
  });

  if (typeof result.status === 'number' && result.status !== 0) {
    process.exit(result.status);
  }

  if (result.error) {
    console.error(result.error.message);
    process.exit(1);
  }
}