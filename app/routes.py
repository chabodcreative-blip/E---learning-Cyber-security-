import re
from datetime import datetime
from io import BytesIO
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, send_file
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func
from . import db, login_manager
from .models import User, Course, Module, Lesson, QuizQuestion, Scenario, CourseEnrollment, LessonProgress, QuizAttempt, FinalAttempt, Certificate, LearningActivity
from .forms import RegisterForm, LoginForm

bp=Blueprint('auth',__name__)

def record(action):
    db.session.add(LearningActivity(user_id=current_user.id, action=action)); db.session.commit()

def enrolled(course):
    return CourseEnrollment.query.filter_by(user_id=current_user.id,course_id=course.id).first() is not None

def course_progress(course):
    lessons=[l for m in course.modules for l in m.lessons]
    if not lessons:return 0
    done=LessonProgress.query.filter_by(user_id=current_user.id,completed=True).filter(LessonProgress.lesson_id.in_([l.id for l in lessons])).count()
    return round(done/len(lessons)*100)

@login_manager.user_loader
def load_user(user_id): return db.session.get(User,int(user_id))

@bp.route('/')
def home(): return render_template('home.html',courses=Course.query.all())

@bp.route('/register',methods=['GET','POST'])
def register():
    if current_user.is_authenticated:return redirect(url_for('auth.dashboard'))
    form=RegisterForm()
    if form.validate_on_submit():
        if User.query.filter(func.lower(User.email)==form.email.data.lower()).first(): flash('An account with that email already exists.','danger')
        else:
            u=User(full_name=form.full_name.data.strip(),email=form.email.data.lower().strip());u.set_password(form.password.data);db.session.add(u);db.session.commit();login_user(u);flash('Account created successfully.','success');return redirect(url_for('auth.dashboard'))
    return render_template('auth/register.html',form=form)

@bp.route('/login',methods=['GET','POST'])
def login():
    if current_user.is_authenticated:return redirect(url_for('auth.dashboard'))
    form=LoginForm()
    if form.validate_on_submit():
        u=User.query.filter(func.lower(User.email)==form.email.data.lower()).first()
        if u and u.check_password(form.password.data): login_user(u);return redirect(url_for('auth.dashboard'))
        flash('Invalid email or password.','danger')
    return render_template('auth/login.html',form=form)

@bp.route('/logout')
@login_required
def logout(): logout_user();flash('You have been logged out.','success');return redirect(url_for('auth.home'))


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        full_name = (request.form.get('full_name') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        current_password = request.form.get('current_password') or ''
        new_password = request.form.get('new_password') or ''
        confirm_password = request.form.get('confirm_password') or ''

        if len(full_name) < 2 or len(full_name) > 120:
            flash('Please enter a valid full name.', 'danger')
            return redirect(url_for('auth.profile'))
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            flash('Please enter a valid email address.', 'danger')
            return redirect(url_for('auth.profile'))

        other = User.query.filter(func.lower(User.email) == email, User.id != current_user.id).first()
        if other:
            flash('That email address is already in use.', 'danger')
            return redirect(url_for('auth.profile'))

        current_user.full_name = full_name
        current_user.email = email

        if new_password:
            if not current_user.check_password(current_password):
                flash('Your current password is incorrect.', 'danger')
                return redirect(url_for('auth.profile'))
            if len(new_password) < 8:
                flash('The new password must be at least 8 characters.', 'danger')
                return redirect(url_for('auth.profile'))
            if new_password != confirm_password:
                flash('The new passwords do not match.', 'danger')
                return redirect(url_for('auth.profile'))
            current_user.set_password(new_password)

        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('auth.profile'))

    student_courses = CourseEnrollment.query.filter_by(user_id=current_user.id).count()
    cert_count = Certificate.query.filter_by(user_id=current_user.id, revoked=False).count()
    activity_count = LearningActivity.query.filter_by(user_id=current_user.id).count()
    return render_template('profile.html',
                           student_courses=student_courses,
                           cert_count=cert_count,
                           activity_count=activity_count)

@bp.route('/dashboard')
@login_required
def dashboard():
    courses=Course.query.all(); certs=Certificate.query.filter_by(user_id=current_user.id,revoked=False).all(); acts=LearningActivity.query.filter_by(user_id=current_user.id).order_by(LearningActivity.created_at.desc()).limit(8).all()
    return render_template('dashboard.html',courses=courses,certs=certs,acts=acts,progress=course_progress)

@bp.route('/courses')
def courses(): return render_template('courses.html',courses=Course.query.all())

@bp.route('/course/<int:course_id>')
def course_detail(course_id):
    c=db.session.get(Course,course_id) or abort(404)
    return render_template('course.html',course=c,progress=course_progress(c) if current_user.is_authenticated else 0,enrolled=enrolled(c) if current_user.is_authenticated else False)

