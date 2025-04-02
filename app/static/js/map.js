/**
 * WeaRisk - Module de carte des risques climatiques
 * Affiche une carte interactive de la France avec coloration des départements 
 * en fonction des niveaux de risque.
 */

// Configuration et variables globales
const RiskMapConfig = {
    // Paramètres de la carte
    mapCenter: [46.8, 2.5],
    mapZoom: 6,
    tileLayerUrl: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    tileLayerAttribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    
    // URL pour les données
    geoJsonUrl: 'https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements.geojson',
    apiUrl: '/api/map-data',
    
    // Seuils de risque pour la coloration
    riskThresholds: [0, 10, 30, 50, 70, 90],
    riskColors: ['#91cf60', '#d9ef8b', '#fee08b', '#fc8d59', '#d73027', '#b10026'],
    
    // Noms des types de risque pour l'affichage
    riskTypeLabels: {
        'overall_risk': 'Risque Global',
        'electrical_risk': 'Risque Électrique',
        'flood_risk': 'Risque d\'Inondation',
        'heat_risk': 'Risque de Chaleur',
        'wind_risk': 'Risque de Vent'
    }
};

// État de l'application
const RiskMapState = {
    map: null,
    geojsonLayer: null,
    info: null,
    legend: null,
    currentRiskType: 'overall_risk',
    currentTimestamp: 'latest',
    departmentsData: {},
    usingRealData: false
};

/**
 * Point d'entrée principal - Initialise la carte
 */
function initMap() {
    // Créer la carte centrée sur la France
    RiskMapState.map = L.map('map-container').setView(
        RiskMapConfig.mapCenter, 
        RiskMapConfig.mapZoom
    );
    
    // Ajouter la couche de fond (tiles)
    L.tileLayer(
        RiskMapConfig.tileLayerUrl, 
        { attribution: RiskMapConfig.tileLayerAttribution }
    ).addTo(RiskMapState.map);
    
    // Ajouter les contrôles d'information
    addInfoControl();
    addLegend();
    
    // Charger les données GeoJSON
    loadGeoJSONData();
}

/**
 * Ajoute le panneau d'information qui apparaît lors du survol d'un département
 */
function addInfoControl() {
    RiskMapState.info = L.control();
    
    RiskMapState.info.onAdd = function(map) {
        this._div = L.DomUtil.create('div', 'info-panel');
        this.update();
        return this._div;
    };
    
    RiskMapState.info.update = function(props) {
        if (props) {
            const deptCode = props.code;
            const deptData = RiskMapState.departmentsData[deptCode];
            
            let content = `<h4>${props.nom}</h4>`;
            
            if (deptData) {
                const getValueWithDefault = (value) => 
                    value !== undefined ? parseFloat(value).toFixed(1) + '%' : 'N/A';
                
                const getRiskClass = value => 
                    value > 70 ? 'high' : (value > 30 ? 'medium' : 'low');
                
                content += `
                    <div class="risk-value">⚡ Risque électrique: <span class="risk-level ${getRiskClass(deptData.electrical_risk)}">${getValueWithDefault(deptData.electrical_risk)}</span></div>
                    <div class="risk-value">🌊 Risque d'inondation: <span class="risk-level ${getRiskClass(deptData.flood_risk)}">${getValueWithDefault(deptData.flood_risk)}</span></div>
                    <div class="risk-value">🔥 Risque de chaleur: <span class="risk-level ${getRiskClass(deptData.heat_risk)}">${getValueWithDefault(deptData.heat_risk)}</span></div>
                    <div class="risk-value">🌬️ Risque de vent: <span class="risk-level ${getRiskClass(deptData.wind_risk)}">${getValueWithDefault(deptData.wind_risk)}</span></div>
                    <div class="risk-value">📊 Risque global: <span class="risk-level ${getRiskClass(deptData.overall_risk)}">${getValueWithDefault(deptData.overall_risk)}</span></div>
                `;
                
                if (!RiskMapState.usingRealData) {
                    content += '<small><i>Données simulées</i></small>';
                }
            } else {
                content += '<p>Aucune donnée disponible pour ce département</p>';
            }
            
            this._div.innerHTML = content;
        } else {
            this._div.innerHTML = '<p>Survolez un département</p>';
        }
    };
    
    RiskMapState.info.addTo(RiskMapState.map);
}

/**
 * Ajoute la légende des niveaux de risque
 */
function addLegend() {
    RiskMapState.legend = L.control({position: 'bottomright'});
    
    RiskMapState.legend.onAdd = function(map) {
        const div = L.DomUtil.create('div', 'info-legend');
        const title = RiskMapConfig.riskTypeLabels[RiskMapState.currentRiskType];
        
        div.innerHTML = `<h4>${title}</h4>`;
        
        // Générer les étiquettes pour chaque intervalle de risque
        for (let i = 0; i < RiskMapConfig.riskThresholds.length; i++) {
            const from = RiskMapConfig.riskThresholds[i];
            const to = RiskMapConfig.riskThresholds[i + 1];
            
            div.innerHTML +=
                '<i style="background:' + getColor(from + 1) + '"></i> ' +
                from + (to ? '&ndash;' + to + '%<br>' : '%+');
        }
        
        return div;
    };
    
    RiskMapState.legend.addTo(RiskMapState.map);
}

