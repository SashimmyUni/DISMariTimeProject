const map = L.map('map').setView([1.29027, 103.851959], 8);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

async function loadShips() {
    const response = await fetch('/api/ships');
    const ships = await response.json();

    ships.forEach(ship => {
        if (ship.latitude && ship.longitude) {
            L.marker([ship.latitude, ship.longitude])
                .addTo(map)
                .bindPopup(`
                    <strong>${ship.vessel_name || 'Unknown Vessel'}</strong><br>
                    MMSI: ${ship.mmsi}<br>
                    Speed: ${ship.speed ?? 'N/A'}<br>
                    Course: ${ship.course ?? 'N/A'}<br>
                    Time: ${ship.timestamp}
                `);
        }
    });
}

loadShips();
