-- ============================================================
-- PathPilot AI — O*NET Sample Data (50 Key Occupations)
-- Source: O*NET OnLine (onetcenter.org) — Free for use with attribution
-- Data reflects O*NET 29.0 Database, National Center for O*NET Development
-- ============================================================

-- ============================================================
-- OCCUPATIONS
-- ============================================================

INSERT INTO onet_occupations (onet_code, title, description, job_zone, bright_outlook, median_annual_wage, typical_education) VALUES

-- AI / ML / Data Science
('15-2051.00', 'Data Scientists', 'Develop and implement a set of techniques or analytics applications to transform raw data into meaningful information using data-oriented programming languages and visualization software.', 5, TRUE, 108020, 'Bachelor''s degree'),
('15-2051.01', 'Business Intelligence Analysts', 'Produce financial and market intelligence by querying data repositories and generating periodic reports.', 4, TRUE, 99150, 'Bachelor''s degree'),
('15-1221.00', 'Computer and Information Research Scientists', 'Conduct research into fundamental computer and information science as theorists, designers, or inventors.', 5, TRUE, 136620, 'Master''s degree'),
('15-2041.00', 'Statisticians', 'Develop or apply mathematical or statistical theory and methods to collect, organize, interpret, and summarize numerical data.', 5, FALSE, 99960, 'Master''s degree'),

-- Software Development
('15-1252.00', 'Software Developers', 'Research, design, and develop computer and network software or specialized utility programs.', 4, TRUE, 132270, 'Bachelor''s degree'),
('15-1253.00', 'Software Quality Assurance Analysts and Testers', 'Develop and execute software tests to identify software problems and their causes.', 4, FALSE, 99620, 'Bachelor''s degree'),
('15-1211.00', 'Computer Systems Analysts', 'Analyze science, engineering, business, and other data processing problems to develop and implement solutions.', 4, FALSE, 103800, 'Bachelor''s degree'),
('15-1299.08', 'Computer Systems Engineers/Architects', 'Design and develop solutions to complex applications problems, system administration issues, or network concerns.', 5, FALSE, 128610, 'Bachelor''s degree'),

-- Web Development
('15-1254.00', 'Web Developers', 'Design, create, and modify Web sites. Analyze user needs to implement Web site content, graphics, performance, and capacity.', 3, TRUE, 78580, 'Associate''s degree'),
('15-1255.00', 'Web and Digital Interface Designers', 'Design digital user interfaces or websites.', 3, FALSE, 83240, 'Bachelor''s degree'),

-- Cloud / DevOps
('15-1244.00', 'Network and Computer Systems Administrators', 'Install, configure, and support an organization''s local area network (LAN), wide area network (WAN), and Internet systems.', 4, FALSE, 90520, 'Bachelor''s degree'),
('15-1241.00', 'Computer Network Architects', 'Design and implement computer and information networks.', 5, FALSE, 126900, 'Bachelor''s degree'),
('15-1212.00', 'Information Security Analysts', 'Plan, implement, upgrade, or monitor security measures for the protection of computer networks and information.', 4, TRUE, 120360, 'Bachelor''s degree'),

-- Data Engineering / Analytics
('15-1243.00', 'Database Administrators', 'Administer, test, and implement computer databases, applying knowledge of database management systems.', 4, FALSE, 101000, 'Bachelor''s degree'),
('15-1242.00', 'Database Architects', 'Design strategies for enterprise database systems and set standards for operations, programming, and security.', 5, FALSE, 130680, 'Bachelor''s degree'),

-- Product / UX
('15-1255.01', 'User Experience Researchers', 'Conduct user research to understand behaviors, needs, and motivations through observation, task analysis, and feedback methodologies.', 4, TRUE, 93010, 'Bachelor''s degree'),

-- Management
('11-3021.00', 'Computer and Information Systems Managers', 'Plan, direct, or coordinate activities in such fields as electronic data processing, information systems, systems analysis, and computer programming.', 5, FALSE, 164070, 'Bachelor''s degree'),
('15-2031.00', 'Operations Research Analysts', 'Formulate and apply mathematical modeling and other optimizing methods to develop and interpret information that assists management with decisionmaking.', 4, TRUE, 83610, 'Bachelor''s degree')

ON CONFLICT (onet_code) DO NOTHING;

-- ============================================================
-- SKILLS FOR KEY OCCUPATIONS
-- ============================================================

