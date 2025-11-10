const API_URL = "/api/stories";
const storyList = document.getElementById("storyList");
const storyTemplate = document.getElementById("storyTemplate");
const storyEmpty = document.getElementById("storyEmpty");
const metricContributors = document.getElementById("metricContributors");
const metricStories = document.getElementById("metricStories");
const metricLastSubmission = document.getElementById("metricLastSubmission");
const storyForm = document.getElementById("storyForm");
const formStatus = document.getElementById("formStatus");
const toast = document.getElementById("toast");

let stories = [];

(async function init() {
  await refreshStories();
  bindForm();
})();

async function refreshStories() {
  try {
    const response = await fetch(API_URL, { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error(`Request failed with status ${response.status}`);
    stories = await response.json();
    renderStories(stories);
    updateMetrics(stories);
  } catch (error) {
    console.error("Unable to fetch stories", error);
    storyEmpty.hidden = false;
    storyEmpty.textContent = "We couldn’t load stories right now. Please try again shortly.";
    setMetricPlaceholders();
  }
}

function renderStories(entries) {
  storyList.innerHTML = "";

  if (!entries || entries.length === 0) {
    storyEmpty.hidden = false;
    return;
  }

  storyEmpty.hidden = true;

  const fragment = document.createDocumentFragment();
  entries
    .slice()
    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    .forEach((entry) => {
      const node = storyTemplate.content.cloneNode(true);
      node.querySelector(".story-tag").textContent = entry.tag;
      node.querySelector(".story-title").textContent = entry.title;
      node.querySelector(".story-content").textContent = entry.content;
      node.querySelector(".story-author").textContent = entry.author;

      const timeEl = node.querySelector(".story-date");
      timeEl.dateTime = entry.createdAt;
      timeEl.textContent = new Intl.DateTimeFormat(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "numeric",
      }).format(new Date(entry.createdAt));

      fragment.appendChild(node);
    });

  storyList.appendChild(fragment);
}

function updateMetrics(entries) {
  if (!entries || entries.length === 0) {
    setMetricPlaceholders();
    return;
  }

  const contributors = new Set(entries.map((entry) => entry.author.trim().toLowerCase()));
  metricContributors.textContent = contributors.size.toString();
  metricStories.textContent = entries.length.toString();

  const latest = entries.reduce((acc, entry) => {
    const entryDate = new Date(entry.createdAt);
    return entryDate > acc ? entryDate : acc;
  }, new Date(0));

  metricLastSubmission.textContent = new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "numeric",
  }).format(latest);
}

function setMetricPlaceholders() {
  metricContributors.textContent = "—";
  metricStories.textContent = "—";
  metricLastSubmission.textContent = "—";
}

function bindForm() {
  storyForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    formStatus.textContent = "Publishing…";

    const formData = new FormData(storyForm);
    const payload = Object.fromEntries(formData.entries());

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const { message } = await response.json().catch(() => ({ message: "Unable to publish story." }));
        throw new Error(message);
      }

      const created = await response.json();
      stories.push(created);
      renderStories(stories);
      updateMetrics(stories);
      storyForm.reset();
      formStatus.textContent = "Story published.";
      showToast("Your story is live for everyone to read.");
    } catch (error) {
      console.error("Unable to publish story", error);
      formStatus.textContent = error.message || "Unable to publish story.";
    } finally {
      setTimeout(() => {
        formStatus.textContent = "";
      }, 3000);
    }
  });
}

function showToast(message) {
  toast.textContent = message;
  toast.hidden = false;
  toast.dataset.visible = "true";
  setTimeout(() => {
    toast.dataset.visible = "false";
    setTimeout(() => {
      toast.hidden = true;
    }, 250);
  }, 3500);
}
