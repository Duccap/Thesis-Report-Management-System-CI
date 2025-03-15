import { Express } from "express";
import { Storage } from "@google-cloud/storage";
import uploadThesis from "./controller/file_upload/uploadThesis";
import { uploadFile } from "./middleware/uploadFile";
import getReport from "./controller/report/getReport";
import pollReport from "./controller/report/pollReport";
import getStudentSubmissions from "./controller/user/instructor/getStudentSubmissions";
import login from "./controller/authen/login";
import getThesisInfo from "./controller/report/getThesisInfo";
import getUserInfo from "./controller/user/getUserInfo";
import getStudentInfo from "./controller/user/student/getStudentInfo";
import getAllSubmissions from "./controller/user/student/getAllSubmissions";
import downloadFile from "./controller/file_upload/downloadFile";
import giveFeedback from "./controller/user/instructor/giveFeedback";
import getFeedback from "./controller/report/getFeedback";
import getGuidelines from "./controller/report/getGuidelines";
import editDeadline from "./controller/user/admin/editDeadline";
import sendNotification from "./controller/user/admin/sendNotification";
import viewNotification from "./controller/user/viewNotification";
import getDeadline from "./controller/user/admin/getDeadline";
import getAllNotifications from "./controller/user/admin/getAllNotifications";
import getSubmissionStatus from "./controller/analysis/getSubmissionStatus";
import getNewNotification from "./controller/user/getNewNotification";
import getInstructor from "./controller/user/student/getInstructor";

// later divide into separate files
import multer from "multer";
const upload = multer();
import Thesis from "./database/Thesis";
import Event from "./database/Event";


const storage = new Storage({
    keyFilename: "/run/secrets/gcp-credentials",
});

const bucketName = process.env.GOOGLE_CLOUD_STORAGE_BUCKET || "default_bucket_name";