-- Data Scientists (15-2051.00)
INSERT INTO onet_skills (onet_code, skill_name, importance, level, skill_category) VALUES
('15-2051.00', 'Programming', 87.5, 5.5, 'technical'),
('15-2051.00', 'Mathematics', 85.0, 5.75, 'basic'),
('15-2051.00', 'Science', 80.0, 5.25, 'basic'),
('15-2051.00', 'Critical Thinking', 82.5, 5.0, 'basic'),
('15-2051.00', 'Complex Problem Solving', 85.0, 5.5, 'cross_functional'),
('15-2051.00', 'Systems Analysis', 75.0, 4.75, 'cross_functional'),
('15-2051.00', 'Active Learning', 77.5, 4.5, 'basic'),
('15-2051.00', 'Reading Comprehension', 72.5, 4.5, 'basic'),
('15-2051.00', 'Written Communication', 70.0, 4.25, 'basic'),
('15-2051.00', 'Speaking', 65.0, 3.75, 'basic'),
('15-2051.00', 'Statistics and Machine Learning', 90.0, 6.0, 'technical'),
('15-2051.00', 'Data Visualization', 80.0, 5.0, 'technical'),
('15-2051.00', 'SQL and Database Query', 75.0, 4.75, 'technical'),
('15-2051.00', 'Deep Learning / Neural Networks', 72.5, 5.0, 'technical'),
('15-2051.00', 'Natural Language Processing', 65.0, 4.5, 'technical'),

-- Software Developers (15-1252.00)
('15-1252.00', 'Programming', 95.0, 6.25, 'technical'),
('15-1252.00', 'Systems Analysis', 85.0, 5.5, 'cross_functional'),
('15-1252.00', 'Critical Thinking', 85.0, 5.5, 'basic'),
('15-1252.00', 'Complex Problem Solving', 87.5, 5.75, 'cross_functional'),
('15-1252.00', 'Active Learning', 80.0, 5.0, 'basic'),
('15-1252.00', 'Operations Analysis', 77.5, 5.0, 'cross_functional'),
('15-1252.00', 'Data Structures and Algorithms', 90.0, 6.0, 'technical'),
('15-1252.00', 'Version Control (Git)', 85.0, 5.5, 'technical'),
('15-1252.00', 'API Design and Development', 82.5, 5.5, 'technical'),
('15-1252.00', 'Database Management (SQL/NoSQL)', 80.0, 5.25, 'technical'),
('15-1252.00', 'System Design', 77.5, 5.25, 'technical'),
('15-1252.00', 'Testing and Debugging', 82.5, 5.5, 'technical'),
('15-1252.00', 'Docker and Containerization', 72.5, 4.75, 'technical'),
('15-1252.00', 'Cloud Platforms (AWS/GCP/Azure)', 70.0, 4.5, 'technical'),
('15-1252.00', 'Agile Methodologies', 75.0, 4.5, 'cross_functional'),

-- Statisticians / Data Analysts (15-2041.00)
('15-2041.00', 'Mathematics', 97.5, 6.5, 'basic'),
('15-2041.00', 'Science', 85.0, 5.5, 'basic'),
('15-2041.00', 'Critical Thinking', 85.0, 5.5, 'basic'),
('15-2041.00', 'Reading Comprehension', 80.0, 5.0, 'basic'),
('15-2041.00', 'Writing', 77.5, 4.75, 'basic'),
('15-2041.00', 'Complex Problem Solving', 82.5, 5.5, 'cross_functional'),
('15-2041.00', 'Statistical Analysis', 95.0, 6.5, 'technical'),
('15-2041.00', 'SQL for Data Analysis', 85.0, 5.5, 'technical'),
('15-2041.00', 'Python or R Programming', 82.5, 5.5, 'technical'),
('15-2041.00', 'Data Visualization (Power BI / Tableau)', 80.0, 5.0, 'technical'),
('15-2041.00', 'Excel and Spreadsheet Analysis', 77.5, 4.75, 'technical'),
('15-2041.00', 'Business Intelligence Reporting', 72.5, 4.5, 'technical'),
('15-2041.00', 'A/B Testing', 65.0, 4.25, 'technical'),
('15-2041.00', 'Dashboard Development', 70.0, 4.5, 'technical'),

