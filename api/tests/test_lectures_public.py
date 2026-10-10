import io
from uuid import uuid4

import requests
from utils import Session


def test_lectures_public():
    # upload a lecture as a superuser
    logo = open("logo.png", "rb").read()
    filename = "logo.png"
    su = Session("superuser")
    logo_file = io.BytesIO(logo)
    title = f"progress-{uuid4()}"
    su.post(
        "/admin/lectures/upload",
        params={"number": 1, "title": title, "description": "description"},
        files={filename: logo_file},
    )

    student = Session("student")
    lectures = student.get('/public/lectures/list', params={'courseId': student.course_id})['lectures']
    lecture = next(item for item in lectures if item['title'] == title)
    assert lecture['completed'] is False

    student.post_json(f"/public/lectures/progress/{lecture['id']}", json={'completed': True})
    lectures = student.get('/public/lectures/list', params={'courseId': student.course_id})['lectures']
    assert next(item for item in lectures if item['id'] == lecture['id'])['completed'] is True

    another_student = Session('student', new=True)
    other_lectures = another_student.get('/public/lectures/list', params={'courseId': student.course_id})['lectures']
    assert next(item for item in other_lectures if item['id'] == lecture['id'])['completed'] is False

    student.post_json(f"/public/lectures/progress/{lecture['id']}", json={'completed': False})
    lectures = student.get('/public/lectures/list', params={'courseId': student.course_id})['lectures']
    assert next(item for item in lectures if item['id'] == lecture['id'])['completed'] is False

    outsider = Session('student', new=True, add_to_os=False)
    outsider.post_json(f"/public/lectures/progress/{lecture['id']}", json={'completed': True}, should_fail=True)
