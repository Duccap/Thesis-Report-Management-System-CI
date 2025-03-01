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
                    }
                    };
                const previewConfig = {
                    embedMode: "FULL_WINDOW",
                    showDownloadPDF: true,
                    showPrintPDF: true,
                    showZoomControl: true,
                    defaultViewMode: "FIT_WIDTH",
                    
                };
                const adobeDCView = new AdobeDC.View({
                    clientId: process.env.REACT_APP_ADOBE_API,
                    divId: "adobe-dc-view",
                    sendAutoPDFAnalytics: false
                });

                adobeDCView.previewFile(
                    {
                        content: { location: { url: pdfUrl } },
                        metaData: { fileName: `Thesis ${id}` },
                    },
                    previewConfig
                );

                adobeDCView.registerCallback(
                    AdobeDC.View.Enum.CallbackType.GET_USER_PROFILE_API,
                    function() {
                        return new Promise((resolve, reject) => {
                            resolve({
                                code: AdobeDC.View.Enum.ApiResponseCode.SUCCESS,
                                data: profile
                            });
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
