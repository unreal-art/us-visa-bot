# Create security questions configuration file
security_questions_json = '''{
    "security_answers": {
        "What is your mother's maiden name?": "YourMothersMaidenName",
        "What was the name of your first pet?": "YourFirstPetName", 
        "What city were you born in?": "YourBirthCity",
        "What is the name of your elementary school?": "YourElementarySchool",
        "What street did you grow up on?": "YourChildhoodStreet",
        "What is your father's middle name?": "YourFathersMiddleName",
        "What was your childhood nickname?": "YourChildhoodNickname",
        "What is the name of the company where you had your first job?": "YourFirstJobCompany",
        "What was the make of your first car?": "YourFirstCarMake",
        "What is your favorite book?": "YourFavoriteBook"
    },
    "instructions": {
        "setup": "Replace the values above with your actual security question answers",
        "encryption": "These answers will be encrypted when stored",
        "usage": "The system will automatically match questions and provide answers during booking"
    }
}'''

with open('security_questions.json', 'w') as f:
    f.write(security_questions_json)

print("✅ Created security_questions.json")