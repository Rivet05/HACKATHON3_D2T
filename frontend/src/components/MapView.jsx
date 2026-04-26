import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, CircleMarker, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// ... Leaflet Icon Fix ...
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: markerIcon2x,
    iconUrl: markerIcon,
    shadowUrl: markerShadow,
});

const MovingVehicle = ({ path, color = "#3b82f6" }) => {
    const [currentIdx, setCurrentIdx] = useState(0);

    useEffect(() => {
        if (!path || path.length === 0) return;
        const interval = setInterval(() => {
            setCurrentIdx(prev => (prev < path.length - 1 ? prev + 1 : prev));
        }, 200); // Animation speed
        return () => clearInterval(interval);
    }, [path]);

    if (!path || path.length === 0) return null;

    const ambulanceIcon = new L.Icon({
        iconUrl: 'https://cdn-icons-png.flaticon.com/512/1042/1042312.png',
        iconSize: [32, 32],
        iconAnchor: [16, 16],
    });

    return (
        <>
            <Polyline pathOptions={{ color: color, weight: 3, opacity: 0.4, dashArray: '5, 10' }} positions={path} />
            <Marker position={path[currentIdx]} icon={ambulanceIcon}>
                <Popup>Véhicule en mission d'urgence</Popup>
            </Marker>
        </>
    );
};

const LocationMarker = ({ setStartPoint }) => {
    useMapEvents({
        click(e) {
            setStartPoint([e.latlng.lat, e.latlng.lng]);
        },
    });
    return null;
};

const MapView = ({ startPoint, setStartPoint, routePath, hospitals, chosenHospital, blockedPoints = [], activeMissions = [] }) => {
    const center = [3.848, 11.502];

    const hospitalIcon = () => new L.Icon({
        iconUrl: 'https://cdn-icons-png.flaticon.com/512/822/822159.png',
        iconSize: [35, 35],
        iconAnchor: [17, 17],
        popupAnchor: [0, -17],
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
                    icon={hospitalIcon()}
                >
                    <Popup>
                        <div className="font-bold">{h.name}</div>
                        <div>Attente: {h.temps_attente_min} min</div>
                        <div>Status: {h.urgences_disponibles ? 'Disponible' : 'Saturé'}</div>
                    </Popup>
                </Marker>
            ))}

            {routePath && (
                <Polyline pathOptions={{ color: '#ef4444', weight: 6, opacity: 0.9 }} positions={routePath} />
            )}

            {/* Active Missions Animation (Twist 09) */}
            {activeMissions.map((mission, idx) => (
                <MovingVehicle key={`mission-${mission.id}`} path={mission.path} color={mission.color} />
            ))}

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
