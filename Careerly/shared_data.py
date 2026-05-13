"""
shared_data.py - shared constants used across multiple modules.
Keeps INTEREST_SPREAD separate to avoid circular imports between careerly.py and job_page.py.
"""

INTEREST_SPREAD = {
    "Numbers": {
        'Financial Analyst': 39.2, 'Corporate Investment Banker': 33.1, 'Tax Advisor': 30.4,
        'Supply Chain Manager': 14.8, 'Marketing Manager': 14.5, 'Product Manager': 13.2,
        'Entrepreneur': 13.0, 'Business Consultant': 12.2, 'Brand Manager': 7.5,
        'Strategic Planning Manager': 3.9, 'Human Resources Manager': 2.4,
        'Data Analyst': 1.5, 'ICT Application Developer': 1.4,
    },
    "Creativity": {
        'Brand Manager': 26.4, 'Marketing Manager': 10.5, 'Product Manager': 7.9,
        'ICT Application Developer': 7.2, 'Data Analyst': 4.9, 'Entrepreneur': 4.1,
        'Supply Chain Manager': 1.1, 'Financial Analyst': 1.7,
    },
    "People": {
        'Human Resources Manager': 19.7, 'Corporate Lawyer': 19.0, 'Brand Manager': 15.1,
        'Product Manager': 13.2, 'Marketing Manager': 10.5, 'Supply Chain Manager': 10.2,
        'Business Consultant': 7.8, 'Tax Advisor': 7.1, 'Data Analyst': 2.4,
        'Corporate Investment Banker': 2.3, 'Entrepreneur': 4.1,
        'ICT Application Developer': 1.4, 'Strategic Planning Manager': 0.8, 'Financial Analyst': 0.8,
    },
    "Languages": {
        'Data Analyst': 1.9, 'ICT Application Developer': 1.4, 'Marketing Manager': 1.3,
        'Entrepreneur': 0.8, 'Human Resources Manager': 0.8, 'Strategic Planning Manager': 0.8,
        'Corporate Investment Banker': 0.8,
    },
    "Writing": {
        'Marketing Manager': 2.6, 'Product Manager': 1.8, 'Tax Advisor': 1.8,
        'Corporate Investment Banker': 1.5, 'ICT Application Developer': 1.4,
        'Supply Chain Manager': 1.1, 'Data Analyst': 1.0, 'Brand Manager': 0.9,
        'Entrepreneur': 0.8, 'Human Resources Manager': 0.8,
    },
    "Technology": {
        'ICT Application Developer': 55.1, 'Data Analyst': 9.2, 'Supply Chain Manager': 4.5,
        'Financial Analyst': 2.5, 'Brand Manager': 1.9,
        'Entrepreneur': 1.6, 'Human Resources Manager': 0.8, 'Strategic Planning Manager': 0.8,
    },
    "Detail & Precision": {
        'Supply Chain Manager': 11.4, 'Corporate Investment Banker': 9.8, 'Data Analyst': 8.3,
        'Product Manager': 5.3, 'Human Resources Manager': 5.5, 'Strategic Planning Manager': 4.7,
        'Entrepreneur': 4.9, 'ICT Application Developer': 4.3, 'Tax Advisor': 1.8,
        'Business Consultant': 1.7, 'Marketing Manager': 1.3,
    },
    "Leadership": {
        'Strategic Planning Manager': 12.4, 'Business Consultant': 11.3, 'Supply Chain Manager': 9.1,
        'Entrepreneur': 4.9, 'Human Resources Manager': 5.5, 'Financial Analyst': 3.3,
        'ICT Application Developer': 2.9, 'Corporate Lawyer': 2.4, 'Corporate Investment Banker': 1.5,
        'Brand Manager': 0.9,
    },
    "Problem Solving": {
        'Supply Chain Manager': 8.0, 'Business Consultant': 7.8, 'Human Resources Manager': 7.1,
        'Corporate Lawyer': 6.0, 'ICT Application Developer': 5.8, 'Entrepreneur': 5.7,
        'Marketing Manager': 5.9, 'Financial Analyst': 4.2, 'Data Analyst': 4.4,
        'Strategic Planning Manager': 4.7, 'Brand Manager': 2.8, 'Product Manager': 1.8,
        'Corporate Investment Banker': 1.5, 'Tax Advisor': 0.0,
    },
    "Research": {
        'Marketing Manager': 7.9, 'Product Manager': 7.9, 'Financial Analyst': 4.2,
        'Tax Advisor': 3.6, 'Brand Manager': 3.8, 'Data Analyst': 2.9,
        'Strategic Planning Manager': 1.6, 'ICT Application Developer': 1.4, 'Entrepreneur': 0.8,
    },
    "Law & Justice": {
        'Corporate Lawyer': 47.6, 'Tax Advisor': 25.0, 'Human Resources Manager': 15.0,
        'Strategic Planning Manager': 3.1, 'Business Consultant': 0.9, 'Product Manager': 0.9,
        'Entrepreneur': 1.6, 'Financial Analyst': 0.8,
    },
    "International": {
        'Product Manager': 3.5, 'Marketing Manager': 3.9, 'Tax Advisor': 3.6,
        'Strategic Planning Manager': 2.3, 'Brand Manager': 1.9, 'Entrepreneur': 0.8,
        'Supply Chain Manager': 1.1, 'Business Consultant': 0.9, 'Financial Analyst': 0.8,
    },
    "Entrepreneurship": {
        'Entrepreneur': 3.3, 'Corporate Investment Banker': 1.5, 'Business Consultant': 1.7,
        'Marketing Manager': 1.3,
    },
    "Strategy": {
        'Strategic Planning Manager': 30.2, 'Marketing Manager': 14.5, 'Business Consultant': 12.2,
        'Brand Manager': 13.2, 'Product Manager': 8.8, 'Human Resources Manager': 8.7,
        'Tax Advisor': 5.4, 'Financial Analyst': 3.3, 'Entrepreneur': 3.3,
        'Supply Chain Manager': 2.3, 'Data Analyst': 0.5,
    },
    "Sustainability": {
        'Entrepreneur': 11.4, 'Strategic Planning Manager': 4.7, 'Supply Chain Manager': 4.5,
        'Data Analyst': 1.5, 'ICT Application Developer': 1.4, 'Corporate Investment Banker': 0.8,
        'Business Consultant': 0.9,
    },
    "Communication": {
        'Strategic Planning Manager': 6.2, 'Brand Manager': 5.7, 'Entrepreneur': 3.3,
        'Marketing Manager': 3.9, 'Data Analyst': 1.9, 'Human Resources Manager': 3.1,
        'Product Manager': 2.6, 'Supply Chain Manager': 2.3, 'Corporate Lawyer': 2.4,
    },
    "Mathematics": {
        'Business Consultant': 1.7, 'Brand Manager': 0.9,
    },
    "Culture": {
        'Entrepreneur': 13.0, 'Brand Manager': 5.7, 'Marketing Manager': 4.6,
        'Strategic Planning Manager': 3.9, 'Human Resources Manager': 3.1,
        'Supply Chain Manager': 3.4, 'Product Manager': 1.8, 'Business Consultant': 2.6,
    },
    "Organisation": {
        'Business Consultant': 20.0, 'Strategic Planning Manager': 17.8,
        'Human Resources Manager': 15.7, 'Supply Chain Manager': 14.8, 'Entrepreneur': 13.0,
        'Tax Advisor': 12.5, 'Financial Analyst': 7.5, 'Corporate Investment Banker': 6.0,
        'Data Analyst': 5.8, 'Product Manager': 6.1, 'Marketing Manager': 6.6, 'Brand Manager': 3.8,
    },
    "Innovation": {
        'Entrepreneur': 2.4, 'Product Manager': 1.8, 'Brand Manager': 1.9,
        'ICT Application Developer': 1.4, 'Data Analyst': 0.5,
    },
    "Data": {
        'Data Analyst': 41.3, 'Financial Analyst': 8.3, 'Product Manager': 3.5,
        'Marketing Manager': 2.6, 'Entrepreneur': 2.4, 'Supply Chain Manager': 1.1,
        'Business Consultant': 0.9, 'Brand Manager': 0.9, 'Corporate Investment Banker': 0.8,
    },
    "Finance": {
        'Corporate Investment Banker': 31.6, 'Financial Analyst': 10.8, 'Tax Advisor': 5.4,
        'Product Manager': 5.3, 'Business Consultant': 3.5, 'Brand Manager': 1.9,
        'Supply Chain Manager': 1.1, 'Entrepreneur': 1.6, 'Marketing Manager': 1.3,
    },
    "Design": {
        'ICT Application Developer': 13.0, 'Product Manager': 8.8, 'Data Analyst': 3.4,
        'Entrepreneur': 3.3, 'Human Resources Manager': 2.4, 'Brand Manager': 1.9,
        'Financial Analyst': 1.7, 'Supply Chain Manager': 1.1, 'Strategic Planning Manager': 0.8,
    },
    "Negotiation": {
        'Supply Chain Manager': 4.5, 'Corporate Lawyer': 3.6, 'Financial Analyst': 2.5,
        'Business Consultant': 2.6, 'Human Resources Manager': 2.4, 'Tax Advisor': 1.8,
        'Corporate Investment Banker': 1.5, 'Data Analyst': 1.0, 'Strategic Planning Manager': 0.8,
    },
}