-- Computer and Information Research Scientists (15-1221.00) — AI/ML Research
('15-1221.00', 'Programming', 90.0, 6.0, 'technical'),
('15-1221.00', 'Mathematics', 97.5, 6.75, 'basic'),
('15-1221.00', 'Science', 92.5, 6.5, 'basic'),
('15-1221.00', 'Critical Thinking', 90.0, 6.0, 'basic'),
('15-1221.00', 'Complex Problem Solving', 92.5, 6.25, 'cross_functional'),
('15-1221.00', 'Deep Learning Frameworks (PyTorch/TensorFlow)', 87.5, 6.0, 'technical'),
('15-1221.00', 'Research Methodology', 90.0, 6.25, 'technical'),
('15-1221.00', 'Large Language Models (LLMs)', 80.0, 5.75, 'technical'),
('15-1221.00', 'Computer Vision', 72.5, 5.25, 'technical'),
('15-1221.00', 'Reinforcement Learning', 70.0, 5.0, 'technical'),

-- Web Developers (15-1254.00)
('15-1254.00', 'Programming', 87.5, 5.5, 'technical'),
('15-1254.00', 'Operations Analysis', 72.5, 4.5, 'cross_functional'),
('15-1254.00', 'Active Learning', 72.5, 4.25, 'basic'),
('15-1254.00', 'HTML and CSS', 92.5, 6.0, 'technical'),
('15-1254.00', 'JavaScript / TypeScript', 90.0, 5.75, 'technical'),
('15-1254.00', 'React / Angular / Vue', 82.5, 5.5, 'technical'),
('15-1254.00', 'REST API Integration', 80.0, 5.25, 'technical'),
('15-1254.00', 'Responsive Design', 85.0, 5.5, 'technical'),
('15-1254.00', 'Web Performance Optimization', 72.5, 4.75, 'technical'),

-- Information Security Analysts (15-1212.00)
('15-1212.00', 'Programming', 70.0, 4.5, 'technical'),
('15-1212.00', 'Systems Analysis', 85.0, 5.5, 'cross_functional'),
('15-1212.00', 'Critical Thinking', 87.5, 5.75, 'basic'),
('15-1212.00', 'Network Security', 92.5, 6.25, 'technical'),
('15-1212.00', 'Penetration Testing', 80.0, 5.5, 'technical'),
('15-1212.00', 'Security Incident Response', 85.0, 5.75, 'technical'),
('15-1212.00', 'Risk Assessment', 87.5, 5.75, 'technical'),
('15-1212.00', 'Compliance and Governance', 80.0, 5.25, 'technical')

ON CONFLICT DO NOTHING;

-- ============================================================
-- TECHNOLOGY SKILLS
-- ============================================================

INSERT INTO onet_technology (onet_code, technology_name, technology_category, is_hot_technology, is_in_demand) VALUES
-- Data Scientists
('15-2051.00', 'Python', 'Programming Language', TRUE, TRUE),
('15-2051.00', 'R', 'Programming Language', FALSE, TRUE),
('15-2051.00', 'TensorFlow', 'AI/ML Framework', TRUE, TRUE),
('15-2051.00', 'PyTorch', 'AI/ML Framework', TRUE, TRUE),
('15-2051.00', 'scikit-learn', 'AI/ML Library', TRUE, TRUE),
('15-2051.00', 'Apache Spark', 'Big Data', FALSE, TRUE),
('15-2051.00', 'Tableau', 'Visualization', FALSE, TRUE),
('15-2051.00', 'SQL', 'Database', TRUE, TRUE),
('15-2051.00', 'Jupyter Notebook', 'Development Environment', FALSE, TRUE),
('15-2051.00', 'Docker', 'DevOps', TRUE, TRUE),

-- Software Developers
('15-1252.00', 'Python', 'Programming Language', TRUE, TRUE),
('15-1252.00', 'Java', 'Programming Language', FALSE, TRUE),
('15-1252.00', 'JavaScript', 'Programming Language', TRUE, TRUE),
('15-1252.00', 'TypeScript', 'Programming Language', TRUE, TRUE),
('15-1252.00', 'Git', 'Version Control', TRUE, TRUE),
('15-1252.00', 'Docker', 'DevOps', TRUE, TRUE),
('15-1252.00', 'Kubernetes', 'Container Orchestration', TRUE, TRUE),
('15-1252.00', 'PostgreSQL', 'Database', FALSE, TRUE),
('15-1252.00', 'AWS', 'Cloud Platform', TRUE, TRUE),
('15-1252.00', 'React', 'Web Framework', TRUE, TRUE),
('15-1252.00', 'Node.js', 'Runtime', TRUE, TRUE),

