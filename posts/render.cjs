// Renders the feed posts in this folder to 1080x1350 PNGs next to their HTML.
// Usage (from the repo root): node posts/render.cjs [name ...]
// Needs Playwright with Chromium. Pages are served over a local HTTP server,
// because Chromium refuses web fonts loaded from file:// URLs.
const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

const POSTS = ["yandex-delivery", "kaspi-store"];
const root = path.resolve(__dirname, "..");
const types = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css",
  ".js": "text/javascript",
  ".woff2": "font/woff2",
};

const server = http.createServer((req, res) => {
  const file = path.join(root, decodeURIComponent(new URL(req.url, "http://x").pathname));
  if (!file.startsWith(root + path.sep) || !fs.existsSync(file)) {
    res.writeHead(404).end();
    return;
  }
  res.writeHead(200, { "Content-Type": types[path.extname(file)] || "application/octet-stream" });
  fs.createReadStream(file).pipe(res);
});

(async () => {
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const base = "http://127.0.0.1:" + server.address().port + "/posts/";
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 1 });
  page.on("requestfailed", (req) => console.error("failed:", req.url()));

  const names = process.argv.length > 2 ? process.argv.slice(2) : POSTS;
  for (const name of names) {
    await page.goto(base + name + ".html", { waitUntil: "networkidle" });
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: path.join(__dirname, name + ".png") });
    console.log("posts/" + name + ".png");
  }

  await browser.close();
  server.close();
})();
