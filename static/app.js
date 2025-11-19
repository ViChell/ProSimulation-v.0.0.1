// Global variables
let map;
let autoplay = false;
let intervalId = null;
let config = {};
let unitMarkers = new Map(); // Зберігаємо маркери юнітів
let destroyedUnits = new Set(); // Відстежуємо знищені юніти
// let activeAnimations = []; // Активні анімації??

// Icon paths for different unit types
const ICON_PATHS = {
    'tank': '/static/icons/tank.png',
    'bmp': '/static/icons/bmp.png',
    'infantry': '/static/icons/infantry.png',
    'mortar': '/static/icons/mortar.png',
    'artillery': '/static/icons/artillery.png',
    'uav': '/static/icons/uav.png'
};

// Initialize map and load configuration
async function initMap() {
    try {
        // Load configuration
        const configResponse = await fetch('/api/config');
        const configData = await configResponse.json();
        
        if (configData.status === 'success') {
            config = configData.config;
        } else {
            config = {
                center: [36.3, 47.6],
                zoom: 8,
                min_zoom: 0,
                max_zoom: 22,
                step_interval: 500,
                unit_colors: {}
            };
        }
        
        // Try to load map metadata
        let center = config.center;
        let zoom = config.zoom;
        
        try {
            const metadataResponse = await fetch('/tiles/metadata');
            const metadata = await metadataResponse.json();
            
            if (metadata.center) {
                const centerParts = metadata.center.split(',');
                center = [parseFloat(centerParts[0]), parseFloat(centerParts[1])];
                zoom = parseFloat(centerParts[2]) || zoom;
            }
        } catch (e) {
            console.log('Using fallback OSM tiles');
        }

        // // Ініціалізація карти
        // map = new maplibregl.Map({
        //     container: 'map',
        //     style: {
        //         version: 8,
        //         sources: {
        //             'osm': {
        //                 type: 'raster',
        //                 tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
        //                 tileSize: 256,
        //                 attribution: '© OpenStreetMap contributors'
        //             },
        //             // ✅ Додай DEM (Digital Elevation Model)
        //             'terrainSource': {
        //                 type: 'raster-dem',
        //                 tiles: ['https://api.maptiler.com/tiles/terrain-rgb/{z}/{x}/{y}.png?key=YOUR_MAPTILER_KEY'],
        //                 tileSize: 256,
        //                 maxzoom: 14
        //             }
        //         },
        //         layers: [
        //             {
        //                 id: 'osm-layer',
        //                 type: 'raster',
        //                 source: 'osm'
        //             }
        //         ],
        //         terrain: {
        //             source: 'terrainSource',
        //             exaggeration: 1.5 // посилення рельєфу
        //         },
        //         // ✅ Hillshading для підсилення візуального рельєфу
        //         layers: [
        //             {
        //                 id: 'hillshade',
        //                 type: 'hillshade',
        //                 source: 'terrainSource',
        //                 layout: { visibility: 'visible' },
        //                 paint: {
        //                     'hillshade-exaggeration': 0.7
        //                 }
        //             },
        //             {
        //                 id: 'osm-layer',
        //                 type: 'raster',
        //                 source: 'osm'
        //             }
        //         ]
        //     },
        //     center: center,
        //     zoom: zoom,
        //     pitch: 60,   // 🔄 Нахил камери для 3D вигляду
        //     bearing: 20  // Оберт карти
        // });

        // // Після завантаження
        // map.on('load', async () => {
        //     // Джерело для ліній пострілів
        //     map.addSource('shots', {
        //         type: 'geojson',
        //         data: { type: 'FeatureCollection', features: [] }
        //     });

        //     // Шар для відображення ліній
        //     map.addLayer({
        //         id: 'shots-layer',
        //         type: 'line',
        //         source: 'shots',
        //         paint: {
        //             'line-color': ['get', 'color'],
        //             'line-width': 2,
        //             'line-opacity': ['get', 'opacity']
        //         }
        //     });

        //     // Початкове оновлення
        //     await updateUnits();

        //     // Опціонально: візуалізація анімації або flyTo
        //     // map.flyTo({ pitch: 75, bearing: 45, duration: 4000 });
        // });

        
        // Initialize MapLibre map
        map = new maplibregl.Map({
            container: 'map',
            style: {
                version: 8,
                sources: {
                    'osm': {
                        type: 'raster',
                        tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
                        tileSize: 256,
                        attribution: '© OpenStreetMap contributors'
                    }
                },
                layers: [{
                    id: 'osm-layer',
                    type: 'raster',
                    source: 'osm'
                }]
            },
            center: center,
            zoom: zoom
        });
        
        map.on('load', async () => {
            // Add source for shot lines
            map.addSource('shots', {
                type: 'geojson',
                data: { type: 'FeatureCollection', features: [] }
            });
            
            map.addLayer({
                id: 'shots-layer',
                type: 'line',
                source: 'shots',
                paint: {
                    'line-color': ['get', 'color'],
                    'line-width': 2,
                    'line-opacity': ['get', 'opacity']
                }
            });
            
            // Load initial state
            await updateUnits();
        });
        
    } catch (error) {
        console.error('Error initializing map:', error);
    }
}

