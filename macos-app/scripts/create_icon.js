const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Create a simple icon for the app
function createAppIcon() {
  const svgContent = `
<svg width="1024" height="1024" xmlns="http://www.w3.org/2000/svg">
  <rect width="1024" height="1024" fill="#1d1d1f"/>
  <circle cx="512" cy="512" r="400" fill="#0071e3"/>
  <path d="M512 312 L712 512 L512 712 L312 512 Z" fill="white"/>
  <circle cx="512" cy="512" r="100" fill="#1d1d1f"/>
</svg>
  `;

  // Make sure the build directory exists
  const buildDir = path.join(__dirname, '..', 'build');
  if (!fs.existsSync(buildDir)) {
    fs.mkdirSync(buildDir, { recursive: true });
  }

  // Save SVG file
  const svgPath = path.join(buildDir, 'icon.svg');
  fs.writeFileSync(svgPath, svgContent);

  console.log('SVG icon created at', svgPath);

  // Create a placeholder icns file
  const icnsPath = path.join(buildDir, 'icon.icns');
  fs.copyFileSync(svgPath, icnsPath);
  console.log('Created placeholder icns file at', icnsPath);
}

// Main function
function main() {
  console.log('Creating app icon...');
  createAppIcon();
  console.log('Done!');
}

main();
