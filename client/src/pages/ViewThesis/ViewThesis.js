/* global AdobeDC */
import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import Spinner from "../../components/Spinner/Spinner";

let adobeScriptLoaded = false;

const ViewThesis = () => {
    const { id } = useParams();
    const [pdfUrl, setPdfUrl] = useState("");
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        const fetchPdf = async () => {
            try {
                const response = await axios.get(
                    `${process.env.REACT_APP_BACKEND_HOST}/get-pdf`,
                    {
                        params: { thesis_id: id },
                        responseType: "blob",
                    }
                );
    
                const url = URL.createObjectURL(new Blob([response.data]));
                setPdfUrl(url);
    
                // Store the lastModifiedInDB timestamp from the response headers
                const lastModifiedInDB = response.headers["last-modified"];
                localStorage.setItem(`lastModifiedInDB_${id}`, lastModifiedInDB);
            } catch (error) {
                console.error("Error fetching PDF:", error);
                setError("Failed to fetch the PDF. Please try again later.");
            } finally {
                setIsLoading(false);
            }
        };
    
        fetchPdf();
    }, [id]);
    
    useEffect(() => {
        if (!pdfUrl) return;
    
        const initializeAdobeView = () => {
            try {
                const fullName = localStorage.getItem("full_name");
                const profile = {
                    userProfile: {
                        name: fullName,
                        firstName: fullName.split(" ")[0],
                        lastName: fullName.split(" ")[1],
                    },
                };
    
                const previewConfig = {
                    embedMode: "FULL_WINDOW",
                    showDownloadPDF: true,
                    showPrintPDF: true,
                    showZoomControl: true,
                    defaultViewMode: "FIT_WIDTH",
                    showDisabledSaveButton: true,
                    enableAnnotationAPIs: true,
                    includePDFAnnotations: true,
                };
    
                const adobeDCView = new AdobeDC.View({
                    clientId: process.env.REACT_APP_ADOBE_API,
                    divId: "adobe-dc-view",
                    sendAutoPDFAnalytics: false,
                });
    
                var previewFilePromise = adobeDCView.previewFile(
                    {
                        content: { location: { url: pdfUrl } },
                        metaData: { fileName: `Thesis ${id}`, id: id },
                    },
                    previewConfig
                );
                
                // Fetch all annotations from the backend
                const fetchAnnotations = async () => {
                    try {
                        const response = await axios.get(
                            `${process.env.REACT_APP_BACKEND_HOST}/get-annotations`,
                            { params: { thesis_id: id } }
                        );

                        if (response.data && response.data.length > 0) {
                            previewFilePromise.then(adobeViewer => {
                                adobeViewer.getAnnotationManager().then(annotationManager => {
                                    annotationManager.addAnnotations(response.data)
                                        .then(() => console.log("Annotations added successfully"))
                                        .catch(error => console.error("Error adding annotations:", error));
                                });
                            });
                        }
                    } catch (error) {
                        console.error("Error fetching annotations:", error);
                    }
                };

                fetchAnnotations();

    
                // Save callback
                adobeDCView.registerCallback(
                    AdobeDC.View.Enum.CallbackType.SAVE_API,
                    async (metaData, content, options) => {
                        try {
                            // Get the stored lastModifiedInDB from localStorage
                            const lastModifiedInDB = localStorage.getItem(`lastModifiedInDB_${id}`);
                
                            // Check if the file has been modified by another user
                            const checkResponse = await axios.get(
                                `${process.env.REACT_APP_BACKEND_HOST}/check-file-modified`,
                                {
                                    params: { thesis_id: id, last_modified: lastModifiedInDB },
                                }
                            );
                
                            if (checkResponse.data.modified) {
                                // File has been modified by another user
                                return Promise.resolve({
                                    code: AdobeDC.View.Enum.ApiResponseCode.FILE_MODIFIED,
                                    data: {
                                        // modifiedBy: {
                                        //     name: "Another User", // Replace with actual user name
                                        //     mail: "anotheruser@example.com", // Replace with actual user email
                                        // },
                                    },
                                });
                            }
                
                            // Fetch all annotations from the PDF
                            const adobeViewer = await previewFilePromise;
                            const annotationManager = await adobeViewer.getAnnotationManager();
                            const existingAnnotations = await annotationManager.getAnnotations();
                
                            // Get the list of service names from .env
                            const serviceNames = process.env.REACT_APP_SERVICE_LIST.split(",");
                
                            // Filter out service annotations
                            const userAnnotations = existingAnnotations.filter(ann => {
                                const creatorName = ann.creator?.name;
                                return !serviceNames.includes(creatorName);
                            });
                
                            // Send only the user annotations to the backend
                            const updateResponse = await axios.post(
                                `${process.env.REACT_APP_BACKEND_HOST}/update-thesis`,
                                {
                                    thesis_id: id,
                                    user_annotations: userAnnotations,
                                },
                                {
                                    headers: {
                                        "Content-Type": "application/json",
                                    },
                                }
                            );
                
                            // Update the lastModifiedInDB value in localStorage
                            localStorage.setItem(`lastModifiedInDB_${id}`, updateResponse.data.last_modified);
                
                            return Promise.resolve({
                                code: AdobeDC.View.Enum.ApiResponseCode.SUCCESS,
                                data: { metaData: metaData },
                            });
                        } catch (error) {
                            console.error("Error saving PDF:", error);
                            return Promise.reject({
                                code: AdobeDC.View.Enum.ApiResponseCode.FAIL,
                            });
                        }
                    },
                    {
                        autoSaveFrequency: 5,
                        enableFocusPolling: true,
                    }
                );
                
                // Register user profile callback
                adobeDCView.registerCallback(
                    AdobeDC.View.Enum.CallbackType.GET_USER_PROFILE_API,
                    function () {
                        return Promise.resolve({
                            code: AdobeDC.View.Enum.ApiResponseCode.SUCCESS,
                            data: profile,
                        });
                    },
                    {}
                );
            } catch (error) {
                console.error("Error initializing Adobe PDF Embed API:", error);
                setError("Failed to load the PDF viewer. Please try again later.");
            }
        };
    
        if (!adobeScriptLoaded) {
            const script = document.createElement("script");
            script.src = "https://acrobatservices.adobe.com/view-sdk/viewer.js";
            script.async = true;
            document.body.appendChild(script);
    
            script.onload = () => {
                adobeScriptLoaded = true;
                document.addEventListener("adobe_dc_view_sdk.ready", initializeAdobeView);
            };
    
            script.onerror = () => {
                console.error("Failed to load Adobe PDF Embed API script.");
                setError("Failed to load the PDF viewer. Please try again later.");
            };
    
            return () => {
                document.body.removeChild(script);
                document.removeEventListener("adobe_dc_view_sdk.ready", initializeAdobeView);
            };
        } else {
            initializeAdobeView();
        }
    }, [pdfUrl, id]);

    if (isLoading) {
        return <Spinner />;
    }

    if (error) {
        return <div className="error-message">{error}</div>;
    }

    return (
        <div
            id="adobe-dc-view"
            style={{
                width: "100%",
                height: "calc(100vh - 60px)",
                marginTop: "60px",
            }}
        ></div>
    );
};

export default ViewThesis;