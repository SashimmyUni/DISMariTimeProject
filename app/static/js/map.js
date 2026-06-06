const map = L.map("map").setView([56.0, 10.0], 6);
const markerLayer = L.layerGroup().addTo(map);
const routeLayer = L.layerGroup().addTo(map);

const tableBody = document.getElementById("ships-table-body");
const statusText = document.getElementById("status-text");
const refreshButton = document.getElementById("refresh-btn");
const dateFilterInput = document.getElementById("date-filter");
const vesselFilterInput = document.getElementById("vessel-filter");
const latestOnlyFilterInput = document.getElementById("latest-only-filter");
const clearDateButton = document.getElementById("clear-date-btn");

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors"
}).addTo(map);

function formatValue(value) {
    return value ?? "N/A";
}

function getDirectionDegrees(ship) {
    if (Number.isFinite(ship.heading) && ship.heading >= 0) {
        return ship.heading;
    }
    if (Number.isFinite(ship.course) && ship.course >= 0) {
        return ship.course;
    }
    return null;
}

function projectPoint(lat, lon, distanceMeters, bearingDegrees) {
    const bearingRad = (bearingDegrees * Math.PI) / 180;
    const latRad = (lat * Math.PI) / 180;
    const metersPerDegLat = 111_320;
    const metersPerDegLon = 111_320 * Math.cos(latRad);
    const dLat = (distanceMeters * Math.cos(bearingRad)) / metersPerDegLat;
    const dLon = (distanceMeters * Math.sin(bearingRad)) / metersPerDegLon;
    return [lat + dLat, lon + dLon];
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
            const marker = L.circleMarker([ship.latitude, ship.longitude], {
                radius: 5,
                color: "#0f766e",
                fillColor: "#14b8a6",
                fillOpacity: 0.9,
                weight: 2
            }).addTo(markerLayer);

            const direction = getDirectionDegrees(ship);
            if (direction !== null) {
                const tip = projectPoint(ship.latitude, ship.longitude, 600, direction);
                L.polyline(
                    [[ship.latitude, ship.longitude], tip],
                    { color: "#0f766e", weight: 3, opacity: 0.85 }
                ).addTo(markerLayer);
            }

            marker.bindPopup(`
                <strong>${ship.vessel_name || "Unknown Vessel"}</strong><br>
                MMSI: ${ship.mmsi}<br>
                Speed: ${formatValue(ship.speed)} kn<br>
                Heading: ${formatValue(ship.heading)}°<br>
                Course: ${formatValue(ship.course)}°<br>
                Time: ${formatValue(ship.timestamp)}
            `);
        }
    });
}

// Draw the full route as a polyline when a single vessel is selected
function renderRoute(ships) {
    routeLayer.clearLayers();

    if (ships.length < 2) return;

    // Sort chronologically
    const sorted = [...ships].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

    const coords = sorted
        .filter(s => s.latitude != null && s.longitude != null)
        .map(s => [s.latitude, s.longitude]);

    if (coords.length < 2) return;

    // Draw route line
    L.polyline(coords, {
        color: "#f59e0b",
        weight: 3,
        opacity: 0.8,
        dashArray: "6, 4"
    }).addTo(routeLayer);

    // Start marker (green)
    L.circleMarker(coords[0], {
        radius: 8,
        color: "#16a34a",
        fillColor: "#22c55e",
        fillOpacity: 1,
        weight: 2
    }).bindPopup(`<strong>Start</strong><br>${sorted[0].timestamp}`).addTo(routeLayer);

    // End marker (red)
    L.circleMarker(coords[coords.length - 1], {
        radius: 8,
        color: "#dc2626",
        fillColor: "#ef4444",
        fillOpacity: 1,
        weight: 2
    }).bindPopup(`<strong>End</strong><br>${sorted[sorted.length - 1].timestamp}`).addTo(routeLayer);

    // Fit map to route
    map.fitBounds(L.polyline(coords).getBounds(), { padding: [40, 40] });
}

function vesselOptionLabel(vessel) {
    const name = vessel.vessel_name || "Unknown Vessel";
    return `${name} (${vessel.mmsi})`;
}

