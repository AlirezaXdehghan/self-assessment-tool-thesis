// src/store.js
import { createStore } from 'redux';

// Initial state
const initialState = {
    globalParameter: "initial_value",
    generatedUuid: "default-uuid",
    globalView: "creator",
    backendServer: "https://loop.ai",
    emailAddress: "alireza@loop.ai"
};

// Reducer function
const rootReducer = (state = initialState, action) => {
    switch (action.type) {
        case 'UPDATE_GLOBAL_PARAMETER':
            return {
                ...state,
                globalParameter: action.payload,
            };
        case 'UPDATE_GLOBAL_VIEW':
            return {
                ...state,
                globalView: action.payload,
            };
        case 'UPDATE_BACKEND_ADDRESS':
            return {
                ...state,
                backendServer: action.payload,
            };
        case 'UPDATE_EMAIL_ADDRESS':
            return {
                ...state,
                emailAddress: action.payload,
            };
        case 'UPDATE_GENERATED_UUID':
            return {
                ...state,
                generatedUuid: action.payload,
            };
        default:
            return state;
    }
};

// Create store
const store = createStore(rootReducer);

export default store;
