import json
import pandas as pd


# 1. Read Excel data
excel_file = '/Users/bbae/GPTCodex/List 17 Strategic Provinces.xlsx'
df = pd.read_excel(excel_file, sheet_name='Sheet1')

# Extract BMA, EEC, Strategic
strategic_df = df[df['BMA_EEC_Strategic'] != 'Non-Strategic']
strategic_provinces = strategic_df['Province'].str.title().tolist()
# Clean up some names to match GeoJSON (e.g., 'Bangkok' instead of 'Bangkok Metropolis')
strategic_provinces = [p.replace('Buri', 'Buri').strip() for p in strategic_provinces]
# Hardcode known strategic provinces from the 17 list to ensure matching
strats = ["Bangkok", "Nonthaburi", "Pathum Thani", "Samut Prakan", "Chachoengsao", "Chon Buri", "Rayong", "Buri Ram", "Chiang Mai", "Chiang Rai", "Nakhon Ratchasima", "Khon Kaen", "Phuket", "Surat Thani", "Songkhla", "Udon Thani", "Nakhon Pathom"]
# We will just use the excel list, but standardize it
strategic_lower = [p.lower().replace(' ', '') for p in strategic_provinces]

# 2. Read GeoJSON
geojson_path = '/Users/bbae/GPTCodex/MAP-L2-Splitter/thailand_provinces.geojson'
with open(geojson_path, 'r', encoding='utf-8') as f:
    geo_data = json.load(f)

