#!/usr/bin/env node
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const venvPath = path.join(__dirname, '..', '.venv');
const pythonBin = process.platform === 'win32'
    ? path.join(venvPath, 'Scripts', 'python.exe')
    : path.join(venvPath, 'bin', 'python');

const runScript = path.join(__dirname, '..', 'run.py');

if (!fs.existsSync(pythonBin)) {
    console.error('❌ Error: Agent-Eye Python environment is not set up.');
    console.error('Please run "npm install" or "node bin/install.js" in the package folder to set up the environment.');
    process.exit(1);
}

// Forward all CLI arguments to the run.py Python script
const args = [runScript, ...process.argv.slice(2)];

const child = spawn(pythonBin, args, { stdio: 'inherit' });

child.on('close', (code) => {
    process.exit(code);
});

child.on('error', (err) => {
    console.error('❌ Failed to launch Agent-Eye engine:', err);
    process.exit(1);
});
