import { Outlet } from "react-router-dom";
// import DownNavbar from "../pages/Navbardown";

const Layout = () => {
  return (
    <>
     {/* <DownNavbar/> */}

      <Outlet />
    </>
  )
};

export default Layout;
