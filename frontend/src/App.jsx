import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './App.css';

const BICING_API =
  'https://api.bsmsa.eu/featureserver/OMSBicing/NOU_ESTACIONS?request=GetFeature&typeName=OMSBicing:NOU_ESTACIONS&outputFormat=application/json';

const fallbackStations = [
  { id: '1', name: 'Plaça de Catalunya', lat: 41.387015, lon: 2.170047, bikes: 12, slots: 8 },
  { id: '2', name: 'Passeig de Gràcia', lat: 41.391055, lon: 2.165064, bikes: 5, slots: 15 },
  { id: '3', name: 'Sagrada Família', lat: 41.403629, lon: 2.174356, bikes: 0, slots: 20 },
  { id: '4', name: 'Camp Nou', lat: 41.380896, lon: 2.12282, bikes: 7, slots: 10 },
  { id: '5', name: 'Barceloneta', lat: 41.380729, lon: 2.18985, bikes: 3, slots: 17 },
  { id: '6', name: 'Arc de Triomf', lat: 41.391052, lon: 2.180644, bikes: 9, slots: 6 },
  { id: '7', name: "Plaça d'Espanya", lat: 41.374962, lon: 2.149805, bikes: 2, slots: 18 },
  { id: '8', name: 'Glòries', lat: 41.402235, lon: 2.188346, bikes: 6, slots: 12 },
];

const toStations = (geojson) => {
  if (!geojson?.features) return [];
  return geojson.features
    .map((f) => ({
      id: f.properties.id?.toString() || f.id,
      name: f.properties.name || 'Estación Bicing',
      lat: f.geometry?.coordinates?.[1],
      lon: f.geometry?.coordinates?.[0],
      bikes: f.properties.bikes ?? f.properties.bicis_disponibles ?? 0,
      slots: f.properties.slots ?? f.properties.docks_disponibles ?? 0,
    }))
    .filter((s) => s.lat && s.lon);
};

function App() {
  const [stations, setStations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(BICING_API)
      .then((res) => res.json())
      .then((data) => {
        const parsed = toStations(data);
        setStations(parsed.length ? parsed : fallbackStations);
      })
      .catch(() => setStations(fallbackStations))
      .finally(() => setLoading(false));
  }, []);

  const markerColor = (bikes) => (bikes > 0 ? '#2e7d32' : '#c62828');

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Bicing cerca de mí</h1>
        <p>Mapa interactivo de estaciones de bicicletas públicas de Barcelona</p>
      </header>
      <main className="map-container">
        {loading && <div className="loading">Cargando estaciones...</div>}
        <MapContainer
          center={[41.3851, 2.1734]}
          zoom={13}
          minZoom={11}
          maxZoom={18}
          scrollWheelZoom
          className="map"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          />
          {stations.map((s) => (
            <CircleMarker
              key={s.id}
              center={[s.lat, s.lon]}
              radius={7}
              pathOptions={{
                fillColor: markerColor(s.bikes),
                color: '#ffffff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.9,
              }}
            >
              <Popup>
                <div className="popup-content">
                  <strong>{s.name}</strong>
                  <span className={s.bikes > 0 ? 'available' : 'empty'}>
                    Bicis: {s.bikes}
                  </span>
                  <span>Anclajes libres: {s.slots}</span>
                </div>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </main>
      <footer className="dashboard-footer">
        Datos de prueba · Barcelona · Tema verde Bicing
      </footer>
    </div>
  );
}

export default App;
