import React, { useState, useEffect } from 'react';
import {useDispatch, useSelector } from 'react-redux';
import './ResponseDisplay.css'
import axios from 'axios';

function ResponseDisplay({ st, sp, textSize, nc}) {
    const dispatch = useDispatch()
    const serverAddress = useSelector(state => state.backendServer)
    const idid = useSelector(state => state.generatedUuid);
    const [currentSection, setCurrentSection] = useState(null);
    const [currentPage, setCurrentPage] = useState(parseInt(st));
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [pageList, setPageList] = useState(Array.from({ length: parseInt(sp) - parseInt(st) + 1 }, (_, i) => parseInt(st) + i));

    const fetchData = async (id) => {
        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch(`${serverAddress}/showSection/${idid}/${id}`, {
    headers: {
        'ngrok-skip-browser-warning': 'true'
    }
});

            if (!response.ok) {
                throw new Error(`Error fetching section ${id}: ${response.statusText}`);
            }
            const data = await response.json();
            setCurrentSection(data.text);
        } catch (error) {
            setError(error.message);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchData(currentPage);
    }, [currentPage]);

    const handleNext = () => {
        if (parseInt(currentPage) + 1 <= parseInt(nc)) {
            setCurrentPage(parseInt(currentPage) + 1);
        }
    };

    const handlePrev = () => {
        if (parseInt(currentPage) - 1 >= 0) {
            setCurrentPage(parseInt(currentPage) - 1);
        }
    };

    const handleCheckboxChange = (page, isChecked) => {
        if (isChecked) {
            setPageList([...pageList, page]);
        } else {
            setPageList(pageList.filter(item => item !== page));
        }
    };

    const handleCreateExam = async () => {
        try {
            const formData = new FormData();
            formData.append('validSections', JSON.stringify(pageList));

            await axios.post(`${serverAddress}/createtheexam/${idid}`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });
            dispatch({ type: 'UPDATE_GLOBAL_VIEW', payload: 'exam' });
            // Handle success if needed
        } catch (error) {
            console.error('Error creating the exam:', error);
        }
    };

    return (
        <div>
            {isLoading && <p>Loading...</p>}
            {error && <p>Error: {error}</p>}
            {currentSection && (
                <div className="preview">
                    <div className="pdf-preview" style={{ maxHeight: '300px', overflowY: 'scroll', border: '1px solid #ccc', padding: '10px' }}>
                        <label>Section: {currentPage}</label>
                        <p>{currentSection}</p>
                    </div>
                    <div className="navigation" style={{padding: '10px'}}>
                    <button onClick={handlePrev} disabled={0 === parseInt(currentPage)}>Previous</button>
                    <label>
                        <input
                            type="checkbox"
                            checked={pageList.includes(currentPage)}
                            onChange={(e) => handleCheckboxChange(currentPage, e.target.checked)}
                        />
                        Use in Question Generation
                    </label>
                    <button onClick={handleNext} disabled={parseInt(nc) === parseInt(currentPage)}>Next</button>
                    </div>
                    <div className="createexam">
                    <button onClick={handleCreateExam}>Create the Exam</button>
                    </div>
                </div>
            )}

        </div>
    );
}

export default ResponseDisplay;
