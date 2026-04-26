import { MapContainer, TileLayer, Marker, Popup, Polyline, CircleMarker, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default marker icons in Leaflet
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: markerIcon2x,
    iconUrl: markerIcon,
    shadowUrl: markerShadow,
});

const LocationMarker = ({ setStartPoint }) => {
    useMapEvents({
        click(e) {
            setStartPoint([e.latlng.lat, e.latlng.lng]);
        },
    });
    return null;
};

const MapView = ({ startPoint, setStartPoint, routePath, hospitals, chosenHospital, blockedPoints = [] }) => {
    const center = [3.848, 11.502];

    const hospitalIcon = (isAvailable) => new L.Icon({
        iconUrl: isAvailable
            ? 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2-green.png'
            : 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2-red.png',
        shadowUrl: markerShadow,
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });

    const startIcon = new L.Icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2-gold.png',
        shadowUrl: markerShadow,
        iconSize: [25, 41],
        iconAnchor: [12, 41],
    });

    return (
        <MapContainer center={center} zoom={13} className="h-full w-full rounded-xl shadow-inner scrollbar-hide">
            <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            <LocationMarker setStartPoint={setStartPoint} />

            {startPoint && (
                <Marker position={startPoint} icon={startIcon}>
                    <Popup>Point de départ de l'urgence</Popup>
                </Marker>
            )}

            {hospitals.map(h => (
                <Marker
                    key={h.id}
                    position={[h.lat, h.lng]}
                    icon={hospitalIcon(h.urgences_disponibles)}
                >
                    <Popup>
                        <div className="font-bold">{h.name}</div>
                        <div>Attente: {h.temps_attente_min} min</div>
                        <div>Status: {h.urgences_disponibles ? 'Disponible' : 'Saturé'}</div>
                    </Popup>
                </Marker>
            ))}

            {routePath && (
                <Polyline pathOptions={{ color: '#ef4444', weight: 5, opacity: 0.8 }} positions={routePath} />
            )}

            {blockedPoints.map((pos, idx) => (
                <CircleMarker
                    key={`blocked-${idx}`}
                    center={pos}
                    radius={10}
                    pathOptions={{ color: 'red', fillColor: 'red', fillOpacity: 0.6 }}
                >
                    <Popup>Obstacle détecté (Twist 04)</Popup>
                </CircleMarker>
            ))}
        </MapContainer>
    );
};

export default MapView;
