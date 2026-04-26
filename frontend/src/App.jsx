import React, { useState, useEffect } from 'react';
import MapView from './components/MapView';
import HospitalPanel from './components/HospitalPanel';
import { RouteForm, RouteResult, AuditPanel } from './components/RouteResult'; // I merged them in previous file
import { routingService } from './services/api';
import { ShieldAlert, AlertTriangle } from 'lucide-react';

function App() {
  const [hospitals, setHospitals] = useState([]);
  const [startPoint, setStartPoint] = useState(null);
  const [hour, setHour] = useState(12);
  const [typeUrgence, setTypeUrgence] = useState('general');
  const [routeResult, setRouteResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadHospitals();
    // Refresh hospitals periodically
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
        temps_attente_min: waitTime + (available ? -5 : 5) // dummy change for demo
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
        type_urgence: typeUrgence
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
      await routingService.injectBlockage();
      loadHospitals(); // Just to trigger a refresh and see traffic status if implemented
      if (startPoint) calculateRoute(); // Recalculate immediately for demo
    } catch (err) {
      console.error("Injection failed", err);
    }
  };

  return (
    <div className="flex h-screen w-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Sidebar Left: Inputs and Results */}
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

        <RouteForm
          hour={hour} setHour={setHour}
          typeUrgence={typeUrgence} setTypeUrgence={setTypeUrgence}
          onCalculate={calculateRoute}
          loading={loading}
        />

        <button
          onClick={handleInjectBlockage}
          className="mt-4 w-full border border-yellow-500/30 bg-yellow-500/5 hover:bg-yellow-500/10 text-yellow-500 text-[10px] font-black uppercase tracking-widest py-2 rounded-lg transition-all"
        >
          ⚡ Injecter Embouteillage (Demo)
        </button>

        {error && (

          <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl mt-4 flex items-start gap-3">
            <AlertTriangle className="shrink-0" size={18} />
            <span className="text-sm font-medium">{error}</span>
          </div>
        )}

        <RouteResult result={routeResult} />

        {routeResult && <AuditPanel audit={routeResult.audit} />}

        <div className="mt-auto py-4 text-center">
          <p className="text-[10px] text-slate-600 font-medium">HACKATHON BUILD — TEAM D2T — 2024</p>
        </div>
      </div>

      {/* Main Center: Map */}
      <div className="flex-1 relative">
        <MapView
          startPoint={startPoint}
          setStartPoint={setStartPoint}
          routePath={routeResult?.path}
          hospitals={hospitals}
          chosenHospital={routeResult?.hopital}
        />

        {/* Floating Tooltip */}
        {!startPoint && (
          <div className="absolute top-10 left-1/2 -translate-x-1/2 z-[1000] bg-slate-900/90 backdrop-blur border border-slate-700 px-6 py-3 rounded-full shadow-2xl pointer-events-none">
            <p className="text-sm font-bold flex items-center gap-2">
              <AlertTriangle className="text-accent animate-pulse" size={16} />
              Cliquez sur la carte pour définir le point de départ
            </p>
          </div>
        )}
      </div>

      {/* Sidebar Right: Admin Controls */}
      <div className="w-[300px] border-l border-slate-800 bg-slate-900/50 flex flex-col p-4 z-10">
        <HospitalPanel
          hospitals={hospitals}
          onToggle={handleToggleHospital}
        />
      </div>
    </div>
  );
}

export default App;