@bp.route('/course/<int:course_id>/enroll',methods=['POST'])
@login_required
def enroll(course_id):
    c=db.session.get(Course,course_id) or abort(404)
    if not enrolled(c):db.session.add(CourseEnrollment(user_id=current_user.id,course_id=c.id));db.session.commit();record(f'Enrolled in {c.title}')
    return redirect(url_for('auth.course_detail',course_id=c.id))

@bp.route('/lesson/<int:lesson_id>')
@login_required
def lesson(lesson_id):
    l=db.session.get(Lesson,lesson_id) or abort(404); c=l.module.course
    if not enrolled(c):flash('Enroll in the course first.','warning');return redirect(url_for('auth.course_detail',course_id=c.id))
    questions=l.questions; scenario=Scenario.query.filter_by(lesson_id=l.id).first(); prog=LessonProgress.query.filter_by(user_id=current_user.id,lesson_id=l.id).first()
    return render_template('lesson.html',lesson=l,course=c,questions=questions,scenario=scenario,prog=prog)

@bp.route('/lesson/<int:lesson_id>/quiz',methods=['POST'])
@login_required
def quiz(lesson_id):
    l=db.session.get(Lesson,lesson_id) or abort(404); qs=l.questions; score=0
    for q in qs:
        try: ans=int(request.form.get(f'q_{q.id}','-1'))
        except ValueError: ans=-1
        if ans==q.correct_index:score+=1
    total=len(qs);pct=round(score/total*100,1) if total else 0
    db.session.add(QuizAttempt(user_id=current_user.id,lesson_id=l.id,score=score,total=total,percentage=pct));db.session.commit()
    return render_template('quiz_result.html',lesson=l,score=score,total=total,percentage=pct,questions=qs,answers=request.form)

@bp.route('/lesson/<int:lesson_id>/complete',methods=['POST'])
@login_required
def complete_lesson(lesson_id):
    l=db.session.get(Lesson,lesson_id) or abort(404); c=l.module.course
    q=QuizAttempt.query.filter_by(user_id=current_user.id,lesson_id=l.id).order_by(QuizAttempt.created_at.desc()).first()
    if not q or q.percentage < 70: flash('Complete the lesson knowledge check with at least 70% before marking this lesson complete.','warning');return redirect(url_for('auth.lesson',lesson_id=l.id))
    p=LessonProgress.query.filter_by(user_id=current_user.id,lesson_id=l.id).first()
    if not p:p=LessonProgress(user_id=current_user.id,lesson_id=l.id);db.session.add(p)
    p.completed=True;p.completed_at=datetime.utcnow();db.session.commit();record(f'Completed lesson: {l.title}')
    return redirect(url_for('auth.course_detail',course_id=c.id))

@bp.route('/course/<int:course_id>/final',methods=['GET','POST'])
@login_required
def final_assessment(course_id):
    c=db.session.get(Course,course_id) or abort(404)
    if not enrolled(c):return redirect(url_for('auth.course_detail',course_id=c.id))
    lessons=[l for m in c.modules for l in m.lessons];completed=sum(bool(LessonProgress.query.filter_by(user_id=current_user.id,lesson_id=l.id,completed=True).first()) for l in lessons)
    if completed<len(lessons):flash('Complete all required lessons before the final assessment.','warning');return redirect(url_for('auth.course_detail',course_id=c.id))
    qs=[]
    for l in lessons: qs.extend(l.questions)
    qs=qs[:10]
    if request.method=='POST':
        score=sum(1 for q in qs if request.form.get(f'q_{q.id}')==str(q.correct_index));total=len(qs);pct=round(score/total*100,1) if total else 0;passed=pct>=70
        a=FinalAttempt(user_id=current_user.id,course_id=c.id,score=score,total=total,percentage=pct,passed=passed);db.session.add(a);db.session.commit()
        if passed and not Certificate.query.filter_by(user_id=current_user.id,course_id=c.id,revoked=False).first():
            count=Certificate.query.count()+1;cid=f'CSEP-{datetime.utcnow().year}-{count:06d}';db.session.add(Certificate(user_id=current_user.id,course_id=c.id,certificate_id=cid));db.session.commit()
        issued_cert=Certificate.query.filter_by(user_id=current_user.id,course_id=c.id,revoked=False).first() if passed else None
        return render_template('final_result.html',course=c,score=score,total=total,percentage=pct,passed=passed,issued_cert=issued_cert)
    return render_template('final.html',course=c,questions=qs)

@bp.route('/certificate/<certificate_id>')
@login_required
def certificate(certificate_id):
    cert=Certificate.query.filter_by(certificate_id=certificate_id,user_id=current_user.id).first() or abort(404);course=db.session.get(Course,cert.course_id);user=db.session.get(User,cert.user_id)
    return render_template('certificate.html',cert=cert,course=course,user=user)