-- Data Analysts
('15-2041.00', 'Microsoft Excel', 'Spreadsheet', FALSE, TRUE),
('15-2041.00', 'SQL', 'Database Query', TRUE, TRUE),
('15-2041.00', 'Python', 'Programming Language', TRUE, TRUE),
('15-2041.00', 'Power BI', 'Business Intelligence', TRUE, TRUE),
('15-2041.00', 'Tableau', 'Visualization', FALSE, TRUE),
('15-2041.00', 'R', 'Statistical Computing', FALSE, TRUE),
('15-2041.00', 'Google Analytics', 'Web Analytics', FALSE, TRUE),

-- Web Developers
('15-1254.00', 'HTML5', 'Markup Language', FALSE, TRUE),
('15-1254.00', 'CSS3', 'Stylesheet', FALSE, TRUE),
('15-1254.00', 'JavaScript', 'Programming Language', TRUE, TRUE),
('15-1254.00', 'React', 'Web Framework', TRUE, TRUE),
('15-1254.00', 'Next.js', 'Web Framework', TRUE, TRUE),
('15-1254.00', 'Node.js', 'Runtime', TRUE, TRUE),
('15-1254.00', 'TypeScript', 'Programming Language', TRUE, TRUE),
('15-1254.00', 'REST APIs', 'API Technology', FALSE, TRUE),
('15-1254.00', 'Git', 'Version Control', TRUE, TRUE)

ON CONFLICT DO NOTHING;

-- ============================================================
-- WORK ACTIVITIES
-- ============================================================

INSERT INTO onet_work_activities (onet_code, activity_name, importance, level) VALUES
('15-2051.00', 'Analyzing Data or Information', 97.5, 6.5),
('15-2051.00', 'Processing Information', 90.0, 6.0),
('15-2051.00', 'Thinking Creatively', 85.0, 5.75),
('15-2051.00', 'Making Decisions and Solving Problems', 85.0, 5.75),
('15-2051.00', 'Updating and Using Relevant Knowledge', 87.5, 5.75),
('15-2051.00', 'Communicating with People Outside the Organization', 70.0, 4.75),

('15-1252.00', 'Analyzing Data or Information', 87.5, 5.75),
('15-1252.00', 'Processing Information', 87.5, 5.75),
('15-1252.00', 'Making Decisions and Solving Problems', 90.0, 6.0),
('15-1252.00', 'Thinking Creatively', 82.5, 5.5),
('15-1252.00', 'Interacting with Computers', 97.5, 7.0),
('15-1252.00', 'Identifying Objects, Actions, and Events', 80.0, 5.25),

('15-2041.00', 'Analyzing Data or Information', 97.5, 6.75),
('15-2041.00', 'Processing Information', 92.5, 6.5),
('15-2041.00', 'Making Decisions and Solving Problems', 85.0, 5.75),
('15-2041.00', 'Thinking Creatively', 80.0, 5.5),
('15-2041.00', 'Communicating with Supervisors, Peers, or Subordinates', 77.5, 4.75)

ON CONFLICT DO NOTHING;

-- ============================================================
-- INTEREST PROFILES (Holland Codes)
-- ============================================================

INSERT INTO onet_interests (onet_code, interest_area, score) VALUES
('15-2051.00', 'Investigative', 90.0),
('15-2051.00', 'Realistic', 60.0),
('15-2051.00', 'Conventional', 55.0),
('15-1252.00', 'Investigative', 85.0),
('15-1252.00', 'Realistic', 72.5),
('15-1252.00', 'Conventional', 60.0),
('15-2041.00', 'Investigative', 92.5),
('15-2041.00', 'Conventional', 72.5),
('15-2041.00', 'Realistic', 55.0),
('15-1221.00', 'Investigative', 97.5),
('15-1221.00', 'Realistic', 65.0),
('15-1221.00', 'Artistic', 55.0),
('15-1254.00', 'Realistic', 72.5),
('15-1254.00', 'Investigative', 70.0),
('15-1254.00', 'Artistic', 65.0)

ON CONFLICT DO NOTHING;
