import http from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";
import Anthropic from "@anthropic-ai/sdk";

const PORT = Number(process.env.PORT) || 3000;
const PUBLIC_DIR = join(fileURLToPath(new URL(".", import.meta.url)), "public");
const MAX_BODY = 8 * 1024 * 1024;

const client = new Anthropic();

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".webmanifest": "application/manifest+json",
  ".svg": "image/svg+xml",
  ".png": "image/png",
};

const SYSTEM_PROMPT = `Ты — нутрициолог, который оценивает калорийность еды по фотографии.
Определи каждое отдельное блюдо или продукт на фото и оцени его вес в граммах по видимому размеру порции (ориентируйся на тарелку, приборы, руки, упаковку).
Для каждого продукта дай пищевую ценность на 100 г по стандартным таблицам (ккал, белки, жиры, углеводы) — расчёт на порцию сделает приложение.
Учитывай способ приготовления: масло при жарке, соусы, заправки — их можно выделить отдельной позицией.
Названия пиши по-русски, коротко и понятно. Если на фото нет еды, верни пустой список items и объясни это в note.`;

const RESULT_SCHEMA = {
  type: "object",
  properties: {
    dish: { type: "string", description: "Короткое общее название приёма пищи" },
    items: {
      type: "array",
      items: {
        type: "object",
        properties: {
          name: { type: "string" },
          grams: { type: "number" },
          kcal_per_100g: { type: "number" },
          protein_per_100g: { type: "number" },
          fat_per_100g: { type: "number" },
          carbs_per_100g: { type: "number" },
        },
        required: ["name", "grams", "kcal_per_100g", "protein_per_100g", "fat_per_100g", "carbs_per_100g"],
        additionalProperties: false,
      },
    },
    confidence: { type: "string", enum: ["low", "medium", "high"] },
    note: { type: "string", description: "Короткий комментарий для пользователя" },
  },
  required: ["dish", "items", "confidence", "note"],
  additionalProperties: false,
};

async function analyzePhoto({ image, mediaType, hint }) {
  const content = [
    { type: "image", source: { type: "base64", media_type: mediaType, data: image } },
    { type: "text", text: hint ? `Подсказка от пользователя: ${hint}` : "Что на фото и сколько это калорий?" },
  ];
  const response = await client.beta.messages.create({
    model: "claude-opus-5-5",
    max_tokens: 16000,
    betas: ["server-side-fallback-2026-07-01"],
    fallbacks: "default",
    output_config: { effort: "low", format: { type: "json_schema", schema: RESULT_SCHEMA } },
    system: SYSTEM_PROMPT,
    messages: [{ role: "user", content }],
  });
  if (response.stop_reason === "refusal") {
    throw Object.assign(new Error("Модель отказалась анализировать это изображение"), { status: 422 });
  }
  const text = response.content.find((b) => b.type === "text")?.text;
  if (!text) throw new Error("Пустой ответ модели");
  return JSON.parse(text);
}

function readJson(req) {
  return new Promise((resolve, reject) => {
    let size = 0;
    const chunks = [];
    req.on("data", (chunk) => {
      size += chunk.length;
      if (size > MAX_BODY) {
        reject(Object.assign(new Error("Фото слишком большое"), { status: 413 }));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on("end", () => {
      try {
        resolve(JSON.parse(Buffer.concat(chunks).toString("utf8")));
      } catch {
        reject(Object.assign(new Error("Некорректный JSON"), { status: 400 }));
      }
    });
    req.on("error", reject);
  });
}

function sendJson(res, status, body) {
  res.writeHead(status, { "Content-Type": MIME[".json"] });
  res.end(JSON.stringify(body));
}

async function serveStatic(req, res) {
  const url = new URL(req.url, "http://localhost");
  const path = normalize(decodeURIComponent(url.pathname)).replace(/^(\.\.[/\\])+/, "");
  const file = join(PUBLIC_DIR, path === "/" ? "index.html" : path);
  if (!file.startsWith(PUBLIC_DIR)) return sendJson(res, 403, { error: "Forbidden" });
  try {
    const data = await readFile(file);
    res.writeHead(200, { "Content-Type": MIME[extname(file)] || "application/octet-stream" });
    res.end(data);
  } catch {
    res.writeHead(404);
    res.end("Not found");
  }
}

const server = http.createServer(async (req, res) => {
  if (req.method === "POST" && req.url === "/api/analyze") {
    try {
      const { image, mediaType, hint } = await readJson(req);
      if (typeof image !== "string" || !/^image\/(jpeg|png|webp|gif)$/.test(mediaType)) {
        return sendJson(res, 400, { error: "Нужно изображение JPEG, PNG, WebP или GIF" });
      }
      sendJson(res, 200, await analyzePhoto({ image, mediaType, hint: String(hint || "").slice(0, 300) }));
    } catch (err) {
      console.error(err);
      if (err instanceof Anthropic.AuthenticationError || (!(err instanceof Anthropic.APIError) && !process.env.ANTHROPIC_API_KEY)) {
        return sendJson(res, 500, { error: "Не задан или неверен ANTHROPIC_API_KEY на сервере" });
      }
      if (err instanceof Anthropic.RateLimitError) {
        return sendJson(res, 429, { error: "Слишком много запросов, попробуйте через минуту" });
      }
      sendJson(res, err.status && err.status < 500 ? err.status : 500, { error: err.message || "Ошибка анализа" });
    }
    return;
  }
  if (req.method === "GET") return serveStatic(req, res);
  res.writeHead(405);
  res.end();
});

server.listen(PORT, () => {
  console.log(`Feel: http://localhost:${PORT}`);
  if (!process.env.ANTHROPIC_API_KEY) console.warn("ANTHROPIC_API_KEY не задан — распознавание по фото работать не будет");
});