const Router = (app: Express) => {
    // Existing routes
    app.post("/login", login);
    app.post("/upload-thesis", uploadFile, uploadThesis);
    app.post("/download-file", downloadFile);
    app.post("/get-thesis-info", getThesisInfo);
    app.post("/get-user-info", getUserInfo);
    app.post("/get-instructor", getInstructor);
    app.post("/get-student-info", getStudentInfo);
    app.post("/get-all-submissions", getAllSubmissions);
    app.post("/get-report", getReport);
    app.post("/poll-report", pollReport);
    app.post("/give-feedback", giveFeedback);
    app.post("/get-feedback", getFeedback);
    app.post("/get-submissions", getStudentSubmissions);
    app.get("/get-guidelines", getGuidelines);
    app.get("/get-deadline", getDeadline);
    app.post("/edit-deadline", editDeadline);
    app.get("/get-all-notifications", getAllNotifications);
    app.post("/send-notification", sendNotification);
    app.post("/view-notification", viewNotification);
    app.post("/get-new-notifications", getNewNotification);
    app.get("/get-submission-status", getSubmissionStatus); // ? unused

    app.get("/get-pdf", async (req, res) => {
        const { thesis_id } = req.query;
    
        if (!thesis_id) {
            return res.status(400).json({ error: "Thesis ID is required" });
        }
    
        try {
            const fileName = `rest/${thesis_id}/${thesis_id}.pdf`;
            const file = storage.bucket(bucketName).file(fileName);
    
            const thesis = await Thesis.findOne({ where: { id: thesis_id } });
            if (!thesis) {
                return res.status(404).json({ error: "Thesis not found" });
            }
    
            const lastModifiedInDB = thesis.getDataValue("last_modified");
    
            res.setHeader("Content-Type", "application/pdf");
            res.setHeader("Last-Modified", lastModifiedInDB.toISOString());
            file.createReadStream().pipe(res);
        } catch (error) {
            console.error("Error fetching PDF:", error);
            res.status(500).json({ error: "Failed to fetch PDF" });
        }
    });

    app.post("/update-thesis", async (req, res) => {
        const { thesis_id, user_annotations } = req.body;
    
        if (!thesis_id || !user_annotations) {
            return res.status(400).json({ error: "Thesis ID and user annotations are required" });
        }
    
        try {
            const storage = new Storage();
            const bucketName = process.env.GOOGLE_CLOUD_STORAGE_BUCKET!;
            const bucket = storage.bucket(bucketName);
    
            // Save user annotations as a JSON file
            const userAnnotationsFileName = `rest/${thesis_id}/user_annotations.json`;
            const userAnnotationsFile = bucket.file(userAnnotationsFileName);
            await userAnnotationsFile.save(JSON.stringify(user_annotations), {
                metadata: {
                    contentType: "application/json",
                },
            });
    
            // Update the last_modified timestamp
            const last_modified = new Date();
            await Thesis.update(
                { last_modified: last_modified },
                { where: { id: thesis_id } }
            );
    
            res.status(200).json({ 
                message: "Thesis annotations updated successfully", 
                last_modified: last_modified.toISOString() 
            });
        } catch (error) {
            console.error("Error updating thesis annotations:", error);
            res.status(500).json({ error: "Failed to update thesis annotations" });
        }
    });

    app.get("/check-file-modified", async (req, res) => {
        const { thesis_id, last_modified } = req.query;
    
        if (!thesis_id || !last_modified) {
            return res.status(400).json({ error: "Thesis ID and last_modified are required" });
        }
    
        try {
            const thesis = await Thesis.findOne({ where: { id: thesis_id } });
            if (!thesis) {
                return res.status(404).json({ error: "Thesis not found" });
            }
    
            const lastModifiedInDB = thesis.getDataValue("last_modified");
    
            const frontendLastModified = new Date(last_modified as string);
    
            if (lastModifiedInDB.getTime() > frontendLastModified.getTime()) {
                return res.status(200).json({ modified: true });
            }
    
            return res.status(200).json({ modified: false });
        } catch (error) {
            console.error("Error checking file modification:", error);
            res.status(500).json({ error: "Failed to check file modification" });
        }
    });

    app.get("/get-annotations", async (req, res) => {
        const { thesis_id } = req.query;
    
        if (!thesis_id) {
            return res.status(400).json({ error: "Thesis ID is required" });
        }
    
        try {
            // Array to store all annotations
            const allAnnotations: any[] = [];
    
            // Fetch user annotations from user_annotations.json
            const userAnnotationsFileName = `rest/${thesis_id}/user_annotations.json`;
            const userAnnotationsFile = storage.bucket(bucketName).file(userAnnotationsFileName);
    
            // Check if the user annotations file exists
            const [userAnnotationsExists] = await userAnnotationsFile.exists();
            if (userAnnotationsExists) {
                const [userAnnotationsData] = await userAnnotationsFile.download();
                const userAnnotations = JSON.parse(userAnnotationsData.toString());
    
                // Ensure user annotations is always an array
                if (!Array.isArray(userAnnotations)) {
                    allAnnotations.push(userAnnotations); // Single annotation object
                } else {
                    allAnnotations.push(...userAnnotations); // Array of annotations
                }
            }
    
            // Fetch service annotations from events
            const events = await Event.findAll({ where: { thesis_id } });
            if (events && events.length > 0) {
                for (const event of events) {
                    const annotationLocation = event.getDataValue("output_annotation_location");
                    if (annotationLocation) {
                        const annotationFile = storage.bucket(bucketName).file(annotationLocation);
                        const [annotationData] = await annotationFile.download();
                        const annotations = JSON.parse(annotationData.toString());
    
                        if (!Array.isArray(annotations)) {
                            allAnnotations.push(annotations); 
                        } else {
                            allAnnotations.push(...annotations); 
                        }
                    }
                }
            }
    
            if (allAnnotations.length === 0) {
                return res.status(404).json({ error: "No annotations found" });
            }
    
    
            // Send all annotations to frontend
            res.status(200).json(allAnnotations);
        } catch (error) {
            console.error("Error fetching annotations:", error);
            res.status(500).json({ error: "Failed to fetch annotations" });
        }
    });
};

export default Router;

