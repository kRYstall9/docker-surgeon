import { logout } from "../../api/auth";
import logo from "../../assets/logo.png";
import { LogOut } from "lucide-react";

export function Navbar() {
  return (
    <div className="w-full flex justify-between items-center container-bg-color p-3 rounded-xl">
      <div className="flex items-center gap-2">
        <img src={logo} alt="Logo" className="w-10 h-10" />
        <p className="font-semibold">Docker Surgeon</p>
      </div>
      <div>
        <button
          className="p-2 rounded-full hover:bg-gray-900/30 transition-colors duration-200 cursor-pointer"
          type="button"
          title="Log out"
          onClick={() => {
            logout().then(() => (window.location.href = "/login"));
          }}
        >
          <LogOut size={20} color="white" />
        </button>
      </div>
    </div>
  );
}
