import React, { useRef, useState, useEffect } from 'react';
import Webcam from 'react-webcam';
import axios from 'axios';
import './exam.css'
import { useSelector } from 'react-redux';
const Exam = () => {
    const idid = useSelector(state => state.generatedUuid);
    const serverAddress = useSelector(state => state.backendServer)
    const webcamRef = useRef(null);
    const mediaRecorderRef = useRef(null);
    const [capturing, setCapturing] = useState(false);
    const [recordedBlob, setRecordedBlob] = useState(null);
    const [currentQuestion, setCurrentQuestion] = useState(null);
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [timestamps, setTimestamps] = useState([]);
    const [startTimestamp, setStartTimestamp] = useState(null);

    useEffect(() => {
        fetchQuestion(currentQuestionIndex);
    }, [currentQuestionIndex]);

    const fetchQuestion = async (index) => {
        try {
            const response = await axios.get(`${serverAddress}/showquestion/${idid}/${index}`);
            const question = response.data.question;
            setCurrentQuestion(question);
        } catch (error) {
            console.error('Error fetching question:', error);
        }
    };

    const handleStartCaptureClick = () => {
        setCapturing(true);
        setStartTimestamp(new Date().getTime());

        const constraints = {
            audio: true,
            video: true
        };

        navigator.mediaDevices.getUserMedia(constraints)
            .then((stream) => {
                const mediaStream = new MediaStream();
                mediaStream.addTrack(stream.getAudioTracks()[0]); // Add audio track
                mediaStream.addTrack(webcamRef.current.stream.getVideoTracks()[0]); // Add video track

                mediaRecorderRef.current = new MediaRecorder(mediaStream, {
                    mimeType: 'video/webm'
                });

                const recordedChunks = [];
                mediaRecorderRef.current.addEventListener('dataavailable', (event) => {
                    if (event.data && event.data.size > 0) {
                        recordedChunks.push(event.data);
                    }
                });

                mediaRecorderRef.current.addEventListener('stop', () => {
                    const videoBlob = new Blob(recordedChunks, {
                        type: 'video/webm'
                    });
                    setRecordedBlob(videoBlob);
                });

                mediaRecorderRef.current.start();
            })
            .catch((error) => {
                console.error('Error accessing media devices:', error);
            });
    };

    const handleNextQuestion = () => {
        const currentTime = new Date().getTime();
        const elapsedTime = currentTime - startTimestamp;
        setTimestamps((prev) => [...prev, elapsedTime]);

        if (currentQuestion !== "Congrats! you can finish now") {
            setCurrentQuestionIndex(currentQuestionIndex + 1);
        } else {
            mediaRecorderRef.current.stop();
            setCapturing(false);
        }
    };

    const handleFinish = () => {
        const formData = new FormData();
        formData.append('video', recordedBlob);
        formData.append('timestamps', JSON.stringify(timestamps));
        axios.post(`${serverAddress}/processVideo/${idid}`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        })
            .then(response => {
                alert('Video and timestamps submitted successfully!');
            })
            .catch(error => {
                console.error('Error submitting video:', error);
                alert('Error submitting video');
            });
    };

    return (
        <div className="exam-container">
            <div className="video-container">
                <Webcam audio={false} ref={webcamRef} />
            </div>
            {!recordedBlob ? (
                capturing ? (
                    <>
                        {currentQuestion && <p className="question-area">{currentQuestion}</p>}
                        <div className="controls">
                            <button onClick={handleNextQuestion}>
                                {currentQuestion !== 'Congrats! you can finish now' ? 'Next Question' : 'Finish'}
                            </button>
                        </div>
                    </>
                ) : (
                    <div className="controls">
                        <button onClick={handleStartCaptureClick}>Start Recording</button>
                    </div>
                )
            ) : (
                <div className="controls">
                    <button onClick={handleFinish}>Send Answers!</button>
                </div>
            )}
        </div>
    );
};

export default Exam;
