const select = document.getElementById("bot-select");
const statusLabel = document.getElementById("ws-status");
const logOutput = document.getElementById("log-output");
const copyLogBtn = document.getElementById("copy-log-btn");

const statHp = document.getElementById("stat-hp");
const statHpBar = document.getElementById("stat-hp-bar");
const statEp = document.getElementById("stat-ep");
const statEpBar = document.getElementById("stat-ep-bar");
const statWeapon = document.getElementById("stat-weapon");
const statArmor = document.getElementById("stat-armor");
const statKills = document.getElementById("stat-kills");
const statLocation = document.getElementById("stat-location");
const statTerrain = document.getElementById("stat-terrain");
const statWeather = document.getElementById("stat-weather");

const inventoryList = document.getElementById("inventory-list");
const radarList = document.getElementById("radar-list");
const groundItemsList = document.getElementById("ground-items-list");
const roomLink = document.getElementById("room-link");

let botsData = {};
let activeBotName = "";

function connect() {
  const ws = new WebSocket("ws://" + window.location.hostname + ":8765");

  ws.onopen = function () {
    statusLabel.textContent = "Connected";
    statusLabel.className = "status connected";
  };

  ws.onclose = function () {
    statusLabel.textContent = "Disconnected";
    statusLabel.className = "status";
    setTimeout(connect, 3000);
  };

  ws.onmessage = function (event) {
    try {
      const message = JSON.parse(event.data);
      if (message.type === "state_update") {
        const botName = message.bot_name;
        if (!botsData[botName]) {
          botsData[botName] = {
            logs: "",
            last_appended_turn: -1,
          };
        }

        const currentTurn = message.data.turn;
        if (botsData[botName].last_appended_turn !== currentTurn) {
          botsData[botName].logs += message.data.logs + "\n";
          botsData[botName].last_appended_turn = currentTurn;
        }

        botsData[botName].state = message.data;
        updateSelector();
        if (botName === activeBotName) {
          updateDashboard(message.data);
        }
      }
    } catch (e) {}
  };
}

function updateSelector() {
  const previousSelection = activeBotName;
  const botNames = Object.keys(botsData);

  select.innerHTML = "";
  if (botNames.length === 0) {
    select.innerHTML = '<option value="">No Bots Active</option>';
    activeBotName = "";
    return;
  }

  botNames.forEach((name) => {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name;
    select.appendChild(option);
  });

  if (botNames.includes(previousSelection)) {
    select.value = previousSelection;
    activeBotName = previousSelection;
  } else {
    select.value = botNames[0];
    activeBotName = botNames[0];
    if (botsData[activeBotName] && botsData[activeBotName].state) {
      updateDashboard(botsData[activeBotName].state);
    }
  }
}

select.addEventListener("change", function () {
  activeBotName = select.value;
  if (
    activeBotName &&
    botsData[activeBotName] &&
    botsData[activeBotName].state
  ) {
    updateDashboard(botsData[activeBotName].state);
  } else {
    clearDashboard();
  }
});

function appendLog(text) {
  const isAtBottom =
    logOutput.scrollHeight - logOutput.clientHeight <= logOutput.scrollTop + 50;
  logOutput.textContent += text + "\n";
  if (isAtBottom) {
    logOutput.scrollTop = logOutput.scrollHeight;
  }
}

function clearDashboard() {
  statHp.textContent = "0/100";
  statHpBar.style.width = "0%";
  statEp.textContent = "0/10";
  statEpBar.style.width = "0%";
  statWeapon.textContent = "None";
  statArmor.textContent = "None";
  statKills.textContent = "0";
  statLocation.textContent = "Unknown";
  statTerrain.textContent = "Unknown";
  statWeather.textContent = "Unknown";
  inventoryList.innerHTML = "";
  radarList.innerHTML = "";
  groundItemsList.innerHTML = "";
  logOutput.textContent = "";
  roomLink.href = "#";
  roomLink.textContent = "No active game";
}

function updateDashboard(data) {
  if (!data) return;

  const hp = data.hp ?? 100;
  statHp.textContent = hp + "/100";
  statHpBar.style.width = hp + "%";

  const ep = data.ep ?? 10;
  statEp.textContent = ep + "/10";
  statEpBar.style.width = ep * 10 + "%";

  statWeapon.textContent = data.weapon ?? "None";
  statArmor.textContent = data.armor ?? "None";
  statKills.textContent = data.kills ?? "0";
  statLocation.textContent = data.location ?? "Unknown";
  statTerrain.textContent = data.terrain ?? "Unknown";
  statWeather.textContent = data.weather ?? "Unknown";

  const gameId = data.game_id;
  if (gameId && gameId !== "Unknown") {
    roomLink.href = "https://www.clawroyale.ai/games/spect/" + gameId;
    roomLink.textContent = "https://www.clawroyale.ai/games/spect/" + gameId;
  } else {
    roomLink.href = "#";
    roomLink.textContent = "No active game";
  }

  inventoryList.innerHTML = "";
  const inventory = data.inventory ?? [];
  inventory.forEach((item) => {
    const div = document.createElement("div");
    div.className = "inventory-item";
    div.textContent = item;
    inventoryList.appendChild(div);
  });

  radarList.innerHTML = "";
  const radar = data.radar ?? {};
  Object.keys(radar).forEach((layer) => {
    const div = document.createElement("div");
    div.className = "radar-layer";

    const title = document.createElement("div");
    title.className = "radar-layer-title";
    title.textContent = "Layer " + layer;
    div.appendChild(title);

    const content = document.createElement("div");
    content.textContent = radar[layer];
    div.appendChild(content);

    radarList.appendChild(div);
  });

  groundItemsList.innerHTML = "";
  const groundItems = data.ground_items ?? [];
  if (groundItems.length === 0) {
    groundItemsList.textContent = "None";
  } else {
    groundItems.forEach((item) => {
      const span = document.createElement("span");
      span.style.display = "block";
      span.textContent = item;
      groundItemsList.appendChild(span);
    });
  }

  const currentLogs =
    botsData[activeBotName] && botsData[activeBotName].logs
      ? botsData[activeBotName].logs
      : "";

  const isAtBottom =
    logOutput.scrollHeight - logOutput.clientHeight <= logOutput.scrollTop + 50;
  logOutput.textContent = currentLogs;
  if (isAtBottom) {
    logOutput.scrollTop = logOutput.scrollHeight;
  }
}

copyLogBtn.addEventListener("click", function () {
  const logsText = logOutput.textContent;
  navigator.clipboard
    .writeText(logsText)
    .then(() => {
      copyLogBtn.textContent = "Copied!";
      copyLogBtn.classList.add("copied");
      setTimeout(() => {
        copyLogBtn.textContent = "Copy Log";
        copyLogBtn.classList.remove("copied");
      }, 2000);
    })
    .catch(() => {});
});

connect();
