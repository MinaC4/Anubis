from flask import Blueprint, request

from anubis.lms.lectures import get_lecture_notes
from anubis.lms.courses import get_student_course_ids
from anubis.models import LectureNotes, LectureProgress, db
from anubis.utils.auth.http import require_user
from anubis.utils.auth.user import current_user
from anubis.utils.data import req_assert
from anubis.utils.http import success_response
from anubis.utils.http.decorators import json_endpoint, json_response

lectures_ = Blueprint("public-lectures", __name__, url_prefix="/public/lectures")


@lectures_.get("/list")
@require_user()
@json_response
def public_static_lectures_list():
    """
    list all lecture notes for the course

    /public/lectures/list

    :return:
    """

    # Get optional class filter from get query
    course_id = request.args.get("courseId", default=None)

    # Get all public static files within this course
    lectures_data = get_lecture_notes(current_user.id, course_id)
    progress = LectureProgress.query.filter(
        LectureProgress.owner_id == current_user.id,
        LectureProgress.lecture_id.in_([lecture["id"] for lecture in lectures_data]),
    ).all() if lectures_data else []
    completed_ids = {item.lecture_id for item in progress}
    for lecture in lectures_data or []:
        lecture["completed"] = lecture["id"] in completed_ids

    # Pass back the list of files
    return success_response({"lectures": lectures_data})


@lectures_.post("/progress/<string:lecture_id>")
@require_user()
@json_endpoint(required_fields=[("completed", bool)])
def public_lecture_progress(lecture_id: str, completed: bool):
    course_ids = get_student_course_ids(current_user)
    lecture = LectureNotes.query.filter(
        LectureNotes.id == lecture_id,
        LectureNotes.course_id.in_(course_ids),
        LectureNotes.hidden == False,
    ).first()
    req_assert(lecture is not None, message="Lecture not found")

    progress = LectureProgress.query.filter_by(owner_id=current_user.id, lecture_id=lecture.id).first()
    if completed and progress is None:
        db.session.add(LectureProgress(owner_id=current_user.id, lecture_id=lecture.id))
    elif not completed and progress is not None:
        db.session.delete(progress)
    db.session.commit()
    return success_response({"completed": completed})
