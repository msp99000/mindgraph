import Container from "react-bootstrap/Container";
import Nav from "react-bootstrap/Nav";
import Navbar from "react-bootstrap/Navbar";

import { GiSpiderBot } from "react-icons/gi";
import { IoSettingsOutline } from "react-icons/io5";
import { useNavigate, useLocation } from "react-router-dom";

function DownNavbar(params) {
  const navi = useNavigate();
  const location = useLocation();

  // Check if the current path is the home page
  const isHomePage = location.pathname === "/";
  const setting = location.pathname === "/page/integration";
  return (
    <>
      <Navbar bg="dark" data-bs-theme="dark">
        <Container>
          <Navbar.Brand href="#home">
            <h2>
              Gen-AI-Scturm: Your AI-Powered Chatbot for Data Interaction{" "}
              <GiSpiderBot size={37} />
            </h2>
          </Navbar.Brand>
          <Nav className="me-auto">
            {!isHomePage && (
              <Nav.Link href="#home" onClick={() => navi("/")}>
                Home
              </Nav.Link>
            )}
            {/* <Nav.Link href="#features">Features</Nav.Link> */}
          </Nav>
          <Nav>
            {!setting && (
              <Nav.Link eventKey={2}  >
                <IoSettingsOutline
                  onClick={() => navi("page/integration")}
                  size={32}
                />
              </Nav.Link>
            )}
          </Nav>
        </Container>
      </Navbar>
    </>
  );
}

export default DownNavbar;
