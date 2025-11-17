import './App.css'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Homepage } from './pages/homepage'
import { Login } from './pages/login'

function App() {

  return (
    <BrowserRouter>
      <Routes>
        <Route path='/login' element={<Login/>}></Route>
        <Route path="/" element={<Homepage/>}></Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