// Create custom marker with icon and HP bar
function createUnitElement(unit) {
    const el = document.createElement('div');
    el.className = 'unit-marker';
    el.setAttribute('data-unit-id', unit.id);
    
    const side = unit.side;
    const borderColor = side === 'A' ? '#0066ff' : '#ff3333';
    const hpPercent = unit.hp_percent;
    const hpColor =
        unit.side === 'A'
            ? hpPercent > 60
            ? '#66b3ff'
            : hpPercent > 25
                ? '#3399ff'
                : '#0066cc'
            : hpPercent > 60
            ? '#ff6666'
            : hpPercent > 25
                ? '#ff4d4d'
                : '#e60000';
    
    el.innerHTML = `
        <img src="${ICON_PATHS[unit.type] || ICON_PATHS['tank']}"  
            class="unit-icon" 
            alt="${unit.type}"
            style="opacity: ${unit.is_alive ? 1 : 0.3}">
        <div class="hp-bar-container">
            <div class="hp-bar" style="width: ${hpPercent}%; background-color: ${hpColor};"></div>
        </div>
        <div class="hp-text">${Math.round(unit.hp)}/${unit.max_hp}</div>
    `;
    
    // Add click handler
    el.addEventListener('click', (e) => {
        e.stopPropagation();
        showUnitPopup(unit);
    });
    
    return el;
}

// Update unit marker element (without recreating the marker)
function updateUnitElement(marker, unit) {
    const el = marker.getElement();
    if (!el) return;
    
    const side = unit.side;
    const borderColor = side === 'A' ? '#0066ff' : '#ff3333';
    const hpPercent = unit.hp_percent;
    const hpColor =
        unit.side === 'A'
            ? hpPercent > 60
            ? '#66b3ff'
            : hpPercent > 25
                ? '#3399ff'
                : '#0066cc'
            : hpPercent > 60
            ? '#ff6666'
            : hpPercent > 25
                ? '#ff4d4d'
                : '#e60000';
    
    // Update innerHTML
    el.innerHTML = `
        <img src="${ICON_PATHS[unit.type]}" 
            class="unit-icon" 
            alt="${unit.type}">
        <div class="hp-bar-container">
            <div class="hp-bar" style="width: ${hpPercent}%; background-color: ${hpColor};"></div>
        </div>
        <div class="hp-text">${Math.round(unit.hp)}/${unit.max_hp}</div>
    `;
    
    // Re-attach click handler (important!)
    el.onclick = (e) => {
        e.stopPropagation();
        showUnitPopup(unit);
    };
}

// Update units on map
async function updateUnits() {
    try {
        const response = await fetch('/api/state');
        const result = await response.json();
        
        if (result.status === 'success') {
            const units = result.data.features;
            const events = result.data.events || [];
            
            // Track which units are still alive
            const currentUnitIds = new Set(units.map(f => f.properties.id));

            // Update or create markers for each unit
            units.forEach(feature => {
                const unit = feature.properties;
                const coords = feature.geometry.coordinates;
                
                if (unitMarkers.has(unit.id)) {
                    // Update existing marker
                    const marker = unitMarkers.get(unit.id);
                    marker.setLngLat(coords);
                    updateUnitElement(marker, unit);
                    
                } else {
                    // Create new marker
                    const el = createUnitElement(unit);
                    const marker = new maplibregl.Marker({ element: el })
                        .setLngLat(coords)
                        .addTo(map);
                    unitMarkers.set(unit.id, marker);
                }
            });
            
            // Find destroyed units (units that were alive but now missing)
            const destroyedInThisStep = [];
            unitMarkers.forEach((marker, id) => {
                if (!currentUnitIds.has(id) && !destroyedUnits.has(id)) {
                    destroyedInThisStep.push({ id, marker });
                    destroyedUnits.add(id);
                }
            });
            
            // Animate destruction and remove markers
            destroyedInThisStep.forEach(({ id, marker }) => {
                const coords = marker.getLngLat();
                
                // Trigger explosion animation
                animateExplosion([coords.lng, coords.lat]);
                
                // Remove marker after short delay
                setTimeout(() => {
                    marker.remove();
                    unitMarkers.delete(id);
                }, 1500);
            });
            
            // Animate combat events
            if (events.length > 0) {
                animateCombatEvents(events);
            }
            
            updateStatistics(result.statistics);
            updateInfo(result);
        }
    } catch (error) {
        console.error('Error updating units:', error);
    }
}

