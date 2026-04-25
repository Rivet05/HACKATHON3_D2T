import React from 'react';
import { Activity, Clock, ToggleLeft, ToggleRight } from 'lucide-react';

const HospitalPanel = ({ hospitals, onToggle }) => {
    return (
        <div className="flex flex-col gap-3 h-full overflow-y-auto custom-scrollbar p-2">
            <h2 className="text-xl font-bold flex items-center gap-2 mb-2">
                <Activity className="text-primary" /> État des Hôpitaux
            </h2>
            {hospitals.map((h) => (
                <div key={h.id} className="glass-panel rounded-lg p-4 flex flex-col gap-2 transition-all hover:bg-slate-800/50">
                    <div className="flex justify-between items-start">
                        <span className="font-semibold text-sm leading-tight">{h.name}</span>
                        <button
                            onClick={() => onToggle(h.id, !h.urgences_disponibles, h.temps_attente_min)}
                            className="focus:outline-none"
                        >
                            {h.urgences_disponibles ?
                                <ToggleRight size={28} className="text-green-500" /> :
                                <ToggleLeft size={28} className="text-slate-500" />
                            }
                        </button>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-slate-400">
                        <span className="flex items-center gap-1">
                            <Clock size={14} /> {h.temps_attente_min} min
                        </span>
                        <span className={`px-2 py-0.5 rounded-full ${h.urgences_disponibles ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                            {h.urgences_disponibles ? 'Ouvert' : 'Saturé'}
                        </span>
                    </div>
                    <div className="flex flex-wrap gap-1 mt-1">
                        {h.specialites.map(s => (
                            <span key={s} className="bg-slate-700 px-1.5 py-0.5 rounded text-[10px] uppercase">
                                {s}
                            </span>
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );
};

export default HospitalPanel;
