import re
import pdfplumber
import spacy
from flask import Flask, render_template, request

app = Flask(__name__)

def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text()
    return text

def extract_info_from_text(text):
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(text)
    info = {
        'name': None,
        'email': None,
        'phone': None,
        'skills': [],
        'experience': []
    }
    
    # Extrair o nome
    for ent in doc.ents:
        if ent.label_ == 'PERSON':
            info['name'] = ent.text
            break
    
    # Extrair e-mail
    for token in doc:
        if token.like_email:
            info['email'] = token.text
    
    # Extrair número de telefone usando expressão regular no texto completo
    phone_pattern = r'\(?\d{2}\)?[-.\s]?\d{4,5}[-.\s]?\d{4}'
    phone_numbers = re.findall(phone_pattern, text)
    if phone_numbers:
        info['phone'] = phone_numbers[0]
    
    # Extrair habilidades e experiência
    skills_keywords = ['Python', 'Java', 'C++', 'Machine Learning', 'Data Analysis']
    experience_keywords = ['experience', 'worked', 'developed', 'managed']
    
    for sentence in doc.sents:
        for keyword in skills_keywords:
            if keyword.lower() in sentence.text.lower():
                info['skills'].append(keyword)
        for keyword in experience_keywords:
            if keyword.lower() in sentence.text.lower():
                info['experience'].append(sentence.text)

    return info

def compare_with_job_requirements(candidate_info, job_requirements):
    match = {
        'skills_match': [],
        'missing_skills': [],
        'experience_match': [],
        'missing_experience': []
    }
    
    for skill in job_requirements['skills']:
        if skill in candidate_info['skills']:
            match['skills_match'].append(skill)
        else:
            match['missing_skills'].append(skill)
    
    for exp in job_requirements['experience']:
        if any(exp.lower() in e.lower() for e in candidate_info['experience']):
            match['experience_match'].append(exp)
        else:
            match['missing_experience'].append(exp)
    
    return match

@app.route('/')
def home():
    return '''
    <form action="/upload" method="post" enctype="multipart/form-data">
        <input type="file" name="file">
        <input type="submit" value="Upload">
    </form>
    '''

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file:
        file.save(file.filename)
        text = extract_text_from_pdf(file.filename)
        candidate_info = extract_info_from_text(text)
        
        job_requirements = {
            'skills': ['Python', 'Machine Learning', 'Data Analysis'],
            'experience': ['developed', 'managed']
        }
        
        match_result = compare_with_job_requirements(candidate_info, job_requirements)
        
        return render_template('result.html', candidate_info=candidate_info, match_result=match_result)

if __name__ == '__main__':
    app.run(debug=True)