@bp.route('/certificate/<certificate_id>/pdf')
@login_required
def certificate_pdf(certificate_id):
    cert=Certificate.query.filter_by(certificate_id=certificate_id,user_id=current_user.id).first() or abort(404)
    course=db.session.get(Course,cert.course_id)
    user=db.session.get(User,cert.user_id)

    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.utils import ImageReader
    import qrcode

    buf=BytesIO()
    c=canvas.Canvas(buf,pagesize=landscape(A4))
    w,h=landscape(A4)

    # Professional certificate frame and restrained cybersecurity palette.
    navy=colors.HexColor('#14213D')
    blue=colors.HexColor('#3157D5')
    pale=colors.HexColor('#F4F7FF')
    ink=colors.HexColor('#172033')
    muted=colors.HexColor('#667085')

    c.setFillColor(pale); c.rect(0,0,w,h,fill=1,stroke=0)
    c.setStrokeColor(navy); c.setLineWidth(3); c.roundRect(28,28,w-56,h-56,14,fill=0,stroke=1)
    c.setStrokeColor(blue); c.setLineWidth(1); c.roundRect(40,40,w-80,h-80,10,fill=0,stroke=1)

    # Decorative corner marks.
    c.setFillColor(blue)
    for x,y in [(58,h-70),(w-58,h-70),(58,58),(w-58,58)]:
        c.circle(x,y,5,fill=1,stroke=0)

    c.setFillColor(blue); c.setFont('Helvetica-Bold',11)
    c.drawCentredString(w/2,h-78,'CS CYBERSAFE LEARN')
    c.setFillColor(navy); c.setFont('Helvetica-Bold',30)
    c.drawCentredString(w/2,h-125,'CERTIFICATE OF COMPLETION')
    c.setFillColor(muted); c.setFont('Helvetica',12)
    c.drawCentredString(w/2,h-153,'This certificate is proudly presented to')

    c.setFillColor(ink); c.setFont('Helvetica-Bold',25)
    c.drawCentredString(w/2,h-205,user.full_name)
    c.setStrokeColor(blue); c.setLineWidth(1)
    c.line(w/2-160,h-215,w/2+160,h-215)

    c.setFillColor(muted); c.setFont('Helvetica',12)
    c.drawCentredString(w/2,h-250,'for successfully completing the course')
    c.setFillColor(navy); c.setFont('Helvetica-Bold',18)
    c.drawCentredString(w/2,h-280,course.title)

    c.setFillColor(ink); c.setFont('Helvetica',10)
    c.drawString(70,75,f'Certificate ID: {cert.certificate_id}')
    c.drawString(70,58,f'Issued: {cert.issued_at.strftime("%d %B %Y")}')
    c.setFillColor(muted)
    c.drawString(w-255,75,'Verify this certificate using the QR code')

    verification_url=url_for('auth.verify_certificate',certificate_id=cert.certificate_id,_external=True)
    qr=qrcode.make(verification_url)
    qbuf=BytesIO(); qr.save(qbuf,format='PNG'); qbuf.seek(0)
    c.drawImage(ImageReader(qbuf),w-150,48,width=78,height=78,mask='auto')

    c.setFillColor(muted); c.setFont('Helvetica-Oblique',9)
    c.drawCentredString(w/2,42,'Educational certificate issued by CS CyberSafe Learn.')

    c.save(); buf.seek(0)
    return send_file(buf,as_attachment=True,
                     download_name=f'{cert.certificate_id}.pdf',
                     mimetype='application/pdf')

@bp.route('/verify/<certificate_id>')
def verify_certificate(certificate_id):
    cert=Certificate.query.filter_by(certificate_id=certificate_id,revoked=False).first()
    if not cert:return render_template('verify.html',valid=False,certificate_id=certificate_id)
    user=db.session.get(User,cert.user_id);course=db.session.get(Course,cert.course_id)
    return render_template('verify.html',valid=True,certificate_id=certificate_id,user=user,course=course,cert=cert)


# Admin

def admin_required():
    if not current_user.is_authenticated or current_user.role!='admin': abort(403)

@bp.route('/admin')
@login_required
def admin_dashboard():
    admin_required();return render_template('admin/dashboard.html',courses=Course.query.count(),students=User.query.filter_by(role='student').count(),certs=Certificate.query.count(),attempts=FinalAttempt.query.count())

@bp.route('/admin/courses')
@login_required
def admin_courses():
    admin_required();return render_template('admin/courses.html',courses=Course.query.all())

@bp.route('/admin/courses/<int:course_id>/delete',methods=['POST'])
@login_required
def admin_delete_course(course_id):
    admin_required();c=db.session.get(Course,course_id) or abort(404);db.session.delete(c);db.session.commit();flash('Course deleted.','success');return redirect(url_for('auth.admin_courses'))

@bp.route('/admin/students')
@login_required
def admin_students():
    admin_required();return render_template('admin/students.html',students=User.query.filter_by(role='student').order_by(User.created_at.desc()).all())

@bp.route('/admin/results')
@login_required
def admin_results():
    admin_required();rows=FinalAttempt.query.order_by(FinalAttempt.created_at.desc()).all();return render_template('admin/results.html',rows=rows)
