const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('\n==================================================');
console.log('👁️  Agent-Eye: Setting up isolated Python environment...');
console.log('==================================================\n');

// 1. Check if python3 or python is available
let pythonCmd = 'python3';
try {
    execSync('python3 --version', { stdio: 'ignore' });
} catch (e) {
    try {
        execSync('python --version', { stdio: 'ignore' });
        pythonCmd = 'python';
    } catch (err) {
        console.error('❌ Error: Python 3 is required to run Agent-Eye.');
        console.error('Please install Python 3.8+ on your system and try again.');
        process.exit(1);
    }
}

const venvPath = path.join(__dirname, '..', '.venv');
const requirementsPath = path.join(__dirname, '..', 'requirements.txt');

// 2. Create Python virtual environment if it doesn't exist
if (!fs.existsSync(venvPath)) {
    console.log(`Creating virtual environment in: ${venvPath}...`);
    try {
        execSync(`${pythonCmd} -m venv "${venvPath}"`, { stdio: 'inherit' });
    } catch (err) {
        console.error('❌ Failed to create Python virtual environment.');
        console.error('Ensure that you have "python3-venv" or "virtualenv" installed.');
        process.exit(1);
    }
}

// 3. Install requirements inside the virtual environment
console.log('\nInstalling Python dependencies in virtual environment...');
const pipPath = process.platform === 'win32' 
    ? path.join(venvPath, 'Scripts', 'pip.exe')
    : path.join(venvPath, 'bin', 'pip');

try {
    execSync(`"${pipPath}" install -r "${requirementsPath}"`, { stdio: 'inherit' });
} catch (err) {
    console.error('❌ Failed to install Python dependencies in the virtual environment.');
    console.error(err);
    process.exit(1);
}

console.log('\n==================================================');
console.log('✓ 👁️  Agent-Eye Python environment successfully set up!');
console.log('==================================================\n');
