// Turns the draft SVGs from build.py into Figma-ready SVGs and PNGs.
// Usage (from the repo root): python3 posts/2gis-review/build.py && node posts/2gis-review/render.cjs
//
// In the browser, with the real fonts, it measures every centred line of text,
// rewrites it as left-anchored at the measured x (Figma's SVG import places
// text by its start), sizes each pill to its label, then saves the SVG next to
// this file and a PNG screenshot. Needs Playwright with Chromium.
const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "../..");
const NAMES = ["2gis-review-post", "2gis-review-story"];
const types = { ".svg": "image/svg+xml", ".woff2": "font/woff2" };

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
  const base = `http://127.0.0.1:${server.address().port}/posts/2gis-review/draft/`;
  const browser = await chromium.launch();

  for (const name of NAMES) {
    const draft = fs.readFileSync(path.join(__dirname, "draft", name + ".svg"), "utf8");
    const [, w, h] = draft.match(/width="(\d+)" height="(\d+)"/).map(Number);
    const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    page.on("requestfailed", (r) => console.error("failed:", r.url()));
    await page.goto(base + name + ".svg", { waitUntil: "networkidle" });
    await page.evaluate(() => document.fonts.ready);

    const svg = await page.evaluate(() => {
      const doc = document.documentElement;
      // Pills: centre the label, then fit the pill around it.
      for (const rect of doc.querySelectorAll("rect[data-chip-for]")) {
        const label = doc.getElementById(rect.getAttribute("data-chip-for"));
        const pad = Number(rect.getAttribute("data-pad"));
        const box = label.getBBox();
        rect.setAttribute("x", (box.x - pad).toFixed(1));
        rect.setAttribute("width", (box.width + 2 * pad).toFixed(1));
        rect.removeAttribute("data-chip-for");
        rect.removeAttribute("data-pad");
      }
      // Centred text becomes start-anchored at its measured left edge.
      for (const t of doc.querySelectorAll('text[text-anchor="middle"]')) {
        const box = t.getBBox();
        t.setAttribute("x", box.x.toFixed(1));
        t.setAttribute("text-anchor", "start");
      }
      return new XMLSerializer().serializeToString(doc);
    });

    // The final SVG sits one folder up from the draft, so fix the font paths for previews.
    const finalSvg = '<?xml version="1.0" encoding="UTF-8"?>\n' + svg.replaceAll("../../../videos/", "../../videos/");
    fs.writeFileSync(path.join(__dirname, name + ".svg"), finalSvg);
    // The page now shows the rewritten SVG, so the screenshot matches the saved file.
    await page.screenshot({ path: path.join(__dirname, name + ".png") });
    console.log(`posts/2gis-review/${name}.svg + .png (${w}x${h})`);
    await page.close();
  }

  await browser.close();
  server.close();
})();
