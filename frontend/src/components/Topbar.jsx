import { Bell, GraduationCap, LogOut } from 'lucide-react';

export default function Topbar({ title, subtitle, user, onLogout }) {
  const avatar = user?.avatar || user?.name?.slice(0, 2).toUpperCase() || 'UV';

  return (
    <div className="topbar">
      <div>
        <h1 style={{ margin: '0 0 6px' }}>{title}</h1>
        <div className="muted">{subtitle}</div>
      </div>

      <div className="profile">
        <Bell size={18} />

        {user?.picture ? (
          <img className="avatar-img" src={user.picture} alt={user.name} />
        ) : (
          <div className="avatar">{avatar}</div>
        )}

        <div>
          <strong>{user?.name}</strong>
          <br />
          <small className="muted">
            <GraduationCap size={12} /> {user?.role === 'teacher' ? 'Docente' : 'Estudiante'}
          </small>
        </div>

        <button className="icon-button" onClick={onLogout} title="Cerrar sesión">
          <LogOut size={18} />
        </button>
      </div>
    </div>
  );
}