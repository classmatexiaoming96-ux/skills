#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';

const [inputArg, outputArg] = process.argv.slice(2);

if (!inputArg || !outputArg) {
  console.error('usage: extract-archify-svg.mjs <input.html> <output.svg>');
  process.exit(2);
}

const input = path.resolve(inputArg);
const output = path.resolve(outputArg);

if (input === output) {
  console.error('input and output must be different files');
  process.exit(2);
}

const html = fs.readFileSync(input, 'utf8');
const starts = [...html.matchAll(/<svg\b/gi)];

if (starts.length !== 1) {
  console.error(`expected exactly one canonical SVG, found ${starts.length}`);
  process.exit(1);
}

const start = starts[0].index;
const endToken = '</svg>';
const end = html.indexOf(endToken, start);

if (end < 0) {
  console.error('canonical SVG has no closing </svg> tag');
  process.exit(1);
}

const svg = html.slice(start, end + endToken.length);

const forbidden = [
  [/<script\b/i, 'script element'],
  [/\son[a-z]+\s*=/i, 'inline event handler'],
  [/\b(?:href|src)\s*=\s*["']\s*(?:https?:)?\/\//i, 'remote resource reference'],
];

for (const [pattern, label] of forbidden) {
  if (pattern.test(svg)) {
    console.error(`refusing SVG containing ${label}`);
    process.exit(1);
  }
}

if (!/<svg\b[^>]*\bviewBox\s*=/i.test(svg)) {
  console.error('canonical SVG is missing viewBox');
  process.exit(1);
}

fs.writeFileSync(output, `${svg}\n`, { encoding: 'utf8', flag: 'wx' });
console.log(JSON.stringify({ ok: true, input, output, bytes: Buffer.byteLength(svg) }));
