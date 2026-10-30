"""Original, unpublished curriculum drafts based on the 2026-2027 course list.

Lesson bodies and review questions are starting drafts, not university lecture
materials. An editor must verify and improve them before publishing a pack.
"""

TRACKS = {
    "metabolic-diseases-oncology": {
        "title": "Metabolic Diseases and Oncology",
        "description": "Medical biotechnology focused on cancer, metabolism, and translational therapeutics.",
    },
    "microbiology-immunity-infection-control": {
        "title": "Microbiology, Immunity and Infection Control",
        "description": "Medical biotechnology focused on infection, immunology, vaccines, and public health.",
    },
}

COMMON_COURSES = [
    ("2019020", "Bioengineering and Artificial Intelligence", 6, ["Biomedical engineering systems", "Experimental design and data", "Bioinformatics foundations", "Machine learning in biomedicine", "Model evaluation and bias", "Responsible translational use"]),
    ("2019021", "Technologies in Cellular and Molecular Analyses", 6, ["Specimens and pre-analytical variables", "Cell culture and microscopy", "Flow cytometry", "Nucleic-acid analysis", "Molecular assay design", "Analytical validation and quality"]),
    ("2019022", "Recombinant Antibodies in Drug Discovery and Development", 6, ["Antibody structure and function", "Antibody discovery platforms", "Recombinant engineering", "Binding and functional assays", "Preclinical development", "Manufacturing and quality attributes"]),
    ("2019024", "Biotechnologies in Drug Discovery and Manufacturing", 6, ["Therapeutic target identification", "Assay development and screening", "Lead optimization", "Biologic drug development", "Scale-up and process control", "Quality systems and lifecycle"]),
    ("2019023", "Viral Biotechnologies in Cancer and Infection", 5, ["Virus structure and replication", "Virus-host interactions", "Oncogenic viruses", "Viral vectors and engineering", "Antiviral and antitumor applications", "Biosafety and translational evidence"]),
    ("2019025", "Human Genetics", 5, ["Genome organization and inheritance", "Genetic variation", "Population genetics", "Disease-associated variants", "Molecular genetic testing", "Ethics and communication"]),
]

METABOLIC_COURSES = [
    ("2019032", "RNA Biology and Therapeutics", 6, ["RNA structure and function", "Transcription and RNA processing", "RNA modifications and regulation", "RNA therapeutic platforms", "Delivery and pharmacology", "Safety and clinical translation"]),
    ("2019033", "Genetics and Epigenetics of Cancer", 6, ["Cancer genomes", "Somatic variation and clonal evolution", "Epigenetic regulation", "Tumor heterogeneity", "Molecular profiling", "Mechanism-informed intervention"]),
    ("2019034", "Molecular Basis of Cancer Diagnosis and Therapy", 6, ["Tumor biology and biomarkers", "Pathology and molecular classification", "Diagnostic assay principles", "Biomarker validation", "Therapy selection evidence", "Limitations and clinical context"]),
    ("2019035", "Biotechnologies in Endocrine and Metabolic Diseases", 5, ["Endocrine signaling", "Metabolic regulation", "Disease mechanisms", "Biomarkers and molecular assays", "Biotechnology-based interventions", "Translational models and evidence"]),
    ("2019036", "Animal Models in Cancer and Metabolic Diseases", 2, ["Model selection and research questions", "Cancer model systems", "Metabolic disease models", "Experimental design and endpoints", "Reproducibility and limitations", "Ethics and welfare"]),
    ("2019037", "Soft Skills in Biotechnology, Scientific Writing and Communication", 1, ["Finding and evaluating scientific literature", "Research questions and argument structure", "Scientific writing", "Figures and data visualization", "Oral and team communication", "Peer review and research integrity"]),
    ("2019044", "Medical Oncology and Cancer Immunotherapy", 6, ["Cancer biology and treatment context", "Tumor-immune interactions", "Immunotherapy platforms", "Biomarkers and response assessment", "Resistance and adverse effects", "Evidence and multidisciplinary care"]),
    ("2019045", "Onco-Hematological Diseases", 6, ["Hematopoiesis and disease classification", "Leukemia and lymphoma biology", "Molecular drivers", "Diagnostic and prognostic markers", "Therapeutic strategies", "Response monitoring and evidence"]),
    ("2019046", "Experimental and Clinical Oncology", 6, ["Translational research questions", "Preclinical evidence", "Clinical trial design", "Endpoints and statistical reasoning", "Ethics and participant protection", "Integrating evidence across stages"]),
    ("2019047", "Biotechnologies for Precision Oncology", 5, ["Precision oncology principles", "Tumor profiling methods", "Target and biomarker validation", "Treatment stratification", "Resistance and combination strategies", "Clinical implementation limits"]),
]

