const express = require("express");
const path = require("path");
const fs = require("fs/promises");
const { randomUUID } = require("crypto");

const app = express();
const PORT = process.env.PORT || 3000;
const DATA_FILE = path.join(__dirname, "stories.json");
const CLIENT_DIR = __dirname;

app.use(express.json({ limit: "1mb" }));
app.use(express.static(CLIENT_DIR));

app.get("/api/stories", async (_req, res, next) => {
  try {
    const stories = await readStories();
    res.json(stories);
  } catch (error) {
    next(error);
  }
});

app.post("/api/stories", async (req, res, next) => {
  try {
    const { title, author, tag, content } = req.body || {};
    const validationError = validateStory({ title, author, tag, content });
    if (validationError) {
      return res.status(400).json({ message: validationError });
    }

    const newStory = {
      id: randomUUID(),
      title: title.trim(),
      author: author.trim(),
      tag: tag.trim(),
      content: content.trim(),
      createdAt: new Date().toISOString(),
    };

    const stories = await readStories();
    stories.push(newStory);
    await writeStories(stories);

    res.status(201).json(newStory);
  } catch (error) {
    next(error);
  }
});

app.get("*", (_req, res) => {
  res.sendFile(path.join(CLIENT_DIR, "index.html"));
});

app.use((err, _req, res, _next) => {
  console.error(err);
  res.status(500).json({ message: "Unexpected server error." });
});

app.listen(PORT, () => {
  console.log(`Open Story Commons listening on http://localhost:${PORT}`);
});

async function readStories() {
  try {
    const data = await fs.readFile(DATA_FILE, "utf8");
    return JSON.parse(data);
  } catch (error) {
    if (error.code === "ENOENT") {
      await writeStories([]);
      return [];
    }
    throw error;
  }
}

async function writeStories(stories) {
  const normalized = Array.isArray(stories) ? stories : [];
  await fs.writeFile(DATA_FILE, JSON.stringify(normalized, null, 2));
}

function validateStory({ title, author, tag, content }) {
  if (!title || typeof title !== "string" || !title.trim()) {
    return "Please provide a story title.";
  }
  if (!author || typeof author !== "string" || !author.trim()) {
    return "Please include your name.";
  }
  if (!tag || typeof tag !== "string" || !tag.trim()) {
    return "Please choose a category.";
  }
  if (!content || typeof content !== "string" || content.trim().length < 40) {
    return "Stories should be at least 40 characters.";
  }
  if (content.trim().length > 1800) {
    return "Stories should be fewer than 1,800 characters.";
  }
  if (title.trim().length > 120) {
    return "Titles must be 120 characters or fewer.";
  }
  if (author.trim().length > 80) {
    return "Names must be 80 characters or fewer.";
  }
  return null;
}
