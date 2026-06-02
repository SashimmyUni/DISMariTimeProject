const map = L.map("map").setView([1.29027, 103.851959], 8);
const markerLayer = L.layerGroup().addTo(map);

const tableBody = document.getElementById("ships-table-body");
const statusText = document.getElementById("status-text");
const refreshButton = document.getElementById("refresh-btn");

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors"
}).addTo(map);

function formatValue(value) {
    return value ?? "N/A";
}

function renderTable(ships) {
    tableBody.innerHTML = "";

    ships.forEach((ship) => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${ship.vessel_name || "Unknown Vessel"}</td>
            <td>${ship.mmsi}</td>
            <td>${ship.latitude?.toFixed?.(5) ?? ship.latitude}</td>
            <td>${ship.longitude?.toFixed?.(5) ?? ship.longitude}</td>
            <td>${formatValue(ship.speed)}</td>
            <td>${formatValue(ship.course)}</td>
            <td>${formatValue(ship.timestamp)}</td>
        `;
        tableBody.appendChild(row);
    });
}

function renderMarkers(ships) {
    markerLayer.clearLayers();

    ships.forEach((ship) => {
        if (ship.latitude != null && ship.longitude != null) {
            L.marker([ship.latitude, ship.longitude])
                .addTo(markerLayer)
                .bindPopup(`
                    <strong>${ship.vessel_name || "Unknown Vessel"}</strong><br>
                    MMSI: ${ship.mmsi}<br>
                    Speed: ${formatValue(ship.speed)}<br>
                    Course: ${formatValue(ship.course)}<br>
                    Time: ${formatValue(ship.timestamp)}
                `);
        }
    });
}

async function loadShips() {
    statusText.textContent = "Loading data...";

    try {
        const response = await fetch("/api/ships");

        if (!response.ok) {
            throw new Error(`Request failed: ${response.status}`);
        }

        const ships = await response.json();

        renderMarkers(ships);
        renderTable(ships);
        statusText.textContent = `Loaded ${ships.length} ships`;
    } catch (error) {
        statusText.textContent = "Failed to load ship data";
        console.error(error);
    }
}

refreshButton.addEventListener("click", loadShips);
loadShips();
setInterval(loadShips, 60000);
