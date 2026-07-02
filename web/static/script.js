async function update_dashboard() {
  try {
    const response = await fetch("/api/status");
    if (response.ok) {
      const data = await response.json();
      const tableBody = document.getElementById("bots-table-body");
      const activeCountEl = document.getElementById("active-bots-count");

      let html = "";
      let botCount = 0;

      for (const [name, state] of Object.entries(data)) {
        botCount++;
        const redeemClass = getBadgeClass(state.redeem);
        const weeklyClass = getBadgeClass(state.weekly);
        const statusClass = getBadgeClass(state.status);

        html += `
                    <tr>
                        <td style="font-weight: 600; color: #f8fafc;">${name}</td>
                        <td><span class="badge ${redeemClass}">${state.redeem || "-"}</span></td>
                        <td><span class="badge ${weeklyClass}">${state.weekly || "-"}</span></td>
                        <td style="font-weight: 600; color: #f59e0b;">${state.smoltz || "0"}</td>
                        <td>${state.target || "-"}</td>
                        <td style="color: #60a5fa; font-weight: 600;">${state.room || "-"}</td>
                        <td><span class="badge ${statusClass}">${state.status || "-"}</span></td>
                    </tr>
                `;
      }

      tableBody.innerHTML = html;
      activeCountEl.textContent = botCount;
    }
  } catch (e) {}
}

function getBadgeClass(status) {
  if (!status) return "";
  const s = status.toLowerCase();
  if (s === "already") return "already";
  if (s === "success" || s === "claimed") return "success";
  if (s === "failed" || s === "disconnect") return "failed";
  if (s === "lobby" || s === "waiting") return "lobby";
  if (s === "queued") return "queued";
  if (s === "in progress" || s === "in game") return "in-progress";
  if (s === "retrying") return "retrying";
  return "";
}

setInterval(update_dashboard, 2000);
update_dashboard();
