
import { useState } from "react";
import classnames from "classnames";
import './Login.css'
import UserData from "../Dashboard/Dashboard";
import { useNavigate } from "react-router-dom";

let Logo = require('./logo.png');


const SignInForm = () => {

    const [swapPanel, setSwapPanel] = useState(false);

    let navigate = useNavigate();

    const routeChange = () => {
        let path = `dashboard`;
        navigate(path);
    }
    const signUpButton = () => {
        setSwapPanel(true);
    };
    const signInButton = () => {
        setSwapPanel(false);
    };

    return (
        <div className="sigin">
            <div
                className={classnames("container", { "right-panel-active": swapPanel })}
                id="container"
            >
                <div className="form-container sign-up-container">
                    <form action="#">
                        <h1>Create Account</h1>
                        {/* <div className="social-container"></div>
                        <span>or use your email for registration</span> */}
                        <input type="text" placeholder="Name" />
                        <input type="email" placeholder="Email" />
                        <input type="password" placeholder="Password" />
                        <button onClick={signUpButton}>Sign Up</button>
                    </form>
                </div>
                <div className="form-container sign-in-container">
                    <form action="#">
                        <h1>Sign in</h1>
                        {/* <div className="social-container"></div>
                        <span>or use your account</span> */}
                        <input type="email" placeholder="Email" />
                        <input type="password" placeholder="Password" />
                        {/* Forgot your password? */}
                        <a href="#">Forgot your password?</a>
                        <button onClick={routeChange} >Sign In</button>

                    </form>
                </div>
                <div className="overlay-container">
                    <div className="overlay">
                        <div className="overlay-panel overlay-left">
                            {/* <h1>Welcome Back!</h1>
                            <p>
                                To keep connected with us please login with your personal info
                            </p> */}
                            <img src={Logo} alt="tech" style={{ width: '250px', height: '125px', }} />
                            <button
                                type="button"
                                onClick={signInButton}
                                className="ghost"
                                id="signIn"
                            >
                                Sign In
                            </button>
                        </div>
                        <div className="overlay-panel overlay-right">
                            {/* <h1>Hello, Friend!</h1>
                            <p>Enter your personal details and start journey with us</p> */}
                            <img src={Logo} alt="tech" style={{ width: '250px', height: '125px', }} />
                            <button
                                type="button"
                                onClick={signUpButton}
                                className="ghost"
                                id="signUp"
                            >
                                Sign Up
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SignInForm;
