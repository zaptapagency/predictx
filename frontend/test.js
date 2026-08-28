/**
 * Frontend smoke tests.
 *
 * These are deliberately narrow: the frontend is static HTML, so rather than
 * pull in a test framework these assert the invariants that have actually
 * broken in production before — a hardcoded signup password, and absolute
 * /predictx/ paths that 404 when served from the custom domain root.
 */

const fs = require('fs');
const path = require('path');

const PUBLIC_DIR = path.join(__dirname, 'public');
const API_HOST = 'predictx-production-6eb5.up.railway.app';

let failures = 0;

function check(name, condition, detail) {
  if (condition) {
    console.log(`  ok   ${name}`);
  } else {
    console.error(`  FAIL ${name}${detail ? ` — ${detail}` : ''}`);
    failures++;
  }
}

console.log('frontend smoke tests');

// Both pages must exist and be non-trivial.
const pages = ['index.html', 'dashboard.html'];
const sources = {};
for (const page of pages) {
  const file = path.join(PUBLIC_DIR, page);
  const exists = fs.existsSync(file);
  check(`${page} exists`, exists);
  if (!exists) continue;
  sources[page] = fs.readFileSync(file, 'utf8');
  check(`${page} is non-empty`, sources[page].length > 500);
}

for (const [page, src] of Object.entries(sources)) {
  // Regression: signup once assigned every account the same hardcoded password.
  check(
    `${page} has no hardcoded password`,
    !/password:\s*['"][^'"]{6,}['"]/.test(src),
    'a string literal is being passed as a password'
  );

  // Regression: absolute /predictx/ paths 404 when served from a domain root.
  check(
    `${page} uses no absolute /predictx/ paths`,
    !src.includes('/predictx/'),
    'use relative paths so the site works on both github.io and the custom domain'
  );

  // Every page that talks to the API must point at the live backend.
  if (src.includes('API_URL') || src.includes('const API')) {
    check(`${page} targets the production API`, src.includes(API_HOST));
  }
}

// Signup must collect a password from the user.
if (sources['index.html']) {
  check(
    'index.html has a password input',
    /<input[^>]*type=["']password["']/.test(sources['index.html'])
  );
}

if (failures > 0) {
  console.error(`\n${failures} check(s) failed`);
  process.exit(1);
}
console.log('\nall checks passed');
