// Elements
const systemVersion = document.getElementById("system-version");
const connectionStatus = document.getElementById("connection-status");
const activeBots = document.getElementById("active-bots");
const botTbody = document.getElementById("bot-tbody");
const botSelect = document.getElementById("bot-select");
const logViewer = document.getElementById("log-viewer");
const autoScrollCheck = document.getElementById("auto-scroll-check");
const copyLogBtn = document.getElementById("copy-log-btn");

function showToast(message) {
  const toast = document.getElementById("toast");
  toast.innerText = message;
  toast.className = "toast show";
  setTimeout(() => {
    toast.className = toast.className.replace("show", "");
  }, 2000);
}

function copyToClipboard(text) {
  if (!text || text === "Waiting" || text === "Room" || text === "Queue")
    return;
  const fullLink = `https://www.clawroyale.ai/games/${text}`;
  navigator.clipboard
    .writeText(fullLink)
    .then(() => {
      showToast(`Spectator link copied to clipboard!`);
    })
    .catch((err) => {
      console.error("Failed to copy: ", err);
    });
}
window.copyToClipboard = copyToClipboard;

copyLogBtn.addEventListener("click", () => {
  const logsText = logViewer.textContent;
  if (
    !logsText ||
    logsText === "Please select a bot to view live logs." ||
    logsText === "No logs recorded yet for this session."
  ) {
    showToast("No logs to copy!");
    return;
  }
  navigator.clipboard
    .writeText(logsText)
    .then(() => {
      showToast("Gameplay log copied to clipboard!");
    })
    .catch((err) => {
      console.error("Failed to copy: ", err);
    });
});

// Fetch and update bot status
async function updateStatus() {
  try {
    const response = await fetch("/api/status");
    const data = await response.json();

    // Update values
    systemVersion.textContent = "Ver 1.12.0";
    connectionStatus.textContent = "Successful";
    activeBots.textContent = Object.keys(data).length;

    const currentSelection = botSelect.value;
    const botNames = Object.keys(data);
    const existingOptions = Array.from(botSelect.options)
      .map((o) => o.value)
      .filter((v) => v !== "");

    if (JSON.stringify(existingOptions) !== JSON.stringify(botNames)) {
      botSelect.innerHTML = '<option value="">Select Bot</option>';
      botNames.forEach((name) => {
        const opt = document.createElement("option");
        opt.value = name;
        opt.textContent = name;
        botSelect.appendChild(opt);
      });
      if (botNames.includes(currentSelection)) {
        botSelect.value = currentSelection;
      }
    }

    botTbody.innerHTML = "";

    for (const [name, state] of Object.entries(data)) {
      const tr = document.createElement("tr");

      // Map status states to styling classes
      const redeemStatus = state.redeem
        ? state.redeem.toLowerCase()
        : "waiting";
      const weeklyStatus = state.weekly
        ? state.weekly.toLowerCase().replace(" ", "-")
        : "waiting";
      const botStatus = state.status
        ? state.status.toLowerCase().replace(" ", "-")
        : "waiting";
      const rawRoom = state.room_id || state.room;
      const lifeStatus = state.alive ? "alive" : "dead";
      const lifeText = state.alive ? "Alive" : "Dead";

      tr.innerHTML = `
                <td class="agent-name">${name}</td>
                <td><span class="badge badge-${redeemStatus}">${state.redeem}</span></td>
                <td><span class="badge badge-${weeklyStatus}">${state.weekly}</span></td>
                <td class="smoltz-value">${state.smoltz}</td>
                <td><span class="badge badge-${lifeStatus}">${lifeText}</span></td>
                <td>${state.target}</td>
                <td class="room-value">
                    <span class="room-clickable" onclick="copyToClipboard('${rawRoom}')" title="Click to copy Room ID">
                        ${state.room}
                    </span>
                </td>
                <td><span class="badge status-${botStatus}">${state.status}</span></td>
            `;
      botTbody.appendChild(tr);
    }
  } catch (error) {
    console.error("Failed to update status:", error);
  }
}

async function updateLogs() {
  const selectedBot = botSelect.value;
  if (!selectedBot) {
    logViewer.textContent = "Please select a bot to view live logs.";
    return;
  }

  try {
    const response = await fetch(
      `/api/logs?bot=${encodeURIComponent(selectedBot)}`,
    );
    const logs = await response.text();

    const isAtBottom =
      logViewer.scrollHeight - logViewer.clientHeight <=
      logViewer.scrollTop + 50;

    logViewer.textContent = logs || "No logs recorded yet for this session.";

    if (autoScrollCheck.checked && isAtBottom) {
      logViewer.scrollTop = logViewer.scrollHeight;
    }
  } catch (error) {
    console.error("Failed to update logs:", error);
  }
}

// Update status immediately and then every 2 seconds
updateStatus();
setInterval(updateStatus, 2000);
setInterval(updateLogs, 1000);