// Animate combat events (shots)
function animateCombatEvents(events) {
    const shotFeatures = [];
    
    events.forEach((event, idx) => {
        if (event.type === 'shot' || event.type === 'hit') {
            const color = event.success ? '#ff0000' : '#ffff00';
            const opacity = event.success ? 0.8 : 0.4;
            
            shotFeatures.push({
                type: 'Feature',
                geometry: {
                    type: 'LineString',
                    coordinates: [event.attacker_pos, event.target_pos]
                },
                properties: {
                    color: color,
                    opacity: opacity,
                    index: idx
                }
            });
        }
    });
    
    // Show shot lines
    if (shotFeatures.length > 0) {
        map.getSource('shots').setData({
            type: 'FeatureCollection',
            features: shotFeatures
        });
        
        // Fade out after delay
        setTimeout(() => {
            const fadeFeatures = shotFeatures.map(f => ({
                ...f,
                properties: { ...f.properties, opacity: 0 }
            }));
            map.getSource('shots').setData({
                type: 'FeatureCollection',
                features: fadeFeatures
            });
            
            // Clear completely
            setTimeout(() => {
                map.getSource('shots').setData({
                    type: 'FeatureCollection',
                    features: []
                });
            }, 500);
        }, 300);
    }
}

// Animate explosion
function animateExplosion(coords) {
    const el = document.createElement('div');
    el.className = 'explosion';
    el.innerHTML = '💥';
    
    const marker = new maplibregl.Marker({ element: el })
        .setLngLat(coords)
        .addTo(map);
    
    // Animate and remove
    setTimeout(() => {
        el.classList.add('exploding');
    }, 10);
    
    setTimeout(() => {
        marker.remove();
    }, 1000);
}

// Show unit popup
function showUnitPopup(unit) {
    const coords = unitMarkers.get(unit.id).getLngLat();
    
    const popupContent = `
        <div style="font-family: Arial; font-size: 12px;">
            <h3 style="margin: 0 0 8px 0; color: ${unit.side === 'A' ? '#0066ff' : '#ff3333'};">
                ${unit.name}
            </h3>
            <div><strong>Side:</strong> ${unit.side}</div>
            <div><strong>Type:</strong> ${unit.type}</div>
            <div><strong>HP:</strong> ${Math.round(unit.hp)}/${unit.max_hp} (${unit.hp_percent}%)</div>
            <div><strong>Kills:</strong> ${unit.kills}</div>
            <div><strong>Accuracy:</strong> ${unit.accuracy_percent}% 
                 (${unit.hits_landed}/${unit.shots_fired})</div>
            ${unit.personnel_count > 0 ? `<div><strong>Personnel:</strong> ${unit.personnel_count}</div>` : ''}
            <div><strong>Has Target:</strong> ${unit.has_target ? 'Yes' : 'No'}</div>
        </div>
    `;
    
    new maplibregl.Popup()
        .setLngLat([coords.lng, coords.lat])
        .setHTML(popupContent)
        .addTo(map);
}

// Execute one simulation step
async function stepSimulation() {
    try {
        const response = await fetch('/api/step', { method: 'POST' });
        const result = await response.json();
        
        if (result.status === 'success') {
            console.log(`Step ${result.step}: A=${result.statistics.sides.A.alive}, B=${result.statistics.sides.B.alive}`);
            if (result.data.events && result.data.events.length > 0) {
                console.log(`Events: ${result.data.events.length}`);
            }
            await updateUnits();
            
            if (!result.running && autoplay) {
                toggleAutoplay();
                showFinalStatistics(result.statistics);
            }
        }
    } catch (error) {
        console.error('Error stepping simulation:', error);
    }
}

