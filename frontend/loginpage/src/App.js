import React from "react";
import UserData from "./Dashboard/Dashboard";
import SignInForm from "./Login/Login";
import { BrowserRouter, Routes, Route } from "react-router-dom";

const App = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<SignInForm />} />
        <Route path="/dashboard" element={<UserData />} />
      </Routes>
    </BrowserRouter>
  )

}

export default App;

