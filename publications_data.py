"""Structured catalog of Dr. Cesar Marolla's books, peer-reviewed papers, preprints, and biography.
To add a new book, paper, or preprint later, simply append a new dictionary entry to the lists below.
"""

PROFILE = {
    "name": "Cesar Marolla, PhD, ALM",
    "tagline": "Risk Mechanism Theory Index (RMTI) · Disaster-Risk Reduction, Climate Resilience & Clinical Oncology Triage",
    "email": "cesar.marolla@alumni.harvard.edu",
    "website": "https://owlstown.net",
    "links": [
        ("Academic Website", "https://owlstown.net"),
        ("Google Scholar", "https://google.com"),
        ("Harvard DASH Repository", "https://harvard.edu"),
        ("ORCID", "https://orcid.org"),
        ("LinkedIn", "https://linkedin.com"),
    ],
    "summary": (
        "Dr. Cesar Marolla is a researcher, educator, and systems risk architect bridging disaster-risk reduction, "
        "urban infrastructure resilience, and quantitative clinical oncology triage. He is the creator of the Risk "
        "Mechanism Theory Index (RMTI), a unified computational framework that decomposes systemic failure across "
        "hazard likelihood (L), exposure (E), vulnerability (V), and resilience capacity (ρ)."
    ),
    "appointments": [
        {
            "role": "Instructor, Division of Continuing Education",
            "org": "Harvard University",
            "detail": "Teaching ENVR E-241: Risk by Design: Building Resilience into Urban Infrastructure.",
        },
        {
            "role": "Visiting Professor, Sustainable Urbanization & Development MBA",
            "org": "Nalanda University",
            "detail": "Graduate instruction on resilient urban systems, climate adaptation, and sustainable development.",
        },
        {
            "role": "Lead Author & Consultant, Sub-Saharan Africa Urban Investment Resilience Program",
            "org": "World Bank Group",
            "detail": "Authored engineering and investment resilience frameworks for infrastructure project design across Sub-Saharan Africa.",
        },
    ],
    "education": [
        ("PhD", "Glasgow Caledonian University"),
        ("ALM (Master of Liberal Arts)", "Harvard University"),
        ("BSc (Cum Laude)", "Columbia College"),
        ("Executive Education Certificate — Sustainability Leadership", "Harvard T.H. Chan School of Public Health"),
    ],
    "honors": [
        ("Derek Bok Civic Award (2013)", "Harvard University (Commencement Committee) — Recognized for outstanding public impact, creative community initiatives, and civic achievement."),
        ("Commander's Challenge Coin & Commendation (2004)", "U.S. Department of Defense (395th QM BN) — Awarded by Lt. Colonel L. Smith for exceptional civilian performance during the Global War on Terror (GWOT)."),
    ],
}

BOOKS_AND_MONOGRAPHS = [
    {
        "title": "Climate Health Risks in Megacities: Sustainable Management and Strategic Planning",
        "year": "2019",
        "publisher": "CRC Press / Taylor & Francis",
        "domain": "Disaster & Climate Health",
        "url": "https://taylorfrancis.com",
        "secondary_url": "https://google.com",
        "summary": "Examines compounding climate hazards, air pollution (1–10 ppb), and health-system vulnerability in high-density megacities, establishing strategic planning models for urban health resilience.",
    },
    {
        "title": "Information and Communication Technology for Sustainable Development",
        "year": "2018",
        "publisher": "CRC Press / Taylor & Francis",
        "domain": "Systems & Digital Resilience",
        "url": "https://taylorfrancis.com",
        "secondary_url": "",
        "summary": "Synthesizes sustainability assessments, digital infrastructure governance, and operational resilience frameworks for enterprise and public-sector systems.",
    },
    {
        "title": "Climate Resilient Investment in Sub-Saharan Africa Compendium Volume — A Focus on Infrastructure Project Design in Key Sectors",
        "year": "2023",
        "publisher": "World Bank Group (Lead Author & Consultant)",
        "domain": "Disaster & Infrastructure Resilience",
        "url": "https://worldbank.org",
        "secondary_url": "",
        "summary": "World Bank technical compendium operationalizing climate-resilient infrastructure project design across Sub-Saharan African metropolitan systems.",
    },
]