async function loadVesselOptions() {
    if (!vesselFilterInput) return;

    try {
        const response = await fetch("/api/vessels");
        if (!response.ok) {
            throw new Error(`Failed to load vessels: ${response.status}`);
        }

        const vessels = await response.json();
        vessels.sort((a, b) => (a.vessel_name || "").localeCompare(b.vessel_name || ""));

        const selected = vesselFilterInput.value;
        vesselFilterInput.innerHTML = "";

        const allOption = document.createElement("option");
        allOption.value = "";
        allOption.textContent = "All vessels";
        vesselFilterInput.appendChild(allOption);

        vessels.forEach((vessel) => {
            const option = document.createElement("option");
            option.value = String(vessel.mmsi);
            option.textContent = vesselOptionLabel(vessel);
            vesselFilterInput.appendChild(option);
        });

        if (selected && Array.from(vesselFilterInput.options).some((opt) => opt.value === selected)) {
            vesselFilterInput.value = selected;
        }
    } catch (error) {
        console.error(error);
    }
}

function buildShipsUrl() {
    const params = new URLSearchParams();

    const selectedDate = dateFilterInput?.value;
    if (selectedDate) {
        params.set("date", selectedDate);
    }

    if (latestOnlyFilterInput?.checked) {
        params.set("latest", "true");
    }

    if (vesselFilterInput?.value) {
        params.set("mmsi", vesselFilterInput.value);
    }

    const queryString = params.toString();
    return queryString ? `/api/ships?${queryString}` : "/api/ships";
}

async function loadShips() {
    statusText.textContent = "Loading data...";

    try {
        const response = await fetch(buildShipsUrl());

        if (!response.ok) {
            const errorPayload = await response.json().catch(() => null);
            const apiMessage = errorPayload && errorPayload.error ? `: ${errorPayload.error}` : "";
            throw new Error(`Request failed: ${response.status}${apiMessage}`);
        }

        const ships = await response.json();
        const selectedDate = dateFilterInput?.value;
        const latestOnly = latestOnlyFilterInput?.checked;
        const selectedVessel = vesselFilterInput?.selectedOptions?.[0]?.textContent;
        const hasSingleVessel = Boolean(vesselFilterInput?.value);

        renderMarkers(ships);
        renderTable(ships);

        // Draw route when a single vessel is selected (and not latest-only)
        if (hasSingleVessel && !latestOnly) {
            renderRoute(ships);
        } else {
            routeLayer.clearLayers();
        }

        // Status text
        if (selectedDate && latestOnly && hasSingleVessel) {
            statusText.textContent = `Loaded ${ships.length} latest positions for ${selectedVessel} on ${selectedDate}`;
        } else if (selectedDate && latestOnly) {
            statusText.textContent = `Loaded ${ships.length} latest ship positions for ${selectedDate}`;
        } else if (selectedDate && hasSingleVessel) {
            statusText.textContent = `Loaded ${ships.length} positions for ${selectedVessel} on ${selectedDate}`;
        } else if (selectedDate) {
            statusText.textContent = `Loaded ${ships.length} ships for ${selectedDate}`;
        } else if (latestOnly && hasSingleVessel) {
            statusText.textContent = `Loaded ${ships.length} latest positions for ${selectedVessel}`;
        } else if (hasSingleVessel) {
            statusText.textContent = `Loaded ${ships.length} positions for ${selectedVessel}`;
        } else if (latestOnly) {
            statusText.textContent = `Loaded ${ships.length} latest ship positions`;
        } else {
            statusText.textContent = `Loaded ${ships.length} ships`;
        }
    } catch (error) {
        statusText.textContent = "Failed to load ship data";
        console.error(error);
    }
}

refreshButton.addEventListener("click", loadShips);
dateFilterInput?.addEventListener("change", loadShips);
vesselFilterInput?.addEventListener("change", loadShips);
latestOnlyFilterInput?.addEventListener("change", loadShips);
clearDateButton?.addEventListener("click", () => {
    if (dateFilterInput) dateFilterInput.value = "";
    if (vesselFilterInput) vesselFilterInput.value = "";
    if (latestOnlyFilterInput) latestOnlyFilterInput.checked = false;
    routeLayer.clearLayers();
    loadShips();
});

loadVesselOptions().then(loadShips);
setInterval(loadShips, 60000);