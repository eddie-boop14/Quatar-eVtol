// Turns a Lighthouse JSON run into a GitHub job summary, and raises an alarm
// only if a category falls through FLOOR. Reaching TARGET is the goal; missing
// it by a point is reported, not enforced. See .github/workflows/lighthouse.yml
// for why scores are not a deploy gate.
import { readFileSync, appendFileSync } from 'node:fs';

const report = JSON.parse(readFileSync('./lh.json', 'utf8'));
const floor = Number(process.env.FLOOR ?? 90);
const target = Number(process.env.TARGET ?? 100);
const url = process.env.SITE_URL ?? report.finalDisplayedUrl ?? '(unknown)';

const categories = Object.values(report.categories).map((c) => ({
  name: c.title,
  score: c.score === null ? null : Math.round(c.score * 100),
}));

const metrics = [
  'first-contentful-paint',
  'largest-contentful-paint',
  'total-blocking-time',
  'cumulative-layout-shift',
  'speed-index',
];

let out = `## ${url}\n\n| Category | Score | vs ${target} |\n|---|---|---|\n`;
for (const c of categories) {
  const delta = c.score === null ? 'n/a' : c.score === target ? 'at target' : c.score - target;
  out += `| ${c.name} | ${c.score ?? 'n/a'} | ${delta} |\n`;
}
out += '\n| Metric | Value |\n|---|---|\n';
for (const key of metrics) {
  const audit = report.audits[key];
  out += `| ${key} | ${audit?.displayValue ?? 'n/a'} |\n`;
}

const summaryPath = process.env.GITHUB_STEP_SUMMARY;
if (summaryPath) appendFileSync(summaryPath, out);
console.log(out);

const below = categories.filter((c) => c.score !== null && c.score < floor);
if (below.length) {
  console.error(
    `ALARM: below floor ${floor} -> ` + below.map((c) => `${c.name} ${c.score}`).join(', ')
  );
  process.exit(1);
}
const short = categories.filter((c) => c.score !== null && c.score < target);
if (short.length) {
  console.log(
    `Above floor, short of ${target}: ` + short.map((c) => `${c.name} ${c.score}`).join(', ')
  );
}
