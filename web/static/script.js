// Elements
const systemVersion = document.getElementById("system-version");
const connectionStatus = document.getElementById("connection-status");
const activeBots = document.getElementById("active-bots");
const botTbody = document.getElementById("bot-tbody");

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
  navigator.clipboard
    .writeText(text)
    .then(() => {
      showToast(`Room ID ${text} copied to clipboard!`);
    })
    .catch((err) => {
      console.error("Failed to copy: ", err);
    });
}
window.copyToClipboard = copyToClipboard;

// Fetch and update bot status
async function updateStatus() {
  try {
    const response = await fetch("/api/status");
    const data = await response.json();

    // Update values
    systemVersion.textContent = "Ver 1.12.0";
    connectionStatus.textContent = "Successful";
    activeBots.textContent = Object.keys(data).length;

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

      tr.innerHTML = `
                <td class="agent-name">${name}</td>
                <td><span class="badge badge-${redeemStatus}">${state.redeem}</span></td>
                <td><span class="badge badge-${weeklyStatus}">${state.weekly}</span></td>
                <td class="smoltz-value">${state.smoltz}</td>
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

// Update status immediately and then every 2 seconds
updateStatus();
setInterval(updateStatus, 2000);