/**
 * Charge les contours des départements français (GeoJSON)
 */
function loadGeoJSONData() {
    fetch(RiskMapConfig.geoJsonUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erreur HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Une fois les contours chargés, on charge les données de risque
            document.getElementById('loading').style.display = 'none';
            loadRiskData(data);
        })
        .catch(error => {
            console.error('Erreur lors du chargement des contours GeoJSON:', error);
            document.getElementById('loading').innerHTML = 
                `<p>Erreur de chargement des contours: ${error.message}</p>
                <button onclick="initMap()" class="btn">Réessayer</button>`;
        });
}

/**
 * Charge les données de risque depuis l'API
 * @param {Object} geoJsonData - Données GeoJSON des contours des départements
 */
function loadRiskData(geoJsonData) {
    const statusMessage = document.getElementById('status-message');
    const apiUrl = constructApiUrl();
    
    // Tentative de récupération des données réelles
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erreur HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Stocker les données
            RiskMapState.departmentsData = {};
            if (data.data && data.data.length > 0) {
                data.data.forEach(dept => {
                    RiskMapState.departmentsData[dept.department_code] = dept;
                });
            } else {
                throw new Error('Aucune donnée de risque disponible');
            }
            
            // Mettre à jour les périodes disponibles
            updateTimestampSelector(data.timestamps, data.current_timestamp);
            
            RiskMapState.usingRealData = true;
            
            // Afficher la carte avec les données
            displayGeoJSON(geoJsonData);
            
            statusMessage.className = 'status-message';
            statusMessage.textContent = 'Utilisation des données réelles.';
            statusMessage.style.display = 'block';
        })
        .catch(error => {
            console.error('Erreur lors du chargement des données de risque:', error);
            
            // Générer des données factices pour chaque département
            RiskMapState.departmentsData = {};
            geoJsonData.features.forEach(feature => {
                const code = feature.properties.code;
                RiskMapState.departmentsData[code] = {
                    department_code: code,
                    department_name: feature.properties.nom,
                    electrical_risk: Math.floor(Math.random() * 100),
                    flood_risk: Math.floor(Math.random() * 100),
                    heat_risk: Math.floor(Math.random() * 100),
                    wind_risk: Math.floor(Math.random() * 100),
                    overall_risk: Math.floor(Math.random() * 100)
                };
            });
            
            RiskMapState.usingRealData = false;
            
            // Afficher la carte avec les données fictives
            displayGeoJSON(geoJsonData);
            
            statusMessage.className = 'status-message warning';
            statusMessage.textContent = `Utilisation de données simulées: ${error.message}`;
            statusMessage.style.display = 'block';
        });
}

/**
 * Construit l'URL de l'API avec les paramètres appropriés
 * @returns {string} URL de l'API
 */
function constructApiUrl() {
    let url = `${RiskMapConfig.apiUrl}?risk_type=${RiskMapState.currentRiskType}`;
    
    if (RiskMapState.currentTimestamp !== 'latest') {
        url += `&timestamp=${RiskMapState.currentTimestamp}`;
    }
    
    return url;
}

/**
 * Met à jour le sélecteur de période avec les timestamps disponibles
 * @param {Array} timestamps - Liste des timestamps disponibles
 * @param {string} currentTimestamp - Timestamp actuel
 */
function updateTimestampSelector(timestamps, currentTimestamp) {
    const select = document.getElementById('timestamp-select');
    select.innerHTML = '';
    
    // Option par défaut
    const defaultOption = document.createElement('option');
    defaultOption.value = 'latest';
    defaultOption.text = 'Données les plus récentes';
    select.appendChild(defaultOption);
    
    // Ajouter les timestamps disponibles
    if (timestamps && timestamps.length > 0) {
        timestamps.forEach(timestamp => {
            const option = document.createElement('option');
            option.value = timestamp;
            option.text = formatTimestamp(timestamp);
            option.selected = timestamp === currentTimestamp;
            select.appendChild(option);
        });
    }
}

/**
 * Formate un timestamp pour l'affichage
 * @param {string} timestamp - Timestamp à formater
 * @returns {string} Timestamp formaté
 */
function formatTimestamp(timestamp) {
    try {
        const date = new Date(timestamp);
        const day = date.getDate().toString().padStart(2, '0');
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const hours = date.getHours().toString().padStart(2, '0');
        const minutes = date.getMinutes().toString().padStart(2, '0');
        
        return `${day}/${month} ${hours}h${minutes}`;
    } catch (e) {
        return timestamp;
    }
}

/**
 * Affiche les données GeoJSON sur la carte
 * @param {Object} geoJsonData - Données GeoJSON des contours des départements
 */
