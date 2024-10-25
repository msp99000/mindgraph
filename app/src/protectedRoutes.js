import React from "react";
import { Navigate } from "react-router-dom";

const ProtectedRoute = ({ children }) => {
  // Check if the user is logged in (i.e., username exists in localStorage)
  const isAuthenticated = localStorage.getItem("username");

  if (!isAuthenticated) {
    // If the user is not authenticated, redirect them to the login page
    return <Navigate to="/" />;
  }

  // Otherwise, allow access to the protected route
  return children;
};

export default ProtectedRoute;
