const fs = require('fs');
const content = fs.readFileSync('c:\\aegisflow\\frontend\\index.html', 'utf8');
const scriptMatch = content.match(/<script>([\s\S]*?)<\/script>/);
if (scriptMatch) {
  const scriptContent = scriptMatch[1];
  try {
    new Function(scriptContent);
    console.log("No syntax errors!");
  } catch (e) {
    console.error("Syntax Error:", e);
    // Find line number
    const lines = scriptContent.split('\n');
    for (let i = 1; i <= lines.length; i++) {
      try {
        new Function(lines.slice(0, i).join('\n'));
      } catch (err) {
        if (err.message !== "Unexpected end of input") {
          console.error(`Error around line ${i + 697}:`, lines[i-1]);
          break;
        }
      }
    }
  }
} else {
  console.log("No script tag found");
}
