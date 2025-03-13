DROP DATABASE IF EXISTS chapter_title;
CREATE DATABASE chapter_title;
GRANT ALL PRIVILEGES ON DATABASE chapter_title TO postgres;
\connect chapter_title;
CREATE TABLE public.output (
    id uuid NOT NULL PRIMARY KEY,
    thesis_id character varying(255) NOT NULL,
    file_name character varying(255) NOT NULL,
    file_location character varying(255) NOT NULL,
    result character varying(55),
    grade character varying(55),
    uploaded_time timestamp with time zone NOT NULL
);

DROP DATABASE IF EXISTS word_frequency;
CREATE DATABASE word_frequency;
GRANT ALL PRIVILEGES ON DATABASE word_frequency TO postgres;
\connect word_frequency;
CREATE TABLE public.output (
    id uuid NOT NULL PRIMARY KEY,
    thesis_id character varying(255) NOT NULL,
    file_name character varying(255) NOT NULL,
    file_location character varying(255) NOT NULL,
    result character varying(55),
    grade character varying(55),
    uploaded_time timestamp with time zone NOT NULL
);

DROP DATABASE IF EXISTS format_check;
CREATE DATABASE format_check;
GRANT ALL PRIVILEGES ON DATABASE format_check TO postgres;
\connect format_check;
CREATE TABLE public.output (
    id uuid NOT NULL PRIMARY KEY,
    thesis_id character varying(255) NOT NULL,
    file_name character varying(255) NOT NULL,
    file_location character varying(255) NOT NULL,
    result character varying(55),
    grade character varying(55),
    uploaded_time timestamp with time zone NOT NULL
);

DROP DATABASE IF EXISTS chapter_summarization;
CREATE DATABASE chapter_summarization;
GRANT ALL PRIVILEGES ON DATABASE chapter_summarization TO postgres;
\connect chapter_summarization;
CREATE TABLE public.output (
    id uuid NOT NULL PRIMARY KEY,
    thesis_id character varying(255) NOT NULL,
    file_name character varying(255) NOT NULL,
    file_location character varying(255) NOT NULL,
    result character varying(55),
    grade character varying(55),
    uploaded_time timestamp with time zone NOT NULL
);

DROP DATABASE IF EXISTS major_classifier;
CREATE DATABASE major_classifier;
GRANT ALL PRIVILEGES ON DATABASE major_classifier TO postgres;
\connect major_classifier;
CREATE TABLE public.output (
    id uuid NOT NULL PRIMARY KEY,
    thesis_id character varying(255) NOT NULL,
    file_name character varying(255) NOT NULL,
    file_location character varying(255) NOT NULL,
    annotation_file_location character varying(255),
    result character varying(55),
    grade character varying(55),
    uploaded_time timestamp with time zone NOT NULL
);

DROP DATABASE IF EXISTS page_count;
CREATE DATABASE page_count;
GRANT ALL PRIVILEGES ON DATABASE page_count TO postgres;
\connect page_count;
CREATE TABLE public.output (
    id uuid NOT NULL PRIMARY KEY,
    thesis_id character varying(255) NOT NULL,
    file_name character varying(255) NOT NULL,
    file_location character varying(255) NOT NULL,
    result character varying(55),
    grade character varying(55),
    uploaded_time timestamp with time zone NOT NULL
);

DROP DATABASE IF EXISTS table_of_content;
CREATE DATABASE table_of_content;
GRANT ALL PRIVILEGES ON DATABASE table_of_content TO postgres;
\connect table_of_content;
CREATE TABLE public.output (
    id uuid NOT NULL PRIMARY KEY,
    thesis_id character varying(255) NOT NULL,
    file_name character varying(255) NOT NULL,
    file_location character varying(255) NOT NULL,
    result character varying(55),
    grade character varying(55),
    uploaded_time timestamp with time zone NOT NULL
);

DROP DATABASE IF EXISTS citation;
CREATE DATABASE citation;
GRANT ALL PRIVILEGES ON DATABASE citation TO postgres;
\connect citation;
CREATE TABLE public.output (
    id uuid NOT NULL PRIMARY KEY,
    thesis_id character varying(255) NOT NULL,
    file_name character varying(255) NOT NULL,
    file_location character varying(255) NOT NULL,
    result character varying(55),
    grade character varying(55),
    uploaded_time timestamp with time zone NOT NULL
);

DROP DATABASE IF EXISTS table_figure_detection;
CREATE DATABASE table_figure_detection;
GRANT ALL PRIVILEGES ON DATABASE table_figure_detection TO postgres;
\connect table_figure_detection;
CREATE TABLE public.output (
    id uuid NOT NULL PRIMARY KEY,
    thesis_id character varying(255) NOT NULL,
    file_name character varying(255) NOT NULL,
    file_location character varying(255) NOT NULL,
    result character varying(55),
    grade character varying(55),
    uploaded_time timestamp with time zone NOT NULL
);