PEER_REVIEWED_AND_CHAPTERS = [
    {
        "title": "From Narrative to Algorithm: A Risk Mechanism Theory Index for Urban Infrastructure Investment in Sub-Saharan Africa",
        "year": "2026",
        "venue": "International Journal of Management and Data Analytics (IJMADA), 6(1): 354–388",
        "domain": "Disaster Science & RMTI Core",
        "url": "https://ijmada.com",
        "summary": "Formalizes the RMTI deterministic scoring algorithm and Expected Annual Loss (EAL) tie-breaker across six Sub-Saharan African urban infrastructure portfolios.",
    },
    {
        "title": "California Wildfires: A Holistic Systemic Management Approach to Urban Resilience",
        "year": "2025",
        "venue": "Cambridge University Press",
        "domain": "Disaster Science",
        "url": "https://cambridge.org",
        "summary": "Analyzes systemic wildfire degradation, psychological health threats, and integrated risk-governance strategies for wildland-urban interface communities.",
    },
    {
        "title": "Urban Flood Resilience: Risk and Business Continuity Management Systems Strategic Approach",
        "year": "2024",
        "venue": "Cambridge University Press",
        "domain": "Disaster Science",
        "url": "https://cambridge.org",
        "summary": "Integrates ISO-aligned business continuity management with urban hydrological flood resilience planning under rapid urbanization.",
    },
    {
        "title": "ICT Transformation in Healthcare: A Risk-Based Approach for Climate Adaptation in Low and Middle-Income Countries",
        "year": "2024",
        "venue": "Cambridge University Press",
        "domain": "Digital Health & Resilience",
        "url": "https://cambridge.org",
        "summary": "Develops a risk-based health information technology framework to buffer LMIC healthcare delivery systems against climate-driven demand surges.",
    },
    {
        "title": "Urban Climate Health Risks and Resilience",
        "year": "2024",
        "venue": "Harvard DASH Repository",
        "domain": "Climate Health",
        "url": "https://harvard.edu",
        "summary": "Evaluates clinical and public-health system vulnerabilities driven by urban heat islands and extreme climate events.",
    },
    {
        "title": "The Dynamics of Global Risks: Sociopolitical Risks in Strategic Management and Policy Decisions",
        "year": "2023",
        "venue": "Developments in Managing and Exploiting Risk (OAPEN)",
        "domain": "Risk Governance",
        "url": "https://oapen.org",
        "summary": "Examines cascading sociopolitical and systemic hazards in strategic policy design.",
    },
    {
        "title": "Climate Change Impacts on Health: The Urban Poor in the World's Megacities",
        "year": "2020",
        "venue": "Harvard DASH Repository",
        "domain": "Climate Health Equity",
        "url": "https://harvard.edu",
        "summary": "Investigates disproportionate climate-health exposure and vulnerability among low-income urban populations.",
    },
    {
        "title": "Health in the Digital World",
        "year": "2020",
        "venue": "Harvard DASH Repository",
        "domain": "Digital Health",
        "url": "https://harvard.edu",
        "summary": "Analyzes health information technology (HIT) adoption and digital resilience across evolving clinical care systems.",
    },
    {
        "title": "Leading Through Uncertainty",
        "year": "2018",
        "venue": "The Routledge Companion to Risk, Crisis and Security in Business",
        "domain": "Risk Management",
        "url": "https://taylorfrancis.com",
        "summary": "Book chapter detailing executive decision-making and institutional resilience under high-uncertainty hazard landscapes.",
    },
]

PREPRINTS_AND_WORKING_PAPERS = [
    {
        "title": "The Risk Mechanism Theory Index (RMTI) as a Triage and Evidence-Grading Layer for Hepatocellular-Carcinoma Surveillance",
        "year": "2026",
        "venue": "SSRN (Abstract 7427450) & Research Square",
        "domain": "Clinical Oncology · HCC",
        "url": "https://ssrn.com",
        "summary": "Translates RMTI into a computable, HL7 FHIR-compatible triage and surveillance-adequacy (ρ) grading model across heterogeneous cirrhosis and HCC cohorts.",
    },
    {
        "title": "From Narrative to Algorithm: A Risk Mechanism Theory Index for Urban Infrastructure Investment in Sub-Saharan Africa (Preprint)",
        "year": "2026",
        "venue": "SSRN (Abstract 7707038)",
        "domain": "Disaster Science · Preprint",
        "url": "https://ssrn.com",
        "summary": "Working paper version establishing the mathematical derivation, sensitivity bounds, and equity-weighted EAL ranking.",
    },
    {
