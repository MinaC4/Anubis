from flask import Blueprint, request
from sqlalchemy.orm import defer, undefer
from sqlalchemy.sql import or_

from anubis.lms.courses import get_student_course_ids
from anubis.models import StaticFile
from anubis.utils.auth.http import require_user
from anubis.utils.auth.user import current_user
from anubis.utils.cache import cache
from anubis.utils.http import success_response
from anubis.utils.http.decorators import json_response
from anubis.utils.http.files import make_blob_response

static = Blueprint("public-static", __name__, url_prefix="/public/static")


@static.get("/list")
@require_user()
@json_response
def public_static_list():
    course_id = request.args.get("courseId")
    course_ids = get_student_course_ids(current_user)
    if course_id:
        course_ids = [course_id] if course_id in course_ids else []
    files = (
        StaticFile.query.filter(
            StaticFile.course_id.in_(course_ids),
            StaticFile.hidden == False,
        )
        .order_by(StaticFile.created.desc())
        .options(defer(StaticFile.blob))
        .all()
    )
    return success_response({"files": [file.data for file in files]})


@static.route("/<string:path>")
@static.route("/<string:path>/<string:filename>")
@cache.memoize(timeout=60)
def public_static(path: str, filename: str = None):
    """
    Get some public static file.

    * response is possibly cached *

    :param filename:
    :param path:
    :return:
    """

    query = StaticFile.query.options(undefer(StaticFile.blob)).filter(  # undefer blob attr to avoid followup query
        or_(StaticFile.path == path, StaticFile.path == "/" + path)
    )

    # If filename was specified, then include it in the query
    if filename is not None:
        query = query.filter(StaticFile.filename == filename)

    # Execute the query
    blob = query.first()

    # If the blob is None, then 404
    if blob is None:
        return "404 Not Found :(", 404

    # Form the blob response
    return make_blob_response(blob)