function showFinalStatistics(stats) {
    const sideA = stats.sides.A;
    const sideB = stats.sides.B;
    const winner = sideA.alive > 0 ? 'Side A (Blue)' : 'Side B (Red)';
    
    const message = `
🏆 BATTLE ENDED 🏆

Winner: ${winner}

Side A (Blue):
  Survived: ${sideA.alive}/${sideA.total}
  Kills: ${sideA.total_kills}
  Accuracy: ${sideA.accuracy}%

Side B (Red):
  Survived: ${sideB.alive}/${sideB.total}
  Kills: ${sideB.total_kills}
  Accuracy: ${sideB.accuracy}%
    `;
    
    alert(message);
}

// Toggle autoplay
function toggleAutoplay() {
    autoplay = !autoplay;
    const btn = document.getElementById('playBtn');
    
    if (autoplay) {
        btn.textContent = '⏸️ Pause';
        btn.classList.add('playing');
        const speed = parseInt(document.getElementById('speed').value);
        intervalId = setInterval(stepSimulation, speed);
    } else {
        btn.textContent = '▶️ Play';
        btn.classList.remove('playing');
        if (intervalId) clearInterval(intervalId);
    }
}

// Reset simulation
async function resetSimulation() {
    if (autoplay) toggleAutoplay();
    
    // Clear all markers
    unitMarkers.forEach(marker => marker.remove());
    unitMarkers.clear();
    destroyedUnits.clear();
        
    // Clear shot lines
    if (map.getSource('shots')) {
        map.getSource('shots').setData({
            type: 'FeatureCollection',
            features: []
        });
    }

    try {
        const response = await fetch('/api/reset', { method: 'POST' });
        const result = await response.json();
        
        if (result.status === 'success') {
            await updateUnits();
        }
    } catch (error) {
        console.error('Error resetting simulation:', error);
    }
}

// Update statistics display
function updateStatistics(stats) {
    if (!stats) return;
    
    const statsContent = document.getElementById('statsContent');
    
    let html = '';
    
    // Side A
    const sideA = stats.sides.A;
    html += `
        <div class="stat-section side-a">
            <h3><span class="side-indicator"></span>Side A (Blue)</h3>
            <div class="stat-row">
                <span class="stat-label">Alive:</span>
                <span class="stat-value ${sideA.alive > sideA.total * 0.7 ? 'stat-good' : sideA.alive > sideA.total * 0.3 ? 'stat-warning' : 'stat-danger'}">
                    ${sideA.alive}/${sideA.total}
                </span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Destroyed:</span>
                <span class="stat-value">${sideA.destroyed}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Kills:</span>
                <span class="stat-value">${sideA.total_kills}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Accuracy:</span>
                <span class="stat-value">${sideA.accuracy}%</span>
            </div>
        </div>
    `;
    
    // Side B
    const sideB = stats.sides.B;
    html += `
        <div class="stat-section side-b">
            <h3><span class="side-indicator"></span>Side B (Red)</h3>
            <div class="stat-row">
                <span class="stat-label">Alive:</span>
                <span class="stat-value ${sideB.alive > sideB.total * 0.7 ? 'stat-good' : sideB.alive > sideB.total * 0.3 ? 'stat-warning' : 'stat-danger'}">
                    ${sideB.alive}/${sideB.total}
                </span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Destroyed:</span>
                <span class="stat-value">${sideB.destroyed}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Kills:</span>
                <span class="stat-value">${sideB.total_kills}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Accuracy:</span>
                <span class="stat-value">${sideB.accuracy}%</span>
            </div>
        </div>
    `;
    
    statsContent.innerHTML = html;
}

// Update info bar
function updateInfo(result) {
    document.getElementById('stepCount').textContent = result.step || 0;
    document.getElementById('simStatus').textContent = result.running ? 'Running' : 'Stopped';
}

// Speed slider handler
document.getElementById('speed').addEventListener('input', (e) => {
    const value = e.target.value;
    document.getElementById('speedValue').textContent = value + 'ms';
    
    if (autoplay) {
        clearInterval(intervalId);
        intervalId = setInterval(stepSimulation, parseInt(value));
    }
});

// Initialize when page loads
window.addEventListener('load', initMap);

// Make functions global
window.stepSimulation = stepSimulation;
window.toggleAutoplay = toggleAutoplay;
window.resetSimulation = resetSimulation;