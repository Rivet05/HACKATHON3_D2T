import React, { useState, useEffect } from 'react';
import MapView from './components/MapView';
import HospitalPanel from './components/HospitalPanel';
import { RouteForm, RouteResult, AuditPanel } from './components/RouteResult';
import { routingService } from './services/api';
import { ShieldAlert, AlertTriangle, RefreshCcw, Navigation, WifiOff } from 'lucide-react';

function App() {
  const [hospitals, setHospitals] = useState([]);
  const [startPoint, setStartPoint] = useState(null);
  const [hour, setHour] = useState(new Date().getHours());
  const [typeUrgence, setTypeUrgence] = useState('general');
  const [vehicleType, setVehicleType] = useState('ambulance');
  const [routeResult, setRouteResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isContaminated, setIsContaminated] = useState(false);
  const [integrityReason, setIntegrityReason] = useState(null);
  const [blockedPoints, setBlockedPoints] = useState([]);
  const [fleet, setFleet] = useState({ available: 2, max: 2, waiting_time_sec: 0 });
  const [activeMissions, setActiveMissions] = useState([]);

  const [isOffline, setIsOffline] = useState(false);

  const handleNetworkCut = async () => {
    try {
      const newStatus = !isOffline;
      await routingService.cutNetwork(newStatus);
      setIsOffline(newStatus);
    } catch (err) { }
  };

  useEffect(() => {
    loadHospitals();
    loadFleet();
    const interval = setInterval(() => { loadHospitals(); loadFleet(); }, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadFleet = async () => {
    try {
      const res = await routingService.getFleetStatus();
      setFleet(res.data);
    } catch (err) { }
  };

  useEffect(() => {
    if (!routeResult || !routeResult.segment_ids || routeResult.is_recovery_path) return;
    const monitor = setInterval(async () => {
      try {
        const res = await routingService.checkIntegrity({
          segment_ids: routeResult.segment_ids,
          hospital_id: routeResult.hospital?.id,
          urgence_type: typeUrgence
        });
        if (!res.data.is_valid && !isContaminated) {
          setIsContaminated(true);
          setIntegrityReason(res.data.integrity_failure_reason);
          setBlockedPoints(res.data.blocked_coordinates || []);
          setTimeout(() => {
            calculateRoute();
            setIsContaminated(false);
            setIntegrityReason(null);
            setBlockedPoints([]);
          }, 2000);
        }
      } catch (err) { }
    }, 3000);
    return () => clearInterval(monitor);
  }, [routeResult, typeUrgence, isContaminated]);

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
        lng: startPoint[1],
        current_route_segments: routeResult?.segment_ids || []
      });
      loadHospitals();
      // On retire calculateRoute() d'ici pour laisser le Pulse (Twist 04) agir
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
    <div className="flex flex-col md:flex-row h-screen w-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Sidebar Left / Top on Mobile */}
      <div className="w-full md:w-[420px] flex flex-col p-4 md:p-6 z-10 custom-scrollbar overflow-y-auto border-b md:border-b-0 md:border-r border-slate-800/50 bg-slate-950/50 backdrop-blur-xl">
        <div className="flex items-center gap-3 mb-8 shrink-0">
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

        {/* Urgency Type Selector (Twist 05) */}
        <div className="flex bg-slate-800 p-1 rounded-xl mb-6 border border-slate-700/50">
          <button
            onClick={() => setTypeUrgence('general')}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs font-bold transition-all duration-300 ${typeUrgence === 'general' ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/30' : 'text-slate-400 hover:text-white'
              }`}
          >
            GÉNÉRAL
          </button>
          <button
            onClick={() => setTypeUrgence('trauma')}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs font-bold transition-all duration-300 ${typeUrgence === 'trauma' ? 'bg-rose-600 text-white shadow-lg shadow-rose-500/30' : 'text-slate-400 hover:text-white'
              }`}
          >
            TRAUMA
          </button>
        </div>

        {/* Fleet Availability (Twist 09) */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-3 mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${fleet.available > 0 ? 'bg-green-500 animate-pulse' : 'bg-red-500 animate-pulse'}`} />
            <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Flux de Flotte</span>
          </div>
          <span className={`text-xs font-black ${fleet.available > 0 ? 'text-green-400' : 'text-red-400'}`}>
            {fleet.available} / {fleet.max} DISPONIBLES
          </span>
        </div>

        <button
          onClick={calculateRoute}
          disabled={loading || !startPoint}
          className="w-full bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 disabled:from-slate-700 disabled:to-slate-800 text-white font-black py-4 rounded-2xl shadow-xl shadow-indigo-500/20 flex items-center justify-center gap-3 transition-all duration-500 active:scale-95 group mb-2"
        >
          {loading ? (
            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <>
              <Navigation className="group-hover:rotate-12 transition-transform" size={20} />
              <span>LANCER L'INTERVENTION</span>
            </>
          )}
        </button>

        {/* Deploy Button (Twist 09) */}
        <button
          onClick={async () => {
            await routingService.launchMission();
            if (routeResult && routeResult.path) {
              const newMission = {
                id: Date.now(),
                path: routeResult.path,
                color: fleet.available === 2 ? '#3b82f6' : '#8b5cf6' // Blue then Purple
              };
              setActiveMissions(prev => [...prev, newMission]);
              // Clear the calculated route from map to focus on animation
              setRouteResult(null);
              setStartPoint(null);
            }
            loadFleet();
          }}
          disabled={!routeResult || fleet.available === 0}
          className="w-full bg-green-600/20 border border-green-600/30 hover:bg-green-600/40 text-green-400 font-bold py-3 rounded-xl transition-all disabled:opacity-20 flex items-center justify-center gap-2 mb-6 text-xs"
        >
          <RefreshCcw size={16} />
          DÉPLOYER LE VÉHICULE (CONFIRMER)
        </button>

        {/* Demo Sabotage Buttons */}
        <div className="grid grid-cols-2 gap-2 mb-4">
          <button
            onClick={async () => {
              if (routeResult && startPoint) {
                await routingService.injectBlockage({
                  lat: startPoint[0],
                  lng: startPoint[1],
                  current_route_segments: routeResult.segment_ids
                });
                alert("Système routier saboté !");
              }
            }}
            disabled={!routeResult}
            className="bg-slate-800 hover:bg-red-900/40 text-red-500 border border-red-900/30 font-bold py-2 rounded-xl text-[10px] transition-all disabled:opacity-30 flex items-center justify-center gap-2"
          >
            <ShieldAlert size={14} />
            SABOTEUR ROUTE
          </button>

          <button
            onClick={async () => {
              if (routeResult?.hospital?.id) {
                await routingService.sabotageHospital(routeResult.hospital.id);
                // Trigger an immediate check
                const res = await routingService.checkIntegrity({
                  segment_ids: routeResult.segment_ids,
                  hospital_id: routeResult.hospital.id,
                  urgence_type: typeUrgence
                });
                if (!res.data.is_valid) {
                  setIsContaminated(true);
                  setIntegrityReason(res.data.integrity_failure_reason);
                  setTimeout(() => { calculateRoute(); setIsContaminated(false); setIntegrityReason(null); }, 2000);
                }
              }
            }}
            disabled={!routeResult}
            className="bg-slate-800 hover:bg-rose-900/40 text-rose-500 border border-rose-900/30 font-bold py-2 rounded-xl text-[10px] transition-all disabled:opacity-30 flex items-center justify-center gap-2"
          >
            <AlertTriangle size={14} />
            SABOTEUR HÔPITAL
          </button>
        </div>

        {/* Global Network Control (Twist 10) */}
        <button
          onClick={handleNetworkCut}
          className={`w-full py-3 rounded-xl font-black text-xs transition-all flex items-center justify-center gap-2 mb-4 border 
            ${isOffline
              ? 'bg-red-600/20 border-red-500/50 text-red-500 animate-pulse'
              : 'bg-slate-800 border-slate-700 text-slate-400 hover:bg-slate-700'}`}
        >
          <WifiOff size={16} />
          {isOffline ? 'RÉSEAU COUPÉ (DONNÉES SPECTRES)' : 'COUPER LA LIAISON RÉSEAU'}
        </button>

        <button
          onClick={async () => {
            await routingService.resetTraffic();
            setRouteResult(null);
            setStartPoint(null);
            setActiveMissions([]);
            setIsOffline(false);
            setIsContaminated(false);
            setIntegrityReason(null);
            loadHospitals();
            alert("Système réinitialisé.");
          }}
          className="w-full text-slate-500 hover:text-white text-[10px] font-bold tracking-widest transition-colors mb-6"
        >
          RÉINITIALISER LE RÉSEAU
        </button>

        {(isContaminated || routeResult?.is_recovery_path) && (
          <div className={`border p-4 rounded-xl mt-4 flex items-center gap-3 shadow-lg ${routeResult?.is_recovery_path ? 'bg-amber-600 border-amber-500' : 'bg-red-600 border-red-500 animate-pulse'
            } text-white`}>
            <AlertTriangle className="shrink-0" size={20} />
            <div className="flex flex-col">
              <span className="text-xs font-black uppercase tracking-widest">
                {integrityReason === 'hospital_trauma_saturated' ? 'Saturation Trauma' :
                  integrityReason === 'hospital_closed' ? 'Hôpital Fermé' :
                    routeResult?.is_recovery_path ? 'Mode Survie' : 'Alerte Obstacle'}
              </span>
              <span className="text-[10px] font-bold opacity-80">
                {integrityReason === 'hospital_trauma_saturated' ? 'Hôpital n\'accepte plus les traumas. Reroutage...' :
                  routeResult?.is_recovery_path ? 'Trajet forcé (Dernier recours)' : 'Recalcul du trajet en cours...'}
              </span>
            </div>
          </div>
        )}

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
          chosenHospital={routeResult?.hospital}
          blockedPoints={blockedPoints}
          activeMissions={activeMissions}
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
