const option = document.querySelector("#option");
const rating = document.querySelector("#rating");
const ratingOut = document.querySelector("#ratingOut");
const notes = document.querySelector("#notes");
const status = document.querySelector("#status");
const form = document.querySelector("#ratingForm");

document.querySelectorAll("[data-choice]").forEach((button) => {
  button.addEventListener("click", () => {
    option.value = button.dataset.choice;
    document.querySelector(".panel").scrollIntoView({ behavior: "smooth", block: "start" });
  });
});

rating.addEventListener("input", () => {
  ratingOut.textContent = rating.value;
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  status.textContent = "Saving...";
  const payload = {
    option: option.value,
    rating: Number(rating.value),
    notes: notes.value.trim(),
    user_agent: navigator.userAgent,
  };

  try {
    const response = await fetch("/ratings", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    });
    const body = await response.json();
    if (!body.ok) throw new Error("Save failed");
    localStorage.setItem("starlight-voice-last-rating", JSON.stringify(payload));
    status.textContent = `Saved to ${body.path}`;
  } catch (error) {
    localStorage.setItem("starlight-voice-last-rating", JSON.stringify(payload));
    status.textContent = "Saved in browser only. Start dashboard server to write JSONL.";
  }
});
