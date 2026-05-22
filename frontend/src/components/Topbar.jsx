import { Bell, GraduationCap } from 'lucide-react';
export default function Topbar({ title, subtitle }) {
  return <div className="topbar">
    <div><h1 style={{margin:'0 0 6px'}}>{title}</h1><div className="muted">{subtitle}</div></div>
    <div className="profile"><Bell size={18}/><div className="avatar">AR</div><div><strong>Ana Rodríguez</strong><br/><small className="muted"><GraduationCap size={12}/> Estudiante</small></div></div>
  </div>;
}
