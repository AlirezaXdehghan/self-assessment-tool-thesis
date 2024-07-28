// src/components/ExamCreator.js
import React, { useState } from 'react';
import Loader from './Loader';
import ResponseDisplay from './ResponseDisplay';
import './ExamCreator.css'
import {useDispatch, useSelector} from "react-redux";

const ExamCreator = () => {
    const dispatch = useDispatch();
    const serverAddress = useSelector(state => state.backendServer)
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [response, setResponse] = useState(null);
    const [startingChapter, setStartingChapter] = useState(null);
    const [endingChapter, setEndingChapter] = useState(null);
    const [numberChapter, setNumberChapter] = useState(null);
    const [tsize, setTsize] = useState(null);

    const handleFileChange = (event) => {
        setFile(event.target.files[0]);
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!file) return;

        const formData = new FormData();
        formData.append('uploaded_file', file);

        setLoading(true);

        try {
            const response = await fetch(`${serverAddress}/uploadPDF`, {
                method: 'POST',
                body: formData,
                headers: {
                    'ngrok-skip-browser-warning': '60241'
                }
            });

            const result = await response.json();
            const starting_chapter = result.starting_chapter;
            const last_chapter = result.last_chapter;
            const uuid = result.uuid;
            const numch = result.number_chapters;
            dispatch({ type: 'UPDATE_GENERATED_UUID', payload: uuid });
            const textSize = result.textSize;
            setNumberChapter(numch)
            setTsize(textSize)
            setStartingChapter(starting_chapter);
            setEndingChapter(last_chapter);
            setResponse(result);
        } catch (error) {
            console.error('Error uploading file:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="exam-creator">
            <h2 className="welcometext">Welcome to the Exam Creator</h2>
            {!loading && !response ? <>
            <p>In this section, you can upload your PDF file so our system can start generating questions and create the exam for you.</p>
            <form onSubmit={handleSubmit}>
                <div className="file-input">
                    <input type="file" onChange={handleFileChange} />
                </div>
                <button type="submit">Next</button>
            </form>
               </> :
            <></>}
            {loading && <Loader />}
            {response && <ResponseDisplay st={startingChapter} sp={endingChapter} textSize={tsize} nc={numberChapter} response={response} />}
        </div>
    );
};

export default ExamCreator;
