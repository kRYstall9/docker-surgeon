import axios from 'axios';

export async function login(password: string){
    return axios.post("/api/auth/login", { password }, {
        withCredentials: true
    });
}

export async function logout(){
    return axios.post("/api/logout", {}, {
        withCredentials: true
    });
}