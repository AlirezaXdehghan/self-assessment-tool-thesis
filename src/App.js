// src/App.js
import React from 'react';
import ExamCreator from './components/ExamCreator';
import Exam from './components/exam.js';
import './App.css';
import {useDispatch, useSelector} from "react-redux";

function App() {
    const view = useSelector(state => state.globalView);
    const dispatch = useDispatch();
    const serverAddress = useSelector(state => state.backendServer)
    return (
        <div className="app">
            <aside className="sidebar">
                <img className="looplogo" src="https://static.wixstatic.com/media/349174_6c78514833ea4b5793e89db925243e0a~mv2.png/v1/fill/w_151,h_64,al_c,q_85,usm_0.66_1.00_0.01,enc_auto/loopai_Group_Logo_2022.png" alt="LoopAI"/>
                <button onClick={() => dispatch({ type: 'UPDATE_GLOBAL_VIEW', payload: 'creator' })} className="menu-item">New Exam</button>
                <button onClick={() => dispatch({ type: 'UPDATE_GLOBAL_VIEW', payload: 'exam' })} className="menu-item">Cheat!Exams</button>
                <button className="menu-item">Support</button>
                <button className="logout-btn">Log Out</button>
                <input
                    type="text"
                    value={serverAddress}
                    onChange={(e) => dispatch({type: 'UPDATE_BACKEND_ADDRESS', payload:e.target.value})}
                />
            </aside>
            <main className="main-content">
                <div className="seperator">
                {view==='creator' && <ExamCreator />}
                {view==='exam' && <Exam/>}
                </div>
            </main>
        </div>
    );
}

export default App;
