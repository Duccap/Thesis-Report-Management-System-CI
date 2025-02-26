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
    app.get("/get-submission-status", getSubmissionStatus);

    app.get("/get-pdf", async (req, res) => {
        const { thesis_id } = req.query;

        if (!thesis_id) {
            return res.status(400).json({ error: "Thesis ID is required" });
        }

        try {
            const fileName = `rest/${thesis_id}.pdf`; 
            const file = storage.bucket(bucketName).file(fileName);

            res.setHeader("Content-Type", "application/pdf");
            file.createReadStream().pipe(res);
        } catch (error) {
            console.error("Error fetching PDF:", error);
            res.status(500).json({ error: "Failed to fetch PDF" });
        }
    });
};

export default Router;