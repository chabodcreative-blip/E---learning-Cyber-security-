# CS CyberSafe Learn

CS CyberSafe Learn is a focused cyber-safety e-learning platform aligned to the written project specification.

## Learning scope

The learner experience is organised around the project's 12 cyber-safety topics:

1. Introduction to Cyber Safety
2. Cybercrime
3. Phishing
4. Online Scams
5. Password Security
6. Social Media Safety
7. Personal Information Protection
8. Malware Awareness
9. Safe Internet Browsing
10. Email Security
11. Cyberbullying
12. Two-Factor Authentication

Each topic contains a focused lesson, an instructional visual, topic-specific examples, a knowledge check, automatic scoring and progress tracking.

## Admin scope

Administrators can:
- review learner accounts and activate/deactivate them;
- manage lesson content and topic assignments;
- manage knowledge-check questions and answers;
- review learner knowledge-check results;
- view curriculum counts from the dashboard.

### Learner progression and certificates
Each lesson now saves a percentage-based progress checkpoint while the learner studies. The checkpoint is stored per learner and lesson, displayed on topic and dashboard pages, and can be resumed from the saved point. A lesson remains incomplete until its existing 70% knowledge-check requirement is met.

Learners who complete every lesson receive a certificate record with a unique certificate number and issue date. The certificate is available from the learner dashboard/profile and can be viewed in the browser or downloaded as a PDF. Administrators can see whether a learner's certificate has been issued.

## Run

Install dependencies from `requirements.txt`, then run:

```bash
python run.py
```

Default development credentials are controlled by environment variables. If none are supplied, the seed creates:
- Admin: `admin@cybersafe.local` / `Admin@12345`
- Demo learner: `student@cybersafe.local` / `Student@12345`

Change these values for any real deployment.


### Student profile pictures
Learners can upload or change a profile picture from their Profile page. Authorized administrators can view the picture from the learner list and learner detail page.

### Learning flow and visual lessons
The learner flow is intentionally sequential: topic overview → detailed lesson material → practical scenario and visual demonstration → separate knowledge check → automatic result → completion/progress update. The knowledge check is never displayed beside the teaching material.

The restricted administrator sign-in is available directly at `/admin/login`. It is intentionally kept separate from the learner-facing navigation.
