import logo from '../../assets/logo.png';

export function Login() {
    return (
        <div className="flex justify-center items-center w-full h-screen">
            <div className="w-full sm:w-2xl max-w-xl rounded-xl m-0 p-0">
                
                <div className="flex items-center justify-center mb-2">
                    <img src={logo} alt="Logo" className="w-20 h-20 sm:w-25 sm:h-25" />
                    <span className="font-bold text-xl sm:text-2xl">Docker Surgeon</span>
                </div>

                <form className="flex flex-col items-center gap-8 bg-[var(--login-bg-color)] p-6 rounded-2xl">
                    <p className="font-semibold text-lg sm:text-xl mb-3">Login</p>

                    <div className="w-full sm:w-[75%]">
                        <label htmlFor="password" className="block text-[0.6rem]/2 sm:text-xs/2 font-normal text-start mb-2">
                            Admin Password
                        </label>
                        <input
                            type="password"
                            id="password"
                            className="w-full rounded bg-[var(--input-bg-color)] py-1.5 px-3"
                            required
                        />
                    </div>

                    <button type="submit" className="w-full sm:w-[75%] bg-orange-500 hover:bg-orange-700 text-white font-semibold py-2 rounded-md">
                        Login
                    </button>
                </form>
            </div>
        </div>
    );
}