MICROBIOLOGY_COURSES = [
    ("2019026", "Genome Editing and Synthetic Biology", 6, ["Genome editing principles", "CRISPR systems and design", "Constructs and delivery", "Editing validation", "Off-target effects and controls", "Biosafety and responsible applications"]),
    ("2019027", "Anti-Infective Drugs, Antimicrobial Resistance and One Health Approach", 6, ["Antimicrobial targets and drug classes", "Susceptibility testing", "Resistance mechanisms", "Resistance surveillance", "Stewardship and infection control", "One Health frameworks"]),
    ("2019028", "Epidemiology of Emerging and Re-emerging Pathogens and Vaccinations", 6, ["Emergence and transmission", "Epidemiological measures", "Surveillance systems", "Pathogen detection evidence", "Vaccination strategies", "Outbreak response and communication"]),
    ("2019029", "Vaccine Immunology", 6, ["Innate and adaptive immunity", "Antigen presentation", "B- and T-cell responses", "Vaccine platforms and adjuvants", "Immune assays and correlates", "Protection, durability, and limitations"]),
    ("2019030", "Animal Models in Infection and Immunity", 2, ["Model choice and research questions", "Host-pathogen systems", "Infection study design", "Immune endpoints", "Reproducibility and translation", "Ethics, welfare, and biosafety"]),
    ("2019031", "Soft Skills in Biotechnology, Scientific Writing and Communication", 1, ["Finding and evaluating scientific literature", "Research questions and argument structure", "Scientific writing", "Figures and data visualization", "Oral and team communication", "Peer review and research integrity"]),
    ("2019038", "Biotechnology in Infectious Diseases Diagnosis", 6, ["Diagnostic workflow and specimen quality", "Pathogen identification", "Molecular diagnostic methods", "Sensitivity, specificity, and prevalence", "Controls and quality assurance", "Result interpretation and limitations"]),
    ("2019039", "Omics Technologies and Big Data Analysis in Microbiology", 6, ["Omics questions and experimental design", "Sequencing and measurement platforms", "Data preprocessing", "Statistical analysis", "Microbial bioinformatics", "Reproducibility and responsible interpretation"]),
    ("2019040", "Pandemic Preparedness", 5, ["Threat assessment", "Surveillance and early warning", "Diagnostics and laboratory capacity", "Countermeasure readiness", "Response coordination", "Risk communication and review"]),
    ("2019041", "Vaccine Research and Clinical Development", 5, ["Vaccine research questions", "Antigen and platform selection", "Preclinical evaluation", "Clinical development phases", "Safety and immune endpoints", "Manufacturing and post-authorization evidence"]),
]

COURSES = COMMON_COURSES + METABOLIC_COURSES + MICROBIOLOGY_COURSES

ASSIGNMENTS = {
    "metabolic-diseases-oncology": [
        *((code, 1, "First semester", "Core") for code in ("2019020", "2019021", "2019022", "2019024")),
        *((code, 1, "First semester", "Supplementary") for code in ("2019023", "2019025")),
        *((code, 1, "Second semester", "Core") for code in ("2019032", "2019033", "2019034")),
        ("2019035", 1, "Second semester", "Supplementary"),
        ("2019036", 1, "Second semester", "Educational activity"),
        ("2019037", 1, "Second semester", "Educational activity"),
        *((code, 2, "", "Core") for code in ("2019044", "2019045", "2019046")),
        ("2019047", 2, "", "Supplementary"),
    ],
    "microbiology-immunity-infection-control": [
        *((code, 1, "First semester", "Core") for code in ("2019020", "2019021", "2019022", "2019024")),
        *((code, 1, "First semester", "Supplementary") for code in ("2019023", "2019025")),
        *((code, 1, "Second semester", "Core") for code in ("2019026", "2019027", "2019028", "2019029")),
        ("2019030", 1, "Second semester", "Educational activity"),
        ("2019031", 1, "Second semester", "Educational activity"),
        *((code, 2, "", "Core") for code in ("2019038", "2019039")),
        *((code, 2, "", "Supplementary") for code in ("2019040", "2019041")),
    ],
}

