import React, { useState, useEffect } from 'react';
import MapView from './components/MapView';
import HospitalPanel from './components/HospitalPanel';
import { RouteForm, RouteResult, AuditPanel } from './components/RouteResult';
import { routingService } from './services/api';
import { ShieldAlert, AlertTriangle, RefreshCcw } from 'lucide-react';

function App() {
  const [hospitals, setHospitals] = useState([]);
  const [startPoint, setStartPoint] = useState(null);
  const [hour, setHour] = useState(new Date().getHours());
  const [typeUrgence, setTypeUrgence] = useState('general');
  const [vehicleType, setVehicleType] = useState('ambulance');
  const [routeResult, setRouteResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadHospitals();
    const interval = setInterval(loadHospitals, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadHospitals = async () => {
    try {
      const res = await routingService.getHospitals();
      setHospitals(res.data);
    } catch (err) {
      console.error("Failed to load hospitals", err);
    }
  };

  const handleToggleHospital = async (id, available, waitTime) => {
    try {
      await routingService.updateHospital(id, {
        urgences_disponibles: available,
        temps_attente_min: waitTime + (available ? -5 : 5)
      });
      loadHospitals();
    } catch (err) {
      console.error("Update failed", err);
    }
  };

  const calculateRoute = async () => {
    if (!startPoint) {
      setError("Veuillez sélectionner un point de départ sur la carte");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await routingService.getRoute({
        lat: startPoint[0],
        lng: startPoint[1],
        heure: hour,
        type_urgence: typeUrgence,
        vehicle_type: vehicleType
      });
      setRouteResult(res.data);
    } catch (err) {
      setError(err.response?.data?.error || "Erreur de calcul de route");
      setRouteResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleInjectBlockage = async () => {
    try {
      await routingService.injectBlockage({
        lat: startPoint[0],
        lng: startPoint[1]
      });
      loadHospitals();
      if (startPoint) calculateRoute();
    } catch (err) {
      console.error("Injection failed", err);
    }
  };

  const handleResetTraffic = async () => {
    try {
      await routingService.resetTraffic();
      loadHospitals();
      if (startPoint) calculateRoute();
    } catch (err) {
      console.error("Reset failed", err);
    }
  };

  return (
    <div className="flex h-screen w-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Sidebar Left */}
      <div className="w-[400px] flex flex-col p-6 z-10 custom-scrollbar overflow-y-auto">
        <div className="flex items-center gap-3 mb-8">
          <div className="bg-primary p-2 rounded-lg shadow-lg shadow-red-500/30">
            <ShieldAlert size={28} />
          </div>
          <div>
            <h1 className="text-2xl font-black uppercase tracking-tighter">Emergency <span className="text-primary">Path</span></h1>
            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest leading-none">Smart African City Routing</p>
          </div>
        </div>

        {/* Vehicle Selection */}
        <div className="bg-white/5 p-4 rounded-2xl border border-white/5 mb-6">
          <label className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 block">Profil de Secours</label>
          <div className="grid grid-cols-3 gap-2">
            {[
              { id: 'ambulance', label: 'Ambi', icon: '🚑' },
              { id: 'fire', label: 'Pompier', icon: '🚒' },
              { id: 'police', label: 'Police', icon: '🚓' },
            ].map((v) => (
              <button
                key={v.id}
                onClick={() => setVehicleType(v.id)}
                className={`flex flex-col items-center p-3 rounded-xl border transition-all ${vehicleType === v.id
                    ? 'bg-indigo-500/20 border-indigo-500 text-indigo-400 scale-105 shadow-lg shadow-indigo-500/20'
                    : 'bg-slate-900/50 border-white/5 text-slate-400 hover:border-white/20'
                  }`}
              >
                <span className="text-2xl mb-1">{v.icon}</span>
                <span className="text-[10px] font-bold">{v.label}</span>
              </button>
            ))}
          </div>
        </div>

        <RouteForm
          hour={hour} setHour={setHour}
          typeUrgence={typeUrgence} setTypeUrgence={setTypeUrgence}
          onCalculate={calculateRoute}
          loading={loading}
        />

        <div className="grid grid-cols-2 gap-2 mt-4">
          <button
            onClick={handleInjectBlockage}
            className="border border-yellow-500/30 bg-yellow-500/5 hover:bg-yellow-500/10 text-yellow-500 text-[10px] font-black uppercase tracking-widest py-3 rounded-xl transition-all"
          >
            ⚡ Sabotage
          </button>
          <button
            onClick={handleResetTraffic}
            className="border border-emerald-500/30 bg-emerald-500/5 hover:bg-emerald-500/10 text-emerald-400 text-[10px] font-black uppercase tracking-widest py-3 rounded-xl transition-all flex items-center justify-center gap-2"
          >
            <RefreshCcw size={12} /> Reset
          </button>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl mt-4 flex items-start gap-3">
            <AlertTriangle className="shrink-0" size={18} />
            <span className="text-sm font-medium">{error}</span>
          </div>
        )}

        <RouteResult result={routeResult} />
        {routeResult && <AuditPanel audit={routeResult.audit} />}
      </div>

      {/* Main Map */}
      <div className="flex-1 relative">
        <MapView
          startPoint={startPoint}
          setStartPoint={setStartPoint}
          routePath={routeResult?.path}
          hospitals={hospitals}
          chosenHospital={routeResult?.hopital}
        />
        {!startPoint && (
          <div className="absolute top-10 left-1/2 -translate-x-1/2 z-[1000] bg-slate-900/90 backdrop-blur border border-slate-700 px-6 py-3 rounded-full shadow-2xl pointer-events-none">
            <p className="text-sm font-bold flex items-center gap-2">
              <AlertTriangle className="text-accent animate-pulse" size={16} />
              Cliquez sur la carte pour définir le point de départ
            </p>
          </div>
        )}
      </div>

      {/* Admin Panel */}
      <div className="w-[300px] border-l border-slate-800 bg-slate-900/50 flex flex-col p-4 z-10 custom-scrollbar overflow-y-auto">
        <HospitalPanel hospitals={hospitals} onToggle={handleToggleHospital} />
      </div>
    </div>
  );
}

export default App;
