import { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Tooltip, useMap } from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-cluster';
import { divIcon } from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import './App.css';

const INFORMACION_API = 'http://127.0.0.1:5000/api/informacion';

const fallbackStations = [
  { id: '1', name: 'Plaça de Catalunya', lat: 41.387015, lon: 2.170047, capacity: 20, postCode: '08002' },
  { id: '2', name: 'Passeig de Gràcia', lat: 41.391055, lon: 2.165064, capacity: 15, postCode: '08007' },
  { id: '3', name: 'Sagrada Família', lat: 41.403629, lon: 2.174356, capacity: 20, postCode: '08013' },
  { id: '4', name: 'Camp Nou', lat: 41.380896, lon: 2.12282, capacity: 17, postCode: '08028' },
  { id: '5', name: 'Barceloneta', lat: 41.380729, lon: 2.18985, capacity: 20, postCode: '08003' },
  { id: '6', name: 'Arc de Triomf', lat: 41.391052, lon: 2.180644, capacity: 15, postCode: '08018' },
  { id: '7', name: "Plaça d'Espanya", lat: 41.374962, lon: 2.149805, capacity: 20, postCode: '08015' },
  { id: '8', name: 'Glòries', lat: 41.402235, lon: 2.188346, capacity: 18, postCode: '08013' },
];

// Área metropolitana de Barcelona (con margen). Sirve para descartar
// estaciones con coordenadas erróneas o de pruebas (p. ej. entradas de test
// en la base de datos con lat/lon de otra ciudad), que de otro modo
// aparecerían como marcadores sueltos fuera del mapa real.
const BCN_BOUNDS = { minLat: 41.15, maxLat: 41.55, minLon: 1.9, maxLon: 2.35 };

// Convierte el objeto { "<station_id>": { address, capacity, latitud, longitud, post_code } }
// devuelto por la API en un array de estaciones fácil de renderizar en el mapa.
const toStations = (data) => {
  if (!data || typeof data !== 'object') return [];
  return Object.entries(data)
    .map(([id, info]) => ({
      id,
      name: info.address || `Estación ${id}`,
      lat: info.latitud,
      lon: info.longitud,
      capacity: info.capacity,
      postCode: info.post_code,
    }))
    .filter(
      (s) =>
        typeof s.lat === 'number' &&
        typeof s.lon === 'number' &&
        s.lat >= BCN_BOUNDS.minLat &&
        s.lat <= BCN_BOUNDS.maxLat &&
        s.lon >= BCN_BOUNDS.minLon &&
        s.lon <= BCN_BOUNDS.maxLon,
    );
};

// Icono tipo "pin globo" rosa, similar a un marcador de estación de bicis.
const bikeStationIcon = divIcon({
  className: 'bike-marker',
  html: `
    <div class="bike-marker-head">
      <span class="bike-marker-dot"></span>
    </div>
    <div class="bike-marker-stem"></div>
    <div class="bike-marker-shadow"></div>
  `,
  iconSize: [26, 38],
  iconAnchor: [13, 36],
  popupAnchor: [0, -34],
});

// Icono de "clúster" (grupo de estaciones cercanas) a bajo zoom, con el
// mismo tema rosa/verde Bicing. El tamaño crece ligeramente con el nº de
// estaciones agrupadas para dar una pista visual de densidad.
const createClusterIcon = (cluster) => {
  const count = cluster.getChildCount();
  const size = count < 10 ? 36 : count < 50 ? 44 : 52;
  return divIcon({
    html: `<div class="cluster-bubble" style="width:${size}px;height:${size}px;">${count}</div>`,
    className: 'bike-cluster',
    iconSize: [size, size],
  });
};

// Leaflet mide el tamaño de su contenedor al montarse. Dentro de un layout
// flexbox (header + mapa + footer) ese tamaño puede terminar de resolverse
// después de que el mapa ya se inicializó, desalineando tiles y marcadores
// (más visible al reducir el zoom). Este componente fuerza un recálculo
// (`invalidateSize`) cada vez que el contenedor cambia de tamaño.
function MapResizeHandler() {
  const map = useMap();
  const containerRef = useRef(null);

  useEffect(() => {
    containerRef.current = map.getContainer();

    // Recalcula en cuanto el contenedor obtiene su tamaño final.
    map.invalidateSize();

    const handleResize = () => map.invalidateSize();

    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(containerRef.current);
    window.addEventListener('resize', handleResize);

    return () => {
      resizeObserver.disconnect();
      window.removeEventListener('resize', handleResize);
    };
  }, [map]);

  return null;
}

function App() {
  const [stations, setStations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(INFORMACION_API)
      .then((res) => res.json())
      .then((data) => {
        const parsed = toStations(data);
        setStations(parsed.length ? parsed : fallbackStations);
      })
      .catch(() => setStations(fallbackStations))
      .finally(() => setLoading(false));
  }, []);

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
          maxBounds={[
            [BCN_BOUNDS.minLat, BCN_BOUNDS.minLon],
            [BCN_BOUNDS.maxLat, BCN_BOUNDS.maxLon],
          ]}
          maxBoundsViscosity={1.0}
          scrollWheelZoom
          className="map"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
          />
          <MapResizeHandler />
          <MarkerClusterGroup
            iconCreateFunction={createClusterIcon}
            maxClusterRadius={60}
            spiderfyOnMaxZoom
            showCoverageOnHover={false}
          >
            {stations.map((s) => (
              <Marker key={s.id} position={[s.lat, s.lon]} icon={bikeStationIcon}>
                <Tooltip direction="top" offset={[0, -30]} opacity={1}>
                  <div className="tooltip-content">
                    <span>
                      <strong>Dirección:</strong> {s.name}
                    </span>
                    {s.postCode && (
                      <span>
                        <strong>Código postal:</strong> {s.postCode}
                      </span>
                    )}
                  </div>
                </Tooltip>
                <Popup>
                  <div className="popup-content">
                    <strong>{s.name}</strong>
                    <span>Capacidad: {s.capacity} anclajes</span>
                    {s.postCode && <span>CP: {s.postCode}</span>}
                  </div>
                </Popup>
              </Marker>
            ))}
          </MarkerClusterGroup>
        </MapContainer>
      </main>
      <footer className="dashboard-footer">
        Datos en vivo de la API de estaciones · Barcelona · Tema Bicing
      </footer>
    </div>
  );
}

export default App;
