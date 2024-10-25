import "./App.css";
import Fetchslack from "./pages/fetch/Fetchs";
import ApiFrontend from "./pages/home";
import "bootstrap/dist/css/bootstrap.min.css";
import NoPage from "./pages/Nopage";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./router/Layout";
import StoreData from "./pages/fetch/Storedata";
import Login from "./pages/login/Login";
import ProtectedRoute from "./protectedRoutes.js"
import EventStreamComponent from "./pages/home";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Login />} />
            {/* Protected routes */}
            <Route
              path="/home"
              element={
                <ProtectedRoute>
                  {/* <ApiFrontend /> */}
                  <EventStreamComponent/>
                </ProtectedRoute>
              }
            />
            <Route
              path="/page/integration"
              element={
                <ProtectedRoute>
                  <Fetchslack />
                </ProtectedRoute>
              }
            />
            <Route
              path="/StoreData"
              element={
                <ProtectedRoute>
                  <StoreData />
                </ProtectedRoute>
              }
            />
            {/* Catch all route for undefined paths */}
            <Route path="*" element={<NoPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