REQUIREMENTS = {
    "metabolic-diseases-oncology": [
        ("2015987", "Training Course on Health and Safety at Work — High Risk", 1, 0, "Required training"),
        ("2019050", "Student's Choice", 2, 8, "Optional study activity"),
        ("2019051", "Final Test", 2, 21, "Degree requirement"),
        ("2019049", "Seminars", 2, 3, "Educational activity"),
        ("2019048", "External Traineeship", 2, 5, "Practical requirement"),
    ],
    "microbiology-immunity-infection-control": [
        ("2015987", "Training Course on Health and Safety at Work — High Risk", 1, 0, "Required training"),
        ("2019050", "Student's Choice", 2, 8, "Optional study activity"),
        ("2019051", "Final Test", 2, 21, "Degree requirement"),
        ("2019043", "Seminars", 2, 3, "Educational activity"),
        ("2019042", "External Traineeship", 2, 5, "Practical requirement"),
    ],
}


def lesson_drafts(course_title: str, topics: list[str]) -> list[dict]:
    lessons = []
    for position, topic in enumerate(topics, 1):
        lessons.append({
            "position": position,
            "title": topic,
            "objectives": [
                f"Define the core ideas behind {topic.lower()}.",
                f"Explain how {topic.lower()} connects to {course_title.lower()}.",
                "Evaluate the evidence, controls, limitations, and responsible applications.",
            ],
            "body": (
                f"This draft lesson introduces {topic.lower()} in the context of {course_title.lower()}. "
                f"Begin by stating the biological or analytical question that {topic.lower()} addresses. "
                "Then connect the relevant mechanism to the methods used to study it, the controls needed "
                "to support the evidence, and the limits of what the result can establish. Separate a "
                "well-supported conclusion from a hypothesis, and explain how new evidence could change "
                "the interpretation. Apply validated protocols and qualified supervision to laboratory "
                "work; educational material does not replace local procedures or clinical judgment."
            ),
            "key_terms": [topic, "mechanism", "assay validation", "controls", "translational evidence"],
        })
    return lessons


def question_drafts(course_title: str, topics: list[str]) -> list[dict]:
    evidence_options = [
        "Assess the study design, controls, and limitations before interpreting the evidence.",
        "Assume a single result proves the mechanism in every biological context.",
        "Ignore pre-analytical and analytical factors if the result fits the hypothesis.",
        "Treat an exploratory finding as a validated clinical decision rule.",
    ]
    items = []
    for index in range(20):
        topic = topics[index % len(topics)]
        prompt_kind = index % 4
        if prompt_kind == 0:
            prompt = f"When reviewing evidence about {topic.lower()} in {course_title}, what is the strongest first step?"
            answer = evidence_options
            explanation = "Study design, controls, and limitations determine what the evidence can support."
            answer_index = 0
        elif prompt_kind == 1:
            prompt = f"Which statement about {topic.lower()} is most scientifically responsible?"
            answer = [
                "Interpret findings in their validated context and distinguish evidence from hypothesis.",
                "One method is sufficient regardless of specimen, platform, or question.",
                "A biological association alone establishes causation.",
                "Limitations need not be considered when a result is statistically significant.",
            ]
            explanation = "Interpretation must match the study design, assay validation, and evidence strength."
            answer_index = 0
        elif prompt_kind == 2:
            prompt = f"A result related to {topic.lower()} conflicts with its control. What should happen next?"
            answer = [
                "Pause interpretation, investigate the control failure, and follow the validated procedure.",
                "Discard the control and report the preferred result.",
                "Repeat until a desired result appears without documenting repeats.",
                "Convert the unexpected result into a diagnosis.",
            ]
            explanation = "Control failures affect result validity and must be investigated and documented."
            answer_index = 0
        else:
            prompt = f"How should a proposed application of {topic.lower()} be evaluated?"
            answer = [
                "Check analytical validity, relevant biological evidence, safety, and the intended-use context.",
                "Assume promising early evidence is enough for routine use.",
                "Use the same threshold and interpretation for every population and platform.",
                "Skip independent review if the method is novel.",
            ]
            explanation = "Translation requires fit-for-purpose evidence, validation, and safety review."
            answer_index = 0
        items.append({
            "prompt": prompt, "options": answer, "answer_index": answer_index,
            "explanation": explanation, "topic": topic,
        })
    return items