DROP DATABASE IF EXISTS grammar;
CREATE DATABASE grammar;
GRANT ALL PRIVILEGES ON DATABASE grammar TO postgres;
\connect grammar;
CREATE TABLE public.output (
    id uuid NOT NULL PRIMARY KEY,
    thesis_id character varying(255) NOT NULL,
    file_name character varying(255) NOT NULL,
    file_location character varying(255) NOT NULL,
    result character varying(55),
    grade character varying(55),
    uploaded_time timestamp with time zone NOT NULL
);

DROP DATABASE IF EXISTS thesis_upload;
CREATE DATABASE thesis_upload;
GRANT ALL PRIVILEGES ON DATABASE thesis_upload TO postgres;
\connect thesis_upload;
CREATE TABLE public.user_type (
    id INTEGER NOT NULL PRIMARY KEY,
    type_name character varying(30) NOT NULL
);
CREATE TABLE public.user (
    id character varying(11) NOT NULL PRIMARY KEY,
    full_name character varying(120) NOT NULL,
    password character varying(36) NOT NULL,
    type_id integer REFERENCES public.user_type(id) ON DELETE SET NULL ON UPDATE CASCADE
);
CREATE TABLE public.instructor (
    instructor_id character varying(11) NOT NULL PRIMARY KEY REFERENCES public.user(id) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE TABLE public.student (
    student_id character varying(11) NOT NULL PRIMARY KEY REFERENCES public.user(id) ON DELETE CASCADE ON UPDATE CASCADE,
    instructor_id character varying(11) NOT NULL REFERENCES public.instructor(instructor_id) ON DELETE CASCADE ON UPDATE CASCADE,
    has_submitted boolean DEFAULT false NOT NULL
);
CREATE TABLE public.thesis (
    id uuid NOT NULL PRIMARY KEY,
    instructor_id character varying(11) NOT NULL REFERENCES public.instructor(instructor_id) ON DELETE SET NULL ON UPDATE CASCADE,
    student_id character(11) NOT NULL REFERENCES public.student(student_id) ON DELETE CASCADE ON UPDATE CASCADE,
    thesis_name character varying(255) NOT NULL,
    file_location character varying(255) NOT NULL,
    file_name character varying(255) NOT NULL,
    submitted_time timestamp with time zone NOT NULL,
    last_modified timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP 
);
CREATE TABLE public.event (
    id uuid NOT NULL PRIMARY KEY,
    thesis_id uuid NOT NULL REFERENCES public.thesis(id) ON DELETE CASCADE ON UPDATE CASCADE,
    service_type character varying(55) NOT NULL,
    output_location character varying(255),
    output_annotation_location character varying(255),
    service_status character varying(55),
    result character varying(55),
    grade character varying(55)
);
CREATE TABLE public.deadline (
    id serial NOT NULL PRIMARY KEY,
    deadline timestamp with time zone NOT NULL
);
CREATE TABLE public.notification (
    id serial NOT NULL PRIMARY KEY,
    title character varying(255) NOT NULL,
    content character varying(255) NOT NULL,
    submitted_time timestamp with time zone NOT NULL
);
CREATE TABLE public.notification_seen (
    id serial NOT NULL PRIMARY KEY,
    notification_id serial NOT NULL REFERENCES public.notification(id) ON DELETE CASCADE ON UPDATE CASCADE,
    user_id character varying(11) NOT NULL REFERENCES public.user(id) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE TABLE public.feedback (
    id uuid NOT NULL PRIMARY KEY,
    thesis_id uuid NOT NULL REFERENCES public.thesis(id) ON DELETE CASCADE,
    content character varying(500) NOT NULL,
    submitted_time timestamp with time zone NOT NULL
);

INSERT INTO public.user_type(id, type_name) VALUES (1, 'Admin');
INSERT INTO public.user_type(id, type_name) VALUES (2, 'Instructor');
INSERT INTO public.user_type(id, type_name) VALUES (3, 'Student');

INSERT INTO public.deadline (deadline) VALUES ('2026-12-01 00:00:00+07');

INSERT INTO public.user (id, full_name, password, type_id) VALUES ('ITITADMIN01', 'Admin', '@IU_Ad#20/24', 1);

INSERT INTO public.user (id, full_name, password, type_id) VALUES ('ITITIU20043', 'Dang Nhat Huy', '13052002', 3);
INSERT INTO public.user (id, full_name, password, type_id) VALUES ('ITITIU20354', 'Pham Minh Vu', '10112002', 3);
INSERT INTO public.user (id, full_name, password, type_id) VALUES ('ITITIU20134', 'Trinh Duc Bao', '06092002', 3);
INSERT INTO public.user (id, full_name, password, type_id) VALUES ('ITITIU20163', 'Nguyen Luan Cong Bang', '07112002', 3);
INSERT INTO public.user (id, full_name, password, type_id) VALUES ('ITDSIU20090', 'Nguyen Hoang Anh Tu', '13062002', 3);
INSERT INTO public.user (id, full_name, password, type_id) VALUES ('ITDSIU20031', 'Nguyen Quang Dieu', '29052002', 3);
INSERT INTO public.user (id, full_name, password, type_id) VALUES ('ITITIU20111', 'Bui Thi Cam Van', '08122002', 3);
INSERT INTO public.user (id, full_name, password, type_id) VALUES ('ITDSIU20085', 'Pham Le Duc Thinh', '07012002', 3);
INSERT INTO public.user (id, full_name, password, type_id) VALUES ('ITDSIU20032', 'Duong Tran Nhat Minh', '29102002', 3);
INSERT INTO public.user (id, full_name, password, type_id) VALUES ('ITDSIU20056', 'Nguyen Thanh Binh', '01062002', 3);
INSERT INTO public.user (id, full_name, password, type_id) VALUES ('ITITIU20252', 'Phan Ngoc Dong Minh', '15102002', 3);
INSERT INTO public.user (id, full_name, password, type_id) VALUES ('ITITIU20338', 'Tran Thi Ngoc Tu', '20112002', 3);

INSERT INTO public.user (id, full_name, password, type_id) VALUES ('ITITEACH001', 'Tran Thanh Tung', '123456789', 2);
INSERT INTO public.user (id, full_name, password, type_id) VALUES ('ITITEACH002', 'Nguyen Van Sinh', '123456789', 2);
INSERT INTO public.user (id, full_name, password, type_id) VALUES ('ITITEACH003', 'Nguyen Thi Thuy Loan', '123456789', 2);
INSERT INTO public.user (id, full_name, password, type_id) VALUES ('ITITEACH004', 'Vo Thi Luu Phuong', '123456789', 2);
INSERT INTO public.user (id, full_name, password, type_id) VALUES ('ITITEACH005', 'Ha Viet Uyen Synh', '123456789', 2);
INSERT INTO public.user (id, full_name, password, type_id) VALUES ('ITITEACH006', 'Dinh Duc Anh Vu', '123456789', 2);
INSERT INTO public.user (id, full_name, password, type_id) VALUES ('ITITEACH007', 'Huynh Kha Tu', '123456789', 2);
INSERT INTO public.user (id, full_name, password, type_id) VALUES ('ITITEACH008', 'Le Duy Tan', '123456789', 2);
INSERT INTO public.user (id, full_name, password, type_id) VALUES ('ITITEACH009', 'Le Hai Duong', '123456789', 2);
INSERT INTO public.user (id, full_name, password, type_id) VALUES ('ITITEACH010', 'Ly Tu Nga', '123456789', 2);
INSERT INTO public.user (id, full_name, password, type_id) VALUES ('ITITEACH011', 'Le Thanh Son', '123456789', 2);

INSERT INTO public.instructor (instructor_id) VALUES ('ITITEACH001');
INSERT INTO public.instructor (instructor_id) VALUES ('ITITEACH002');
INSERT INTO public.instructor (instructor_id) VALUES ('ITITEACH003');
INSERT INTO public.instructor (instructor_id) VALUES ('ITITEACH004');
INSERT INTO public.instructor (instructor_id) VALUES ('ITITEACH005');
INSERT INTO public.instructor (instructor_id) VALUES ('ITITEACH006');
INSERT INTO public.instructor (instructor_id) VALUES ('ITITEACH007');
INSERT INTO public.instructor (instructor_id) VALUES ('ITITEACH008');
INSERT INTO public.instructor (instructor_id) VALUES ('ITITEACH009');
INSERT INTO public.instructor (instructor_id) VALUES ('ITITEACH010');
INSERT INTO public.instructor (instructor_id) VALUES ('ITITEACH011');

INSERT INTO public.student (student_id, instructor_id) VALUES ('ITITIU20043', 'ITITEACH001');
INSERT INTO public.student (student_id, instructor_id) VALUES ('ITITIU20354', 'ITITEACH002');
INSERT INTO public.student (student_id, instructor_id) VALUES ('ITITIU20134', 'ITITEACH003');
INSERT INTO public.student (student_id, instructor_id) VALUES ('ITITIU20163', 'ITITEACH004');
INSERT INTO public.student (student_id, instructor_id) VALUES ('ITDSIU20090', 'ITITEACH005');
INSERT INTO public.student (student_id, instructor_id) VALUES ('ITDSIU20031', 'ITITEACH006');
INSERT INTO public.student (student_id, instructor_id) VALUES ('ITITIU20111', 'ITITEACH007');
INSERT INTO public.student (student_id, instructor_id) VALUES ('ITDSIU20085', 'ITITEACH008');
INSERT INTO public.student (student_id, instructor_id) VALUES ('ITDSIU20032', 'ITITEACH009');
INSERT INTO public.student (student_id, instructor_id) VALUES ('ITDSIU20056', 'ITITEACH010');
INSERT INTO public.student (student_id, instructor_id) VALUES ('ITITIU20252', 'ITITEACH011');
INSERT INTO public.student (student_id, instructor_id) VALUES ('ITITIU20338', 'ITITEACH006');