function displayGeoJSON(geoJsonData) {
    if (RiskMapState.geojsonLayer) {
        RiskMapState.map.removeLayer(RiskMapState.geojsonLayer);
    }
    
    RiskMapState.geojsonLayer = L.geoJSON(geoJsonData, {
        style: styleFeature,
        onEachFeature: onEachFeature
    }).addTo(RiskMapState.map);
    
    // Mettre à jour la légende
    RiskMapState.map.removeControl(RiskMapState.legend);
    addLegend();
}

/**
 * Définit le style pour chaque département
 * @param {Object} feature - Feature GeoJSON représentant un département
 * @returns {Object} Style à appliquer au département
 */
function styleFeature(feature) {
    const deptCode = feature.properties.code;
    const deptData = RiskMapState.departmentsData[deptCode];
    
    let riskValue = 0;
    if (deptData && deptData[RiskMapState.currentRiskType] !== undefined) {
        riskValue = parseFloat(deptData[RiskMapState.currentRiskType]);
    }
    
    return {
        fillColor: getColor(riskValue),
        weight: 1,
        opacity: 1,
        color: 'white',
        dashArray: '3',
        fillOpacity: 0.7
    };
}

/**
 * Détermine la couleur en fonction du niveau de risque
 * @param {number} value - Valeur de risque
 * @returns {string} Code couleur
 */
function getColor(value) {
    const thresholds = RiskMapConfig.riskThresholds;
    const colors = RiskMapConfig.riskColors;
    
    for (let i = thresholds.length - 1; i >= 0; i--) {
        if (value > thresholds[i]) {
            return colors[i];
        }
    }
    
    return colors[0];
}

/**
 * Configure les événements pour chaque département
 * @param {Object} feature - Feature GeoJSON
 * @param {Object} layer - Couche Leaflet
 */
function onEachFeature(feature, layer) {
    layer.on({
        mouseover: highlightFeature,
        mouseout: resetHighlight,
        click: zoomToFeature
    });
}

/**
 * Met en évidence un département au survol
 * @param {Object} e - Événement
 */
function highlightFeature(e) {
    const layer = e.target;
    
    layer.setStyle({
        weight: 3,
        color: '#666',
        dashArray: '',
        fillOpacity: 0.8
    });
    
    if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
        layer.bringToFront();
    }
    
    RiskMapState.info.update(layer.feature.properties);
}

/**
 * Réinitialise le style d'un département
 * @param {Object} e - Événement
 */
function resetHighlight(e) {
    RiskMapState.geojsonLayer.resetStyle(e.target);
    RiskMapState.info.update();
}

/**
 * Zoome sur un département au clic
 * @param {Object} e - Événement
 */
function zoomToFeature(e) {
    RiskMapState.map.fitBounds(e.target.getBounds());
}

/**
 * Met à jour la carte lorsque les filtres changent
 */
function updateMap() {
    const riskTypeSelect = document.getElementById('risk-type');
    const timestampSelect = document.getElementById('timestamp-select');
    
    const newRiskType = riskTypeSelect.value;
    const newTimestamp = timestampSelect.value;
    
    // Si le type de risque ou le timestamp a changé
    if (newRiskType !== RiskMapState.currentRiskType || newTimestamp !== RiskMapState.currentTimestamp) {
        RiskMapState.currentRiskType = newRiskType;
        RiskMapState.currentTimestamp = newTimestamp;
        
        // Afficher l'indicateur de chargement
        document.getElementById('loading').style.display = 'block';
        
        // Si on utilise des données réelles, recharger les données
        if (RiskMapState.usingRealData) {
            const apiUrl = constructApiUrl();
            
            fetch(apiUrl)
                .then(response => response.json())
                .then(data => {
                    // Stocker les données
                    RiskMapState.departmentsData = {};
                    if (data.data && data.data.length > 0) {
                        data.data.forEach(dept => {
                            RiskMapState.departmentsData[dept.department_code] = dept;
                        });
                    }
                    
                    // Mettre à jour la carte
                    if (RiskMapState.geojsonLayer) {
                        RiskMapState.geojsonLayer.setStyle(styleFeature);
                        RiskMapState.map.removeControl(RiskMapState.legend);
                        addLegend();
                    }
                    
                    document.getElementById('loading').style.display = 'none';
                })
                .catch(error => {
                    console.error('Erreur lors de la mise à jour des données:', error);
                    document.getElementById('loading').style.display = 'none';
                });
        } else {
            // Si on utilise des données factices, simplement mettre à jour la carte
            if (RiskMapState.geojsonLayer) {
                RiskMapState.geojsonLayer.setStyle(styleFeature);
                RiskMapState.map.removeControl(RiskMapState.legend);
                addLegend();
            }
            document.getElementById('loading').style.display = 'none';
        }
    }
}

// Initialiser la carte au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    initMap();
    
    // Ajouter des écouteurs d'événements pour les contrôles
    document.getElementById('risk-type').addEventListener('change', updateMap);
    document.getElementById('timestamp-select').addEventListener('change', updateMap);
});