# 3. Create the HTML Map Dashboard manually using Leaflet
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XGS-PON vs GPON 3-Year Strategic Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        body { margin: 0; padding: 0; font-family: 'Outfit', sans-serif; background: #fffdf2; color: #333; }
        #map { width: 100vw; height: 100vh; background: #fffdf2; }
        .panel {
            position: absolute; top: 20px; left: 20px; z-index: 1000;
            background: rgba(255, 253, 242, 0.95); backdrop-filter: blur(10px);
            padding: 20px; border-radius: 15px; border: 1px solid rgba(0,0,0,0.1);
            box-shadow: 0 10px 30px rgba(0,0,0,0.1); width: 320px;
        }
        h1 { margin: 0 0 10px 0; font-size: 1.5rem; color: #0284c7; }
        .slider-container { margin-top: 20px; }
        input[type=range] { width: 100%; cursor: pointer; accent-color: #0284c7; }
        .year-display { font-size: 2.5rem; font-weight: 800; color: #1e293b; text-align: center; margin: 10px 0; text-shadow: 0 0 10px rgba(255,255,255,0.8); }
        .legend { margin-top: 20px; font-size: 0.9rem; }
        .legend-item { display: flex; align-items: center; margin-bottom: 8px; color: #334155; }
        .color-box { width: 20px; height: 20px; margin-right: 10px; border-radius: 4px; border: 1px solid rgba(0,0,0,0.1); }
        /* XGS-PON Colors */
        .c-xgs-1 { background: #93c5fd; } /* Y2027 */
        .c-xgs-2 { background: #3b82f6; } /* Y2028 */
        .c-xgs-3 { background: #1e3a8a; } /* Y2029 */
        /* GPON Colors */
        .c-gpon-1 { background: #86efac; } /* Y2027 */
        .c-gpon-2 { background: #22c55e; } /* Y2028 */
        .c-gpon-3 { background: #1e3a8a; } /* Y2029 - Becomes XGS */
    </style>
</head>
<body>

    <div id="map"></div>
    
    <div class="panel">
        <h1>Deployment Strategy</h1>
        <p style="color: #64748b; font-size: 0.85rem; margin-top: -5px;">Strategic 17 Provinces vs 60 Provinces</p>
        
        <div class="slider-container">
            <input type="range" id="yearSlider" min="2027" max="2029" value="2027" step="1">
            <div class="year-display" id="yearText">Y2027</div>
        </div>

        <div class="legend">
            <div style="margin-bottom: 10px; font-weight: bold; border-bottom: 1px solid #cbd5e1; padding-bottom: 5px; color: #0f172a;">XGS-PON (17 Strategic)</div>
            <div class="legend-item"><div class="color-box c-xgs-1" id="l-x-1"></div> <span id="t-x-1">Phase 1 (Preparation)</span></div>
            <div class="legend-item"><div class="color-box c-xgs-2" id="l-x-2"></div> <span id="t-x-2">Phase 2 (Expansion)</span></div>
            <div class="legend-item"><div class="color-box c-xgs-3" id="l-x-3"></div> <span id="t-x-3">Phase 3 (Full Coverage)</span></div>
            
            <div style="margin: 15px 0 10px 0; font-weight: bold; border-bottom: 1px solid #cbd5e1; padding-bottom: 5px; color: #0f172a;">GPON (60 Non-Strategic)</div>
            <div class="legend-item"><div class="color-box c-gpon-1" id="l-g-1"></div> <span id="t-g-1">Sustain & Upgrade</span></div>
            <div class="legend-item"><div class="color-box c-gpon-2" id="l-g-2"></div> <span id="t-g-2">Density Focus</span></div>
            <div class="legend-item"><div class="color-box c-gpon-3" id="l-g-3"></div> <span id="t-g-3">100% XGS-PON Upgraded</span></div>
        </div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const geoData = REPLACE_ME_GEOJSON;
        const strategicList = REPLACE_ME_STRATEGIC;

        const map = L.map('map', {
            zoomControl: false,
            attributionControl: false
        }).setView([13.75, 100.5], 6);

        // Light map tiles
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png', {
            subdomains: 'abcd',
            maxZoom: 20
        }).addTo(map);

        let geojsonLayer;

        function isStrategic(shapeName) {
            let n = shapeName.toLowerCase().replace(' province', '').replace(' ', '');
            for (let s of strategicList) {
                if (n.includes(s) || s.includes(n)) return true;
            }
            if(shapeName.includes("Bangkok")) return true;
            return false;
        }

        function getColor(shapeName, year) {
            let isStrat = isStrategic(shapeName);
            if (isStrat) {
                if (year == 2027) return '#93c5fd';
                if (year == 2028) return '#3b82f6';
                if (year == 2029) return '#1e3a8a';
            } else {
                if (year == 2027) return '#86efac';
                if (year == 2028) return '#22c55e';
                if (year == 2029) return '#1e3a8a'; // Become XGS-PON fully
            }
            return '#ccc';
        }

        function style(feature, year) {
            return {
                fillColor: getColor(feature.properties.shapeName, year),
                weight: 1,
                opacity: 1,
                color: 'rgba(0,0,0,0.15)',
                fillOpacity: 0.85
            };
        }

        function updateMap(year) {
            if (geojsonLayer) {
                map.removeLayer(geojsonLayer);
            }
            
            geojsonLayer = L.geoJson(geoData, {
                style: function(feature) {
                    return style(feature, year);
                },
                onEachFeature: function(feature, layer) {
                    let strat = isStrategic(feature.properties.shapeName) ? "XGS-PON (Strategic)" : "GPON (Standard)";
                    layer.bindTooltip(`<b>${feature.properties.shapeName}</b><br>Tech Focus: ${strat}`, {sticky: true});
                    
                    layer.on({
                        mouseover: function(e) {
                            var layer = e.target;
                            layer.setStyle({ weight: 3, color: '#0f172a', fillOpacity: 1 });
                            if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) { layer.bringToFront(); }
                        },
                        mouseout: function(e) {
                            geojsonLayer.resetStyle(e.target);
                        }
                    });
                }
            }).addTo(map);
        }

        // Init
        updateMap(2027);

        // Slider logic
        const slider = document.getElementById('yearSlider');
        const yearText = document.getElementById('yearText');

        slider.addEventListener('input', function(e) {
            const y = e.target.value;
            yearText.innerText = "Y" + y;
            updateMap(y);
            
            // Highlight legend
            document.querySelectorAll('.color-box').forEach(el => el.style.boxShadow = 'none');
            document.querySelectorAll('.legend-item span').forEach(el => el.style.fontWeight = 'normal');
            
            let idx = y - 2026; // 2027->1, 2028->2, 2029->3
            document.getElementById('l-x-'+idx).style.boxShadow = '0 0 15px #38bdf8';
            document.getElementById('t-x-'+idx).style.fontWeight = 'bold';
            document.getElementById('l-g-'+idx).style.boxShadow = '0 0 15px #4ade80';
            document.getElementById('t-g-'+idx).style.fontWeight = 'bold';
        });

    </script>
</body>
</html>
"""

# Inject JSON data
html_content = html_content.replace('REPLACE_ME_GEOJSON', json.dumps(geo_data))
html_content = html_content.replace('REPLACE_ME_STRATEGIC', json.dumps(strategic_lower))

with open('/Users/bbae/GPTCodex/xgs_pon_map_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("Dashboard created successfully!")
